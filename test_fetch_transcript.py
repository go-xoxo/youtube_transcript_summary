#!/usr/bin/env python3
"""
Basic test script for fetch_transcript.py
Tests various scenarios and configurations without requiring network access.
"""
import os
import tempfile
import subprocess
import sys
from pathlib import Path

def run_test(description, command, expected_exit_code=0, should_contain=None, should_not_contain=None):
    """Run a test and check the results."""
    print(f"\n--- Test: {description} ---")
    print(f"Command: {' '.join(command)}")
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        
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
    """Run all tests for fetch_transcript.py."""
    print("Testing fetch_transcript.py")
    print("=" * 50)
    
    script_path = Path(__file__).parent / "fetch_transcript.py"
    if not script_path.exists():
        print(f"❌ ERROR: fetch_transcript.py not found at {script_path}")
        return False
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Help message
    total_tests += 1
    if run_test(
        "Display help message",
        ["python", str(script_path), "--help"],
        expected_exit_code=0,
        should_contain=["usage:", "video_id", "output"]
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
    
    # Test 3: Non-YouTube source type
    total_tests += 1
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp_file:
        tmp_path = tmp_file.name
    try:
        if run_test(
            "Non-YouTube source type",
            ["python", str(script_path), "--video_id", "test123", "--output", tmp_path, "--source_type", "other"],
            expected_exit_code=1,
            should_contain=["Non-YouTube sources are not yet supported"]
        ):
            tests_passed += 1
    finally:
        os.unlink(tmp_path)
    
    # Test 4: Directory creation
    total_tests += 1
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = os.path.join(tmp_dir, "subdir", "transcript.txt")
        if run_test(
            "Output directory creation",
            ["python", str(script_path), "--video_id", "test123", "--output", output_path],
            expected_exit_code=0,
            should_contain=["Output directory ensured"]
        ):
            tests_passed += 1
            # Check if directory was created
            if Path(output_path).parent.exists():
                print("✅ Directory creation verified")
            else:
                print("❌ Directory was not created")
                tests_passed -= 1
    
    # Test 5: Transcript type preferences
    total_tests += 1
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp_file:
        tmp_path = tmp_file.name
    try:
        if run_test(
            "Transcript type preference (manual)",
            ["python", str(script_path), "--video_id", "test123", "--output", tmp_path, "--transcript_type", "manual"],
            expected_exit_code=0,
            should_contain=["Transcript type preference: manual"]
        ):
            tests_passed += 1
    finally:
        os.unlink(tmp_path)
    
    # Test 6: Language preference
    total_tests += 1
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp_file:
        tmp_path = tmp_file.name
    try:
        if run_test(
            "Language preference",
            ["python", str(script_path), "--video_id", "test123", "--output", tmp_path, "--language", "es"],
            expected_exit_code=0,
            should_contain=["Language preference: es"]
        ):
            tests_passed += 1
    finally:
        os.unlink(tmp_path)
    
    # Test 7: Sponsor filtering flag
    total_tests += 1
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp_file:
        tmp_path = tmp_file.name
    try:
        if run_test(
            "Sponsor filtering enabled",
            ["python", str(script_path), "--video_id", "test123", "--output", tmp_path, "--filter_sponsors"],
            expected_exit_code=0,
            should_contain=["Fetching transcript for video: test123"]
        ):
            tests_passed += 1
    finally:
        os.unlink(tmp_path)
    
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