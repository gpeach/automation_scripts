## Setup

1. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
2. Create a `.env` file in the root directory of the project and add your Dropbox access token:
    ```
    DROPBOX_ACCESS_TOKEN=your_access_token_here
    ```
3. use url in auth.http to get auth code
4. add auth code to request in auth.http to get access and refresh tokens
5. add access and refresh tokens into .env file
6. Run the script:
    ```bash
    python dropbox_download.py
    ```
