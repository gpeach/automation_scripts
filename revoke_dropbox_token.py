import os
import dropbox
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve the access token from the environment variable
ACCESS_TOKEN = os.getenv('DROPBOX_ACCESS_TOKEN')

if not ACCESS_TOKEN:
    raise ValueError("No Dropbox access token found. Please set the 'DROPBOX_ACCESS_TOKEN' environment variable.")

# Initialize Dropbox client
dbx = dropbox.Dropbox(ACCESS_TOKEN)

try:
    # Revoke the access token
    dbx.auth_token_revoke()
    print("Access token revoked successfully.")
except dropbox.exceptions.AuthError as e:
    print(f"Failed to revoke access token: {e}")