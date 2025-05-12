import os
from twilio.rest import Client
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()


def test_twilio_credentials():
    """Test if Twilio credentials are valid"""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")

    if not account_sid or not auth_token:
        return False

    # Try a simple account info request to test credentials
    try:
        response = requests.get(
            f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}.json",
            auth=(account_sid, auth_token),
        )
        return response.status_code == 200
    except:
        return False


def send_notification(message):
    """
    Send a notification message via Twilio with enhanced error handling
    """
    # Twilio credentials
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_FROM_NUMBER")
    to_number = os.getenv("TWILIO_TO_NUMBER")

    # Debug credentials (masked for security)
    print(
        f"Twilio SID: {account_sid[:5]}...{account_sid[-5:] if account_sid else 'None'}"
    )
    print(f"Auth Token Set: {'Yes' if auth_token else 'No'}")
    print(f"From Number: {from_number}")
    print(f"To Number: {to_number[:3]}...{to_number[-3:] if to_number else 'None'}")

    # Check if credentials exist
    if not account_sid or not auth_token or not from_number or not to_number:
        print("Twilio notification SKIPPED: Missing credentials in .env file")
        return False

    # Verify credentials before attempting to send
    if not test_twilio_credentials():
        print(
            "Twilio notification SKIPPED: Invalid credentials - Please check your account_sid and auth_token"
        )
        print("You may need to log into Twilio console and regenerate your Auth Token")
        return False

    try:
        client = Client(account_sid, auth_token)

        twilio_message = client.messages.create(
            body=message, from_=from_number, to=to_number
        )

        print(f"Notification sent with SID: {twilio_message.sid}")
        return True
    except Exception as e:
        print(f"Failed to send Twilio notification: {e}")

        # Handle common error cases
        if hasattr(e, "code") and e.code == 20003:
            print(
                "Authentication failed. Please regenerate your Auth Token in the Twilio console."
            )
        elif hasattr(e, "code") and e.code == 21608:
            print("This number is not verified with your Twilio trial account.")
            print(
                "Please verify the recipient number in your Twilio console or upgrade your account."
            )

        # Log more detailed error information for debugging
        if hasattr(e, "msg"):
            print(f"Error message: {e.msg}")
        if hasattr(e, "code"):
            print(f"Error code: {e.code}")

        return False


def send_notification_with_fallback(message):
    """Attempt to send with Twilio, fall back to console only if it fails"""
    if not send_notification(message):
        print(f"NOTIFICATION (Console only): {message}")
        return False
    return True
