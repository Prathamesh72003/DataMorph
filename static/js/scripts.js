// Global variables
let currentFilename = ""; // Store uploaded filename globally
let successModal;

document.addEventListener("DOMContentLoaded", () => {
  // Initialize Bootstrap modal
  successModal = new bootstrap.Modal(document.getElementById("successModal"));

  // Setup drag and drop functionality
  setupDragAndDrop();

  // Setup file input change handler
  setupFileInput();

  // Setup remove file button
  document.getElementById("remove-file").addEventListener("click", (e) => {
    e.preventDefault();
    resetFileUpload();
  });

  // Setup process button
  document.getElementById("process-btn").addEventListener("click", processData);

  // Setup modal download link
  document.getElementById("modal-download-link").addEventListener("click", function (e) {
    // Copy the href from the main download link
    this.href = document.getElementById("download-link").href;
  });
});

function setupDragAndDrop() {
  const uploadArea = document.getElementById("upload-area");

  // Prevent default drag behaviors
  ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
    uploadArea.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
  });

  // Highlight drop area when item is dragged over it
  ["dragenter", "dragover"].forEach((eventName) => {
    uploadArea.addEventListener(eventName, highlight, false);
  });
  ["dragleave", "drop"].forEach((eventName) => {
    uploadArea.addEventListener(eventName, unhighlight, false);
  });

  // Handle dropped files
  uploadArea.addEventListener("drop", handleDrop, false);

  // Handle click to upload
  uploadArea.addEventListener("click", () => {
    document.getElementById("csv-file").click();
  });

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  function highlight() {
    uploadArea.classList.add("dragover");
  }

  function unhighlight() {
    uploadArea.classList.remove("dragover");
  }

  function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;

    if (files.length) {
      document.getElementById("csv-file").files = files;
      handleFileUpload(files[0]);
    }
  }
}

function setupFileInput() {
  document.getElementById("csv-file").addEventListener("change", (e) => {
    if (e.target.files.length) {
      handleFileUpload(e.target.files[0]);
    }
  });
}

function handleFileUpload(file) {
  document.getElementById("filename-display").textContent = file.name;
  document.getElementById("filesize-display").textContent = `Size: ${formatFileSize(file.size)}`;

  document.getElementById("upload-area").style.display = "none";
  document.getElementById("file-info").style.display = "flex";

  document.getElementById("loading-container").style.display = "flex";
  document.getElementById("loading-text").textContent = "Analyzing your data...";

  const formData = new FormData();
  formData.append("file", file);

  fetch("/upload", {
    method: "POST",
    body: formData,
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      if (data.error) {
        showError(data.error);
        return;
      }
      currentFilename = data.filename; // Store filename globally
      analyzeFile(currentFilename);
    })
    .catch((error) => {
      showError("Upload failed: " + error.message);
      console.error("Error:", error);
    });
}

function analyzeFile(filename) {
  // Update loading text
  document.getElementById("loading-text").textContent = "Analyzing data quality issues...";

  fetch("/analyze", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ filename: filename }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      // Hide loading spinner
      document.getElementById("loading-container").style.display = "none";

      if (data.error) {
        showError("Analysis failed: " + data.error);
        return;
      }

      displayIssues(data.issues);
    })
    .catch((error) => {
      document.getElementById("loading-container").style.display = "none";
      showError("Analysis failed: " + error.message);
      console.error("Error:", error);
    });
}

