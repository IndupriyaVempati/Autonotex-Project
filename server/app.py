from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os
import jwt
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from agents.orchestrator import Orchestrator
from config import Config

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True)
Config.init_app(app)

orchestrator = Orchestrator()

def _create_token(user: dict) -> str:
    payload = {
        "sub": str(user.get("_id")),
        "email": user.get("email"),
        "role": user.get("role", "user"),
        "exp": datetime.utcnow() + timedelta(minutes=Config.JWT_EXPIRES_MIN)
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm="HS256")

def _get_bearer_token():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    return auth_header.split(" ", 1)[1].strip()

def _get_current_user():
    token = _get_bearer_token()
    if not token:
        return None
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            return None
        user = orchestrator.db_service.get_user_by_id(user_id)
        if not user:
            return None

        token_role = payload.get("role")
        if token_role and user.get("role") != token_role:
            user["role"] = token_role

        admin_email = (Config.ADMIN_EMAIL or "").strip().lower()
        if admin_email and user.get("email", "").lower() == admin_email:
            user["role"] = "admin"
        return user
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = _get_current_user()
        if not user:
            return jsonify({"error": "Unauthorized"}), 401
        request.user = user
        return fn(*args, **kwargs)
    return wrapper

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "Autonotex Backend"}), 200

@app.route('/auth/register', methods=['POST'])
def register_user():
    data = request.json or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    if Config.ADMIN_EMAIL and email == Config.ADMIN_EMAIL.lower():
        return jsonify({"error": "Admin account is restricted"}), 403

    if orchestrator.db_service.get_user_by_email(email):
        return jsonify({"error": "User already exists"}), 409

    password_hash = generate_password_hash(password)
    user = orchestrator.db_service.create_user(email, password_hash)
    if not user:
        return jsonify({"error": "Failed to create user"}), 500

    token = _create_token(user)
    return jsonify({
        "token": token,
        "user": {
            "id": user.get("_id"),
            "email": user.get("email"),
            "role": user.get("role", "user")
        }
    }), 201

