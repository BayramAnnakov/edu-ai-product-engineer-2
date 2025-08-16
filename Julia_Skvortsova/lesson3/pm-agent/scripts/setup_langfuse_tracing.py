#!/usr/bin/env python3
"""
Langfuse Tracing Setup Script

This script completes the Langfuse tracing setup by sending test traces
that will change the "Setup Tracing" status from pending to completed.

Usage:
    python setup_langfuse_tracing.py
    
Or with specific keys:
    LANGFUSE_PUBLIC_KEY=pk-... LANGFUSE_SECRET_KEY=sk-... python setup_langfuse_tracing.py
"""

import os
import sys
import time
from typing import Optional

def get_langfuse_keys():
    """Get Langfuse keys from environment or prompt user"""
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY") 
    host = os.getenv("LANGFUSE_HOST", "http://localhost:3000")
    
    if not public_key or not secret_key:
        print("🔑 Langfuse keys not found in environment variables")
        print("Please get your current keys from the Langfuse UI at http://localhost:3000")
        print("(Note: Keys change each time you refresh the page)")
        print()
        
        if not public_key:
            public_key = input("Enter LANGFUSE_PUBLIC_KEY (pk-lf-...): ").strip()
        if not secret_key:
            secret_key = input("Enter LANGFUSE_SECRET_KEY (sk-lf-...): ").strip()
    
    return public_key, secret_key, host

def test_langfuse_version():
    """Test which Langfuse version we have and use appropriate API"""
    try:
        from langfuse import Langfuse
        
        # Try to detect version by testing API methods
        temp_client = Langfuse(public_key="test", secret_key="test", host="http://localhost:3000")
        
        # Test for v2 API (has .trace method)
        if hasattr(temp_client, 'trace'):
            return "v2", Langfuse
        # Test for v3 API (has .start_generation method) 
        elif hasattr(temp_client, 'start_generation'):
            return "v3", Langfuse
        else:
            return "unknown", Langfuse
            
    except ImportError:
        print("❌ Error: langfuse package not found")
        print("Install with: pip install langfuse")
        return None, None

def send_v2_traces(langfuse_client, public_key: str) -> bool:
    """Send traces using Langfuse v2 API"""
    try:
        print("📊 Using Langfuse v2 API...")
        
        # Create trace
        trace = langfuse_client.trace(
            name="langfuse_setup_completion",
            metadata={
                "purpose": "Complete Langfuse tracing setup",
                "version": "v2",
                "public_key_prefix": public_key[:15] + "..."
            }
        )
        
        # Create generation within trace
        generation = trace.generation(
            name="setup_test_generation",
            model="gpt-4.1-nano-2025-04-14",
            input={"message": "Testing Langfuse v2 tracing setup"},
            output={"response": "Langfuse v2 tracing setup completed successfully!"},
            usage={"input_tokens": 8, "output_tokens": 8, "total_tokens": 16}
        )
        
        # Create span within trace
        span = trace.span(
            name="setup_verification",
            input={"action": "verify_langfuse_connection"},
            output={"result": "success", "api_version": "v2"}
        )
        
        # End everything
        span.end()
        generation.end() 
        trace.update(output={"setup_status": "completed", "api_version": "v2"})
        
        return True
        
    except Exception as e:
        print(f"❌ V2 API failed: {e}")
        return False

def send_v3_traces(langfuse_client, public_key: str) -> bool:
    """Send traces using Langfuse v3 API"""
    try:
        print("📊 Using Langfuse v3 API...")
        
        # Create generation
        generation = langfuse_client.start_generation(
            name="langfuse_setup_completion",
            model="gpt-4.1-nano-2025-04-14"
        )
        
        generation.update(
            input={"message": "Testing Langfuse v3 tracing setup"},
            output={"response": "Langfuse v3 tracing setup completed successfully!"},
            usage={"input_tokens": 8, "output_tokens": 8, "total_tokens": 16},
            metadata={
                "purpose": "Complete Langfuse tracing setup", 
                "version": "v3",
                "public_key_prefix": public_key[:15] + "..."
            }
        )
        
        generation.end()
        
        # Create span
        span = langfuse_client.start_span(name="setup_verification")
        span.update(
            input={"action": "verify_langfuse_connection"},
            output={"result": "success", "api_version": "v3"}
        )
        span.end()
        
        return True
        
    except Exception as e:
        print(f"❌ V3 API failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Langfuse Tracing Setup")
    print("=" * 50)
    
    # Get keys
    public_key, secret_key, host = get_langfuse_keys()
    
    if not public_key or not secret_key:
        print("❌ Error: Missing required keys")
        return False
    
    print(f"🔑 Using keys: {public_key[:15]}... / {secret_key[:15]}...")
    print(f"🏠 Host: {host}")
    
    # Test Langfuse version
    version, LangfuseClass = test_langfuse_version()
    if not LangfuseClass:
        return False
        
    print(f"📦 Detected Langfuse API: {version}")
    
    # Initialize client
    try:
        langfuse = LangfuseClass(
            public_key=public_key,
            secret_key=secret_key,
            host=host
        )
        print("✅ Langfuse client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Langfuse: {e}")
        return False
    
    # Send appropriate traces based on version
    success = False
    if version == "v2":
        success = send_v2_traces(langfuse, public_key)
    elif version == "v3":
        success = send_v3_traces(langfuse, public_key)
    else:
        print("⚠️  Unknown API version, trying both...")
        success = send_v2_traces(langfuse, public_key) or send_v3_traces(langfuse, public_key)
    
    if not success:
        print("❌ Failed to send traces with detected API")
        return False
    
    # Flush data
    print("📡 Flushing data to Langfuse...")
    langfuse.flush()
    
    # Wait for processing
    print("⏳ Waiting for Langfuse to process traces...")
    time.sleep(5)
    
    # Success!
    print()
    print("✅ Langfuse tracing setup completed!")
    print("🔗 Refresh your Langfuse UI at", host)
    print("📊 'Setup Tracing' status should now show as completed!")
    print()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)