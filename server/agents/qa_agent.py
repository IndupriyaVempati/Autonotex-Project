from .base_agent import BaseAgent, rate_limit_retry
import os
import json
from groq import Groq

class QAAgent(BaseAgent):
    def __init__(self):
        super().__init__("QAAgent")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.groq_client = None
        if self.groq_key and self.groq_key != "gsk-placeholder":
            self.groq_client = Groq(api_key=self.groq_key)

    def process(self, content):
        """
        Process method required by BaseAgent.
        Generates questions from content.
        
        Args:
            content: Text content to generate questions from
            
        Returns:
            List of generated questions
        """
        return self.generate_questions(content, 10)

    def generate_questions(self, content: str, num_questions: int = 10) -> list:
        """
        Generate multiple choice questions from content.
        
        Args:
            content: Text content to generate questions from
            num_questions: Number of questions to generate
            
        Returns:
            List of multiple choice questions with options and correct answer
        """
        if not self.groq_client:
            return self._fallback_questions()

        try:
            chat_completion = rate_limit_retry(
                self.groq_client,
                dict(
                    messages=[
                        {
                            "role": "system",
                            "content": f"""You are an expert educator creating high-quality multiple choice quiz questions.

Generate {num_questions} multiple choice questions about the provided content.
Each question must have 4 options (A, B, C, D) and one correct answer.
Include a mix of easy, medium, and hard difficulties.

Return ONLY a JSON object with this exact structure:
{{
    "questions": [
        {{
            "question": "What is...?",
            "options": ["Option A text", "Option B text", "Option C text", "Option D text"],
            "correct_answer": 0,
            "explanation": "Short explanation",
            "explanation_long": "Longer, step-by-step explanation",
            "learning_suggestion": "What to review if the learner got this wrong",
            "topic": "Specific topic",
            "category": "Topic Name",
            "difficulty": "easy|medium|hard"
        }}
    ]
}}

IMPORTANT:
- options must be a list of 4 strings (NOT objects)
- correct_answer must be 0, 1, 2, or 3
- explanation_long should be richer than explanation
- learning_suggestion should be actionable
- Make questions test understanding and application, not just memorization"""
                        },
                        {
                            "role": "user",
                            "content": f"Generate {num_questions} multiple choice questions from this content:\n\n{content[:8000]}"
                        }
                    ],
                    model="llama-3.3-70b-versatile",
                    response_format={"type": "json_object"}
                ),
                agent_name="QAAgent"
            )
            result = json.loads(chat_completion.choices[0].message.content or '{}')
            questions = result.get('questions', []) if isinstance(result, dict) else result
            
            # Validate and fix questions
            validated_questions = []
            for q in questions:
                if isinstance(q, dict):
                    # Ensure options is a list of strings
                    options = q.get('options', [])
                    if not isinstance(options, list) or len(options) == 0:
                        print(f"QAAgent: Skipping question with invalid options: {q.get('question')[:50]}")
                        continue
                    
                    # Ensure correct_answer is a valid index
                    correct_answer = q.get('correct_answer', 0)
                    if not isinstance(correct_answer, int) or correct_answer < 0 or correct_answer >= len(options):
                        correct_answer = 0
                    
                    validated_questions.append({
                        "question": q.get("question", ""),
                        "options": options,
                        "correct_answer": correct_answer,
                        "explanation": q.get("explanation", ""),
                        "explanation_long": q.get("explanation_long", q.get("explanation", "")),
                        "learning_suggestion": q.get("learning_suggestion", ""),
                        "topic": q.get("topic", q.get("category", "General")),
                        "category": q.get("category", "General"),
                        "difficulty": q.get("difficulty", "medium")
                    })
            
            print(f"QAAgent: Generated {len(validated_questions)} valid multiple choice questions")
            return validated_questions if len(validated_questions) > 0 else self._fallback_questions()
        except Exception as e:
            print(f"QAAgent: Question generation error: {e}")
            import traceback
            traceback.print_exc()
            return self._fallback_questions()

    def answer_question(self, question: str, context: str) -> str:
        """
        Answer a question based on provided context.
        
        Args:
            question: The question to answer
            context: Relevant context/content to base answer on
            
        Returns:
            Detailed answer with explanation
        """
        if not self.groq_client:
            return "Please enable API for question answering."

        try:
            chat_completion = rate_limit_retry(
                self.groq_client,
                dict(
                    messages=[
                        {
                            "role": "system",
                            "content": """You are an expert tutor providing detailed, clear explanations.
                        Answer the question comprehensively using the provided context.
                        Include examples, reasoning, and any relevant diagrams in markdown format."""
                        },
                        {
                            "role": "user",
                            "content": f"""Question: {question}
                        
Context:
{context[:6000]}

Provide a detailed, educational answer."""
                        }
                    ],
                    model="llama-3.3-70b-versatile",
                ),
                agent_name="QAAgent"
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"QAAgent: Answer error: {e}")
            return f"Unable to generate answer. Error: {str(e)}"

    def generate_concept_explanation(self, concept: str, content: str) -> dict:
        """
        Generate detailed explanation of a specific concept.
        
        Args:
            concept: Concept to explain
            content: Related content
            
        Returns:
            Dict with explanation, examples, and related concepts
        """
        if not self.groq_client:
            return {
                "concept": concept,
                "explanation": "API disabled",
                "examples": [],
                "relatedConcepts": []
            }

        try:
            chat_completion = rate_limit_retry(
                self.groq_client,
                dict(
                    messages=[
                        {
                            "role": "system",
                            "content": """You are an expert educator explaining concepts.
                        Return ONLY a JSON object with:
                        - explanation: Detailed explanation of the concept
                        - examples: 2-3 real-world examples
                        - relatedConcepts: 3-5 related concepts
                        - importance: Why this concept matters
                        - commonMisunderstandings: Common mistakes about this concept"""
                        },
                        {
                            "role": "user",
                            "content": f"""Explain the concept: {concept}
                        
Based on this content:
{content[:5000]}

Provide a comprehensive explanation."""
                        }
                    ],
                    model="llama-3.3-70b-versatile",
                    response_format={"type": "json_object"}
                ),
                agent_name="QAAgent"
            )
            return json.loads(chat_completion.choices[0].message.content or '{}')
        except Exception as e:
            print(f"QAAgent: Concept explanation error: {e}")
            return {
                "concept": concept,
                "explanation": "Error generating explanation",
                "error": str(e)
            }

    def _fallback_questions(self) -> list:
        """Fallback multiple choice questions when API is unavailable."""
        return [
            {
                "question": "What is the primary focus of this material?",
                "options": ["Understanding concepts", "Memorizing facts", "Practical application", "Historical context"],
                "correct_answer": 0,
                "explanation": "The material focuses on helping students understand core concepts.",
                "explanation_long": "The most important goal is building a conceptual foundation so learners can apply ideas later.",
                "learning_suggestion": "Review the core definitions and relationships between the main ideas.",
                "topic": "Fundamentals",
                "category": "General",
                "difficulty": "easy"
            },
            {
                "question": "How do the main concepts relate to real-world scenarios?",
                "options": ["They don't apply", "Limited application", "Highly applicable in practice", "Only theoretical"],
                "correct_answer": 2,
                "explanation": "These concepts have strong real-world applications.",
                "explanation_long": "These ideas show up in real systems and workflows, which is why application-focused learning matters.",
                "learning_suggestion": "Look for one real-world example and map each concept to that example.",
                "topic": "Applications",
                "category": "Application",
                "difficulty": "medium"
            },
            {
                "question": "What would be the best way to apply this knowledge?",
                "options": ["Memorization alone", "Passive reading", "Active learning and practice", "Watching videos"],
                "correct_answer": 2,
                "explanation": "Active learning and practice is the best approach to mastering these concepts.",
                "explanation_long": "Hands-on practice reveals gaps and reinforces understanding better than passive exposure.",
                "learning_suggestion": "Create a short practice task that uses one key concept and reflect on the outcome.",
                "topic": "Learning Strategy",
                "category": "Learning Strategy",
                "difficulty": "hard"
            }
        ]
