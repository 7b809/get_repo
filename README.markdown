# GitHub File Management API

This is a Flask-based API that allows you to interact with a GitHub repository to upload, list, and delete files using the GitHub API. The application uses a personal access token (PAT) for authentication and Fernet encryption for securely handling sensitive keys.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [API Endpoints](#api-endpoints)
  - [Home Endpoint](#home-endpoint)
  - [Upload File](#upload-file)
  - [List Files](#list-files)
  - [Delete File](#delete-file)
- [Sample Requests](#sample-requests)
  - [Upload File Request](#upload-file-request)
  - [List Files Request](#list-files-request)
  - [Delete File Request](#delete-file-request)
- [Error Handling](#error-handling)

## Prerequisites
- Python 3.8+
- GitHub Personal Access Token (PAT) with `repo` scope
- Required Python packages:
  - `flask`
  - `requests`
  - `cryptography`
  - `python-dotenv`
  - `flask-cors`
- A GitHub repository where files will be managed
- Encrypted keys stored in a JSON string (see Setup for details)

## Setup
1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd <your-repo-directory>
   ```

2. **Install dependencies**:
   ```bash
   pip install flask requests cryptography python-dotenv flask-cors
   ```

3. **Set up environment variables**:
   Create a `.env` file in the project root with the following:
   ```plaintext
   SECRET_KEY=your-secret-key-for-fernet-encryption
   ```

4. **Prepare encrypted keys**:
   - Create a JSON object with your GitHub credentials:
     ```json
     {
       "GITHUB_USERNAME": "your-github-username",
       "REPO_NAME": "your-repo-name",
       "BRANCH": "main",
       "PAT_TOKEN": "your-github-pat-token"
     }
     ```
   - Encrypt this JSON string using Fernet with your `SECRET_KEY` and provide the encrypted string as `encoded_str` in the code.

5. **Run the application**:
   ```bash
   python app.py
   ```
   The server will start on `http://127.0.0.1:5000` in debug mode.

## API Endpoints

### Home Endpoint
- **URL**: `/`
- **Method**: `GET`
- **Description**: Checks if the server is running.
- **Response**:
  ```json
  {
    "status": "success",
    "msg": "Server working fine"
  }
  ```

### Upload File
- **URL**: `/upload`
- **Method**: `POST`
- **Description**: Downloads a GitHub repository as a ZIP file from the provided URL and uploads it to the target repository with a unique filename.
- **Request Body**:
  - `gurl`: The URL of the GitHub repository to download (e.g., `https://github.com/owner/repo.git`).
- **Response**:
  - Success: `{ "status": "success", "msg": "<repo> uploaded successfully as <filename>" }`
  - Error: `{ "status": "error", "msg": "<error message>" }`

### List Files
- **URL**: `/list`
- **Method**: `GET`
- **Description**: Lists all files in the target repository's root directory with their index, name, SHA, and type.
- **Response**:
  ```json
  {
    "status": "success",
    "files": [
      { "index": 0, "name": "file1.zip", "sha": "<sha>", "type": "file" },
      { "index": 1, "name": "file2.zip", "sha": "<sha>", "type": "file" }
    ]
  }
  ```

### Delete File
- **URL**: `/delete`
- **Method**: `DELETE`
- **Description**: Deletes a file from the target repository based on the provided index.
- **Request Body**:
  - `index`: The index of the file to delete (from the `/list` endpoint).
- **Response**:
  - Success: `{ "index": <index>, "filename": "<filename>", "status": "success" }`
  - Error: `{ "status": "error", "msg": "<error message>" }`

## Sample Requests

### Upload File Request
Upload a repository ZIP file to the target repository.

**cURL**:
```bash
curl -X POST http://127.0.0.1:5000/upload \
-H "Content-Type: application/json" \
-d '{"gurl": "https://github.com/owner/repo.git"}'
```

**Python (requests)**:
```python
import requests

url = "http://127.0.0.1:5000/upload"
payload = {"gurl": "https://github.com/owner/repo.git"}
headers = {"Content-Type": "application/json"}

response = requests.post(url, json=payload, headers=headers)
print(response.json())
```

**Expected Response** (Success):
```json
{
  "status": "success",
  "msg": "repo uploaded successfully as uploaded_repo.zip"
}
```

### List Files Request
Retrieve the list of files in the target repository.

**cURL**:
```bash
curl -X GET http://127.0.0.1:5000/list
```

**Python (requests)**:
```python
import requests

url = "http://127.0.0.1:5000/list"
response = requests.get(url)
print(response.json())
```

**Expected Response** (Success):
```json
{
  "status": "success",
  "files": [
    {"index": 0, "name": "uploaded_repo.zip", "sha": "abc123...", "type": "file"},
    {"index": 1, "name": "uploaded_repo_1.zip", "sha": "def456...", "type": "file"}
  ]
}
```

### Delete File Request
Delete a file from the target repository using its index.

**cURL**:
```bash
curl -X DELETE http://127.0.0.1:5000/delete \
-H "Content-Type: application/json" \
-d '{"index": 0}'
```

**Python (requests)**:
```python
import requests

url = "http://127.0.0.1:5000/delete"
payload = {"index": 0}
headers = {"Content-Type": "application/json"}

response = requests.delete(url, json=payload, headers=headers)
print(response.json())
```

**Expected Response** (Success):
```json
{
  "index": 0,
  "filename": "uploaded_repo.zip",
  "status": "success"
}
```

## Error Handling
The API returns appropriate error messages with a `status: "error"` and a descriptive `msg` field in the following cases:
- Missing or invalid GitHub repository URL
- Private or non-existent repository
- Invalid file index for deletion
- Missing environment variables or decryption issues
- GitHub API errors (e.g., invalid PAT token, rate limits)

For any issues, check the error message in the response and ensure your setup (e.g., PAT token, repository access) is correct.