"""
Traditional PM Analytics Agent using Docker-based code execution.

This demonstrates how LLMs can generate and execute analytics code
with proper Docker sandboxing for product metrics analysis.
"""

from dotenv import load_dotenv
load_dotenv()

import os
import subprocess
import tempfile
import shutil
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import asyncio
import pandas as pd
import numpy as np
from openai import OpenAI

# Fixed output directory for charts generated in the container
OUTPUT_DIR = "sandbox_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@dataclass
class AnalyticsResult:
    """Result from analytics code execution"""
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    code: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    files_created: List[str] = None

class DockerTool:
    """Docker execution tool for sandboxed code execution"""
    
    def __init__(self):
        self.docker_image = "pm_analytics_sandbox"
        self.output_dir = OUTPUT_DIR
        self._ensure_docker_image()
    
    def _ensure_docker_image(self):
        """Ensure Docker image exists or build it"""
        # Check if image exists
        result = subprocess.run(
            ["docker", "images", "-q", self.docker_image],
            capture_output=True,
            text=True
        )
        
        if not result.stdout.strip():
            print(f"Building Docker image: {self.docker_image}")
            self._build_docker_image()
    
    def _build_docker_image(self):
        """Build Docker image for sandbox"""
        
        # Create temporary directory for Dockerfile
        temp_dir = tempfile.mkdtemp(prefix="docker_build_")
        
        # Create requirements.txt
        requirements_content = """pandas==2.0.3
numpy==1.24.3
matplotlib==3.7.2
seaborn==0.12.2
plotly==5.15.0
scikit-learn==1.3.0
scipy==1.11.1
statsmodels==0.14.0
tabulate==0.9.0"""
        
        requirements_path = os.path.join(temp_dir, "requirements.txt")
        with open(requirements_path, "w") as f:
            f.write(requirements_content)
        
        # Create Dockerfile
        dockerfile_content = """# Dockerfile for PM Analytics Sandbox
FROM python:3.10-slim

# Copy requirements
COPY requirements.txt /app/requirements.txt

# Install required Python libraries
RUN pip install --no-cache-dir -r /app/requirements.txt

# Create non-root user for security
RUN useradd -m sandboxuser
USER sandboxuser

WORKDIR /app

# Set matplotlib to use non-interactive backend
ENV MPLBACKEND=Agg
"""
        
        dockerfile_path = os.path.join(temp_dir, "Dockerfile")
        with open(dockerfile_path, "w") as f:
            f.write(dockerfile_content)
        
        # Build image
        try:
            subprocess.run(
                ["docker", "build", "-t", self.docker_image, temp_dir],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"✅ Docker image {self.docker_image} built successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to build Docker image: {e.stderr}")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def execute_python(self, code: str, data_path: Optional[str] = None) -> str:
        """
        Executes the given Python code string inside a sandboxed Docker container.
        Returns the combined stdout/stderr output from the code execution.
        Any files saved to /app/output/ in the code will be available in the host OUTPUT_DIR.
        """
        print("\n=== Docker Tool Execution Started ===")
        print(f"Code to execute:\n{'-'*50}\n{code}\n{'-'*50}")
        
        # Write the code to a temporary file
        temp_dir = tempfile.mkdtemp(prefix="agent_code_")
        code_path = os.path.join(temp_dir, "user_code.py")
        with open(code_path, "w") as f:
            f.write(code)
        print(f"\nTemporary code file created at: {code_path}")
        
        # Form the docker run command
        container_cmd = [
            "docker", "run", "--rm",
            "--network", "none",           # no network access for security
            "--memory", "1g", "--cpus", "1",  # limit resources: 1 GB RAM, 1 CPU
            "--security-opt", "no-new-privileges",  # prevent privilege escalation
            "-v", f"{os.path.abspath(self.output_dir)}:/app/output:rw",  # mount output dir for charts
            "-v", f"{code_path}:/app/user_code.py:ro",  # mount the code file
            "-w", "/app",   # working directory inside container
        ]
        
        # Add data mount if provided
        if data_path and os.path.exists(data_path):
            container_cmd.extend(["-v", f"{os.path.abspath(data_path)}:/app/data.csv:ro"])
        
        container_cmd.extend([self.docker_image, "python3", "-u", "user_code.py"])
        
        print("\nDocker command to execute:")
        print(" ".join(container_cmd))
        
        try:
            print("\nExecuting Docker container...")
            result = subprocess.run(container_cmd, capture_output=True, text=True, timeout=60)
            print("\nDocker execution completed")
            print("\nDocker stdout:")
            print(result.stdout)
            if result.stderr:
                print("\nDocker stderr:")
                print(result.stderr)
        except subprocess.TimeoutExpired:
            print("\nDocker execution timed out!")
            # Kill the container if still running and return timeout message
            subprocess.run(["docker", "kill", f"$(docker ps -q --filter ancestor={self.docker_image})"], shell=True)
            shutil.rmtree(temp_dir, ignore_errors=True)
            return "Error: Code execution timed out."
        except Exception as e:
            error_msg = f"Error executing Docker container: {str(e)}"
            print(f"\n{error_msg}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            return error_msg
        
        # Clean up the temp code file directory
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("\nTemporary files cleaned up")
        
        # Combine stdout and stderr
        output_text = result.stdout + ("\n" + result.stderr if result.stderr else "")
        # Truncate output if very long (prevent overwhelming response)
        if len(output_text) > 10000:
            output_text = output_text[:10000] + "... [output truncated]"
        
        print("\n=== Docker Tool Execution Completed ===")
        return output_text.strip()

class ProductAnalyticsAgent:
    """
    Agent that generates and executes analytics code for PM tasks.
    Uses Docker for safe code execution in isolated environment.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.docker_tool = DockerTool()
        
    def generate_analytics_code(self, 
                               task: str, 
                               data_context: Dict[str, Any]) -> str:
        """Generate Python code for analytics task"""
        
        prompt = f"""
        You are a Product Manager's analytics assistant. Generate Python code to analyze product metrics.
        
        Task: {task}
        
        Available data context:
        {json.dumps(data_context, indent=2)}
        
        Requirements:
        1. Use pandas for data manipulation
        2. Calculate relevant metrics
        3. Save any visualizations to /app/output/ directory
        4. Print results as JSON-serializable dictionary
        5. Include clear metric names and values
        6. Add brief interpretation comments
        7. Data is available at /app/data.csv if provided
        
        Generate only executable Python code, no markdown formatting.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "You are an expert data analyst for product management."},
                {"role": "user", "content": prompt}
            ],
        )
        
        return response.choices[0].message.content
    
    def execute_code_safely(self, code: str, data_path: Optional[str] = None) -> AnalyticsResult:
        """Execute code in Docker sandbox"""
        
        try:
            # Execute in Docker
            output = self.docker_tool.execute_python(code, data_path)
            
            # Check for created files
            files_created = []
            if os.path.exists(OUTPUT_DIR):
                files_created = [f for f in os.listdir(OUTPUT_DIR) 
                               if os.path.isfile(os.path.join(OUTPUT_DIR, f))]
            
            # Try to parse JSON from output
            metrics = None
            try:
                # Look for JSON in output
                import re
                json_pattern = r'\{[^{}]*\}'
                matches = re.findall(json_pattern, output)
                if matches:
                    metrics = json.loads(matches[-1])  # Use last JSON found
            except:
                pass
            
            return AnalyticsResult(
                success=True,
                output=output,
                code=code,
                metrics=metrics,
                files_created=files_created
            )
            
        except Exception as e:
            return AnalyticsResult(
                success=False,
                error=str(e),
                code=code
            )
    
    async def analyze_product_metrics(self, 
                                     metrics_type: str,
                                     data_source: str) -> AnalyticsResult:
        """
        Analyze product metrics based on type and data source.
        
        Args:
            metrics_type: Type of metrics (retention, engagement, conversion, etc.)
            data_source: Path to data file or data description
        """
        
        # Define context based on metrics type
        contexts = {
            "retention": {
                "metrics": ["DAU", "WAU", "MAU", "retention_rate", "churn_rate"],
                "time_period": "last_30_days",
                "cohort_analysis": True
            },
            "engagement": {
                "metrics": ["session_duration", "pages_per_session", "bounce_rate", "feature_adoption"],
                "segmentation": ["user_type", "platform", "geo"]
            },
            "conversion": {
                "metrics": ["conversion_rate", "funnel_analysis", "drop_off_points"],
                "attribution": ["source", "campaign", "landing_page"]
            },
            "revenue": {
                "metrics": ["MRR", "ARR", "ARPU", "LTV", "CAC"],
                "growth_rate": True,
                "cohort_revenue": True
            }
        }
        
        context = contexts.get(metrics_type, {})
        
        # Generate analytics code
        code = self.generate_analytics_code(
            task=f"Calculate {metrics_type} metrics",
            data_context=context
        )

        print(f"Generated code:\n{code}")
        
        # Execute code
        result = self.execute_code_safely(code, data_source if os.path.exists(data_source) else None)
        
        print(f"Result:\n{result}")

        # Interpret results if successful
        if result.success and result.metrics:
            interpretation = await self.interpret_metrics(metrics_type, result.metrics)
            result.metrics['interpretation'] = interpretation
        
        return result
    
    async def interpret_metrics(self, 
                               metrics_type: str, 
                               metrics: Dict[str, Any]) -> str:
        """Use LLM to interpret metrics and provide PM insights"""
        
        prompt = f"""
        As a Product Manager, interpret these {metrics_type} metrics:
        
        {json.dumps(metrics, indent=2)}
        
        Provide:
        1. Key insights (2-3 bullet points)
        2. Potential concerns or opportunities
        3. Recommended actions
        
        Keep response concise and actionable.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "You are a senior product manager providing data-driven insights."},
                {"role": "user", "content": prompt}
            ],
        )
        
        return response.choices[0].message.content
    
    def generate_sample_data(self, data_type: str = "user_events") -> str:
        """Generate sample data for testing"""
        
        np.random.seed(42)
        
        if data_type == "user_events":
            # Generate sample user event data
            n_users = 1000
            n_events = 10000
            
            data = {
                'user_id': np.random.choice(range(1, n_users+1), n_events),
                'event_type': np.random.choice(['page_view', 'click', 'signup', 'purchase', 'churn'], n_events, p=[0.4, 0.3, 0.1, 0.15, 0.05]),
                'timestamp': pd.date_range(end=datetime.now(), periods=n_events, freq='H').tolist(),
                'session_duration': np.random.exponential(300, n_events),  # seconds
                'platform': np.random.choice(['web', 'mobile', 'desktop'], n_events, p=[0.5, 0.35, 0.15]),
                'revenue': np.where(
                    np.random.choice(['purchase'], n_events) == 'purchase',
                    np.random.gamma(2, 50, n_events),
                    0
                )
            }
            
            df = pd.DataFrame(data)
            
            # Save to temp file
            temp_path = tempfile.mktemp(suffix='.csv')
            df.to_csv(temp_path, index=False)
            
            return temp_path
        
        return ""


# Example usage
async def main():
    """Example demonstrating PM analytics agent with Docker sandboxing"""
    
    agent = ProductAnalyticsAgent()
    
    # Generate sample data
    print("📊 Generating sample user event data...")
    data_path = agent.generate_sample_data("user_events")
    
    # Analyze just engagement metrics (simplified)
    metrics_type = "engagement"
    print(f"\n{'='*50}")
    print(f"Analyzing {metrics_type.upper()} metrics...")
    print('='*50)
    
    result = await agent.analyze_product_metrics(metrics_type, data_path)
    
    if result.success:
        print(f"\n✅ Analysis successful!")
        if result.metrics:
            print(f"\nMetrics calculated:")
            for key, value in result.metrics.items():
                if key != 'interpretation':
                    print(f"  • {key}: {value}")
            
            if 'interpretation' in result.metrics:
                print(f"\n📊 PM Insights:")
                print(result.metrics['interpretation'])
        
        if result.files_created:
            print(f"\n📁 Files created in {OUTPUT_DIR}:")
            for file in result.files_created:
                print(f"  • {file}")
    else:
        print(f"\n❌ Analysis failed: {result.error}")
        print(f"\nGenerated code:\n{result.code}")
    
    # Clean up
    os.unlink(data_path)
    print(f"\n✨ Analysis complete! Check {OUTPUT_DIR}/ for any generated visualizations.")

if __name__ == "__main__":
    asyncio.run(main())