async function downloadRepo() {

    // =====================================================
    // GET INPUT VALUES
    // =====================================================

    const repoUrl =
        document.getElementById("repo_url").value.trim();

    const branch =
        document.getElementById("branch").value.trim();

    // =====================================================
    // GET ELEMENTS
    // =====================================================

    const progressContainer =
        document.getElementById("progressContainer");

    const statusBox =
        document.getElementById("statusBox");

    // =====================================================
    // RESET UI
    // =====================================================

    statusBox.innerHTML = "";

    progressContainer.classList.remove("d-none");

    // =====================================================
    // BASIC VALIDATION
    // =====================================================

    if (!repoUrl) {

        progressContainer.classList.add("d-none");

        statusBox.innerHTML = `
            <div class="alert alert-danger">
                Repository URL is required
            </div>
        `;

        return;
    }

    if (!branch) {

        progressContainer.classList.add("d-none");

        statusBox.innerHTML = `
            <div class="alert alert-danger">
                Branch name is required
            </div>
        `;

        return;
    }

    try {

        // =================================================
        // SEND REQUEST
        // =================================================

        const response = await fetch("/download", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                repo_url: repoUrl,

                branch: branch
            })

        });

        // =================================================
        // PARSE RESPONSE
        // =================================================

        const data = await response.json();

        // =================================================
        // HIDE PROGRESS
        // =================================================

        progressContainer.classList.add("d-none");

        // =================================================
        // SUCCESS
        // =================================================

        if (data.success) {

            statusBox.innerHTML = `

                <div class="alert alert-success">

                    <h5 class="mb-3">
                        ${data.message}
                    </h5>

                    <p class="mb-3">

                        <strong>
                            File Size:
                        </strong>

                        ${data.data.file_size_mb} MB

                    </p>

                    <a
                        href="${data.data.download_url}"
                        class="btn btn-success btn-lg"
                    >
                        Download ZIP
                    </a>

                </div>
            `;

        }

        // =================================================
        // FAILED
        // =================================================

        else {

            statusBox.innerHTML = `

                <div class="alert alert-danger">

                    <h5 class="mb-2">
                        Download Failed
                    </h5>

                    <p class="mb-0">
                        ${data.message}
                    </p>

                </div>
            `;
        }

    }

    // =====================================================
    // CATCH ERROR
    // =====================================================

    catch (error) {

        console.error(error);

        progressContainer.classList.add("d-none");

        statusBox.innerHTML = `

            <div class="alert alert-danger">

                <h5 class="mb-2">
                    Unexpected Error
                </h5>

                <p class="mb-0">
                    Something went wrong while downloading the repository.
                </p>

            </div>
        `;
    }
}