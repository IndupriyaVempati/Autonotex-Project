import os
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
from datetime import datetime
import re
import time

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
                print("DBService: Connected to MongoDB Atlas")
            except (ServerSelectionTimeoutError, ConnectionFailure) as e:
                print(f"DBService Connection Warning: {e}")
                print("DBService: Continuing without database persistence (data will be in-memory)")
                self.db = None
            except Exception as e:
                print(f"DBService Error: {e}")
                self.db = None

    def save_note(self, note_data, doc_id=None):
        """Save comprehensive note data with subject, diagrams, etc."""
        if self.db is None:
            print("DBService: No DB connection available. Skipping MongoDB save.")
            return False

        # Extract subject from note_data
        subject = note_data.get('subject', 'General') if isinstance(note_data, dict) else "General"

        try:
            record = {
                "doc_id": doc_id,
                "subject": subject,
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

    def get_note_by_id(self, doc_id: str):
        """Retrieve a note by document ID."""
        if self.db is None:
            return None
        
        try:
            note = self.db.notes.find_one({"doc_id": doc_id})
            return note
        except Exception as e:
            print(f"DBService Get Error: {e}")
            return None

    def get_all_notes(self, limit: int = 10):
        """Get all notes with optional limit."""
        if self.db is None:
            return []
        
        try:
            notes = list(self.db.notes.find().sort("created_at", -1).limit(limit))
            return notes
        except Exception as e:
            print(f"DBService Get All Error: {e}")
            return []

    def search_notes_by_subject(self, subject: str):
        """Search notes by subject."""
        if self.db is None:
            return []
        
        try:
            notes = list(self.db.notes.find({"subject": {"$regex": subject, "$options": "i"}}))
            return notes
        except Exception as e:
            print(f"DBService Search Error: {e}")
            return []

    def get_all_subjects(self):
        """Get all unique subjects in database."""
        if self.db is None:
            print("DBService: No database connection")
            return []
        
        try:
            subjects = self.db.notes.distinct("subject")
            print(f"DBService: Found {len(subjects)} subjects: {subjects}")
            return sorted([s for s in subjects if s and str(s).strip()])
        except Exception as e:
            print(f"DBService Get Subjects Error: {e}")
            return []

    def delete_note(self, doc_id: str):
        """Delete a note by document ID."""
        if self.db is None:
            return False
        
        try:
            result = self.db.notes.delete_one({"doc_id": doc_id})
            if result.deleted_count > 0:
                print(f"DBService: Deleted note with doc_id {doc_id}")
                return True
            return False
        except Exception as e:
            print(f"DBService Delete Error: {e}")
            return False
