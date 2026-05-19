async function downloadRepo() {

    const repoUrl = document.getElementById("repo_url").value;
    const branch = document.getElementById("branch").value;

    const progressContainer =
        document.getElementById("progressContainer");

    const statusBox =
        document.getElementById("statusBox");

    progressContainer.classList.remove("d-none");

    statusBox.innerHTML = "";

    try {

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

        const data = await response.json();

        progressContainer.classList.add("d-none");

        if (data.success) {

            statusBox.innerHTML = `
                <div class="alert alert-success">

                    Repo downloaded successfully.

                    <br><br>

                    <a
                        href="/download-file/${data.filename}"
                        class="btn btn-success"
                    >
                        Download ZIP
                    </a>

                </div>
            `;

        } else {

            statusBox.innerHTML = `
                <div class="alert alert-danger">
                    ${data.message}
                </div>
            `;
        }

    } catch (error) {

        progressContainer.classList.add("d-none");

        statusBox.innerHTML = `
            <div class="alert alert-danger">
                Error occurred
            </div>
        `;
    }
}