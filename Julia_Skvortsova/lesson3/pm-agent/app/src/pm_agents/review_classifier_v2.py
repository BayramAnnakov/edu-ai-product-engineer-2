"""
Review Classifier Agent V2 - Using TracingProcessor for automatic Langfuse integration
"""
import asyncio
import csv
import uuid
import structlog
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from agents import Agent, Runner, function_tool

# Load environment variables from .env file
load_dotenv()

# Set up Langfuse tracing automatically
from langfuse_tracing import setup_langfuse_tracing
setup_langfuse_tracing()

from db.review_service import create_review_service
from db.models import ReviewCategory
from prompts import format_prompt, ReviewClassifierPrompts
from schemas import (
    SingleReviewClassification, 
    ReviewClassificationBatch,
    get_single_review_schema_formatted,
    get_batch_review_schema_formatted
)
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


class ReviewClassifierAgentV2:
    """Agent that classifies reviews with automatic Langfuse tracing"""
    
    def __init__(self):
        # Standard Runner - tracing is handled by TracingProcessor
        self.runner = Runner()
        self.db_service = None
        
        # Create the classifier agent
        self.agent = Agent(
            name="ReviewClassifier",
            instructions=format_prompt(
                ReviewClassifierPrompts.INSTRUCTIONS,
                classification_schema=get_single_review_schema_formatted()
            ),
            model="gpt-4.1-nano-2025-04-14",
            tools=[read_reviews_csv]
        )
        
        logger.info("ReviewClassifier V2 agent initialized with automatic tracing", 
                   agent_name=self.agent.name,
                   tools_count=len(self.agent.tools))
    
    async def _ensure_db_service(self):
        """Ensure database service is initialized"""
        if not self.db_service:
            self.db_service = await create_review_service()
    
    def _parse_agent_json_output(self, output: str) -> dict:
        """Parse agent JSON output, handling potential formatting issues"""
        try:
            return json.loads(output)
        except json.JSONDecodeError:
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
        
        try:
            # Create workflow run
            workflow_run = await self.db_service.create_workflow_run(
                input_text=f"Classify reviews from {file_path}",
                langfuse_trace_id=langfuse_trace_id,
                metadata={"source_file": file_path, "store_in_db": store_in_db}
            )
            
            logger.info("Created workflow run for classification",
                       run_id=str(workflow_run.id),
                       file_path=file_path)
            
            # Run agent classification - tracing happens automatically!
            prompt = format_prompt(
                ReviewClassifierPrompts.WORKFLOW,
                file_path=file_path,
                workflow_run_id=workflow_run.id,
                batch_classification_schema=get_batch_review_schema_formatted()
            )

            logger.info("Starting agent classification (with automatic tracing)", 
                       workflow_run_id=str(workflow_run.id),
                       file_path=file_path)
            
            # No manual tracing needed - TracingProcessor handles it
            result = await self.runner.run(self.agent, prompt)
            final_output = result.final_output if hasattr(result, 'final_output') else str(result)
            
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
                logger.exception("Failed to parse agent JSON output")
                validated_output = {"error": "JSON parsing failed", "raw_output": str(final_output)}
            
            # Complete workflow run
            await self.db_service.complete_workflow_run(
                workflow_run.id,
                result_text=str(final_output),
                status="completed"
            )
            
            # Get stats
            stats = await self.db_service.get_classification_stats()
            
            logger.info("Classification workflow completed",
                       workflow_run_id=str(workflow_run.id))
            
            reviews_processed = (
                len(validated_output.get('reviews', [])) 
                if 'reviews' in validated_output 
                else stats.get('total_reviews', 0)
            )
            
            return {
                "workflow_run_id": str(workflow_run.id),
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
                category_str = review_data['category']
                category_enum = ReviewCategory(category_str.lower())
                
                await self.db_service.store_review_classification(
                    run_id=workflow_run_id,
                    text=review_data['text'],
                    category=category_enum,
                    confidence=review_data['confidence'],
                    source='csv',
                    original_id=review_data.get('id')
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
            
            # No manual tracing needed - TracingProcessor handles it
            result = await self.runner.run(self.agent, prompt)
            final_output = result.final_output if hasattr(result, 'final_output') else str(result)
            
            return {
                'id': review_id,
                'text': review_text,
                'classification': str(final_output),
                'timestamp': asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            logger.exception("Single review classification failed", review_id=review_id)
            raise