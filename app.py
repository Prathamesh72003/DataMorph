from flask import Flask, render_template, request, jsonify, send_file, session
import pandas as pd
import os
from datetime import datetime
from config import Config
from utils.data_analyzer import DataAnalyzer
from utils.data_processor import DataProcessor
from utils.data_visualization import DataVisualization
from werkzeug.utils import secure_filename
from groq import Groq
import camelot
import dotenv
import csv
import re
from flask_cors import CORS

dotenv.load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

analyzer = DataAnalyzer()
processor = DataProcessor()
visualizer = DataVisualization()

CORS(app, origins=["http://localhost:3000"], supports_credentials=True)

@app.route('/')
def index():
    return render_template('index.html')

def extract_insert_values(sql_file, csv_file):
    """
    Robustly extracts INSERT values from an SQL file and saves them as a CSV.
    Handles more complex SQL scenarios.
    """
    try:
        with open(sql_file, "r", encoding="utf-8") as f:
            sql_content = f.read()

        # More robust INSERT statement pattern
        insert_pattern = re.compile(r"INSERT\s+(?:(?:LOW_PRIORITY|DELAYED|HIGH_PRIORITY)\s+)?(?:IGNORE\s+)?INTO\s+`?(\w+)`?\s*(?:\([^)]+\))?\s*VALUES\s*((?:\s*\([^)]+\)\s*,?)+)", re.IGNORECASE | re.DOTALL)
        matches = insert_pattern.findall(sql_content)

        if not matches:
            return None, "No INSERT statements found in the SQL file."

        all_rows = []
        column_names = None

        for table_name, values_part in matches:
            # Extract values using a more complex regex
            values_pattern = re.compile(r'\(([^)]+)\)')
            values_matches = values_pattern.findall(values_part)

            for value in values_matches:
                # More robust value parsing
                parsed_values = []
                for v in re.split(r',(?=(?:[^\'"`]*[\'"`][^\'"`]*[\'"`])*[^\'"`]*$)', value):
                    v = v.strip()
                    # Handle different value types: NULL, numbers, strings
                    if v.upper() == 'NULL':
                        parsed_values.append(None)
                    elif v.startswith("'") and v.endswith("'"):
                        parsed_values.append(v.strip("'").replace("''", "'"))
                    elif v.startswith('"') and v.endswith('"'):
                        parsed_values.append(v.strip('"').replace('""', '"'))
                    else:
                        try:
                            # Try to convert to number if possible
                            parsed_values.append(float(v) if '.' in v else int(v))
                        except ValueError:
                            parsed_values.append(v)

                if column_names is None:
                    # Attempt to get column names from table metadata or use generic names
                    column_names = [f'{table_name}_col_{i+1}' for i in range(len(parsed_values))]

                all_rows.append(parsed_values)

        # Write to CSV
        with open(csv_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(column_names) 
            writer.writerows(all_rows)  

        return csv_file, None

    except Exception as e:
        return None, f"Error processing SQL file: {str(e)}"

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

        if filename.endswith('.csv') or filename.endswith('.xlsx'):
            session['filename'] = filename
            return jsonify({'filename': filename})

        elif filename.endswith('.pdf'):
            try:
                tables = camelot.read_pdf(save_path, pages='all', flavor='lattice', suppress_stdout=True)
                if tables.n == 0:
                    tables = camelot.read_pdf(save_path, pages='all', flavor='stream', suppress_stdout=True)

                if tables.n == 0:
                    return jsonify({'error': 'No tables found in PDF. Ensure tables are in text format (not images).'}), 400

                dataframes = [table.df for table in tables]
                final_df = pd.concat(dataframes, ignore_index=True)
            
                final_df.columns = final_df.iloc[0]
                final_df = final_df[1:].reset_index(drop=True)

                output_filename = f"extracted_data_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
                output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
                final_df.to_csv(output_path, index=False)

                session['filename'] = output_filename
                return jsonify({'filename': output_filename})
            except Exception as e:
                return jsonify({'error': f'PDF processing failed: {str(e)}'}), 500
        
        elif filename.endswith('.sql'):
            try:
                output_filename = f"converted_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
                output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
                
                csv_file, error = extract_insert_values(save_path, output_path)
                
                if error:
                    app.logger.error(f"SQL Processing Error: {error}")
                    return jsonify({'error': error}), 400

                if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                    return jsonify({'error': 'No data extracted from SQL file'}), 400

                session['filename'] = output_filename
                return jsonify({'filename': output_filename})
            
            except Exception as e:
                app.logger.exception("Unexpected error processing SQL file")
                return jsonify({'error': f'SQL processing failed: {str(e)}'}), 500


    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], data['filename'])
        if data['filename'].endswith('.csv'):
            df = pd.read_csv(filepath)
        elif data['filename'].endswith('.xlsx'):
            df = pd.read_excel(filepath, engine='openpyxl')
        else:
            return jsonify({'error': 'Unsupported file format for analysis'}), 400

        issues = analyzer.detect_all_issues(df)
        filtered_issues = {k: v for k, v in issues.items() if v}
        session['file_context'] = f"Detected issues: {filtered_issues}"
        return jsonify({'issues': filtered_issues})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/process', methods=['POST'])
def process():
    data = request.get_json()
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], data['filename'])
        if data['filename'].endswith('.csv'):
            df = pd.read_csv(filepath)
        elif data['filename'].endswith('.xlsx'):
            df = pd.read_excel(filepath, engine='openpyxl')
        else:
            return jsonify({'error': 'Unsupported file format for processing'}), 400

        all_detected_issues = analyzer.detect_all_issues(df)
        cleaned_df = processor.process_data(df, data['methods'],all_detected_issues.keys())

        output_filename = f'cleaned_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv'
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
        cleaned_df.to_csv(output_path, index=False)

        session['file_context'] = f"File processed. Applied methods: {processor.applied_methods}"
        return jsonify({'download_url': f'/download/{output_filename}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/visualize', methods=['POST'])
def visualize():
    data = request.get_json()
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], data['filename'])
        if data['filename'].endswith('.csv'):
            df = pd.read_csv(filepath)
        elif data['filename'].endswith('.xlsx'):
            df = pd.read_excel(filepath, engine='openpyxl')
        else:
            return jsonify({'error': 'Unsupported file format for visualization'}), 400

        before_plots = visualizer.visualize_all(df)
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
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=API_KEY)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '')
    history = session.get('chat_history', [])
    file_context = session.get('file_context', '')
    
    if file_context and (not history or history[0].get('role') != 'system'):
        history.insert(0, {"role": "system", "content": f"File context: {file_context}"})

    history.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            messages=history,
            model="llama-3.3-70b-versatile",
            max_tokens=700  
        )
        reply = response.choices[0].message.content
        history.append({"role": "assistant", "content": reply})
        session['chat_history'] = history
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