function displayIssues(issues) {
  const issuesTable = document.getElementById("issues-table").querySelector("tbody");
  const issuesSection = document.getElementById("issues-section");
  const processBtn = document.getElementById("process-btn");
  const issuesSummary = document.getElementById("issues-summary");

  issuesTable.innerHTML = ""; // Clear previous issues
  issuesSummary.innerHTML = ""; // Clear previous summary

  let hasIssues = false;
  // Initialize counts for generic categories
  const issueCounts = {
    "Missing Values": 0,
    "Duplicate Data": 0,
    "Format Issues": 0,
    "Outliers": 0,
    "Data Type Issues": 0
  };

  // Loop through each detected issue category
  for (const [category, details] of Object.entries(issues)) {
    let displayCategory = "";
    const cat = category.toLowerCase();
    let count = 0;
    let detailContent = "";

    if (cat === "duplicates") {
      count = details; // duplicates is a number
      displayCategory = "Duplicate Data";
      detailContent = `<p>Total duplicates: ${details}</p>`;
    } else {
      // For object-based details
      count = Object.keys(details).length;
      if (cat === "missing") {
        displayCategory = "Missing Values";
      } else if (cat === "outliers") {
        displayCategory = "Outliers";
      } else if (cat === "dtypes") {
        displayCategory = "Data Type Issues";
      } else if (cat === "formatting") {
        displayCategory = "Format Issues";
      } else {
        displayCategory = category;
      }

      detailContent = "<ul>";
      for (const [key, value] of Object.entries(details)) {
        detailContent += `<li><strong>${key}:</strong> ${value}</li>`;
      }
      detailContent += "</ul>";
    }

    if (count > 0) {
      hasIssues = true;
      issueCounts[displayCategory] = (issueCounts[displayCategory] || 0) + count;

      const row = `
                <tr>
                    <td><strong class="text-primary">${displayCategory}</strong></td>
                    <td>${detailContent}</td>
                </tr>`;
      issuesTable.innerHTML += row;
    }
  }

  // Build summary badges
  for (const [category, count] of Object.entries(issueCounts)) {
    if (count > 0) {
      let badgeClass = "";
      let icon = "";

      if (category === "Missing Values") {
        badgeClass = "missing";
        icon = "bi-exclamation-triangle";
      } else if (category === "Duplicate Data") {
        badgeClass = "duplicate";
        icon = "bi-files";
      } else if (category === "Format Issues" || category === "Data Type Issues") {
        badgeClass = "format";
        icon = "bi-type";
      } else if (category === "Outliers") {
        badgeClass = "outlier";
        icon = "bi-graph-up";
      }

      issuesSummary.innerHTML += `
                <div class="issue-badge ${badgeClass}">
                    <i class="bi ${icon}"></i>
                    ${category}: ${count}
                </div>
            `;
    }
  }

  if (hasIssues) {
    // Show the issues section with a fade-in animation
    issuesSection.style.display = "block";
    issuesSection.classList.add("animate__animated", "animate__fadeIn");
    processBtn.disabled = false;
  } else {
    // No issues found: hide issues section and show success message
    issuesSection.style.display = "none";
    showSuccess("No issues found in your data! Your data is clean.");
  }
}

function processData() {
  // Show loading spinner and update status text
  document.getElementById("loading-container").style.display = "flex";
  document.getElementById("loading-text").textContent = "Cleaning your data...";

  // Disable process button during processing
  document.getElementById("process-btn").disabled = true;

  // Send only the filename; backend will process all issues generically
  fetch("/process", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      filename: currentFilename
    }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      // Hide loading spinner
      document.getElementById("loading-container").style.display = "none";

      if (data.error) {
        showError("Processing failed: " + data.error);
        document.getElementById("process-btn").disabled = false;
        return;
      }

      // Enable download button and set the link
      const downloadLink = document.getElementById("download-link");
      downloadLink.href = data.download_url;
      downloadLink.style.display = "inline-block";

      // Set the modal download link
      document.getElementById("modal-download-link").href = data.download_url;

      // Show success modal
      successModal.show();
    })
    .catch((error) => {
      document.getElementById("loading-container").style.display = "none";
      document.getElementById("process-btn").disabled = false;
      showError("Processing failed: " + error.message);
      console.error("Error:", error);
    });
}

function resetFileUpload() {
  // Reset file input
  document.getElementById("csv-file").value = "";

  // Hide file info and show upload area
  document.getElementById("file-info").style.display = "none";
  document.getElementById("upload-area").style.display = "block";

  // Hide issues section and download button
  document.getElementById("issues-section").style.display = "none";
  document.getElementById("download-link").style.display = "none";

  // Reset current filename
  currentFilename = "";
}

function formatFileSize(bytes) {
  if (bytes === 0) return "0 Bytes";

  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

function showError(message) {
  // Reset file upload and show error alert
  resetFileUpload();
  alert(message);
}

function showSuccess(message) {
  // Show success message alert
  alert(message);
}
