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

  // Setup visualize button
  // document.getElementById("visualize-btn").addEventListener("click", visualizeData);


  // Setup modal download link
  document.getElementById("download-link").addEventListener("click", function (e) {
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

function formatValue(value) {
  if (typeof value === "object" && value !== null) {
    return JSON.stringify(value, null, 2) // Pretty print JSON
      .replace(/[{}"]+/g, '') // Remove curly braces and quotes
      .replace(/,/g, '<br>'); // Line breaks for readability
  }
  return value;
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
      visualizeData();
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
    "Data Type Issues": 0,
    "Class Imbalance": 0,
    "Categorical Conversion Needed": 0,
    "Lexical Issues": 0
  };

  // Loop through each detected issue category
  for (const [category, details] of Object.entries(issues)) {
    let displayCategory = "";
    const cat = category.toLowerCase();
    let count = 0;
    // let detailContent = "";
    detailContent = "<ul>";

    if (cat === "duplicates") {
      count = details; // duplicates is a number
      displayCategory = "Duplicate Data";
      detailContent = `<p>Total duplicates: ${count}</p>`;
    } else {
      // For object-based details
      count = Object.keys(details).length;
      if (cat === "missing") {
        displayCategory = "Missing Values";
        for (const [key, value] of Object.entries(details)) {
          detailContent += `<li><strong>${key}:</strong> ${value}</li>`;
        }
      } else if (cat === "outliers") {
        displayCategory = "Outliers";
        for (const [key, value] of Object.entries(details)) {
          detailContent += `<li><strong>${key}:</strong> ${value}</li>`;
        }
      } else if (cat === "dtypes") {
        displayCategory = "Data Type Issues";
        for (const [key, value] of Object.entries(details)) {
          detailContent += `<li><strong>${key}:</strong> ${value}</li>`;
        }
      } else if (cat === "formatting") {
        displayCategory = "Format Issues";
        for (const [key, value] of Object.entries(details)) {
          detailContent += `<li><strong>${key}:</strong> ${value}</li>`;
        }
      } else if (category.toLowerCase() === "class_imbalance") {
        displayCategory = "Class Imbalance";
        for (const [key, value] of Object.entries(details)) {
          detailContent += `<li><strong>${key}:</strong><ul><br>`;
          for (const [subKey, subValue] of Object.entries(value)) {
            detailContent += `<li>${subKey}: ${subValue.toFixed(4)}</li>`;
          }
          detailContent += "</ul></li>";
        }
      } else if (cat === "categorical_conversion_needed"){
        displayCategory = "Categorical Conversion Needed";
        for (const [key, value] of Object.entries(details)) {
          detailContent += `<li><strong>${key}:</strong> ${value}</li>`;
        }
      } else if (cat==="lexical_issues"){
        displayCategory = "Lexical Issues";
        for (const [key, value] of Object.entries(details)) {
          detailContent += `<li><strong>${key}:</strong> ${value}</li>`;
        }
      } else {
        displayCategory = category;
        for (const [key, value] of Object.entries(details)) {
          detailContent += `<li><strong>${key}:</strong> ${value}</li>`;
        }
      }
    }

    detailContent += "</ul>";

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
      } else if (category === "Class Imbalance") {
        badgeClass = "class_imbalance";
        icon = "bi-bar-chart-line";
      } else if (category === "Lexical Issues") {
        badgeClass = "lexical_issues"
        icon = "bi-spellcheck"
      } else if (category === "Categorical Conversion Needed"){
        badgeClass = "categorical_conversion_needed"
        icon = "bi-table"
      } else {  
        badgeClass = category
        icon = "bi-slash-circle";
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
      document.getElementById("download-link").href = data.download_url;

      // Display applied methods in the success modal
      document.getElementById("applied-methods").innerHTML = data.applied_methods;

      // Display first 10 rows of cleaned data
      document.getElementById("cleaned-data").innerHTML = data.cleaned_data_html;

      // Show success modal
      let successModal = new bootstrap.Modal(document.getElementById("successModal"));
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


function updateSuccessModal(data) {
  // Populate applied methods
  const appliedMethodsContainer = document.getElementById("applied-methods");
  appliedMethodsContainer.innerHTML = ""; // Clear previous

  // successModal.querySelector("#visualization-details").textContent = `Visualization Details: ${data.details}`;
  data.applied_methods.forEach(method => {
      const badge = document.createElement("span");
      badge.classList.add("badge", "bg-success", "me-1", "p-2", "rounded");
      badge.textContent = method;
      appliedMethodsContainer.appendChild(badge);
  });

  // Populate Data Preview
  const table = document.getElementById("cleaned-data");
  table.innerHTML = ""; // Clear previous
  const dfHead = data.df_head; // Expecting a list of lists (rows)

  if (dfHead.length > 0) {
      // Create header row
      const thead = document.createElement("thead");
      const headerRow = document.createElement("tr");
      dfHead[0].forEach(colName => {
          const th = document.createElement("th");
          th.textContent = colName;
          headerRow.appendChild(th);
      });
      thead.appendChild(headerRow);
      table.appendChild(thead);

      // Create body rows
      const tbody = document.createElement("tbody");
      for (let i = 1; i < dfHead.length; i++) {
          const row = document.createElement("tr");
          dfHead[i].forEach(cell => {
              const td = document.createElement("td");
              td.textContent = cell;
              row.appendChild(td);
          });
          tbody.appendChild(row);
      }
      table.appendChild(tbody);
  }

  // Set download link
  document.getElementById("download-link").href = data.download_url;

  // Show modal
  new bootstrap.Modal(document.getElementById("successModal")).show();
}


function visualizeData() {
  // Show loading spinner and update status text
  document.getElementById("loading-container").style.display = "flex";
  document.getElementById("loading-text").textContent = "Visualizing your data...";

  // Disable process button during processing
  document.getElementById("process-btn").disabled = true;
  console.log(currentFilename);

  // Send the current filename to the backend for visualization
  fetch("/visualize", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      filename: currentFilename,
    }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      console.log("Response data:", data);  // Log the response data

      // Hide loading spinner
      document.getElementById("loading-container").style.display = "none";

      if (data.error) {
        showError("Visualization data failed: " + data.error);
        document.getElementById("process-btn").disabled = false;
        return;
      }

      const visualizationContainer = document.getElementById("visualization-container");
  
      if (data.before_plot?.length) {
          // Show the container if not already visible
          if (visualizationContainer.style.display === "none") {
              visualizationContainer.style.display = "block";
          }
  
          data.before_plot.forEach(imageUrl => {
              const imgElement = document.createElement("img");
              console.log(imageUrl);
              imgElement.src = imageUrl;
              imgElement.alt = "Before Plot Image";
              imgElement.classList.add("visualization-image");
              visualizationContainer.appendChild(imgElement);
          });
      }
    })
    .catch((error) => {
      document.getElementById("loading-container").style.display = "none";
      document.getElementById("process-btn").disabled = false;
      showError("Visualization failed: " + error.message);
      console.error("Error:", error);
    });
}




