import os
import json
import tempfile
import pandas as pd
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from datetime import datetime, timezone

# Grabbing our own logic files
# Nota: La importación de fitz/PyMuPDF ahora debe ser segura en pdf_processor.py
from pdf_processor import extraer_texto_de_pdf
from data_extractor import parsear_lineas_a_dataframe, clasificar_resultados
from report_generator import generar_reporte_ia, create_medical_report_pdf

load_dotenv()
app = Flask(__name__)
# Permitimos CORS para todos los orígenes en la API (necesario para Netlify)
CORS(app) 

# Solo necesitamos la clave secreta para la configuración de la app
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key_if_missing')


# --- ENDPOINTS FUNCIONALES (NO PROTEGIDOS) ---

# 1. The main event! This is the REAL analyze endpoint (Ahora público)
@app.route('/api/analyze', methods=['POST'])
def analyze_reports():
    
    try:
        # Ya no necesitamos el ID de usuario, es un servicio público
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        # La fecha es opcional, si la recibe del formulario
        report_date_str = request.form.get('date', datetime.now(timezone.utc).strftime('%Y-%m-%d'))
        file = files[0] # Just grab the first file
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = os.path.join(tmp_dir, secure_filename(file.filename))
            file.save(pdf_path)
            
            # --- Lógica de Extracción Única y Robustez ---
            lineas = extraer_texto_de_pdf(pdf_path) 
            
            # Step 2: Turn text into data (pandas)
            df = parsear_lineas_a_dataframe(lineas)
            
            # Step 3: Classify the data (High, Low, etc.)
            if not df.empty:
                df = clasificar_resultados(df)
            else:
                return jsonify({'error': 'No data could be extracted from this PDF.'}), 400
        
        # Convert the data to JSON for our frontend
        results_json = df.to_dict(orient='records')
        
        return jsonify({
            'success': True,
            'results': results_json,
            'summary': calculate_summary_from_df(df),
            'report_date': report_date_str
        })
        
    except Exception as e:
        return jsonify({'error': f'Analysis failed due to: {str(e)}'}), 500
    

# 2. The REAL PDF generator endpoint (Ahora público)
@app.route('/api/generate-pdf', methods=['POST'])
def generate_pdf():
    try:
        data = request.json
        report_type = data.get('type', 'patient')
        analysis_results_json = data.get('results', [])
        
        df = pd.DataFrame(analysis_results_json)
        
        if df.empty:
            return jsonify({'error': 'No results to generate report from'}), 400

        # Step 1: Call the AI to get the text
        report_text = generar_reporte_ia(df, report_type)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
            # Step 2: Build the PDF with that text
            create_medical_report_pdf(temp_pdf.name, report_text)
            temp_pdf_path = temp_pdf.name
            
        return send_file(
            temp_pdf_path,
            as_attachment=True,
            download_name=f'{report_type}_report.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def calculate_summary_from_df(df):
    # A helper to count the results
    status_counts = df['Status'].value_counts()
    return {
        'normal': status_counts.get('Normal', 0),
        'near': status_counts.get('Near', 0),
        'abnormal': status_counts.get('Low', 0) + status_counts.get('High', 0),
        'total': len(df)
    }

if __name__ == '__main__':
    app.run(debug=True, port=5000)