document.getElementById("verifyBtn").addEventListener("click", async () => {
  const fileInput = document.getElementById("fileInput");
  const file = fileInput.files[0];

  if (!file) {
    alert("Please upload a CSV file first!");
    return;
  }

  // Show progress bar
  document.getElementById("progressSection").style.display = "block";
  const progressBar = document.getElementById("progressBar");

  // Read CSV file
  const emails = await readCSV(file);
  const results = await verifyEmails(emails, (progress) => {
    progressBar.style.width = `${progress}%`;
    progressBar.textContent = `${progress}%`;
  });

  displayResults(results);
});

// Helper: Read CSV file
function readCSV(file) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const emails = e.target.result.split("\n")
        .map(email => email.trim())
        .filter(email => email.length > 0);
      resolve(emails);
    };
    reader.readAsText(file);
  });
}

// Verify emails one-by-one
async function verifyEmails(emails, onProgress) {
  const results = [];
  for (let i = 0; i < emails.length; i++) {
    const email = emails[i];
    const response = await fetch("http://localhost:5000/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });
    const result = await response.json();
    results.push(result);
    onProgress(Math.floor((i + 1) / emails.length * 100));
  }
  return results;
}

// Display results in table
function displayResults(results) {
  const tableBody = document.getElementById("resultsTable");
  tableBody.innerHTML = results.map(result => `
    <tr>
      <td>${result.email}</td>
      <td>${result.status}</td>
      <td>${result.reason || ""}</td>
    </tr>
  `).join("");
  
  document.getElementById("resultsSection").style.display = "block";
}

// Export to CSV
document.getElementById("exportBtn").addEventListener("click", () => {
  const rows = Array.from(document.querySelectorAll("#resultsTable tr"))
    .map(row => {
      const [email, status, reason] = row.children;
      return `"${email.textContent}","${status.textContent}","${reason.textContent}"`;
    }).join("\n");

  const csv = "Email,Status,Reason\n" + rows;
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "verified_emails.csv";
  a.click();
});