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
        os.environ["PUBPLUS_AUTH_TOKEN"] = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE3NTMwODI5MTEsImV4cCI6MTc1NDI5MjUxMSwiYXV0aF9zZWNyZXQiOiIyMTAzODcyMGFkYjBmZTFhMTY5ZGIyODg0NmQ2OWIwYTIxMGYwOTYxMjY4NmM3M2Y5YzMwNWUxMGU0NDNjMDIzNjc1MzVkYTM3NzVkM2JjN2RkYTM0MTk1OWM1ODk1Yjc0ODgxMWM1MmI5MDQ2YjI1YjE4NGM0OTlhNjBlYTEwMiJ9.JSBQV22O8oAVotWQYLpm9C9fZKY29vZOhdV0z0rUhRM"
        os.environ["PUBPLUS_CLIENT_ID"] = "832b24e7-4224-4ca9-84c5-74e98aacf469"
        os.environ["PUBPLUS_GIT_VERSION"] = "c8fe6405f550b9d6abf3047ebde250981f672f0b"
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
