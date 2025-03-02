import traceback
from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import os
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime
from config import Config
from utils.data_analyzer import DataAnalyzer
from utils.data_processor import DataProcessor
from utils.data_visualization import DataVisualization
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

analyzer = DataAnalyzer()
processor = DataProcessor()
visualizer = DataVisualization()

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
        print(error_trace)
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

        all_detected_issues = analyzer.detect_all_issues(df)
        cleaned_df = processor.process_data(df, all_detected_issues.keys())

        output_filename = f'cleaned_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv'
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
        cleaned_df.to_csv(output_path, index=False)

        applied_methods_str = "\n".join([f"<b>{key}:</b> {value}" for key, value in processor.applied_methods.items()])
        cleaned_data_html = cleaned_df.head(10).to_html(classes="table table-striped", escape=False)

        return jsonify({
            'download_url': f'/download/{output_filename}',
            'applied_methods': applied_methods_str,
            'cleaned_data_html': cleaned_data_html
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/visualize', methods=['POST'])
def visualize():
    data = request.get_json()
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], data['filename'])
        if data['filename'].endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath, engine='openpyxl')
        
        before_plots = visualizer.visualize_all(df)
        
        # all_detected_issues = analyzer.detect_all_issues(df)
        # cleaned_df = processor.process_data(df, all_detected_issues.keys())
        # after_plots = visualizer.visualize_all(cleaned_df)
        
        # return jsonify({'before_cleaning': before_plots, 'after_cleaning': after_plots})
        return jsonify({'before_plot': before_plots})
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
