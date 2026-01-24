import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGO_URI = os.getenv('MONGO_URI')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    
    @staticmethod
    def init_app(app):
        if not os.path.exists(Config.UPLOAD_FOLDER):
            os.makedirs(Config.UPLOAD_FOLDER)
            
        key = Config.GROQ_API_KEY
        if not key or key.startswith("gsk-placeholder"):
            print("\n" + "="*50)
            print("WARNING: GROQ_API_KEY is missing or invalid in server/.env")
            print("Please add a valid key starting with 'gsk_'")
            print("="*50 + "\n")
        elif not key.startswith("gsk_"):
             print(f"WARNING: API Key '{key[:4]}...' may be invalid (should start with 'gsk_')")
