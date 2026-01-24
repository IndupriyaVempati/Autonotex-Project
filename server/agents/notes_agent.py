from .base_agent import BaseAgent
import os
from groq import Groq

class NotesAgent(BaseAgent):
    def __init__(self):
        super().__init__("NotesAgent")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.groq_client = None
        if self.groq_key and self.groq_key != "gsk-placeholder":
             self.groq_client = Groq(api_key=self.groq_key)

    def process(self, content):
        """
        Takes raw text content and returns structured markdown notes.
        """
        if not content:
            return ""

        if self.groq_client:
            return self._generate_notes(content)
        
        return self._generate_fallback(content)

    def _generate_notes(self, content):
        try:
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert Professor for B.Tech Engineering subjects (e.g., DBMS, Machine Learning, OS, Data Structures).
                        Analyze the provided content and generate comprehensive notes.
                        
                        Structure:
                        1. **Subject Detection**: Start with "Subject: [Name]" (e.g., DBMS).
                        2. **Summary**: Brief executive summary.
                        3. **Core Concepts**: Detailed explanation.
                        4. **Visual Diagrams**: Generate 1 simple MERMAID diagram using ```mermaid graph TD``` syntax. Use short, simple node labels (no special chars). Visualize the core concept architecture.
                        5. **Adaptive Learning Path**: 3 distinct topics to study next.
                        
                        Output strictly in Markdown."""
                    },
                    {
                        "role": "user",
                        "content": f"Generate notes for: {content[:15000]}", # Limit context quite generous for Llama 3
                    }
                ],
                model="llama-3.3-70b-versatile",
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"Notes Generation Error: {e}")
            return self._generate_fallback(content)

    def _generate_fallback(self, content):
        return f"""
# Auto-Generated Notes (Offline Mode)

**Note:** Please add a valid GROQ_API_KEY to generate smart AI notes.

## Content Preview
{content[:500]}...

## Adaptive Learning Path (Mock)
* Check your API connection.
* Review the document manually.
* Upload a smaller file.
        """
