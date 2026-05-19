import requests
import os
import traceback
from urllib.parse import urlparse


def extract_repo_info(repo_url):

    try:

        repo_url = repo_url.strip()

        if not repo_url:
            raise ValueError("Repository URL is empty")

        repo_url = repo_url.replace(".git", "")

        parsed = urlparse(repo_url)

        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid repository URL format")

        parts = repo_url.split("/")

        if len(parts) < 5:
            raise ValueError("Invalid GitHub repository URL")

        owner = parts[-2].strip()
        repo = parts[-1].strip()

        if not owner or not repo:
            raise ValueError("Owner or repository name missing")

        return {"success": True, "owner": owner, "repo": repo}

    except Exception as e:

        return {
            "success": False,
            "message": "Failed to extract repository information",
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


def download_repo_zip(repo_url, branch, download_folder):

    try:

        # =====================================================
        # VALIDATIONS
        # =====================================================

        if not repo_url:
            return {"success": False, "message": "Repository URL is required"}

        if not branch:
            return {"success": False, "message": "Branch name is required"}

        # =====================================================
        # EXTRACT REPO INFO
        # =====================================================

        repo_info = extract_repo_info(repo_url)

        if not repo_info["success"]:
            return repo_info

        owner = repo_info["owner"]
        repo = repo_info["repo"]

        # =====================================================
        # CREATE DOWNLOAD FOLDER
        # =====================================================

        os.makedirs(download_folder, exist_ok=True)

        # =====================================================
        # CREATE ZIP URL
        # =====================================================

        zip_url = (
            f"https://github.com/" f"{owner}/{repo}/archive/refs/heads/{branch}.zip"
        )

        # =====================================================
        # SEND REQUEST
        # =====================================================

        try:

            response = requests.get(zip_url, stream=True, timeout=60)

        except requests.exceptions.Timeout:

            return {
                "success": False,
                "message": "Request timeout while downloading repository",
                "repo_url": repo_url,
                "branch": branch,
            }

        except requests.exceptions.ConnectionError:

            return {
                "success": False,
                "message": "Internet connection error",
                "repo_url": repo_url,
                "branch": branch,
            }

        except requests.exceptions.RequestException as e:

            return {
                "success": False,
                "message": "Request failed",
                "error": str(e),
                "repo_url": repo_url,
                "branch": branch,
            }

        # =====================================================
        # STATUS CODE CHECK
        # =====================================================

        if response.status_code == 404:

            return {
                "success": False,
                "message": ("Repository or branch not found"),
                "repo": repo,
                "branch": branch,
                "status_code": response.status_code,
                "zip_url": zip_url,
            }

        if response.status_code != 200:

            return {
                "success": False,
                "message": "Failed to download repository",
                "status_code": response.status_code,
                "repo": repo,
                "branch": branch,
                "zip_url": zip_url,
            }

        # =====================================================
        # FILE NAME
        # =====================================================

        safe_repo_name = repo.replace(" ", "_")
        safe_branch_name = branch.replace("/", "_")

        filename = f"{safe_repo_name}-{safe_branch_name}.zip"

        file_path = os.path.join(download_folder, filename)

        # =====================================================
        # DOWNLOAD
        # =====================================================

        total_size = int(response.headers.get("content-length", 0))

        downloaded = 0

        with open(file_path, "wb") as file:

            for chunk in response.iter_content(chunk_size=8192):

                if chunk:

                    file.write(chunk)

                    downloaded += len(chunk)

                    progress = (downloaded / total_size) * 100 if total_size > 0 else 0

                    print(f"[INFO] Downloaded " f"{progress:.2f}%")

        # =====================================================
        # VERIFY FILE EXISTS
        # =====================================================

        if not os.path.exists(file_path):

            return {
                "success": False,
                "message": "ZIP file not saved properly",
                "file_path": file_path,
            }

        file_size = os.path.getsize(file_path)

        # =====================================================
        # SUCCESS RESPONSE
        # =====================================================

        return {
            "success": True,
            "message": "Repository ZIP downloaded successfully",
            "data": {
                "repo_owner": owner,
                "repo_name": repo,
                "branch": branch,
                "zip_url": zip_url,
                "filename": filename,
                "file_path": file_path,
                "file_size_bytes": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "downloaded_bytes": downloaded,
                "status_code": response.status_code,
            },
        }

    except Exception as e:

        # =====================================================
        # CLEANUP FAILED FILE
        # =====================================================

        try:

            if "file_path" in locals():

                if os.path.exists(file_path):
                    os.remove(file_path)

        except:
            pass

        return {
            "success": False,
            "message": "Unexpected error occurred",
            "error": str(e),
            "traceback": traceback.format_exc(),
            "repo_url": repo_url,
            "branch": branch,
        }
