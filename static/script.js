console.log("Script loaded!"); // Check if JS file loads

document.getElementById("verifyBtn").addEventListener("click", async () => {
  console.log("Button clicked!"); // Debug if this fires
  
  const fileInput = document.getElementById("fileInput");
  const file = fileInput.files[0];
  console.log("Selected file:", file); // Debug file upload

  if (!file) {
    console.error("No file selected!"); // Debug
    alert("Please select a file first!");
    return;
  }

  // Show progress bar
  document.getElementById("progressSection").style.display = "block";
  const progressBar = document.getElementById("progressBar");
  console.log("Progress bar shown"); // Debug UI state

  // Read file (CSV)
  const emails = await readCSV(file);
  console.log("Emails read from CSV:", emails); // Debug CSV parsing
  
  // Call real API (replace mock with this)
  try {
    console.log("Starting email verification..."); // Debug API call
    const results = await verifyEmails(emails, (progress) => {
      progressBar.style.width = `${progress}%`;
      progressBar.textContent = `${progress}%`;
      console.log(`Progress: ${progress}%`); // Debug progress updates
    });
    console.log("Verification results:", results); // Debug results
    displayResults(results);
  } catch (error) {
    console.error("API Error:", error); // More detailed error logging
    alert("API Error: " + error.message);
  }
});

// Helper: Read CSV file
function readCSV(file) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target.result;
      console.log("Raw CSV text:", text); // Debug raw file content
      const emails = text.split("\n").map(line => line.trim()).filter(Boolean);
      resolve(emails);
    };
    reader.readAsText(file);
  });
}

// Real API call to Flask backend
async function verifyEmails(emails, onProgress) {
  console.log("Preparing API request with emails:", emails); // Debug request prep
  const formData = new FormData();
  formData.append("file", new Blob([emails.join("\n")], { type: "text/csv" }));

  const response = await fetch("http://localhost:5000/verify", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    console.error("API Response Error:", response); // Debug bad response
    throw new Error(`HTTP error! Status: ${response.status}`);
  }

  const data = await response.json();
  console.log("API Response data:", data); // Debug response data
  return data;
}

// Display results in table
function displayResults(results) {
  // Validate the response
  if (!Array.isArray(results)) {
    console.error("API Error: Expected array, got:", results);
    alert("Server returned invalid data. Check console for details.");
    return;
  }

  const tableBody = document.getElementById("resultsTable");
  tableBody.innerHTML = results.map(result => `
    <tr>
      <td>${result.email}</td>
      <td>${result.status}</td>
    </tr>
  `).join("");

  document.getElementById("resultsSection").style.display = "block";
}

// Export to CSV
document.getElementById("exportBtn").addEventListener("click", () => {
  console.log("Export button clicked"); // Debug export
  const rows = Array.from(document.querySelectorAll("#resultsTable tr"))
    .map(row => {
      const [email, status] = row.children;
      return `${email.textContent},${status.textContent.replace(/[✅❌]/g, "").trim()}`;
    }).join("\n");

  const csv = "Email,Status\n" + rows;
  console.log("Generated CSV:", csv); // Debug CSV content
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "verified_emails.csv";
  a.click();
  console.log("CSV download initiated"); // Debug download
});