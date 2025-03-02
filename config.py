import os

class Config:
    UPLOAD_FOLDER = 'data/uploads'
    PROCESSED_FOLDER = 'data/processed'
    VISUALS_FOLDER = "data/visuals"
    ALLOWED_EXTENSIONS = {'csv', 'xlsx'}
    SECRET_KEY = 'your-secret-key-here'
    
    @staticmethod
    def init_app(app):
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.PROCESSED_FOLDER, exist_ok=True)
        os.makedirs(Config.VISUALS_FOLDER, exist_ok=True)

