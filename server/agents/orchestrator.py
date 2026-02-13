from .multimodal_agent import MultimodalAgent
from .graph_agent import GraphAgent
from .notes_agent import NotesAgent
from .qa_agent import QAAgent
from services.db_service import DBService
from services.vector_db_service import VectorDBService
import concurrent.futures
import os
import uuid
import re

class Orchestrator:
    def __init__(self):
        self.multimodal_agent = MultimodalAgent()
        self.graph_agent = GraphAgent()
        self.notes_agent = NotesAgent()
        self.qa_agent = QAAgent()
        self.db_service = DBService()
        self.vector_db = VectorDBService()
        self.default_scope = "private"

    
    def handle_multiple_uploads(self, file_paths, file_types, user_id: str, scope: str = None):
        combined_text = ""
        doc_id = str(uuid.uuid4())[:8]
        self.multimodal_agent.source_diagrams = []
        resolved_scope = scope if scope in {"private", "shared"} else self.default_scope
        
        # 1. Process All Content
        for path, f_type in zip(file_paths, file_types):
            print(f"Orchestrator: Processing {path} (type: {f_type})")
            text = self.multimodal_agent.process({"file_path": path, "file_type": f_type})
            combined_text += f"\n\n--- Source: {os.path.basename(path)} ---\n{text}"

        combined_text = self._dedupe_text(combined_text)
        
        print(f"Orchestrator: Source diagrams extracted: {len(self.multimodal_agent.source_diagrams)}")
        for i, diagram in enumerate(self.multimodal_agent.source_diagrams):
            print(f"  - Diagram {i+1}: {diagram.get('title', 'Unknown')}")

        # 2. Parallel Generation (Graph + Notes + QA) on Combined Text
        print("Orchestrator: Generating Knowledge Artifacts (Merged)")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_graph = executor.submit(self.graph_agent.process, combined_text)
            future_notes = executor.submit(self.notes_agent.process, combined_text)
            future_questions = executor.submit(self.qa_agent.generate_questions, combined_text, 10)
            
            graph_data = future_graph.result()
            notes_text = future_notes.result()
            questions = future_questions.result()
        
        # 3. Add to Vector DB for RAG
        print("Orchestrator: Adding to Vector Database")
        metadata = {
            "doc_id": doc_id,
            "subject": self._extract_subject(notes_text),
            "timestamp": __import__('datetime').datetime.utcnow().isoformat(),
            "user_id": user_id,
            "scope": resolved_scope
        }
        
        chunk_ids = self.vector_db.add_document(combined_text, metadata, doc_id)
        
        # Add concepts to vector DB
        concepts = graph_data.get('concepts', [])
        concept_ids = self.vector_db.add_concepts(concepts, metadata, doc_id)
        
        # 4. Save to MongoDB
        note_data = {
            "content": combined_text,
            "graph": graph_data,
            "notes": notes_text,
            "questions": questions,
            "diagrams": self.multimodal_agent.source_diagrams,
            "subject": self.notes_agent.subject if hasattr(self.notes_agent, 'subject') else "General",
            "source_diagrams": self.multimodal_agent.source_diagrams,
            "user_id": user_id,
            "scope": resolved_scope
        }
        self.db_service.save_note(note_data, doc_id)

        return {
            "doc_id": doc_id,
            "summary": combined_text[:200] + "...",
            "graph": graph_data,
            "notes": notes_text,
            "questions": questions,
            "source_diagrams": self.multimodal_agent.source_diagrams,
            "chunk_count": len(chunk_ids),
            "concept_count": len(concept_ids)
        }

    def _dedupe_text(self, text: str) -> str:
        if not text:
            return text

        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        seen = set()
        kept = []

        for paragraph in paragraphs:
            normalized = self._normalize_text(paragraph)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            kept.append(paragraph)

        return "\n\n".join(kept)

    def _normalize_text(self, text: str) -> str:
        lowered = text.lower()
        lowered = re.sub(r"[^a-z0-9\s]", " ", lowered)
        lowered = re.sub(r"\s+", " ", lowered).strip()
        return lowered

    def handle_upload(self, file_path, file_type, user_id: str, scope: str = None):
        return self.handle_multiple_uploads([file_path], [file_type], user_id, scope)

    def generate_notes_for_subject(self, subject: str, user_id: str, is_admin: bool = False, scope: str = None) -> dict:
        """Retrieve notes using RAG (vector DB) or DB for a subject-only request (no generation)."""
        if not subject:
            return {}

        subject = subject.strip()
        print(f"Orchestrator: Fetching notes for subject '{subject}' using RAG")

        rag_results = []
        if self.vector_db and getattr(self.vector_db, "index", None):
            rag_results = self._scoped_rag_search(
                subject,
                collection_name="notes",
                n_results=8,
                subject=subject,
                user_id=user_id,
                is_admin=is_admin,
                scope=scope
            )

        notes_text = ""
        if rag_results:
            chunks = [r.get("content", "") for r in rag_results if r.get("content")]
            notes_text = "\n\n".join(chunks).strip()

        # Also try MongoDB for richer artifacts (graph/questions) if available
        notes = self.db_service.search_notes_by_subject(subject, user_id, is_admin, scope)
        note = None
        if notes:
            notes_sorted = sorted(
                notes,
                key=lambda n: n.get("updated_at") or n.get("created_at") or 0,
                reverse=True
            )
            note = notes_sorted[0]

        if not notes_text and note:
            notes_text = note.get("notes_text") or note.get("notes") or ""

        if not notes_text:
            return {}

        return {
            "doc_id": note.get("doc_id") if note else None,
            "summary": notes_text[:200] + "...",
            "graph": (note.get("graph_data") if note else None) or (note.get("graph") if note else None) or {"nodes": [], "edges": []},
            "notes": notes_text,
            "questions": note.get("questions") if note else [],
            "source_diagrams": note.get("source_diagrams") if note else [],
            "mode": "subject"
        }

    def get_quiz_questions(self, subject: str, user_id: str, is_admin: bool = False, count: int = 15, scope: str = None) -> list:
        """Get quiz questions - use stored questions if available, otherwise generate from RAG content."""
        if not subject:
            return []

        subject = subject.strip()
        print(f"get_quiz_questions: Looking for questions for {subject}")
        
        # Step 1: Check if questions already exist in MongoDB for this subject
        notes = self.db_service.search_notes_by_subject(subject, user_id, is_admin, scope)
        if notes:
            note = sorted(
                notes,
                key=lambda n: n.get("updated_at") or n.get("created_at") or 0,
                reverse=True
            )[0]
            
            stored_questions = note.get("questions", [])
            print(f"get_quiz_questions: Found {len(stored_questions)} stored questions for {subject}")
            
            if stored_questions and len(stored_questions) > 0:
                # Try to format and validate stored questions
                formatted = self._format_questions(stored_questions, subject)
                if formatted and len(formatted) >= 3:
                    print(f"get_quiz_questions: Using {len(formatted)} valid stored questions")
                    return formatted
                else:
                    print(f"get_quiz_questions: Stored questions not properly formatted, regenerating...")
        
        # Step 2: If no valid stored questions, generate from RAG content
        print(f"get_quiz_questions: Generating new questions from RAG + LLM")
        
        rag_results = self._scoped_rag_search(
            subject,
            collection_name="notes",
            n_results=min(max(8, count * 2), 24),
            subject=subject,
            user_id=user_id,
            is_admin=is_admin,
            scope=scope
        )

        if not rag_results or len(rag_results) == 0:
            print(f"get_quiz_questions: No RAG results, using fallback questions")
            return self._get_fallback_rag_questions(subject)
        
        # Combine RAG results into one coherent content block
        content_chunks = [r.get("content", "") for r in rag_results if r.get("content")]
        content = "\n\n".join(content_chunks)
        print(f"get_quiz_questions: Got {len(content_chunks)} chunks from RAG ({len(content)} chars)")

        # Pass the content to LLM for question generation (only if LLM available)
        if self.qa_agent and self.qa_agent.groq_client:
            print(f"get_quiz_questions: Calling LLM to generate questions...")
            questions = self.qa_agent.generate_questions(content, count)
            if questions and len(questions) > 0:
                print(f"get_quiz_questions: LLM generated {len(questions)} questions, returning")
                return questions
        
        # Fallback if LLM is not available
        print(f"get_quiz_questions: LLM unavailable, using fallback questions")
        return self._get_fallback_rag_questions(subject, count)

    def _get_fallback_rag_questions(self, subject: str, count: int = 15) -> list:
        """Fallback questions based on subject when RAG/LLM fails."""
        base = [
            {
                "question": f"What is the primary focus of {subject}?",
                "options": [
                    f"Understanding {subject} concepts",
                    "Memorizing definitions",
                    "Learning historical facts",
                    "Solving theoretical problems"
                ],
                "correct_answer": 0,
                "explanation": f"The main focus is understanding core {subject} concepts.",
                "explanation_long": f"{subject} emphasizes understanding core ideas and how they connect, not just rote memorization.",
                "category": subject,
                "topic": "Fundamentals",
                "difficulty": "easy",
                "learning_suggestion": f"Review the key definitions and high-level goals of {subject}.",
                "source": "Fallback"
            },
            {
                "question": f"How are the key concepts in {subject} applied in practice?",
                "options": [
                    "Only in academic settings",
                    "Limited real-world application",
                    "Extensively in industry and research",
                    "No practical application"
                ],
                "correct_answer": 2,
                "explanation": f"The concepts in {subject} have extensive real-world applications.",
                "explanation_long": f"Most {subject} concepts translate directly into real systems and workflows used in practice.",
                "category": subject,
                "topic": "Applications",
                "difficulty": "medium",
                "learning_suggestion": f"Look for case studies that show {subject} in real systems.",
                "source": "Fallback"
            }
        ]
        if count <= len(base):
            return base[:count]
        return base

    def _format_questions(self, questions: list, subject: str) -> list:
        """Format and validate questions, accepting both old and new formats."""
        formatted = []
        for q in questions:
            if not isinstance(q, dict):
                continue
                
            # Try to get options (new format)
            options = q.get("options", q.get("choices", []))
            
            # If no options, skip (old format without options)
            if not isinstance(options, list) or len(options) == 0:
                print(f"_format_questions: Skipping question without options: {q.get('question', '')[:50]}")
                continue
            
            # Get correct answer
            correct_answer = q.get("correct_answer", q.get("answer", 0))
            if isinstance(correct_answer, str):
                try:
                    correct_answer = options.index(correct_answer)
                except (ValueError, IndexError):
                    correct_answer = 0
            elif not isinstance(correct_answer, int):
                correct_answer = 0
            
            # Validate correct_answer index
            if correct_answer < 0 or correct_answer >= len(options):
                correct_answer = 0
            
            formatted.append({
                "question": q.get("question", ""),
                "options": options,
                "correct_answer": correct_answer,
                "explanation": q.get("explanation", q.get("explanation_text", "")),
                "explanation_long": q.get("explanation_long", q.get("explanation", q.get("explanation_text", ""))),
                "learning_suggestion": q.get("learning_suggestion", ""),
                "topic": q.get("topic", q.get("category", subject)),
                "category": q.get("category", subject),
                "difficulty": q.get("difficulty", "medium"),
                "source": "From database"
            })
        
        print(f"_format_questions: Formatted {len(formatted)} out of {len(questions)} questions")
        return formatted
    
    def search_knowledge_base(self, query: str, user_id: str, doc_id: str = None, is_admin: bool = False) -> dict:
        """Search for relevant content using RAG."""
        print(f"Orchestrator: Searching for '{query}'")
        
        # Search both notes and concepts
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_notes = executor.submit(
                self._scoped_rag_search,
                query,
                "notes",
                5,
                doc_id,
                None,
                user_id,
                is_admin
            )
            future_concepts = executor.submit(
                self._scoped_rag_search,
                query,
                "concepts",
                3,
                doc_id,
                None,
                user_id,
                is_admin
            )
            
            note_results = future_notes.result()
            concept_results = future_concepts.result()
        
        return {
            "query": query,
            "note_results": note_results,
            "concept_results": concept_results
        }
    
    def get_concept_details(self, concept_label: str, user_id: str, doc_id: str = None, is_admin: bool = False) -> dict:
        """Get detailed information about a specific concept."""
        print(f"Orchestrator: Getting details for concept '{concept_label}'")
        
        # Get related content
        related = self._scoped_rag_search(concept_label, "notes", 3, doc_id, None, user_id, is_admin)
        
        # Generate detailed explanation
        context = "\n".join([r.get('content', '') for r in related[:2]])
        explanation = self.qa_agent.generate_concept_explanation(concept_label, context)
        
        return {
            "concept": concept_label,
            "explanation": explanation,
            "related_content": related
        }
    
    def answer_user_question(self, question: str, user_id: str, doc_id: str = None, is_admin: bool = False) -> dict:
        """Answer a user question using RAG."""
        print(f"Orchestrator: Answering question: '{question}'")
        
        # Search for relevant context
        search_results = self.search_knowledge_base(question, user_id, doc_id, is_admin)
        note_results = search_results.get('note_results', [])

        if not note_results:
            return {
                "question": question,
                "answer": "I couldn't find relevant information in the document to answer this question. Try asking something related to the uploaded content.",
                "sources": [],
                "insufficient_context": True
            }

        top_score = max(r.get('distance', 0) for r in note_results)
        relevance_threshold = 0.25
        if top_score < relevance_threshold:
            return {
                "question": question,
                "answer": "The question seems unrelated to the uploaded document, so I cannot answer it reliably. Please ask something tied to the document content.",
                "sources": note_results[:3],
                "insufficient_context": True
            }
        
        # Build context from search results
        context = "\n\n".join([
            r.get('content', '') for r in note_results[:3]
        ])
        
        # Generate answer
        answer = self.qa_agent.answer_question(question, context)
        
        return {
            "question": question,
            "answer": answer,
            "sources": note_results,
            "insufficient_context": False
        }
    
    def _extract_subject(self, notes_text: str) -> str:
        """Extract subject from notes text."""
        import re
        match = re.search(r"Subject:\s*(.*?)(?:\n|$)", notes_text)
        if match:
            return match.group(1).strip()
        match = re.search(r"#\s*Subject:\s*(.*?)(?:\n|$)", notes_text)
        if match:
            return match.group(1).strip()
        return "General"

    def _scoped_rag_search(
        self,
        query: str,
        collection_name: str = "notes",
        n_results: int = 5,
        doc_id: str = None,
        subject: str = None,
        user_id: str = None,
        is_admin: bool = False,
        scope: str = None
    ) -> list:
        if not self.vector_db or not getattr(self.vector_db, "index", None):
            return []

        if scope == "shared":
            shared_filter = {"scope": {"$eq": "shared"}}
            if doc_id:
                shared_filter["doc_id"] = {"$eq": doc_id}
            if subject:
                shared_filter["subject"] = {"$eq": subject}

            return self.vector_db.semantic_search(
                query,
                collection_name=collection_name,
                n_results=n_results,
                metadata_filter=shared_filter
            )

        if scope == "private":
            if not user_id:
                return []
            private_filter = {"scope": {"$eq": "private"}, "user_id": {"$eq": user_id}}
            if doc_id:
                private_filter["doc_id"] = {"$eq": doc_id}
            if subject:
                private_filter["subject"] = {"$eq": subject}

            return self.vector_db.semantic_search(
                query,
                collection_name=collection_name,
                n_results=n_results,
                metadata_filter=private_filter
            )

        if is_admin:
            admin_filter = {}
            if doc_id:
                admin_filter["doc_id"] = {"$eq": doc_id}
            if subject:
                admin_filter["subject"] = {"$eq": subject}

            return self.vector_db.semantic_search(
                query,
                collection_name=collection_name,
                n_results=n_results,
                metadata_filter=admin_filter or None
            )

        shared_filter = {"scope": {"$eq": "shared"}}
        if doc_id:
            shared_filter["doc_id"] = {"$eq": doc_id}
        if subject:
            shared_filter["subject"] = {"$eq": subject}

        shared_results = self.vector_db.semantic_search(
            query,
            collection_name=collection_name,
            n_results=n_results,
            metadata_filter=shared_filter
        )

        private_results = []
        if user_id:
            private_filter = {"scope": {"$eq": "private"}, "user_id": {"$eq": user_id}}
            if doc_id:
                private_filter["doc_id"] = {"$eq": doc_id}
            if subject:
                private_filter["subject"] = {"$eq": subject}

            private_results = self.vector_db.semantic_search(
                query,
                collection_name=collection_name,
                n_results=n_results,
                metadata_filter=private_filter
            )

        return self._merge_rag_results(shared_results, private_results, n_results)

    def _merge_rag_results(self, shared_results: list, private_results: list, limit: int) -> list:
        seen = set()
        merged = []

        for item in (shared_results or []) + (private_results or []):
            item_id = item.get("id")
            if not item_id or item_id in seen:
                continue
            seen.add(item_id)
            merged.append(item)

        merged.sort(key=lambda x: x.get("distance", 0), reverse=True)
        return merged[:limit]


