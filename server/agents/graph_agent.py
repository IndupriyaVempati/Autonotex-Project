from .base_agent import BaseAgent, rate_limit_retry
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
        Takes text content and returns a JSON structure for nodes/edges with detailed information.
        """
        if not content:
            return {"nodes": [], "edges": [], "concepts": []}

        # 1. Try Groq (Preferred for speed/cost)
        if self.groq_client:
            print("GraphAgent: Using Groq with retry logic")
            return self._process_groq_with_retry(content)

        # 2. Fallback to Heuristic (Free/Offline)
        print("GraphAgent: Using Heuristic Fallback")
        return self._process_heuristic(content)

    def _process_groq_with_retry(self, content, max_retries=3):
        """Process with Groq and retry on failure (with rate-limit backoff + model fallback)."""
        try:
            print(f"GraphAgent: Processing content of length {len(content)}")
            chat_completion = rate_limit_retry(
                self.groq_client,
                dict(
                    messages=[
                        {
                            "role": "system",
                            "content": """You are a Knowledge Graph generator for academic subjects. Extract ONLY core concepts as nodes.
                            FILTER OUT: common words (is, are, the, this, that, here, there, etc.), pronouns, prepositions.
                            KEEP ONLY: subject-specific technical terms, key concepts, domain terminology.
                            Return ONLY a JSON object with:
                            - 'nodes': list of {id, label, type, description} - max 12 nodes, only core concepts
                            - 'edges': list of {id, source, target, label, strength} - relationships between core concepts
                            - 'concepts': list of {id, label, category, description, importance}
                            Do not wrap in markdown code blocks."""
                        },
                        {
                            "role": "user",
                            "content": f"Extract core concept graph (NOT common words, only technical terms) from:\n\n{content[:5000]}",
                        }
                    ],
                    model="llama-3.3-70b-versatile",
                    response_format={"type": "json_object"}
                ),
                max_retries=max_retries,
                agent_name="GraphAgent"
            )
            result = json.loads(chat_completion.choices[0].message.content)
            print(f"GraphAgent: Raw LLM result - nodes count: {len(result.get('nodes', []))}")
            
            # Filter nodes to remove any remaining stop words
            result['nodes'] = self._filter_stop_word_nodes(result.get('nodes', []))
            
            # If after filtering we have 0 nodes, use heuristic fallback
            if len(result['nodes']) == 0:
                print("GraphAgent: LLM extracted no meaningful concepts, falling back to heuristic")
                return self._process_heuristic(content)
            
            # Ensure all required fields exist
            if 'concepts' not in result:
                result['concepts'] = self._extract_concepts_from_nodes(result.get('nodes', []))
            
            print(f"GraphAgent: Successfully processed with Groq. Extracted {len(result['nodes'])} core concepts")
            return result
        except Exception as e:
            print(f"GraphAgent: All attempts failed ({e}), falling back to heuristic")
            return self._process_heuristic(content)

    def _extract_concepts_from_nodes(self, nodes):
        """Extract concepts from nodes for detailed view."""
        concepts = []
        for i, node in enumerate(nodes):
            concepts.append({
                "id": node.get('id', str(i)),
                "label": node.get('label', 'Unknown'),
                "category": node.get('type', 'general'),
                "description": node.get('description', f"Concept related to {node.get('label', 'this topic')}"),
                "importance": "high" if node.get('type') == 'topic' else 'medium'
            })
        return concepts

    def _filter_stop_word_nodes(self, nodes):
        """Remove common stop words that should not be core concept nodes."""
        stop_words = {
            'is', 'are', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'from', 'this', 'that', 'these', 'those', 'here', 'there', 
            'they', 'them', 'their', 'he', 'she', 'it', 'we', 'you', 'i', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'can', 'may', 'might', 'must', 'as', 'if', 'because', 'so', 'what', 'which', 'who',
            'when', 'where', 'why', 'how', 'much', 'many', 'some', 'any', 'all', 'each', 'every',
            'no', 'not', 'only', 'own', 'same', 'then', 'than', 'more', 'most', 'other', 'such',
            'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'up', 'down'
        }
        
        filtered = []
        for node in nodes:
            label = node.get('label', '').lower().strip()
            # Keep node if it's not a stop word and has meaningful length
            if label not in stop_words and len(label) > 2 and not label.replace(' ', '').isdigit():
                filtered.append(node)
        
        return filtered[:12]  # Max 12 core concepts

    def _process_heuristic(self, content):
        """
        Extracts capitalized words and frequent terms to build a graph without an LLM.
        Filters to keep only meaningful domain concepts.
        """
        # Clean text
        text = re.sub(r'\s+', ' ', content)
        
        if "No API Key Provided" in text:
            return {
                "nodes": [{"id": "error", "label": "Please Add Groq API Key", "type": "warning", "description": "API key is required for full features"}],
                "edges": [],
                "concepts": []
            }

        # Extended stop words list
        stopwords = {
            'The', 'A', 'An', 'In', 'On', 'At', 'To', 'For', 'Of', 'With', 'By', 'And', 'But', 'Or', 'Is', 'Are',
            'Be', 'Been', 'Being', 'Have', 'Has', 'Had', 'Do', 'Does', 'Did', 'Will', 'Would', 'Could', 'Should',
            'Can', 'May', 'Might', 'Must', 'As', 'If', 'Because', 'So', 'What', 'Which', 'Who', 'When', 'Where',
            'Why', 'How', 'Much', 'Many', 'Some', 'Any', 'All', 'Each', 'Every', 'No', 'Not', 'Only', 'Own',
            'Same', 'Then', 'Than', 'More', 'Most', 'Other', 'Such', 'About', 'Into', 'Through', 'During',
            'Before', 'After', 'Above', 'Below', 'Up', 'Down', 'Out', 'Off', 'Over', 'Under', 'Again', 'Further',
            'Their', 'They', 'Them', 'He', 'She', 'It', 'We', 'You', 'I', 'He', 'Here', 'There', 'This', 'That',
            'These', 'Those'
        }

        # 1. Find potential concepts (Capitalized words or specific patterns)
        concepts = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        
        # Filter out stop words and short terms
        concepts = [c for c in concepts if c not in stopwords and len(c) > 2]
        
        # Count frequency to find "Main" nodes
        counts = Counter(concepts)
        top_concepts = counts.most_common(12)  # Limit to 12 core concepts
        
        nodes = []
        edges = []
        concept_list = []
        
        # Create Nodes
        for i, (label, count) in enumerate(top_concepts):
            node_type = "topic" if count >= 3 else "concept"
            nodes.append({
                "id": str(i),
                "label": label,
                "type": node_type,
                "description": f"Core concept in domain"
            })
            
            concept_list.append({
                "id": str(i),
                "label": label,
                "category": node_type,
                "description": f"Key domain concept mentioned {count} times",
                "importance": "high" if count >= 3 else 'medium'
            })
            
        # Create Edges (Star topology with some connectivity)
        if nodes:
            center_id = nodes[0]['id']
            for i in range(1, min(len(nodes), 8)):  # Limit edges for clarity
                edges.append({
                    "id": f"e{center_id}-{nodes[i]['id']}",
                    "source": center_id,
                    "target": nodes[i]['id'],
                    "label": "related",
                    "strength": 0.7
                })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "concepts": concept_list
        }
