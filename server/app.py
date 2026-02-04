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
        print(f"Upload successful. Result keys: {result.keys()}")
        print(f"Graph nodes count: {len(result.get('graph', {}).get('nodes', []))}")
        return jsonify(result), 200
    except Exception as e:
        import traceback
        print("Upload Error:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/search', methods=['POST'])
def search_knowledge_base():
    """
    Search the knowledge base using RAG.
    Request body: {"query": "search term"}
    """
    try:
        data = request.json
        query = data.get('query', '')
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        results = orchestrator.search_knowledge_base(query)
        return jsonify(results), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/concept/<concept_name>', methods=['GET'])
def get_concept_details(concept_name):
    """
    Get detailed information about a specific concept.
    """
    try:
        doc_id = request.args.get('doc_id', None)
        details = orchestrator.get_concept_details(concept_name, doc_id)
        return jsonify(details), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/question', methods=['POST'])
def answer_question():
    """
    Answer a user question using RAG.
    Request body: {"question": "your question", "doc_id": "optional"}
    """
    try:
        data = request.json
        question = data.get('question', '')
        doc_id = data.get('doc_id', None)
        
        if not question:
            return jsonify({"error": "Question is required"}), 400
        
        answer_data = orchestrator.answer_user_question(question, doc_id)
        return jsonify(answer_data), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/notes/<doc_id>', methods=['GET'])
def get_note(doc_id):
    """
    Retrieve a specific note by document ID.
    """
    try:
        note = orchestrator.db_service.get_note_by_id(doc_id)
        if not note:
            return jsonify({"error": "Note not found"}), 404
        
        # Convert MongoDB ObjectId to string for JSON serialization
        note['_id'] = str(note['_id'])
        return jsonify(note), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/notes', methods=['GET'])
def get_all_notes():
    """
    Retrieve all notes (limited) or by subject.
    Query params: limit=10, subject=DBMS
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        subject = request.args.get('subject', None)
        
        if subject:
            # Get notes for specific subject
            notes = orchestrator.db_service.search_notes_by_subject(subject)
            print(f"Retrieved {len(notes)} notes for subject: {subject}")
        else:
            # Get all notes
            notes = orchestrator.db_service.get_all_notes(limit)
        
        # Convert MongoDB ObjectIds to strings for JSON serialization
        for note in notes:
            note['_id'] = str(note['_id'])
        
        return jsonify({"notes": notes, "count": len(notes), "subject": subject}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/generate/notes/subject', methods=['POST'])
def generate_notes_for_subject():
    """
    Generate notes for a typed subject.
    Request body: {"subject": "DBMS"}
    """
    try:
        data = request.json or {}
        subject = data.get('subject', '').strip()

        if not subject:
            return jsonify({"error": "Subject is required"}), 400

        result = orchestrator.generate_notes_for_subject(subject)
        if not result:
            return jsonify({"error": "No notes found for this subject"}), 404

        return jsonify(result), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/subjects', methods=['GET'])
def get_all_subjects():
    """
    Get list of all unique subjects in database.
    """
    try:
        subjects = orchestrator.db_service.get_all_subjects()
        print(f"API /subjects endpoint returning: {subjects}")
        return jsonify({"subjects": subjects, "count": len(subjects)}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/quiz/questions/<subject>', methods=['GET'])
def get_quiz_questions(subject):
    """
    Get quiz questions for a subject.
    """
    try:
        questions = orchestrator.get_quiz_questions(subject)
        if not questions:
            return jsonify({"error": "No quiz questions found for this subject"}), 404
        return jsonify({"questions": questions, "count": len(questions)}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
