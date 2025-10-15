import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import json

# File paths for authentication
CLIENT_SECRETS_FILE = os.path.join(os.path.dirname(__file__), 'google_auth.json')
TOKEN_PATH = os.path.join(os.path.dirname(__file__), 'google_token.json')
SCOPES = ['https://www.googleapis.com/auth/calendar']

def create_token_file():
    if not os.path.exists(CLIENT_SECRETS_FILE):
        raise FileNotFoundError(f"Client secrets file not found at: {CLIENT_SECRETS_FILE}. Please download it from Google Cloud Console.")
    
    token_path = TOKEN_PATH
    
    creds = None
    # Check if token file exists
    if os.path.exists(token_path):
        with open(token_path, 'r') as token:
            try:
                creds = Credentials.from_authorized_user_info(
                    json.load(token), 
                    ['https://www.googleapis.com/auth/calendar']
                )
            except:
                pass
    
    # If credentials don't exist or are invalid
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, 
                ['https://www.googleapis.com/auth/calendar']
            )
            creds = flow.run_local_server(port=0)
        
        # Save the credentials in the proper format
        with open(token_path, 'w') as token:
            token_data = {
                'token': creds.token,
                'refresh_token': creds.refresh_token,
                'token_uri': creds.token_uri,
                'client_id': creds.client_id,
                'client_secret': creds.client_secret,
                'scopes': creds.scopes,
                'expiry': creds.expiry.isoformat() if creds.expiry else None
            }
            json.dump(token_data, token)
    
    print(f"Token successfully created at: {token_path}")

if __name__ == "__main__":
    create_token_file()
    print("Authentication successful! Token saved to", TOKEN_PATH)