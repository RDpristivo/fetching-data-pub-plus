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
        os.environ["PUBPLUS_AUTH_TOKEN"] = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE3NTQyOTM3MzUsImV4cCI6MTc1NTUwMzMzNSwiYXV0aF9zZWNyZXQiOiJmYzdmNzkyYjA0NGFlYTljYWYxZTc2YmE2MzE4M2FmNTNjMDY4NTcxMzU1MjFmNDE5ZDQ1ZDVjNzVkYmNmNDU3N2Y3NjA4MDFiYzc0MTBmMjUxMmY2MGFhYmIwY2FhZjQ2NDAyYmJlMmRlZjQ1MTkwNWQ4MDM1Yjg4Y2IzM2IyNSJ9.J_3WoUeT3Vpff_S4Da5YKji4uD_EwxV5TIzx7a6D7OU"
        os.environ["PUBPLUS_CLIENT_ID"] = "9eb52ef8-6cf4-4b97-baeb-3b0180c54444"
        os.environ["PUBPLUS_GIT_VERSION"] = "037be91812f50e7157f7c7c23780b81066971760"
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
