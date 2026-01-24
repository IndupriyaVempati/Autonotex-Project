from .base_agent import BaseAgent
import os
import json
import re
from collections import Counter
from groq import Groq

class GraphAgent(BaseAgent):
    def __init__(self):
        super().__init__("GraphAgent")
        self.groq_key = os.getenv("GROQ_API_KEY")
        
        self.groq_client = None
        if self.groq_key and self.groq_key != "gsk-placeholder":
             self.groq_client = Groq(api_key=self.groq_key)
        else:
            print("GraphAgent: No GROQ_API_KEY found. Will use Heuristic Fallback.")

    def process(self, content):
        """
        Takes text content and returns a JSON structure for nodes/edges.
        """
        if not content:
            return {"nodes": [], "edges": []}

        # 1. Try Groq (Preferred for speed/cost)
        if self.groq_client:
            print("GraphAgent: Using Groq")
            return self._process_groq(content)

        # 2. Fallback to Heuristic (Free/Offline)
        print("GraphAgent: Using Heuristic Fallback")
        return self._process_heuristic(content)

    def _process_groq(self, content):
        try:
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Knowledge Graph generator. Extract main concepts as nodes and relationships as edges. Return ONLY JSON object with keys 'nodes' (list of {id, label, type}) and 'edges' (list of {id, source, target, label}). Do not wrap in markdown code blocks."
                    },
                    {
                        "role": "user",
                        "content": f"Extract graph from: {content[:4000]}",
                    }
                ],
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"},
            )
            return json.loads(chat_completion.choices[0].message.content)
        except Exception as e:
            print(f"Groq Error: {e}")
            return self._process_heuristic(content)

    def _process_heuristic(self, content):
        """
        Extracts capitalized words and frequent terms to build a graph without an LLM.
        """
        # Clean text
        text = re.sub(r'\s+', ' ', content)
        
        if "No API Key Provided" in text:
            return {
                "nodes": [{"id": "error", "label": "Please Add Groq API Key", "type": "warning"}],
                "edges": []
            }

        # 1. Find potential concepts (Capitalized words or specific patterns)
        concepts = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        
        # Filter frequent common words
        stopwords = {'The', 'A', 'An', 'In', 'On', 'At', 'To', 'For', 'Of', 'With', 'By', 'And', 'But', 'Or', 'Is', 'Are'}
        concepts = [c for c in concepts if c not in stopwords and len(c) > 2]
        
        # Count frequency to find "Main" nodes
        counts = Counter(concepts)
        top_concepts = counts.most_common(15) 
        
        nodes = []
        edges = []
        
        # Create Nodes
        for i, (label, count) in enumerate(top_concepts):
            nodes.append({
                "id": str(i),
                "label": label,
                "type": "concept" if count < 3 else "topic"
            })
            
        # Create Edges (Star topology)
        if nodes:
            center_id = nodes[0]['id']
            for i in range(1, len(nodes)):
                edges.append({
                    "id": f"e{center_id}-{nodes[i]['id']}",
                    "source": center_id,
                    "target": nodes[i]['id'],
                    "label": "related to"
                })

        return {"nodes": nodes, "edges": edges}
