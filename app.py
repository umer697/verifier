from flask import Flask, request, jsonify
from email_verifier import verify_email
from flask_cors import CORS  # Add this line

app = Flask(__name__)
CORS(app)  # Allow frontend to connect

@app.route("/verify", methods=["POST"])
def verify_emails():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["file"]
    emails = file.read().decode("utf-8").splitlines()
    
    results = []
    for email in emails:
        is_valid, reason = verify_email(email)  # Real verification
        results.append({
            "email": email,
            "status": "✅ Valid" if is_valid else "❌ Invalid",
            "reason": reason
        })
    
    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)