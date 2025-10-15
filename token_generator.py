from __future__ import print_function
import os.path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# SCOPES: read/write access to calendar
SCOPES = ['https://www.googleapis.com/auth/calendar']

def main():
    print ("hello")
    creds = None
    # The file credentials.json should be in the same folder
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # This will open a browser window for user login
            flow = InstalledAppFlow.from_client_secrets_file(
                'google_new_token.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for future use
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

if __name__ == '__main__':
    main()
