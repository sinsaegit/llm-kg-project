// Menu functions
function openMenu() {
    document.getElementById("menu").style.width = "250px";
}

function closeMenu() {
    document.getElementById("menu").style.width = "0";
}

function openAbout() {
    document.getElementById("about-modal").style.display = "block";
}

function closeAbout() {
    document.getElementById("about-modal").style.display = "none";
}

// Submit Prompt function
function submitPrompt() {
    const promptInput = document.getElementById("prompt-input").value;
    const outputDiv = document.getElementById("prompt-output");

    // Clear the output area before fetching
    outputDiv.innerHTML = "";

    // Send the prompt to the Flask backend
    fetch('/submit-prompt', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            'prompt': promptInput // Send the prompt entered by the user
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error("Network response was not ok");
        }
        return response.json();
    })
    .then(data => {
        // Check if data is returned
        console.log("Data received:", data);
        let results = data.response;

        // Display the results in the output div
        outputDiv.innerHTML = "<h3>NER Results:</h3><pre>" + JSON.stringify(results, null, 2) + "</pre>";
    })
    .catch(error => {
        console.error("Error:", error);
        outputDiv.innerHTML = "Error processing the input!";
    });
}

// Upload file function
function uploadFile() {
    const fileInput = document.getElementById("file-upload");
    const progressBar = document.getElementById("progress-bar");
    const progressText = document.getElementById("progress-text");

    if (!fileInput.files[0]) {
        alert("Please select a file to upload.");
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);

    // Simulating a file upload
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/upload-file", true);

    xhr.upload.onprogress = function(event) {
        if (event.lengthComputable) {
            const percentComplete = Math.round((event.loaded / event.total) * 100);
            progressBar.value = percentComplete;
            progressText.textContent = percentComplete + "%";
        }
    };

    xhr.onload = function() {
        if (xhr.status === 200) {
            progressText.textContent = "Upload complete!";
        } else {
            progressText.textContent = "Upload failed!";
        }
    };

    xhr.send(formData);
}
