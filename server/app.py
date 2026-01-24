from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os
from agents.orchestrator import Orchestrator
from config import Config

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)
Config.init_app(app)

orchestrator = Orchestrator()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "Autonotex Backend"}), 200

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'files' not in request.files:
        if 'file' in request.files: # Fallback for single file
            files = [request.files['file']]
        else:
            return jsonify({"error": "No file part"}), 400
    else:
        files = request.files.getlist('files')

    if not files or files[0].filename == '':
        return jsonify({"error": "No selected file"}), 400

    uploaded_paths = []
    file_types = []

    for file in files:
        if file:
            filepath = os.path.join(Config.UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            uploaded_paths.append(filepath)
            file_types.append(file.content_type)
        
    # Process with Agents
    try:
        # We pass the list to orchestrator to merge
        result = orchestrator.handle_multiple_uploads(uploaded_paths, file_types)
        return jsonify(result), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
