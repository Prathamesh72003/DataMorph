import traceback
from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import os
from datetime import datetime
from config import Config
from utils.data_analyzer import DataAnalyzer
from utils.data_processor import DataProcessor
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

analyzer = DataAnalyzer()
processor = DataProcessor()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename) 
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        return jsonify({'filename': filename})  
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], data['filename'])
        if data['filename'].endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath, engine='openpyxl')

        issues = analyzer.detect_all_issues(df)
        
        filtered_issues = {category: {k: v for k, v in details.items() if v != 0} 
                           for category, details in issues.items()}
        
        filtered_issues = {k: v for k, v in filtered_issues.items() if v}

        return jsonify({'issues': filtered_issues})
    
    except Exception as e:
        error_trace = traceback.format_exc()
        print(error_trace)  # This will print the full error message in your console
        return jsonify({'error': str(e)}), 500


@app.route('/process', methods=['POST'])
def process():
    data = request.get_json()
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], data['filename'])
        if data['filename'].endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath, engine='openpyxl')
        
        # Automatically detect all issues
        all_detected_issues = analyzer.detect_all_issues(df)
        
        # Process and clean the data for ALL detected issues
        cleaned_df = processor.process_data(df, all_detected_issues.keys())  # Pass all issue categories
        
        output_filename = f'cleaned_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv'
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
        cleaned_df.to_csv(output_path, index=False)

        return jsonify({'download_url': f'/download/{output_filename}'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/download/<filename>')
def download(filename):
    return send_file(
        os.path.join(app.config['PROCESSED_FOLDER'], filename),
        as_attachment=True
    )

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

if __name__ == '__main__':
    app.run(debug=True)