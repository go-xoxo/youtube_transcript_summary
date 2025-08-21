#!/usr/bin/env python3
"""
Basic test script for youtube_summary.py
Tests various scenarios and configurations.
"""
import os
import tempfile
import subprocess
import sys
from pathlib import Path

def create_test_transcript(content="This is a test transcript content."):
    """Create a temporary transcript file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp_file:
        tmp_file.write(content)
        return tmp_file.name

def run_test(description, command, expected_exit_code=0, should_contain=None, should_not_contain=None, env=None):
    """Run a test and check the results."""
    print(f"\n--- Test: {description} ---")
    print(f"Command: {' '.join(command)}")
    
    test_env = os.environ.copy()
    if env:
        test_env.update(env)
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30, env=test_env)
        
        print(f"Exit code: {result.returncode}")
        if result.stdout:
            print(f"STDOUT: {result.stdout[:500]}")
        if result.stderr:
            print(f"STDERR: {result.stderr[:500]}")
        
        # Check exit code
        if result.returncode != expected_exit_code:
            print(f"❌ FAIL: Expected exit code {expected_exit_code}, got {result.returncode}")
            return False
        
        # Check output contains expected strings
        output = result.stdout + result.stderr
        if should_contain:
            for text in should_contain:
                if text not in output:
                    print(f"❌ FAIL: Output should contain '{text}'")
                    return False
        
        if should_not_contain:
            for text in should_not_contain:
                if text in output:
                    print(f"❌ FAIL: Output should not contain '{text}'")
                    return False
        
        print("✅ PASS")
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ FAIL: Test timed out")
        return False
    except Exception as e:
        print(f"❌ FAIL: Test failed with exception: {e}")
        return False

def main():
    """Run all tests for youtube_summary.py."""
    print("Testing youtube_summary.py")
    print("=" * 50)
    
    script_path = Path(__file__).parent / "youtube_summary.py"
    if not script_path.exists():
        print(f"❌ ERROR: youtube_summary.py not found at {script_path}")
        return False
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Help message
    total_tests += 1
    if run_test(
        "Display help message",
        ["python", str(script_path), "--help"],
        expected_exit_code=0,
        should_contain=["usage:", "input", "output", "video_id"]
    ):
        tests_passed += 1
    
    # Test 2: Missing required arguments
    total_tests += 1
    if run_test(
        "Missing required arguments",
        ["python", str(script_path)],
        expected_exit_code=2,
        should_contain=["required"]
    ):
        tests_passed += 1
    
    # Test 3: Missing API key
    total_tests += 1
    input_file = create_test_transcript()
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as tmp_output:
            output_path = tmp_output.name
        
        if run_test(
            "Missing OpenAI API key",
            ["python", str(script_path), "--input", input_file, "--output", output_path, "--video_id", "test123"],
            expected_exit_code=1,
            should_contain=["OpenAI API key not found"],
            env={"OPENAI_API_KEY": ""}  # Ensure API key is not set
        ):
            tests_passed += 1
    finally:
        os.unlink(input_file)
        if os.path.exists(output_path):
            os.unlink(output_path)
    
    # Test 4: Non-existent input file
    total_tests += 1
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as tmp_output:
        output_path = tmp_output.name
    try:
        if run_test(
            "Non-existent input file",
            ["python", str(script_path), "--input", "/nonexistent/file.txt", "--output", output_path, "--video_id", "test123"],
            expected_exit_code=1,
            should_contain=["Transcript file not found"],
            env={"OPENAI_API_KEY": "fake-key-for-testing"}
        ):
            tests_passed += 1
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)
    
    # Test 5: Directory creation for output
    total_tests += 1
    input_file = create_test_transcript()
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = os.path.join(tmp_dir, "subdir", "summary.md")
            if run_test(
                "Output directory creation",
                ["python", str(script_path), "--input", input_file, "--output", output_path, "--video_id", "test123"],
                expected_exit_code=1,  # Will fail due to fake API key, but should create directory
                should_contain=["Reading transcript from"],
                env={"OPENAI_API_KEY": "fake-key-for-testing"}
            ):
                # Check if directory was created
                if Path(output_path).parent.exists():
                    print("✅ Directory creation verified")
                    tests_passed += 1
                else:
                    print("❌ Directory was not created")
    finally:
        os.unlink(input_file)
    
    # Test 6: Sponsor content detection
    total_tests += 1
    sponsor_content = """
    This video is sponsored by Ground News.
    Get 50% off with promo code SAVE50.
    Visit sponsor.com/deal for more info.
    Now back to the main content.
    """
    input_file = create_test_transcript(sponsor_content)
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as tmp_output:
            output_path = tmp_output.name
        
        if run_test(
            "Sponsor content detection",
            ["python", str(script_path), "--input", input_file, "--output", output_path, "--video_id", "test123"],
            expected_exit_code=1,  # Will fail due to fake API key
            should_contain=["Sponsor/ad content detected"],
            env={"OPENAI_API_KEY": "fake-key-for-testing"}
        ):
            tests_passed += 1
    finally:
        os.unlink(input_file)
        if os.path.exists(output_path):
            os.unlink(output_path)
    
    # Test 7: Valid input with fake API key (to test up to API call)
    total_tests += 1
    input_file = create_test_transcript("Clean transcript content without sponsors.")
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as tmp_output:
            output_path = tmp_output.name
        
        if run_test(
            "Valid input with logging",
            ["python", str(script_path), "--input", input_file, "--output", output_path, "--video_id", "test123"],
            expected_exit_code=1,  # Will fail at API call
            should_contain=["Reading transcript from", "Generating summary using OpenAI"],
            should_not_contain=["Sponsor/ad content detected"],
            env={"OPENAI_API_KEY": "fake-key-for-testing"}
        ):
            tests_passed += 1
    finally:
        os.unlink(input_file)
        if os.path.exists(output_path):
            os.unlink(output_path)
    
    print(f"\n{'='*50}")
    print(f"Tests completed: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)