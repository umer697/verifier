from flask import Flask, request, jsonify, send_file, render_template
from bulk_verifier import verify_bulk
import os
import uuid
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow all origins (for local testing)
app.config['UPLOAD_FOLDER'] = 'temp_uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Serve frontend
@app.route("/")
def home():
    return render_template("index.html")

# Original bulk verification endpoint
@app.route('/verify_bulk', methods=['POST'])
def api_verify():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty file"}), 400
    
    # Generate unique filenames
    file_id = str(uuid.uuid4())
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_input.csv")
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_output.csv")
    
    try:
        file.save(input_path)
        output_file, stats = verify_bulk(
            input_path,
            output_path,
            smtp_check=False
        )
        
        # Cleanup input file
        os.remove(input_path)
        
        return jsonify({
            "status": "success",
            "download_url": f"/download/{file_id}",
            "stats": stats
        })
    except Exception as e:
        # Clean up if something went wrong
        if os.path.exists(input_path):
            os.remove(input_path)
        return jsonify({"error": str(e)}), 500

# New simple verification endpoint
@app.route("/verify", methods=["POST"])
def verify_emails():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    emails = file.read().decode("utf-8").splitlines()

    # Simulate verification (replace with your actual logic)
    results = []
    for email in emails:
        results.append({"email": email, "status": "valid"})  # Ensure this is an array!

    print("Debug: API response:", results)  # Check the output in terminal
    return jsonify(results)  # Send as JSON array

@app.route('/download/<file_id>', methods=['GET'])
def download(file_id):
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_output.csv")
    if not os.path.exists(output_path):
        return jsonify({"error": "File not found"}), 404
        
    response = send_file(
        output_path,
        as_attachment=True,
        download_name="verified_emails.csv"
    )
    
    # Cleanup output file after sending
    @response.call_on_close
    def remove_file():
        try:
            os.remove(output_path)
        except:
            pass
            
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)