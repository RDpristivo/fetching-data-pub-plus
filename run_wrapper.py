#!/usr/bin/env python3
import os
import subprocess
import sys
import platform
import io

def main():
    try:
        # Get the directory of the script file we want to run
        dir_path = os.path.dirname(os.path.realpath(__file__))
        main_script = os.path.join(dir_path, "main.py")
        
        print("Starting script with error handling wrapper...")
        
        # Set environment variable to help with encoding issues
        os.environ["PYTHONIOENCODING"] = "utf-8"
        
        # Set all required headers from the curl command
        os.environ["PUBPLUS_AUTH_TOKEN"] = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE3NDc2MzYzNzgsImV4cCI6MTc0ODg0NTk3OCwiYXV0aF9zZWNyZXQiOiIxOTNlMzRkMTdiY2I0ZmMzYzBjYjc4NzE4NzliODQyZWY0YzU3Mzk1OGI3MTExYzA4NDRiZjA5MmEyYTZmYjIxNTc4NjJhYWQxYmRiNTAyMzc4NjAxNTAwOWM2ZTJjYTU5NTcwY2M3MjRhNDE2YTg3YjM2NDdlZDE3Mjk5NzI5NCJ9.PEhdULJAmfST_wg_Pgj5CnlHV9t52f9lg2OF9e70Rro"
        os.environ["PUBPLUS_CLIENT_ID"] = "7f156802-18bf-47f1-a8da-719a625fcaca"
        os.environ["PUBPLUS_GIT_VERSION"] = "c6986e576d509b7e5a53299009ff5792a3455863"
        os.environ["PUBPLUS_ACCEPT"] = "application/json, text/plain, */*"
        os.environ["PUBPLUS_ORIGIN"] = "https://app.pubplus.com"
        os.environ["PUBPLUS_REFERER"] = "https://app.pubplus.com/"
        os.environ["PUBPLUS_USER_AGENT"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
        os.environ["PUBPLUS_NETWORK_CODE"] = "PRR"
        
        # Determine python command based on OS
        python_cmd = "python" if platform.system() == "Windows" else "python3"
        
        # Set up process with proper encoding for Windows
        if platform.system() == "Windows":
            # For Windows, use shell=True to handle encoding properly
            process = subprocess.run(
                f'"{python_cmd}" "{main_script}"',
                shell=True,
                capture_output=True,
                encoding='utf-8',
                errors='replace',
                check=True
            )
        else:
            # For Unix-like systems
            process = subprocess.run(
                [python_cmd, main_script],
                capture_output=True,
                text=True,
                check=True
            )
        
        # Print stdout
        if process.stdout:
            print(process.stdout)
            
        return 0
            
    except subprocess.CalledProcessError as e:
        print(f"Error running main.py: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return 1
    except Exception as e:
        print(f"Error in wrapper script: {str(e)}")
        return 1

if __name__ == "__main__":
    # Set up UTF-8 encoding for Windows
    if platform.system() == "Windows":
        # Force UTF-8 encoding for stdout and stderr
        if sys.stdout.encoding != 'utf-8':
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        if sys.stderr.encoding != 'utf-8':
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    exit(main())
