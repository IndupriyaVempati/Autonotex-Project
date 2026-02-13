import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from datetime import datetime
from pinecone import Pinecone, ServerlessSpec
import json
import re
from difflib import SequenceMatcher

class VectorDBService:
    def __init__(self):
        """Initialize Pinecone vector database for semantic search and RAG."""
        self.index_name = os.getenv("PINECONE_INDEX", "autonotex-notes")
        self.embedding_model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.embedding_dimension = int(os.getenv("EMBEDDING_DIM", "384"))

        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            print("WARNING: PINECONE_API_KEY not found. Vector DB will be unavailable.")
            self.pc = None
            self.index = None
        else:
            try:
                self.pc = Pinecone(api_key=api_key)

                # Create index if it doesn't exist
                existing_indexes = [idx.name for idx in self.pc.list_indexes()]
                if self.index_name not in existing_indexes:
                    cloud = os.getenv("PINECONE_CLOUD", "aws")
                    region = os.getenv("PINECONE_REGION", "us-east-1")
                    print(f"Creating Pinecone index: {self.index_name}")
                    self.pc.create_index(
                        name=self.index_name,
                        dimension=self.embedding_dimension,
                        metric="cosine",
                        spec=ServerlessSpec(cloud=cloud, region=region)
                    )

                self.index = self.pc.Index(self.index_name)
                print("VectorDBService: Connected to Pinecone")
            except Exception as e:
                print(f"ERROR: Failed to connect to Pinecone: {e}")
                self.pc = None
                self.index = None

        self.embedding_model = SentenceTransformer(self.embedding_model_name)

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", " ", ""]
        )

        print("VectorDBService: Initialized successfully")

    def add_document(self, content: str, metadata: dict, doc_id: str) -> list:
        """
        Add document to vector DB with semantic chunking.
        """
        if not self.index:
            print("VectorDBService: Vector DB not available, skipping document storage")
            return []
        
        try:
            # Split content into meaningful chunks
            chunks = self.text_splitter.split_text(content)
            chunks = self._dedupe_chunks(chunks)
            if not chunks:
                return []

            embeddings = self.embedding_model.encode(chunks).tolist()
            chunk_ids = []
            vectors = []

            for i, (chunk, vector) in enumerate(zip(chunks, embeddings)):
                chunk_id = f"{doc_id}_chunk_{i}"
                chunk_ids.append(chunk_id)
                vectors.append((
                    chunk_id,
                    vector,
                    {
                        **metadata,
                        "content": chunk,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "added_at": datetime.utcnow().isoformat()
                    }
                ))

            self.index.upsert(vectors=vectors, namespace="notes")

            print(f"VectorDBService: Added {len(chunks)} chunks for document {doc_id}")
            return chunk_ids
        except Exception as e:
            print(f"VectorDBService Error adding document: {e}")
            return []

    def _dedupe_chunks(self, chunks: list) -> list:
        seen = set()
        kept = []
        recent = []
        max_recent = 50

        for chunk in chunks:
            normalized = self._normalize_text(chunk)
            if not normalized:
                continue

            if normalized in seen:
                continue

            is_near_duplicate = False
            for prev in recent:
                if SequenceMatcher(None, normalized, prev).ratio() >= 0.92:
                    is_near_duplicate = True
                    break

            if is_near_duplicate:
                continue

            seen.add(normalized)
            kept.append(chunk)
            recent.append(normalized)
            if len(recent) > max_recent:
                recent.pop(0)

        removed = len(chunks) - len(kept)
        if removed > 0:
            print(f"VectorDBService: Deduped {removed} duplicate chunks")
        return kept

    def _normalize_text(self, text: str) -> str:
        lowered = text.lower()
        lowered = re.sub(r"[^a-z0-9\s]", " ", lowered)
        lowered = re.sub(r"\s+", " ", lowered).strip()
        return lowered

    def add_concepts(self, concepts: list, metadata: dict, doc_id: str) -> list:
        """
        Add extracted concepts to vector DB.
        
        Args:
            concepts: List of concept dictionaries with 'label' and 'description'
            metadata: Document metadata
            doc_id: Document identifier
            
        Returns:
            List of concept IDs added
        """
        try:
            if not concepts:
                return []

            descriptions = []
            concept_ids = []
            vectors = []

            for i, concept in enumerate(concepts):
                concept_id = f"{doc_id}_concept_{i}"
                concept_ids.append(concept_id)
                description = f"{concept.get('label', '')}: {concept.get('description', '')}"
                descriptions.append(description)

            embeddings = self.embedding_model.encode(descriptions).tolist()

            for i, (concept, vector) in enumerate(zip(concepts, embeddings)):
                concept_id = concept_ids[i]
                description = descriptions[i]
                vectors.append((
                    concept_id,
                    vector,
                    {
                        **metadata,
                        "content": description,
                        "concept_label": concept.get('label', ''),
                        "concept_type": concept.get('type', 'general'),
                        "added_at": datetime.utcnow().isoformat()
                    }
                ))

            self.index.upsert(vectors=vectors, namespace="concepts")

            print(f"VectorDBService: Added {len(concept_ids)} concepts")
            return concept_ids
        except Exception as e:
            print(f"VectorDBService Error adding concepts: {e}")
            return []

    def semantic_search(
        self,
        query: str,
        collection_name: str = "notes",
        n_results: int = 5,
        doc_id: str = None,
        subject: str = None,
        metadata_filter: dict = None
    ) -> list:
        """
        Search for relevant documents using semantic similarity.
        
        Args:
            query: Search query
            collection_name: "notes" or "concepts"
            n_results: Number of results to return
            
        Returns:
            List of relevant chunks/concepts with metadata
        """
        try:
            vector = self.embedding_model.encode([query]).tolist()[0]
            query_kwargs = {
                "vector": vector,
                "top_k": n_results,
                "include_metadata": True,
                "namespace": collection_name
            }

            filters = {}
            if doc_id:
                filters["doc_id"] = {"$eq": doc_id}
            if subject:
                filters["subject"] = {"$eq": subject}
            if metadata_filter:
                filters.update(metadata_filter)

            if filters:
                query_kwargs["filter"] = filters

            results = self.index.query(**query_kwargs)

            formatted_results = []
            for match in results.get("matches", []):
                metadata = match.get("metadata", {}) or {}
                formatted_results.append({
                    "id": match.get("id"),
                    "content": metadata.get("content", ""),
                    "metadata": metadata,
                    "distance": match.get("score", 0)
                })

            return formatted_results
        except Exception as e:
            print(f"VectorDBService Search Error: {e}")
            return []

    def get_related_content(self, concept_label: str, n_results: int = 3) -> list:
        """Get content related to a specific concept."""
        try:
            results = self.semantic_search(concept_label, "notes", n_results)
            related = []
            for item in results:
                related.append({
                    "content": item.get("content", ""),
                    "metadata": item.get("metadata", {})
                })

            return related
        except Exception as e:
            print(f"Error getting related content: {e}")
            return []

    def get_document_summary(self, doc_id: str) -> dict:
        """Get all chunks for a document with context."""
        try:
            vector = self.embedding_model.encode([doc_id]).tolist()[0]
            results = self.index.query(
                vector=vector,
                top_k=100,
                include_metadata=True,
                namespace="notes",
                filter={"doc_id": {"$eq": doc_id}}
            )

            chunks = []
            for match in results.get("matches", []):
                metadata = match.get("metadata", {}) or {}
                chunks.append({
                    "chunk_index": metadata.get("chunk_index", 0),
                    "content": metadata.get("content", ""),
                    "metadata": metadata
                })

            chunks.sort(key=lambda x: x["chunk_index"])
            return {
                "doc_id": doc_id,
                "total_chunks": len(chunks),
                "chunks": chunks
            }
        except Exception as e:
            print(f"Error getting document summary: {e}")
            return {}

    def delete_document(self, doc_id: str):
        """Delete all chunks of a document."""
        try:
            self.index.delete(filter={"doc_id": {"$eq": doc_id}}, namespace="notes")
            self.index.delete(filter={"doc_id": {"$eq": doc_id}}, namespace="concepts")
            print(f"VectorDBService: Deleted document {doc_id}")
        except Exception as e:
            print(f"Error deleting document: {e}")
