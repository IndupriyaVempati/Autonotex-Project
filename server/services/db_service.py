import os
from pymongo import MongoClient
from datetime import datetime
import re

class DBService:
    def __init__(self):
        self.mongo_uri = os.getenv('MONGO_URI')
        self.client = None
        self.db = None
        
        if self.mongo_uri:
            try:
                self.client = MongoClient(self.mongo_uri)
                self.db = self.client.get_database("autonotex_db")
                print("DBService: Connected to MongoDB Atlas")
            except Exception as e:
                print(f"DBService Error: {e}")

    def save_note(self, content, graph_data, notes_text):
        if self.db is None:
            print("DBService: No DB connection, skipping save.")
            return

        # Extract Subject from Notes (looking for "Subject: [Name]")
        subject = "General"
        match = re.search(r"Subject:\s*(.*)", notes_text)
        if match:
            subject = match.group(1).strip()

        try:
            record = {
                "subject": subject,
                "content_summary": content[:500],
                "graph_data": graph_data,
                "notes_text": notes_text,
                "created_at": datetime.utcnow()
            }
            self.db.notes.insert_one(record)
            print(f"DBService: Saved note for subject '{subject}'")
        except Exception as e:
            print(f"DBService Save Error: {e}")
