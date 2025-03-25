import os

class Config:
    UPLOAD_FOLDER = 'data/uploads'
    PROCESSED_FOLDER = 'data/processed'
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'pdf', 'sql'}
    SECRET_KEY = 'your-secret-key-here'
    
    @staticmethod
    def init_app(app):
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.PROCESSED_FOLDER, exist_ok=True)