@app.route('/auth/login', methods=['POST'])
def login_user():
    data = request.json or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    if Config.ADMIN_EMAIL and Config.ADMIN_PASSWORD:
        if email == Config.ADMIN_EMAIL.lower() and password == Config.ADMIN_PASSWORD:
            user = orchestrator.db_service.get_user_by_email(email)
            if not user:
                user = orchestrator.db_service.create_user(email, generate_password_hash(password), role="admin")
            elif orchestrator.db_service.db is not None:
                orchestrator.db_service.db.users.update_one(
                    {"_id": user.get("_id")},
                    {"$set": {"role": "admin"}}
                )
                user["role"] = "admin"
            else:
                return jsonify({"error": "Database unavailable"}), 503

            token = _create_token(user)
            return jsonify({
                "token": token,
                "user": {
                    "id": str(user.get("_id")),
                    "email": user.get("email"),
                    "role": user.get("role", "admin")
                }
            }), 200

    user = orchestrator.db_service.get_user_by_email(email)
    if not user or not check_password_hash(user.get("password_hash", ""), password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = _create_token(user)
    return jsonify({
        "token": token,
        "user": {
            "id": str(user.get("_id")),
            "email": user.get("email"),
            "role": user.get("role", "user")
        }
    }), 200

@app.route('/auth/me', methods=['GET'])
@require_auth
def get_current_user_profile():
    user = request.user
    return jsonify({
        "user": {
            "id": str(user.get("_id")),
            "email": user.get("email"),
            "role": user.get("role", "user")
        }
    }), 200

@app.route('/upload', methods=['POST'])
@require_auth
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
        
    user = request.user
    scope = "shared" if user.get("role") == "admin" else "private"

    # Process with Agents
    try:
        # We pass the list to orchestrator to merge
        result = orchestrator.handle_multiple_uploads(uploaded_paths, file_types, str(user.get("_id")), scope)
        print(f"Upload successful. Result keys: {result.keys()}")
        print(f"Graph nodes count: {len(result.get('graph', {}).get('nodes', []))}")
        return jsonify(result), 200
    except Exception as e:
        import traceback
        print("Upload Error:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/search', methods=['POST'])
@require_auth
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
        
        user = request.user
        is_admin = user.get("role") == "admin"
        results = orchestrator.search_knowledge_base(query, str(user.get("_id")), None, is_admin)
        return jsonify(results), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/concept/<concept_name>', methods=['GET'])
@require_auth
def get_concept_details(concept_name):
    """
    Get detailed information about a specific concept.
    """
    try:
        doc_id = request.args.get('doc_id', None)
        user = request.user
        is_admin = user.get("role") == "admin"
        details = orchestrator.get_concept_details(concept_name, str(user.get("_id")), doc_id, is_admin)
        return jsonify(details), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/question', methods=['POST'])
@require_auth
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
        
        user = request.user
        is_admin = user.get("role") == "admin"
        answer_data = orchestrator.answer_user_question(question, str(user.get("_id")), doc_id, is_admin)
        return jsonify(answer_data), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/notes/<doc_id>', methods=['GET'])
@require_auth
def get_note(doc_id):
    """
    Retrieve a specific note by document ID.
    """
    try:
        user = request.user
        is_admin = user.get("role") == "admin"
        note = orchestrator.db_service.get_note_by_id(doc_id, str(user.get("_id")), is_admin)
        if not note:
            return jsonify({"error": "Note not found"}), 404
        
        # Convert MongoDB ObjectId to string for JSON serialization
        note['_id'] = str(note['_id'])
        return jsonify(note), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/notes/<doc_id>', methods=['DELETE'])
@require_auth
def delete_note(doc_id):
    try:
        user = request.user
        is_admin = user.get("role") == "admin"
        deleted = orchestrator.db_service.delete_note(doc_id, str(user.get("_id")), is_admin)
        if not deleted:
            return jsonify({"error": "Not found or not allowed"}), 404

        if orchestrator.vector_db:
            orchestrator.vector_db.delete_document(doc_id)
        return jsonify({"status": "deleted", "doc_id": doc_id}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/notes', methods=['GET'])
@require_auth
def get_all_notes():
    """
    Retrieve all notes (limited) or by subject.
    Query params: limit=10, subject=DBMS
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        subject = request.args.get('subject', None)
        
        user = request.user
        is_admin = user.get("role") == "admin"
        if subject:
            # Get notes for specific subject
            notes = orchestrator.db_service.search_notes_by_subject(subject, str(user.get("_id")), is_admin)
            print(f"Retrieved {len(notes)} notes for subject: {subject}")
        else:
            # Get all notes
            notes = orchestrator.db_service.get_all_notes(limit, str(user.get("_id")), is_admin)
        
        # Convert MongoDB ObjectIds to strings for JSON serialization
        for note in notes:
            note['_id'] = str(note['_id'])
        
        return jsonify({"notes": notes, "count": len(notes), "subject": subject}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/generate/notes/subject', methods=['POST'])
@require_auth
def generate_notes_for_subject():
    """
    Generate notes for a typed subject.
    Request body: {"subject": "DBMS"}
    """
    try:
        data = request.json or {}
        subject = data.get('subject', '').strip()
        scope = (data.get('scope') or '').strip().lower() or None

        if not subject:
            return jsonify({"error": "Subject is required"}), 400

        user = request.user
        is_admin = user.get("role") == "admin"
        result = orchestrator.generate_notes_for_subject(subject, str(user.get("_id")), is_admin, scope)
        if not result:
            return jsonify({"error": "No notes found for this subject"}), 404

        return jsonify(result), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/subjects', methods=['GET'])
@require_auth
def get_all_subjects():
    """
    Get list of all unique subjects in database.
    """
    try:
        user = request.user
        is_admin = user.get("role") == "admin"
        scope = (request.args.get('scope') or '').strip().lower() or None
        subjects = orchestrator.db_service.get_all_subjects(str(user.get("_id")), is_admin, scope)
        print(f"API /subjects endpoint returning: {subjects}")
        return jsonify({"subjects": subjects, "count": len(subjects)}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/quiz/questions/<subject>', methods=['GET'])
@require_auth
def get_quiz_questions(subject):
    """
    Get quiz questions for a subject.
    """
    try:
        user = request.user
        is_admin = user.get("role") == "admin"
        scope = (request.args.get('scope') or '').strip().lower() or None
        count = request.args.get('count', 15, type=int)
        questions = orchestrator.get_quiz_questions(subject, str(user.get("_id")), is_admin, count, scope)
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
