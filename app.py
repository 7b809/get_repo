import os
import base64
import requests
import json
from flask import Flask, request, jsonify
from flask_cors import CORS  # <--- import CORS
import base64,hashlib
from cryptography.fernet import Fernet

my_secret_key = 'theSecretKey321!@#'

app = Flask(__name__)
CORS(app)  # <--- enable CORS for all routes

encoded_str = 'gAAAAABo3rWTHA42jZzJXaO3aCss3jKyfuVRkOAExR0nymO7vrFGBMCXVFejXPq_h8t2r1VmrBRRO-yQ7IV2nEMHti7eMuOqrh99SgFM7QzVAMnhG3fUYn9Al2Srh0YawYoS5lcSlp_dsHhOTigUSwyGXaXoK3L6ZxGHgGcqVKbUngNgjLZn8R79wulEvZcTQHQNlJ5SYA5OcSrm8nqW1B-yKz010LywTGDYIM9yLWpt4ZbspQIgfBaHH5SljRvPJRHa9pj0Efplc4QSYQh7STcWiRkBO7jdLsoG0iOiBKn__Fw4zRAKuPNUkhi--ndyUiWzihJinF0q'
keys = dict()
# --- Step 1: Derive 32-byte key and encode to base64 ---
key_hash = hashlib.sha256(my_secret_key.encode()).digest()
fernet_key = base64.urlsafe_b64encode(key_hash)  # Fernet requires base64 32-byte key

# --- Step 2: Initialize Fernet ---
fernet = Fernet(fernet_key)
# --- Step 4: Decode back to object ---
decoded_bytes = fernet.decrypt(encoded_str.encode())
decoded_json_str = decoded_bytes.decode()
keys = json.loads(decoded_json_str)

GITHUB_USERNAME = keys["GITHUB_USERNAME"]
REPO_NAME = keys["REPO_NAME"]
BRANCH = keys["BRANCH"]
PAT_TOKEN = keys["PAT_TOKEN"]

# --- Common Headers ---
HEADERS = {"Authorization": f"token {PAT_TOKEN}"}


def get_repo_files():
    """Get all files in repo root"""
    api_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{REPO_NAME}/contents/?ref={BRANCH}"
    resp = requests.get(api_url, headers=HEADERS)
    if resp.status_code == 200:
        return resp.json()
    return []


def get_file_sha(repo_file_path):
    """Get SHA of a file (needed to update/delete existing file)"""
    api_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{REPO_NAME}/contents/{repo_file_path}?ref={BRANCH}"
    resp = requests.get(api_url, headers=HEADERS)
    if resp.status_code == 200:
        return resp.json().get("sha")
    return None


def get_unique_filename(base_name):
    """Generate a unique filename if a conflict exists in the repo"""
    files = get_repo_files()
    existing_names = [f["name"] for f in files if f["type"] == "file"]

    if base_name not in existing_names:
        return base_name

    name_only, ext = os.path.splitext(base_name)
    i = 1
    new_name = f"{name_only}_{i}{ext}"
    while new_name in existing_names:
        i += 1
        new_name = f"{name_only}_{i}{ext}"
    return new_name


def upload_file_to_github(file_path, repo_file_path):
    """Upload or update file in GitHub repo"""
    api_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{REPO_NAME}/contents/{repo_file_path}"

    with open(file_path, "rb") as f:
        content = f.read()
    encoded = base64.b64encode(content).decode("utf-8")

    sha = get_file_sha(repo_file_path)  # include SHA if updating

    data = {
        "message": f"Add or update {repo_file_path}",
        "content": encoded,
        "branch": BRANCH
    }

    if sha:
        data["sha"] = sha

    resp = requests.put(api_url, headers=HEADERS, json=data)
    return resp

# ... your existing imports and code ...

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "success", "msg": "Server working fine"}), 200


@app.route("/upload", methods=["POST"])
def upload():
    try:
        # Get repo URL from request
        body = request.get_json(force=True, silent=True)
        if not body:
            repo_url = request.data.decode("utf-8").strip()
        else:
            repo_url = body.get("gurl")

        if not repo_url:
            return jsonify({"status": "error", "msg": "No GitHub URL provided"}), 400

        # Extract owner/repo
        if repo_url.endswith(".git"):
            repo_url = repo_url[:-4]

        parts = repo_url.split("/")
        if len(parts) < 5:
            return jsonify({"status": "error", "msg": "Invalid GitHub repo URL"}), 400

        owner, repo = parts[-2], parts[-1]
        zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/main.zip"

        # Step 1: Download repo as zip
        r = requests.get(zip_url)
        if r.status_code != 200:
            return jsonify({"status": "error", "msg": "Repo is private or does not exist"}), 400

        local_file = f"{repo}.zip"
        with open(local_file, "wb") as f:
            f.write(r.content)

        # Step 2: Generate unique target filename
        base_name = f"uploaded_{repo}.zip"
        target_name = get_unique_filename(base_name)

        # Step 3: Upload to GitHub
        resp = upload_file_to_github(local_file, target_name)

        # Step 4: Cleanup local zip
        if os.path.exists(local_file):
            os.remove(local_file)

        if resp.status_code in [200, 201]:
            return jsonify({
                "status": "success",
                "msg": f"{repo} uploaded successfully as {target_name}"
            }), 200
        else:
            return jsonify({"status": "error", "msg": resp.json()}), resp.status_code

    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500


@app.route("/list", methods=["GET"])
def list_files():
    try:
        files = get_repo_files()
        indexed_files = [
            {"index": i, "name": f["name"], "sha": f.get("sha"), "type": f.get("type")}
            for i, f in enumerate(files)
        ]
        return jsonify({"status": "success", "files": indexed_files}), 200
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500


@app.route("/delete", methods=["DELETE"])
def delete_file_by_index():
    try:
        body = request.get_json(force=True, silent=True)
        index = body.get("index") if body else None

        if index is None:
            return jsonify({"status": "error", "msg": "Index required"}), 400

        files = get_repo_files()
        if not files or not (0 <= index < len(files)):
            return jsonify({"status": "error", "msg": "Invalid index"}), 400

        filename = files[index]["name"]
        sha = files[index]["sha"]

        delete_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{REPO_NAME}/contents/{filename}"
        data = {"message": f"Delete {filename}", "sha": sha, "branch": BRANCH}
        del_resp = requests.delete(delete_url, headers=HEADERS, json=data)

        status_msg = "success" if del_resp.status_code == 200 else "error"

        return jsonify({
            "index": index,
            "filename": filename,
            "status": status_msg
        }), 200 if status_msg == "success" else del_resp.status_code

    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
