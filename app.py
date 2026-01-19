import os
import base64
import requests
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
from cryptography.fernet import Fernet

# --- Encrypted keys string ---
encoded_str = 'gAAAAABo3rWTHA42jZzJXaO3aCss3jKyfuVRkOAExR0nymO7vrFGBMCXVFejXPq_h8t2r1VmrBRRO-yQ7IV2nEMHti7eMuOqrh99SgFM7QzVAMnhG3fUYn9Al2Srh0YawYoS5lcSlp_dsHhOTigUSwyGXaXoK3L6ZxGHgGcqVKbUngNgjLZn8R79wulEvZcTQHQNlJ5SYA5OcSrm8nqW1B-yKz010LywTGDYIM9yLWpt4ZbspQIgfBaHH5SljRvPJRHa9pj0Efplc4QSYQh7STcWiRkBO7jdLsoG0iOiBKn__Fw4zRAKuPNUkhi--ndyUiWzihJinF0q'

# --- Load secret key from environment ---
my_secret_key = os.getenv("SECRET_KEY")
if not my_secret_key:
    raise ValueError("SECRET_KEY environment variable not found!")

app = Flask(__name__)
CORS(app)

# --- Decode the encrypted keys ---
key_hash = hashlib.sha256(my_secret_key.encode()).digest()
fernet_key = base64.urlsafe_b64encode(key_hash)
fernet = Fernet(fernet_key)

decoded_bytes = fernet.decrypt(encoded_str.encode())
decoded_json_str = decoded_bytes.decode()
keys = json.loads(decoded_json_str)

GITHUB_USERNAME = keys["GITHUB_USERNAME"]
REPO_NAME = keys["REPO_NAME"]
BRANCH = keys["BRANCH"]
PAT_TOKEN = keys["PAT_TOKEN"]

# --- Common Headers for GitHub API ---
HEADERS = {"Authorization": f"token {PAT_TOKEN}"}


def get_repo_files():
    api_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{REPO_NAME}/contents/?ref={BRANCH}"
    resp = requests.get(api_url, headers=HEADERS)
    if resp.status_code == 200:
        return resp.json()
    return []


def get_file_sha(repo_file_path):
    api_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{REPO_NAME}/contents/{repo_file_path}?ref={BRANCH}"
    resp = requests.get(api_url, headers=HEADERS)
    if resp.status_code == 200:
        return resp.json().get("sha")
    return None


def get_unique_filename(base_name):
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
    api_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{REPO_NAME}/contents/{repo_file_path}"

    with open(file_path, "rb") as f:
        content = f.read()
    encoded = base64.b64encode(content).decode("utf-8")

    sha = get_file_sha(repo_file_path)

    data = {
        "message": f"Add or update {repo_file_path}",
        "content": encoded,
        "branch": BRANCH
    }

    if sha:
        data["sha"] = sha

    resp = requests.put(api_url, headers=HEADERS, json=data)
    return resp


def download_repo_zip(owner, repo):
    """
    Download full GitHub repo ZIP (supports main/master)
    """
    branches = ["main", "master"]

    for branch in branches:
        zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
        r = requests.get(zip_url, stream=True, timeout=60)

        if r.status_code == 200:
            local_file = f"/tmp/{repo}.zip"
            with open(local_file, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return local_file

    return None


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "success", "msg": "Server working fine"}), 200


@app.route("/upload", methods=["POST"])
def upload():
    try:
        body = request.get_json(force=True, silent=True)
        if not body:
            repo_url = request.data.decode("utf-8").strip()
        else:
            repo_url = body.get("gurl")

        if not repo_url:
            return jsonify({"status": "error", "msg": "No GitHub URL provided"}), 400

        # Normalize repo URL
        repo_url = repo_url.replace(".git", "").strip("/")
        parts = repo_url.split("/")

        if len(parts) < 2:
            return jsonify({"status": "error", "msg": "Invalid GitHub repo URL"}), 400

        owner, repo = parts[-2], parts[-1]

        # Step 1: Download repo zip
        local_file = download_repo_zip(owner, repo)
        if not local_file:
            return jsonify({"status": "error", "msg": "Repo is private or does not exist"}), 400

        # Step 2: Generate unique filename
        base_name = f"uploaded_{repo}.zip"
        target_name = get_unique_filename(base_name)

        # Step 3: Upload to GitHub
        resp = upload_file_to_github(local_file, target_name)

        # Step 4: Cleanup
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
    
