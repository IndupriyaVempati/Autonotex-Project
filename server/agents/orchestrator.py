from .multimodal_agent import MultimodalAgent
from .graph_agent import GraphAgent
from .notes_agent import NotesAgent
from services.db_service import DBService
import concurrent.futures
import os

class Orchestrator:
    def __init__(self):
        self.multimodal_agent = MultimodalAgent()
        self.graph_agent = GraphAgent()
        self.notes_agent = NotesAgent()
        self.db_service = DBService()

    
    def handle_multiple_uploads(self, file_paths, file_types):
        combined_text = ""
        
        # 1. Process All Content
        for path, f_type in zip(file_paths, file_types):
            print(f"Orchestrator: Processing {path}")
            text = self.multimodal_agent.process({"file_path": path, "file_type": f_type})
            combined_text += f"\n\n--- Source: {os.path.basename(path)} ---\n{text}"

        # 2. Parallel Generation (Graph + Notes) on Combined Text
        print("Orchestrator: Generating Knowledge Artifacts (Merged)")
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_graph = executor.submit(self.graph_agent.process, combined_text)
            future_notes = executor.submit(self.notes_agent.process, combined_text)
            
            graph_data = future_graph.result()
            notes_text = future_notes.result()
        
        # 3. Save to DB
        self.db_service.save_note(combined_text, graph_data, notes_text)

        return {
            "summary": combined_text[:200] + "...",
            "graph": graph_data,
            "notes": notes_text
        }

    def handle_upload(self, file_path, file_type):
        return self.handle_multiple_uploads([file_path], [file_type])


