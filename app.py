from flask import Flask, render_template, request, jsonify, send_file

import os
import traceback

from utils.github_downloader import download_repo_zip

app = Flask(__name__)

# =====================================================
# CONFIG
# =====================================================

# DOWNLOAD_FOLDER = "downloads"
DOWNLOAD_FOLDER = "/tmp/downloads"

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# =====================================================
# HOME PAGE
# =====================================================


@app.route("/")
def index():

    try:

        return render_template("index.html")

    except Exception as e:

        return (
            jsonify(
                {
                    "success": False,
                    "message": "Failed to load homepage",
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                }
            ),
            500,
        )


# =====================================================
# DOWNLOAD REPOSITORY
# =====================================================


@app.route("/download", methods=["POST"])
def download_repo():

    try:

        # =================================================
        # VALIDATE JSON BODY
        # =================================================

        if not request.is_json:

            return (
                jsonify(
                    {
                        "success": False,
                        "message": ("Request content type " "must be application/json"),
                    }
                ),
                400,
            )

        data = request.get_json()

        if not data:

            return jsonify({"success": False, "message": "Request body is empty"}), 400

        # =================================================
        # GET INPUTS
        # =================================================

        repo_url = data.get("repo_url", "").strip()

        branch = data.get("branch", "").strip()

        # =================================================
        # VALIDATIONS
        # =================================================

        if not repo_url:

            return (
                jsonify({"success": False, "message": "Repository URL is required"}),
                400,
            )

        if not branch:

            return (
                jsonify({"success": False, "message": "Branch name is required"}),
                400,
            )

        # =================================================
        # DOWNLOAD REPO
        # =================================================

        result = download_repo_zip(
            repo_url=repo_url, branch=branch, download_folder=DOWNLOAD_FOLDER
        )

        # =================================================
        # HANDLE FAILURE
        # =================================================

        if not result.get("success"):

            return jsonify(result), 400

        # =================================================
        # SUCCESS RESPONSE
        # =================================================

        return (
            jsonify(
                {
                    "success": True,
                    "message": ("Repository downloaded successfully"),
                    "data": result.get("data"),
                }
            ),
            200,
        )

    except Exception as e:

        return (
            jsonify(
                {
                    "success": False,
                    "message": (
                        "Unexpected error occurred " "while downloading repository"
                    ),
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                }
            ),
            500,
        )


# =====================================================
# DOWNLOAD FILE
# =====================================================


@app.route("/download-file/<filename>")
def download_file(filename):

    try:

        # =================================================
        # BASIC SECURITY
        # =================================================

        if ".." in filename or "/" in filename:

            return jsonify({"success": False, "message": "Invalid filename"}), 400

        # =================================================
        # FILE PATH
        # =================================================

        file_path = os.path.join(DOWNLOAD_FOLDER, filename)

        # =================================================
        # CHECK FILE EXISTS
        # =================================================

        if not os.path.exists(file_path):

            return (
                jsonify(
                    {
                        "success": False,
                        "message": "File not found",
                        "filename": filename,
                    }
                ),
                404,
            )

        # =================================================
        # CHECK FILE TYPE
        # =================================================

        if not filename.endswith(".zip"):

            return (
                jsonify({"success": False, "message": ("Only ZIP files are allowed")}),
                400,
            )

        # =================================================
        # SEND FILE
        # =================================================

        return send_file(file_path, as_attachment=True, download_name=filename)

    except Exception as e:

        return (
            jsonify(
                {
                    "success": False,
                    "message": ("Failed to send file"),
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                    "filename": filename,
                }
            ),
            500,
        )


# =====================================================
# HEALTH CHECK
# =====================================================


@app.route("/health")
def health_check():

    return (
        jsonify(
            {
                "success": True,
                "message": "Application running",
                "download_folder": DOWNLOAD_FOLDER,
            }
        ),
        200,
    )


# =====================================================
# GLOBAL ERROR HANDLER
# =====================================================


@app.errorhandler(404)
def not_found(error):

    return jsonify({"success": False, "message": "Route not found"}), 404


@app.errorhandler(405)
def method_not_allowed(error):

    return jsonify({"success": False, "message": "Method not allowed"}), 405


@app.errorhandler(500)
def internal_server_error(error):

    return jsonify({"success": False, "message": "Internal server error"}), 500


# =====================================================
# RUN APP
# =====================================================

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5000, debug=True)
