import os
import subprocess
import sys

# The directory of the script file we want to run
dir_path = os.path.dirname(os.path.realpath(__file__))
main_script = os.path.join(dir_path, "main.py")

def run_with_error_handling():
    """Run the main script with improved error handling"""
    print("Starting script with error handling wrapper...")
    
    try:
        # Set environment variable to help with encoding issues
        os.environ["PYTHONIOENCODING"] = "utf-8"
        
        # Run the actual script
        result = subprocess.run(
            ["python", main_script],
            capture_output=True,
            text=True,
            errors="replace"  # This helps with character encoding issues
        )
        
        # Print stdout
        if result.stdout:
            print(result.stdout)
            
        # Print stderr if there was an error
        if result.returncode != 0 and result.stderr:
            print(f"ERROR (code {result.returncode}):", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            
        return result.returncode
        
    except Exception as e:
        print(f"Error in wrapper script: {str(e)}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    exit_code = run_with_error_handling()
    sys.exit(exit_code)
