from .base_agent import BaseAgent, rate_limit_retry
import os
import re
import math
from groq import Groq

class NotesAgent(BaseAgent):
    def __init__(self):
        super().__init__("NotesAgent")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.groq_client = None
        if self.groq_key and self.groq_key != "gsk-placeholder":
             self.groq_client = Groq(api_key=self.groq_key)
        self.subject = "General"

    def process(self, content):
        """
        Takes raw text content and returns structured comprehensive markdown notes.
        """
        if not content:
            return ""

        if self.groq_client:
            if self._should_use_multi_pass(content):
                notes = self._generate_notes_multi_pass(content)
            else:
                notes = self._generate_notes(content)
            self.subject = self._extract_subject_from_notes(notes)
            return notes
        
        notes = self._generate_fallback(content)
        self.subject = self._extract_subject_from_notes(notes)
        return notes

    def _should_use_multi_pass(self, content: str) -> bool:
        if self._has_section_markers(content):
            return True
        return len(content) > 30000

    def _has_section_markers(self, content: str) -> bool:
        return "--- Page" in content or "--- Slide" in content or "--- Segment" in content or "--- Source:" in content

    def _generate_notes_multi_pass(self, content: str) -> str:
        sections = self._split_content_sections(content)
        if not sections:
            return self._generate_notes(content)

        output = []
        total = len(sections)
        for index, (title, text) in enumerate(sections, start=1):
            if not text.strip():
                continue
            include_subject = index == 1
            section_notes = self._generate_section_notes(title, text, index, total, include_subject)
            if section_notes:
                output.append(section_notes)

        return "\n\n".join(output).strip()

    def _split_content_sections(self, content: str) -> list:
        sections = []
        current_title = "Section 1"
        current_lines = []

        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("--- ") and stripped.endswith(" ---") and len(stripped) <= 160:
                if current_lines:
                    sections.append((current_title, "\n".join(current_lines).strip()))
                current_title = stripped.strip("-").strip()
                current_lines = []
                continue
            current_lines.append(line)

        if current_lines:
            sections.append((current_title, "\n".join(current_lines).strip()))

        if not sections:
            return []

        max_sections = 60
        if len(sections) <= max_sections:
            return sections

        group_size = int(math.ceil(len(sections) / max_sections))
        grouped = []
        for start in range(0, len(sections), group_size):
            chunk = sections[start:start + group_size]
            title = f"Sections {start + 1}-{start + len(chunk)}"
            text = "\n\n".join([c[1] for c in chunk])
            grouped.append((title, text))
        return grouped

    def _generate_section_notes(self, title: str, text: str, index: int, total: int, include_subject: bool) -> str:
        try:
            subject_line = "Include a '# Subject: <Subject>' line at the top." if include_subject else "Do not repeat the subject line."
            chat_completion = rate_limit_retry(
                self.groq_client,
                dict(
                    messages=[
                        {
                            "role": "system",
                            "content": f"""You are a senior professor creating detailed study notes for ONE section of a larger document.

{subject_line}
Start the section with a heading '## {title}'.

Write detailed, exam-oriented notes for this section only:
- Explain key concepts step by step
- Include definitions, examples, and important rules
- Use bullet points where helpful
- Avoid referencing other sections
"""
                        },
                        {
                            "role": "user",
                            "content": f"""Section {index} of {total}.

SECTION CONTENT:

{text[:12000]}"""
                        }
                    ],
                    model="llama-3.3-70b-versatile",
                    temperature=0.4,
                    max_tokens=3000,
                ),
                agent_name="NotesAgent"
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"NotesAgent: Section generation error: {e}")
            return ""

    def generate_subject_notes(self, subject: str) -> str:
        """
        Generate comprehensive notes for a subject without an uploaded document.
        """
        if not subject:
            return ""

        self.subject = subject.strip()

        if self.groq_client:
            notes = self._generate_subject_notes(self.subject)
            self.subject = self._extract_subject_from_notes(notes) or self.subject
            return notes

        return self._generate_subject_fallback(self.subject)

    def _generate_notes(self, content):
        try:
            chat_completion = rate_limit_retry(
                self.groq_client,
                dict(
                    messages=[
                        {
                            "role": "system",
                            "content": """You are a Senior Professor with 15+ years of experience teaching B.Tech Engineering students (DBMS, OS, CN, ML, DS, AI) and preparing them for Semester exams, GATE, and Technical interviews.

CRITICAL INSTRUCTION: Analyze the ENTIRE provided document thoroughly (even if 60+ pages). DO NOT summarize briefly. DO NOT skip details. ASSUME the student has NOT read the document.

Your goal: Convert the document into **FULL-LENGTH, EXAM-ORIENTED CLASS NOTES** that can REPLACE reading the original document completely.

────────────────────────────────────────
STRICT OUTPUT EXPECTATIONS
────────────────────────────────────────
• Depth > Brevity (long answers are REQUIRED)
• Explain EVERYTHING clearly and step-by-step
• Expand all bullet points into paragraphs
• Include formulas, rules, assumptions, edge cases, examples
• Write like a professor explaining on a blackboard
• Cover ALL sections thoroughly - NO compression

────────────────────────────────────────
MANDATORY STRUCTURE (DO NOT SKIP ANY SECTION)
────────────────────────────────────────

# Subject: [Exact Subject Name]

## 1. Overview (Detailed - 1-2 pages equivalent)
- Purpose and scope of the subject
- Why it matters in real systems and industry
- How it appears in exams and placements
- High-level flow connecting all topics

## 2. Detailed Core Concepts (VERY EXTENSIVE - This is the HEART)
For EACH concept identified in the document:
- Clear definition with context
- Why this concept exists and when it's needed
- How it works (step-by-step mechanics)
- Internal working mechanism
- Practical example (numerical or real-world)
- Common exam questions related to this
- Comparison with related concepts if applicable

⚠️ This section should be EXTREMELY DETAILED and LONG.

## 3. Key Definitions (Strictly Technical)
- Define ALL important terms precisely
- Include both simple and formal definitions
- Highlight keywords frequently used in exams
- Include alternate names/terminology

## 4. Visual Diagrams & Architecture (If Applicable)
Include **3-5 valid Mermaid diagrams** such as:
- System/Component architecture
- Process flow and interactions
- Hierarchy and relationships
- Algorithm steps
- Data structure organization

DIAGRAM RULES:
- Use ONLY valid Mermaid syntax
- Simple node names (A, B, C or brief labels)
- Always wrap in ```mermaid``` blocks
- Add brief explanation below each diagram

## 5. Algorithms, Processes & Procedures (If Applicable)
For each algorithm or process:
- INPUT: What goes in?
- OUTPUT: What comes out?
- STEP-BY-STEP procedure: Numbered detailed steps
- PSEUDOCODE: If relevant and helpful
- COMPLEXITY ANALYSIS: Time and space complexity
- EXAMPLE WALKTHROUGH: Trace through an example
- VARIATIONS: Different approaches or optimizations

## 6. Real-World Applications (DETAILED & COMPREHENSIVE)
- At least 5-7 practical use cases
- Explain HOW the concept is actually used
- Mention specific companies, systems, or databases using it
- Include current industry relevance
- Connect to emerging technologies where relevant

## 7. Common Mistakes, Misconceptions & Exam Traps
- List student misunderstandings in detail
- Explain what students typically get WRONG
- Clarify the correct understanding with examples
- Highlight exam traps and gotchas
- Provide memory techniques to remember correctly

## 8. Advanced Topics, Optimizations & Internals
- Advanced variations of concepts
- Optimization techniques used in production systems
- Edge cases and corner cases
- Internal implementation details
- Industry-level insights and best practices
- Recent research or innovations

## 9. Comprehensive Exam-Oriented Q&A (8-10+ Questions)
Mix of question types:
- 2-mark questions (definition, basic concept)
- 5-mark questions (explain concept with example)
- 10-mark questions (detailed analysis, comparisons, problem-solving)

For EACH question provide:
- Complete, detailed answer
- Key points students MUST write in exams
- Common variations of the question
- Related concepts to mention

## 10. Learning Path & Knowledge Map
- List 5-7 PREREQUISITE topics (must understand first)
- List 5-7 ADVANCED follow-up topics (learn after this)
- Suggest optimal order of learning
- Show connections between topics

────────────────────────────────────────
CRITICAL RULES FOR OUTPUT
────────────────────────────────────────

❌ DO NOT give short/brief notes
❌ DO NOT skip or compress large topics
❌ DO NOT say \"briefly\", \"in summary\", or \"to summarize\"
❌ DO NOT omit any section from mandatory structure
❌ DO NOT assume student background knowledge

✅ Treat this as the ONLY study material the student will use
✅ Write in clean, well-structured Markdown
✅ Use proper formatting with headers, bold, bullet points
✅ Be EXHAUSTIVE and EXAM-FOCUSED throughout
✅ Include numbers, formulas, and technical details
✅ Provide context for every concept

Output ONLY the comprehensive notes in Markdown format."""
                        },
                        {
                            "role": "user",
                            "content": f"""Generate COMPREHENSIVE EXAM-ORIENTED CLASS NOTES for the following document. 
                        
⚠️ CRITICAL: Generate FULL, DETAILED, EXHAUSTIVE NOTES covering ALL 10 mandatory sections.
⚠️ Output should be 5000+ words, covering every concept thoroughly.
⚠️ Do NOT abbreviate. Write like classroom notes that replace the entire document.

DOCUMENT CONTENT:

{content[:30000]}""",
                        }
                    ],
                    model="llama-3.3-70b-versatile",
                    temperature=0.9,
                    max_tokens=6000,
                ),
                agent_name="NotesAgent"
            )
            result = chat_completion.choices[0].message.content
            print(f"NotesAgent: Generated notes (length: {len(result)})")
            if not result or len(result.strip()) < 100:
                print("NotesAgent: Notes too short, using enhanced fallback")
                return self._generate_enhanced_fallback(content)
            # Ensure diagrams are valid
            result = self._validate_mermaid_diagrams(result)
            return result
        except Exception as e:
            print(f"NotesAgent: Notes Generation Error: {e}")
            import traceback
            traceback.print_exc()
            return self._generate_enhanced_fallback(content)

    def _generate_subject_notes(self, subject: str) -> str:
        """Generate comprehensive notes based on subject only."""
        try:
            chat_completion = rate_limit_retry(
                self.groq_client,
                dict(
                    messages=[
                        {
                            "role": "system",
                            "content": """You are a Senior Professor with 15+ years of experience teaching B.Tech Engineering students (DBMS, OS, CN, ML, DS, AI) and preparing them for Semester exams, GATE, and Technical interviews.

Your goal: Create **FULL-LENGTH, EXAM-ORIENTED CLASS NOTES** for the given SUBJECT using your knowledge. Assume no source document is provided.

────────────────────────────────────────
STRICT OUTPUT EXPECTATIONS
────────────────────────────────────────
• Depth > Brevity (long answers are REQUIRED)
• Explain EVERYTHING clearly and step-by-step
• Expand all bullet points into paragraphs
• Include formulas, rules, assumptions, edge cases, examples
• Write like a professor explaining on a blackboard
• Cover ALL sections thoroughly - NO compression

────────────────────────────────────────
MANDATORY STRUCTURE (DO NOT SKIP ANY SECTION)
────────────────────────────────────────

# Subject: [Exact Subject Name]

## 1. Overview (Detailed - 1-2 pages equivalent)
- Purpose and scope of the subject
- Why it matters in real systems and industry
- How it appears in exams and placements
- High-level flow connecting all topics

## 2. Detailed Core Concepts (VERY EXTENSIVE - This is the HEART)
For EACH concept identified in the subject:
- Clear definition with context
- Why this concept exists and when it's needed
- How it works (step-by-step mechanics)
- Internal working mechanism
- Practical example (numerical or real-world)
- Common exam questions related to this
- Comparison with related concepts if applicable

## 3. Key Definitions (Strictly Technical)
## 4. Visual Diagrams & Architecture (If Applicable)
## 5. Algorithms, Processes & Procedures (If Applicable)
## 6. Real-World Applications (DETAILED & COMPREHENSIVE)
## 7. Common Mistakes, Misconceptions & Exam Traps
## 8. Advanced Topics, Optimizations & Internals
## 9. Comprehensive Exam-Oriented Q&A (8-10+ Questions)
## 10. Learning Path & Knowledge Map

────────────────────────────────────────
CRITICAL RULES FOR OUTPUT
────────────────────────────────────────

❌ DO NOT give short/brief notes
❌ DO NOT skip or compress large topics
❌ DO NOT say "briefly", "in summary", or "to summarize"
❌ DO NOT omit any section from mandatory structure
❌ DO NOT assume student background knowledge

✅ Treat this as the ONLY study material the student will use
✅ Write in clean, well-structured Markdown
✅ Use proper formatting with headers, bold, bullet points
✅ Be EXHAUSTIVE and EXAM-FOCUSED throughout
✅ Include numbers, formulas, and technical details
✅ Provide context for every concept

Output ONLY the comprehensive notes in Markdown format."""
                        },
                        {
                            "role": "user",
                            "content": f"""Generate COMPREHENSIVE EXAM-ORIENTED CLASS NOTES for the subject below.

⚠️ CRITICAL: Generate FULL, DETAILED, EXHAUSTIVE NOTES covering ALL 10 mandatory sections.
⚠️ Output should be 5000+ words, covering every concept thoroughly.
⚠️ Do NOT abbreviate. Write like classroom notes.

SUBJECT:
{subject}
""",
                        }
                    ],
                    model="llama-3.3-70b-versatile",
                    temperature=0.9,
                    max_tokens=6000,
                ),
                agent_name="NotesAgent"
            )
            result = chat_completion.choices[0].message.content
            print(f"NotesAgent: Generated subject notes (length: {len(result)})")
            if not result or len(result.strip()) < 100:
                print("NotesAgent: Subject notes too short, using fallback")
                return self._generate_subject_fallback(subject)
            result = self._validate_mermaid_diagrams(result)
            return result
        except Exception as e:
            print(f"NotesAgent: Subject Notes Generation Error: {e}")
            import traceback
            traceback.print_exc()
            return self._generate_subject_fallback(subject)

    def _validate_mermaid_diagrams(self, content: str) -> str:
        """Ensure all Mermaid diagrams have valid syntax."""
        # Simple validation - if diagram is malformed, add basic one
        if "```mermaid" in content:
            # Check for syntax errors
            if "graph" not in content.lower():
                # Replace invalid diagrams with valid fallback
                content = re.sub(
                    r'```mermaid\s*.*?```',
                    '''```mermaid
graph TD
    A[Core Concept]
    B[Component 1]
    C[Component 2]
    A --> B
    A --> C
```''',
                    content,
                    flags=re.DOTALL
                )
        return content

    def _generate_enhanced_fallback(self, content):
        """Generate enhanced fallback notes from document content directly."""
        print("NotesAgent: Generating fallback notes from document")
        
        import re
        
        # Extract key information from content
        lines = content.split('\n')
        title = "Study Notes"
        
        # Try to find subject
        for line in lines[:20]:
            if 'subject' in line.lower() or 'chapter' in line.lower():
                title = line.strip()
                break
        
        # Build structured notes
        sections = []
        sections.append(f"# {title}\n")
        sections.append("## 1. Overview\n")
        sections.append(content[:500] + "\n\n")
        
        sections.append("## 2. Key Concepts\n")
        # Extract bullet points and lists
        for line in lines[:100]:
            if line.strip().startswith(('-', '•', '*')):
                sections.append(line + "\n")
        
        sections.append("\n## 3. Important Definitions\n")
        sections.append("- Review the knowledge graph for detailed concept explanations\n")
        sections.append("- Use the Q&A section to test your understanding\n")
        
        sections.append("\n## 4. Diagrams & Visualizations\n")
        sections.append("```mermaid\n")
        sections.append("graph TD\n")
        sections.append("    A[Main Topic]\n")
        sections.append("    B[Key Concept 1]\n")
        sections.append("    C[Key Concept 2]\n")
        sections.append("    A --> B\n")
        sections.append("    A --> C\n")
        sections.append("```\n")
        
        sections.append("\n## 5. Key Takeaways\n")
        sections.append("- Comprehensive notes generated from document content\n")
        sections.append("- Use Knowledge Graph for detailed concept relationships\n")
        sections.append("- Use Q&A section to test understanding\n")
        sections.append("- Use Diagrams section for visual learning\n")
        
        return "".join(sections)

    def _generate_fallback(self, content):
        return f"""
# Auto-Generated Notes (Offline Mode)

**Note:** Please add a valid GROQ_API_KEY to generate smart AI notes with comprehensive structure.

## Content Summary
{content[:800]}...

## Key Points Identified
- Please enable API for full feature set
- Content analysis requires LLM processing
- Rich formatting and diagrams need AI enhancement

## Next Steps
1. Add GROQ_API_KEY to your .env file
2. Restart the application
3. Re-upload documents for comprehensive notes

## Adaptive Learning Path
* Review the document manually
* Study the knowledge graph
* Explore related topics
        """

    def _generate_subject_fallback(self, subject: str) -> str:
        return f"""
# Subject: {subject}

**Note:** Please add a valid GROQ_API_KEY to generate smart AI notes with comprehensive structure.

## 1. Overview
Offline mode cannot generate full notes for subject-only requests.

## 2. Detailed Core Concepts
Please enable API access to generate exhaustive subject notes.

## 3. Key Definitions
API required for detailed definitions.

## 4. Visual Diagrams & Architecture
Mermaid diagrams require AI generation.

## 5. Algorithms, Processes & Procedures
Enable API to receive step-by-step procedures.

## 6. Real-World Applications
Enable API for comprehensive use cases.

## 7. Common Mistakes, Misconceptions & Exam Traps
Enable API to generate exam-oriented traps and misconceptions.

## 8. Advanced Topics, Optimizations & Internals
Enable API for advanced topic coverage.

## 9. Comprehensive Exam-Oriented Q&A
Enable API to generate full question bank.

## 10. Learning Path & Knowledge Map
Enable API to generate prerequisites and learning path.
        """

    def _extract_subject_from_notes(self, notes_text: str) -> str:
        if not notes_text:
            return "General"
        match = re.search(r"Subject:\s*(.*?)(?:\n|$)", notes_text)
        if match:
            return match.group(1).strip()
        match = re.search(r"#\s*Subject:\s*(.*?)(?:\n|$)", notes_text)
        if match:
            return match.group(1).strip()
        return "General"
