import os
import dropbox
import tkinter as tk
from tkinter import filedialog, simpledialog
from dotenv import load_dotenv
import re
import threading
import time
import requests
from dropbox.exceptions import AuthError, ApiError
import json

# Load environment variables from .env file
load_dotenv()

# Retrieve the access token and refresh token from environment variables
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
REFRESH_TOKEN = os.getenv('REFRESH_TOKEN')
APP_KEY = os.getenv('APP_KEY')
APP_SECRET = os.getenv('APP_SECRET')

if not ACCESS_TOKEN or not REFRESH_TOKEN or not APP_KEY or not APP_SECRET:
    raise ValueError("Please set the 'ACCESS_TOKEN', 'REFRESH_TOKEN', 'APP_KEY', and 'APP_SECRET' environment variables.")

def refresh_access_token():
    """Refresh the Dropbox access token."""
    token_url = "https://api.dropbox.com/oauth2/token"
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': REFRESH_TOKEN,
    }
    auth = (APP_KEY, APP_SECRET)
    response = requests.post(token_url, data=data, auth=auth)
    if response.status_code == 200:
        tokens = response.json()
        new_access_token = tokens['access_token']
        os.environ['DROPBOX_ACCESS_TOKEN'] = new_access_token
        return new_access_token
    else:
        raise Exception(f"Failed to refresh access token: {response.text}")

def get_dbx_client():
    """Get Dropbox client with a valid access token."""
    global ACCESS_TOKEN
    try:
        dbx = dropbox.Dropbox(ACCESS_TOKEN)
        # Try an API call to check if the token is valid
        dbx.users_get_current_account()
        return dbx
    except dropbox.exceptions.AuthError as e:
        if 'expired_access_token' in str(e):
            ACCESS_TOKEN = refresh_access_token()
            return dropbox.Dropbox(ACCESS_TOKEN)
        else:
            raise e

def download_file(dbx, dropbox_path, local_path, original_display_path):
    """Download a single file from Dropbox."""
    try:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, "wb") as f:
            start_time = time.time()
            download_thread = threading.Thread(target=show_progress, args=(start_time,))
            download_thread.start()

            metadata, res = dbx.files_download(dropbox_path)
            f.write(res.content)
            download_thread.do_run = False  # Stop the progress thread

        print(f"Downloaded: {original_display_path} to {local_path}")
    except Exception as e:
        print(f"Failed to download {original_display_path}: {e}")

def show_progress(start_time):
    """Show download progress if the file takes longer than 30 seconds."""
    t = threading.current_thread()
    while getattr(t, "do_run", True):
        if time.time() - start_time > 30:
            print("Downloading... Please wait.")
        time.sleep(5)  # Check every 5 seconds

def download_files_preserving_structure(dbx, folder_path, local_base_path, include_deleted):
    """Download files from a Dropbox folder while preserving directory structure."""
    try:
        result = dbx.files_list_folder(folder_path, recursive=True, include_deleted=include_deleted)
        print(f"Listing folder: {folder_path}")

        for entry in result.entries:
            if isinstance(entry, dropbox.files.FileMetadata):
                relative_path = entry.path_display[len(folder_path):].lstrip('/')
                local_file_path = os.path.join(local_base_path, relative_path.replace('/', os.sep))
                print(f"File: {entry.path_display} Path: {local_file_path}")
                download_file(dbx, entry.path_lower, local_file_path, entry.path_display)
            elif include_deleted and isinstance(entry, dropbox.files.DeletedMetadata):
                relative_path = entry.path_display[len(folder_path):].lstrip('/')
                local_file_path = os.path.join(local_base_path, relative_path.replace('/', os.sep))
                print(f"Deleted file (will download as restored): {entry.path_display} Path: {local_file_path}")
                download_deleted_file(dbx, entry.path_lower, local_file_path, entry.path_display)

        # Handle pagination
        while result.has_more:
            result = dbx.files_list_folder_continue(result.cursor)
            for entry in result.entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                    relative_path = entry.path_display[len(folder_path):].lstrip('/')
                    local_file_path = os.path.join(local_base_path, relative_path.replace('/', os.sep))
                    print(f"File: {entry.path_display} Path: {local_file_path}")
                    download_file(dbx, entry.path_lower, local_file_path, entry.path_display)
                elif include_deleted and isinstance(entry, dropbox.files.DeletedMetadata):
                    relative_path = entry.path_display[len(folder_path):].lstrip('/')
                    local_file_path = os.path.join(local_base_path, relative_path.replace('/', os.sep))
                    print(f"Deleted file (will download as restored): {entry.path_display} Path: {local_file_path}")
                    download_deleted_file(dbx, entry.path_lower, local_file_path, entry.path_display)

    except dropbox.exceptions.ApiError as err:
        print(f"Folder listing failed: {err}")

def download_deleted_file(dbx, dropbox_path, local_path, original_display_path):
    """Download a deleted file from Dropbox as if it were restored."""
    try:
        print(f"Attempting to download deleted file as restored: {original_display_path}")
        revisions = dbx.files_list_revisions(dropbox_path, limit=1)
        if revisions.entries:
            latest_revision = revisions.entries[0]
            with open(local_path, "wb") as f:
                start_time = time.time()
                download_thread = threading.Thread(target=show_progress, args=(start_time,))
                download_thread.start()

                metadata, res = dbx.files_download(dropbox_path, rev=latest_revision.rev)
                f.write(res.content)
                download_thread.do_run = False  # Stop the progress thread

            print(f"Downloaded deleted file as restored: {original_display_path} to {local_path}")
        else:
            print(f"No revisions found for deleted file: {original_display_path}")
    except Exception as e:
        print(f"Failed to download deleted file: {original_display_path}: {e}")

def select_folder():
    """Open a dialog to select a local folder."""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    folder_path = filedialog.askdirectory(title="Select Folder to Save Files")
    return folder_path

def get_url_input():
    """Open a dialog to input a Dropbox folder path."""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    url = simpledialog.askstring("Input", "Enter the Dropbox folder path (e.g., '/path/to/your/folder?d=1' to include deleted files):")
    return url

def validate_dropbox_path(path):
    """Validate Dropbox path format."""
    valid_pattern = re.compile(r'^(/(.|[\r\n])*)?|id:.*|(ns:[0-9]+(/.*)?)$')
    return valid_pattern.match(path) is not None

def parse_path_and_flags(dropbox_path):
    """Parse the path to determine if it includes deleted files."""
    include_deleted = False
    if '?d=1' in dropbox_path:
        include_deleted = True
        dropbox_path = dropbox_path.split('?d=1')[0]  # Remove the ?d=1 flag from the path
    return dropbox_path, include_deleted

if __name__ == "__main__":
    # Open dialog to input Dropbox folder path
    dropbox_folder_path = get_url_input()

    if dropbox_folder_path:
        dropbox_folder_path, include_deleted = parse_path_and_flags(dropbox_folder_path)

        if validate_dropbox_path(dropbox_folder_path):
            print(f"Entered Dropbox path: {dropbox_folder_path} (Include deleted: {include_deleted})")
            # Open dialog to select local path to save files
            local_save_path = select_folder()

            if local_save_path:
                dbx = get_dbx_client()
                download_files_preserving_structure(dbx, dropbox_folder_path, local_save_path, include_deleted)
                print("Download complete.")
            else:
                print("No folder selected. Exiting.")
        else:
            print("Invalid Dropbox path entered. Exiting.")
    else:
        print("No path entered. Exiting.")