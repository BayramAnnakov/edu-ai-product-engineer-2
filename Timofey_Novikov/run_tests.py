#!/usr/bin/env python3
"""
Simple test runner for TDD approach
Run tests before implementing code
"""

import subprocess
import sys
import os

def run_tests():
    """Run all tests and display results"""
    
    print("🧪 Running Tests for AppStore Review Analyzer")
    print("=" * 60)
    
    # Add current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    test_files = [
        "tests/test_appstore_client.py",
        "tests/test_deterministic_analyzer.py", 
        "tests/test_agents.py",
        "tests/test_comparison.py"
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for test_file in test_files:
        if not os.path.exists(test_file):
            print(f"⚠️  Test file not found: {test_file}")
            continue
            
        print(f"\n📋 Running {test_file}...")
        print("-" * 40)
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", test_file, "-v"
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print(f"✅ {test_file} - All tests passed")
                # Count passed tests from output
                passed_count = result.stdout.count("PASSED")
                passed_tests += passed_count
                total_tests += passed_count
            else:
                print(f"❌ {test_file} - Some tests failed")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                
                # Count failed tests
                failed_count = result.stdout.count("FAILED")
                passed_count = result.stdout.count("PASSED")
                failed_tests += failed_count
                passed_tests += passed_count
                total_tests += (failed_count + passed_count)
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_file} - Tests timed out")
            failed_tests += 1
            total_tests += 1
        except Exception as e:
            print(f"💥 {test_file} - Error running tests: {e}")
            failed_tests += 1
            total_tests += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    
    if failed_tests == 0 and total_tests > 0:
        print("\n🎉 All tests passed! Ready to implement code.")
        return True
    elif total_tests == 0:
        print("\n⚠️  No tests found. Need to create tests first.")
        return False
    else:
        print(f"\n🔧 {failed_tests} tests failing. Implement missing code to make them pass.")
        return False

def check_dependencies():
    """Check if required test dependencies are installed"""
    
    try:
        import pytest
        print("✅ pytest found")
    except ImportError:
        print("❌ pytest not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pytest"])
        print("✅ pytest installed")
    
    # Check if we can import the modules (they may not exist yet - that's ok for TDD)
    print("\n📦 Checking module structure...")
    
    required_dirs = [
        "src",
        "src/data", 
        "src/analyzers",
        "src/agents",
        "src/comparison",
        "tests"
    ]
    
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            print(f"📁 Creating missing directory: {dir_path}")
            os.makedirs(dir_path, exist_ok=True)
            
            # Create __init__.py files
            init_file = os.path.join(dir_path, "__init__.py")
            if not os.path.exists(init_file):
                with open(init_file, 'w') as f:
                    f.write("# Module initialization\n")

if __name__ == "__main__":
    print("🚀 TDD Test Runner for AppStore Review Analyzer")
    print("Following Test-Driven Development approach\n")
    
    check_dependencies()
    success = run_tests()
    
    if success:
        print("\n✨ Next step: All tests are passing! Code is working correctly.")
    else:
        print("\n⚡ Next step: Implement the missing code to make failing tests pass.")
        print("   Start with the simplest failing test and work your way up.")
    
    sys.exit(0 if success else 1)