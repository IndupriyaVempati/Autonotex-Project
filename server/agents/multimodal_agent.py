from .base_agent import BaseAgent
import os
import base64
from groq import Groq
from pypdf import PdfReader

class MultimodalAgent(BaseAgent):
    def __init__(self):
        super().__init__("MultimodalAgent")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.groq_client = None
        if self.groq_key and self.groq_key != "gsk-placeholder":
             self.groq_client = Groq(api_key=self.groq_key)

    def process(self, data):
        """
        Data expectations: {'file_path': str, 'file_type': str}
        """
        file_path = data.get('file_path')
        file_type = data.get('file_type', 'text')

        if not file_path or not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")

        try:
            # Handle Images (Vision)
            if file_type.startswith('image/'):
                print(f"MultimodalAgent: Processing Image {file_path}")
                if self.groq_client:
                    return self._process_image(file_path)
                else:
                    return "[Image Content - No API Key Provided]"

            # Handle PDF
            elif file_type == 'application/pdf':
                print(f"MultimodalAgent: Processing PDF {file_path}")
                return self._extract_pdf_text(file_path)

            # Handle PowerPoint
            elif file_type == 'application/vnd.openxmlformats-officedocument.presentationml.presentation':
                print(f"MultimodalAgent: Processing PPT {file_path}")
                return self._extract_pptx_text(file_path)

            # Handle Audio/Video
            elif file_type.startswith('audio/') or file_type.startswith('video/'):
                print(f"MultimodalAgent: Processing Audio/Video {file_path}")
                return self._transcribe_media(file_path)
            
            # Handle Text
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return content
        except Exception as e:
            print(f"Error processing file: {e}")
            return ""

    def _extract_pdf_text(self, pdf_path):
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text if text.strip() else "[Empty PDF]"
        except Exception as e:
            print(f"PDF Error: {e}")
            return "[Error reading PDF]"

    def _extract_pptx_text(self, ppt_path):
        try:
            from pptx import Presentation
            prs = Presentation(ppt_path)
            text = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text.append(shape.text)
            return "\n".join(text)
        except Exception as e:
            print(f"PPT Error: {e}")
            return "[Error reading PowerPoint]"

    def _transcribe_media(self, media_path):
        try:
            # For video, extract audio first using moviepy if needed, 
            # but Groq API might accept video/audio file directly depending on size.
            # For stability, passing the file object directly to Groq Whisper.
            
            with open(media_path, "rb") as file:
                transcription = self.groq_client.audio.transcriptions.create(
                    file=(os.path.basename(media_path), file.read()),
                    model="distil-whisper-large-v3-en",
                    response_format="text"
                )
            return transcription
        except Exception as e:
            print(f"Whisper Error: {e}")
            return "[Error transcribing media]"

    def _process_image(self, image_path):
        try:
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe this image in detail to extract key concepts and relationships for a knowledge graph."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                },
                            },
                        ],
                    }
                ],
                model="llama-3.2-11b-vision-preview",
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"Vision Error: {e}")
            return "[Error analyzing image]"
