import os
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
from datetime import datetime
import re
import time
from bson import ObjectId

class DBService:
    def __init__(self):
        self.mongo_uri = os.getenv('MONGO_URI')
        self.client = None
        self.db = None
        
        if self.mongo_uri:
            try:
                # Add connection pooling and timeout settings
                self.client = MongoClient(
                    self.mongo_uri,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=10000,
                    socketTimeoutMS=10000,
                    retryWrites=True,
                    maxPoolSize=10,
                    minPoolSize=1
                )
                # Test connection
                self.client.admin.command('ping')
                self.db = self.client.get_database("autonotex_db")
                self._ensure_indexes()
                print("DBService: Connected to MongoDB Atlas")
            except (ServerSelectionTimeoutError, ConnectionFailure) as e:
                print(f"DBService Connection Warning: {e}")
                print("DBService: Continuing without database persistence (data will be in-memory)")
                self.db = None
            except Exception as e:
                print(f"DBService Error: {e}")
                self.db = None

    def _ensure_indexes(self):
        if self.db is None:
            return
        try:
            self.db.notes.create_index([("created_at", -1)])
            self.db.notes.create_index([("scope", 1), ("user_id", 1), ("created_at", -1)])
        except Exception as e:
            print(f"DBService Index Warning: {e}")

    def save_note(self, note_data, doc_id=None):
        """Save comprehensive note data with subject, diagrams, etc."""
        if self.db is None:
            print("DBService: No DB connection available. Skipping MongoDB save.")
            return False

        # Extract subject from note_data
        subject = note_data.get('subject', 'General') if isinstance(note_data, dict) else "General"
        scope = note_data.get('scope', 'private') if isinstance(note_data, dict) else "private"
        user_id = note_data.get('user_id') if isinstance(note_data, dict) else None

        try:
            record = {
                "doc_id": doc_id,
                "subject": subject,
                "scope": scope,
                "user_id": user_id,
                "content_summary": note_data.get('content', '')[:500] if isinstance(note_data, dict) else str(note_data)[:500],
                "content_length": len(note_data.get('content', '')) if isinstance(note_data, dict) else len(str(note_data)),
                "graph_data": note_data.get('graph', {}) if isinstance(note_data, dict) else {},
                "notes_text": note_data.get('notes', '') if isinstance(note_data, dict) else str(note_data),
                "questions": note_data.get('questions', []) if isinstance(note_data, dict) else [],
                "diagrams": note_data.get('diagrams', []) if isinstance(note_data, dict) else [],  # Store diagrams
                "source_diagrams": note_data.get('source_diagrams', []) if isinstance(note_data, dict) else [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            if doc_id:
                # Update if exists, otherwise insert
                result = self.db.notes.update_one(
                    {"doc_id": doc_id},
                    {"$set": record},
                    upsert=True
                )
                print(f"DBService: Saved/updated note for subject '{subject}' with {len(record.get('diagrams', []))} diagrams (doc_id: {doc_id})")
            else:
                self.db.notes.insert_one(record)
                print(f"DBService: Saved note for subject '{subject}'")
            return True
        except (ServerSelectionTimeoutError, ConnectionFailure) as e:
            print(f"DBService Save Warning: Connection issue - {type(e).__name__}")
            print("DBService: Note will be cached in-memory only (not persisted to MongoDB)")
            return False
        except Exception as e:
            print(f"DBService Save Error: {e}")
            return False

    def get_note_by_id(self, doc_id: str, user_id: str = None, is_admin: bool = False):
        """Retrieve a note by document ID."""
        if self.db is None:
            return None
        
        try:
            query = {"doc_id": doc_id}
            scope_filter = self._build_scope_filter(user_id, is_admin)
            if scope_filter:
                query.update(scope_filter)
            note = self.db.notes.find_one(query)
            return note
        except Exception as e:
            print(f"DBService Get Error: {e}")
            return None

    def get_all_notes(self, limit: int = 10, user_id: str = None, is_admin: bool = False):
        """Get all notes with optional limit."""
        if self.db is None:
            return []
        
        try:
            query = self._build_scope_filter(user_id, is_admin) or {}
            notes = list(self.db.notes.find(query).sort("created_at", -1).limit(limit))
            return notes
        except Exception as e:
            print(f"DBService Get All Error: {e}")
            try:
                query = self._build_scope_filter(user_id, is_admin) or {}
                pipeline = [
                    {"$match": query},
                    {"$sort": {"created_at": -1}},
                    {"$limit": limit}
                ]
                notes = list(self.db.notes.aggregate(pipeline, allowDiskUse=True))
                return notes
            except Exception as agg_error:
                print(f"DBService Get All Fallback Error: {agg_error}")
                return []

    def search_notes_by_subject(self, subject: str, user_id: str = None, is_admin: bool = False, scope: str = None):
        """Search notes by subject."""
        if self.db is None:
            return []
        
        try:
            query = {"subject": {"$regex": subject, "$options": "i"}}
            scope_filter = self._build_scope_override(user_id, is_admin, scope) or self._build_scope_filter(user_id, is_admin)
            if scope_filter:
                query.update(scope_filter)
            notes = list(self.db.notes.find(query))
            return notes
        except Exception as e:
            print(f"DBService Search Error: {e}")
            return []

    def get_all_subjects(self, user_id: str = None, is_admin: bool = False, scope: str = None):
        """Get all unique subjects in database."""
        if self.db is None:
            print("DBService: No database connection")
            return []
        
        try:
            filter_query = self._build_scope_override(user_id, is_admin, scope) or self._build_scope_filter(user_id, is_admin) or {}
            subjects = self.db.notes.distinct("subject", filter_query)
            print(f"DBService: Found {len(subjects)} subjects: {subjects}")
            return sorted([s for s in subjects if s and str(s).strip()])
        except Exception as e:
            print(f"DBService Get Subjects Error: {e}")
            return []

    def get_user_by_email(self, email: str):
        if self.db is None or not email:
            return None
        try:
            return self.db.users.find_one({"email": email.lower().strip()})
        except Exception as e:
            print(f"DBService Get User Error: {e}")
            return None

    def get_user_by_id(self, user_id: str):
        if self.db is None or not user_id:
            return None
        try:
            return self.db.users.find_one({"_id": ObjectId(user_id)})
        except Exception as e:
            print(f"DBService Get User By ID Error: {e}")
            return None

    def create_user(self, email: str, password_hash: str, role: str = "user"):
        if self.db is None:
            return None
        try:
            record = {
                "email": email.lower().strip(),
                "password_hash": password_hash,
                "role": role,
                "created_at": datetime.utcnow()
            }
            result = self.db.users.insert_one(record)
            record["_id"] = str(result.inserted_id)
            return record
        except Exception as e:
            print(f"DBService Create User Error: {e}")
            return None

    def _build_scope_filter(self, user_id: str = None, is_admin: bool = False) -> dict:
        if is_admin:
            return {}
        if not user_id:
            return {"scope": "shared"}
        return {
            "$or": [
                {"scope": "shared"},
                {"scope": "private", "user_id": user_id}
            ]
        }

    def _build_scope_override(self, user_id: str = None, is_admin: bool = False, scope: str = None) -> dict:
        if not scope:
            return {}
        if scope == "shared":
            return {"scope": "shared"}
        if scope == "private":
            if not user_id:
                return {"scope": "private", "user_id": "__none__"}
            return {"scope": "private", "user_id": user_id}
        return {}

    def delete_note(self, doc_id: str, user_id: str = None, is_admin: bool = False):
        """Delete a note by document ID with scope enforcement."""
        if self.db is None:
            return False
        
        try:
            query = {"doc_id": doc_id}
            if not is_admin:
                query.update({"scope": "private", "user_id": user_id})

            result = self.db.notes.delete_one(query)
            if result.deleted_count > 0:
                print(f"DBService: Deleted note with doc_id {doc_id}")
                return True
            return False
        except Exception as e:
            print(f"DBService Delete Error: {e}")
            return False
