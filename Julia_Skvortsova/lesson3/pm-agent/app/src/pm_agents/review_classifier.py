"""
Review Classifier Agent - Categorizes user reviews into bug/feature/other
"""
import asyncio
import csv
import uuid
import structlog
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from agents import Agent, function_tool

# Load environment variables from .env file
load_dotenv()
from langfuse_integration import create_traced_runner
from db.review_service import create_review_service
from db.workflow_service import create_workflow_service
from db.models import ReviewCategory
from prompts import format_prompt, ReviewClassifierPrompts
from schemas import (
    SingleReviewClassification, 
    ReviewClassificationBatch,
    get_single_review_schema_formatted,
    get_batch_review_schema_formatted
)
from src.config import settings
import json

logger = structlog.get_logger()

# Tools for the classifier agent
@function_tool
def read_reviews_csv(file_path: str) -> str:
    """Read reviews from a CSV file and return them as formatted text"""
    try:
        reviews = []
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, 1):
                review_id = row.get('id', str(i))
                text = row.get('text', row.get('review', ''))
                reviews.append(f"ID:{review_id} - {text}")
        
        return f"Found {len(reviews)} reviews:\n" + "\n".join(reviews)
    except Exception as e:
        return f"Error reading reviews: {str(e)}"



class ReviewClassifierAgent:
    """Agent that classifies reviews into bug/feature/other categories"""
    
    def __init__(self):
        self.runner = create_traced_runner()
        self.db_service = None  # Will be initialized async
        self.workflow_service = None  # Will be initialized async
        
        # Create the classifier agent with single review schema for instructions
        # The agent processes one review at a time, so single schema is appropriate
        self.agent = Agent(
            name="ReviewClassifier",
            instructions=format_prompt(
                ReviewClassifierPrompts.INSTRUCTIONS,
                classification_schema=get_single_review_schema_formatted()
            ),
            model=settings.models.review_classifier,
            tools=[read_reviews_csv]
        )
        
        logger.info("ReviewClassifier agent initialized", 
                   agent_name=self.agent.name,
                   tools_count=len(self.agent.tools))
    
    async def _ensure_db_service(self):
        """Ensure database services are initialized"""
        if not self.db_service:
            self.db_service = await create_review_service()
        if not self.workflow_service:
            self.workflow_service = await create_workflow_service()
    
    def _parse_agent_json_output(self, output: str) -> dict:
        """Parse agent JSON output, handling potential formatting issues"""
        try:
            # Try to parse as-is first
            return json.loads(output)
        except json.JSONDecodeError:
            # Try to extract JSON from text (in case there's extra text)
            import re
            json_match = re.search(r'\{.*\}', output, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise ValueError(f"No valid JSON found in agent output: {output[:200]}...")
    
    def _validate_classification_output(self, parsed_json: dict, is_batch: bool = False) -> dict:
        """Validate agent output against Pydantic schemas"""
        try:
            if is_batch:
                # Handle case where agent returns a list instead of object with "reviews" key
                if isinstance(parsed_json, list):
                    # Calculate summary statistics
                    total = len(parsed_json)
                    bug_count = sum(1 for r in parsed_json if r.get('category', '').lower() == 'bug')
                    feature_count = sum(1 for r in parsed_json if r.get('category', '').lower() == 'feature')
                    other_count = sum(1 for r in parsed_json if r.get('category', '').lower() == 'other')
                    avg_confidence = sum(r.get('confidence', 0) for r in parsed_json) / total if total > 0 else 0
                    
                    # Wrap in expected format
                    parsed_json = {
                        "reviews": parsed_json,
                        "summary": {
                            "total_reviews": total,
                            "bug_count": bug_count,
                            "feature_count": feature_count,
                            "other_count": other_count,
                            "average_confidence": avg_confidence
                        }
                    }
                
                validated = ReviewClassificationBatch(**parsed_json)
                return validated.model_dump()
            else:
                validated = SingleReviewClassification(**parsed_json)
                return validated.model_dump()
        except Exception as e:
            logger.error("Schema validation failed", 
                        error=str(e),
                        json_data=parsed_json)
            raise
    
    async def classify_reviews_file_with_storage(
        self, 
        file_path: str,
        store_in_db: bool = True,
        langfuse_trace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Classify reviews from file and store in PostgreSQL"""
        await self._ensure_db_service()
        
        # Generate trace ID upfront if not provided
        # This ensures we always have a trace ID to store
        if not langfuse_trace_id:
            langfuse_trace_id = str(uuid.uuid4())
        
        try:
            # Create workflow run with the trace ID
            workflow_run = await self.workflow_service.create_workflow_run(
                input_text=f"Classify reviews from {file_path}",
                langfuse_trace_id=langfuse_trace_id,  # Now always has a valid ID
                metadata={"source_file": file_path, "store_in_db": store_in_db}
            )
            
            logger.info("Created workflow run for classification",
                       run_id=str(workflow_run.id),
                       file_path=file_path)
            
            # Agent will read from CSV directly using its tools
            # Run agent classification using prompt template with schema
            prompt = format_prompt(
                ReviewClassifierPrompts.WORKFLOW,
                file_path=file_path,
                workflow_run_id=workflow_run.id,
                batch_classification_schema=get_batch_review_schema_formatted()
            )

            logger.info("Starting agent classification", 
                       workflow_run_id=str(workflow_run.id),
                       file_path=file_path,
                       langfuse_trace_id=langfuse_trace_id)
            
            # Pass trace ID to the runner so Langfuse uses our ID
            result = await self.runner.run(self.agent, prompt, trace_id=langfuse_trace_id)
            final_output = result.final_output if hasattr(result, 'final_output') else str(result)
            
            # Get the actual trace ID used (in case it was different)
            actual_trace_id = self.runner.get_last_trace_id() or langfuse_trace_id
            
            # Parse and validate JSON output
            try:
                parsed_json = self._parse_agent_json_output(str(final_output))
                validated_output = self._validate_classification_output(parsed_json, is_batch=True)
                
                logger.info("Agent output parsed and validated",
                           reviews_classified=len(validated_output.get('reviews', [])))
                
                # Store in database if requested
                if store_in_db:
                    await self._store_structured_classifications(
                        validated_output, workflow_run.id
                    )
                    
            except Exception as e:
                logger.exception("Failed to parse agent JSON output, no database storage")
                # When JSON parsing fails, we cannot store structured data in DB
                # The agent output is still available in the raw format
                validated_output = {"error": "JSON parsing failed", "raw_output": str(final_output)}
            
            # Complete workflow run
            await self.workflow_service.complete_workflow_run(
                workflow_run.id,
                result_text=str(final_output),
                status="completed"
            )
            
            # Get stats
            stats = await self.db_service.get_classification_stats()
            
            logger.info("Classification workflow completed",
                       workflow_run_id=str(workflow_run.id))
            
            # Count reviews from validated output if available, otherwise from stats
            reviews_processed = (
                len(validated_output.get('reviews', [])) 
                if 'reviews' in validated_output 
                else stats.get('total_reviews', 0)
            )
            
            return {
                "workflow_run_id": str(workflow_run.id),
                "langfuse_trace_id": actual_trace_id,  # Return the actual trace ID
                "agent_output": str(final_output),
                "reviews_processed": reviews_processed,
                "stats": stats,
                "stored_in_db": store_in_db
            }
            
        except Exception as e:
            logger.exception("Classification workflow failed", file_path=file_path)
            raise
    
    async def _store_structured_classifications(
        self,
        validated_output: dict,
        workflow_run_id: uuid.UUID
    ):
        """Store structured JSON output in database"""
        try:
            reviews = validated_output.get('reviews', [])
            
            for review_data in reviews:
                # Handle both string and enum categories
                category = review_data['category']
                if isinstance(category, str):
                    category_enum = ReviewCategory(category.lower())
                else:
                    # Already an enum from Pydantic validation
                    category_enum = category
                
                await self.db_service.store_review_classification(
                    run_id=workflow_run_id,
                    text=review_data['text'],
                    category=category_enum,
                    confidence=review_data['confidence'],
                    source='csv',
                    original_id=review_data.get('id')  # Store the original CSV review ID
                )
            
            logger.info("Stored structured classifications in database",
                       workflow_run_id=str(workflow_run_id),
                       count=len(reviews))
            
        except Exception as e:
            logger.exception("Failed to store structured classifications",
                           workflow_run_id=str(workflow_run_id))
            raise

    
    async def classify_single_text(self, review_text: str, review_id: str = "single") -> Dict[str, Any]:
        """Classify a single review text"""
        try:
            prompt = format_prompt(
                ReviewClassifierPrompts.SINGLE_REVIEW,
                review_id=review_id,
                review_text=review_text,
                single_classification_schema=get_single_review_schema_formatted()
            )
            
            result = await self.runner.run(self.agent, prompt)
            final_output = result.final_output if hasattr(result, 'final_output') else str(result)
            
            # Parse the result (simplified - in practice you'd use structured output)
            return {
                'id': review_id,
                'text': review_text,
                'classification': str(final_output),
                'timestamp': asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            logger.exception("Single review classification failed", review_id=review_id)
            raise

# Convenience functions
async def classify_reviews(file_path: str, store_in_db: bool = True) -> Dict[str, Any]:
    """Classify reviews from a CSV file with database storage"""
    classifier = ReviewClassifierAgent()
    return await classifier.classify_reviews_file_with_storage(file_path, store_in_db=store_in_db)

async def classify_review(text: str, review_id: str = "single") -> Dict[str, Any]:
    """Classify a single review"""
    classifier = ReviewClassifierAgent()
    return await classifier.classify_single_text(text, review_id)