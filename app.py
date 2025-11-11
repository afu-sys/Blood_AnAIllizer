import os
import json
import tempfile
import pandas as pd
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from datetime import datetime, timezone

# Importamos la lógica que sí usamos
from pdf_processor import extraer_texto_de_pdf
from data_extractor import parsear_lineas_a_dataframe, clasificar_resultados
from report_generator import generar_reporte_ia, create_medical_report_pdf

load_dotenv()
app = Flask(__name__)
CORS(app)

# Ya no necesitamos configuración de BD o JWT
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'un-secreto-de-respaldo')

def calculate_summary_from_df(df):
    """ Función de resumen (corregida para JSON) """
    status_counts = df['Status'].value_counts()
    return {
        'normal': int(status_counts.get('Normal', 0)),
        'total': int(len(df))
    }

@app.route('/api/analyze', methods=['POST'])
def analyze_reports():
    """ Endpoint principal: Recibe un PDF y devuelve el análisis JSON """
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        report_date_str = request.form.get('date', datetime.now(timezone.utc).strftime('%Y-%m-%d'))
        file = files[0]
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = os.path.join(tmp_dir, secure_filename(file.filename))
            file.save(pdf_path)
            
            # 1. Extraer
            lineas = extraer_texto_de_pdf(pdf_path) 
            
            # 2. Parsear
            df = parsear_lineas_a_dataframe(lineas)
            
            # 3. Clasificar
            if not df.empty:
                df = clasificar_resultados(df)
            else:
                return jsonify({'error': 'No data could be extracted from this PDF.'}), 400
        
        # 4. Convertir a JSON (con la corrección de int64)
        results_json = json.loads(df.to_json(orient='records'))
        
        return jsonify({
            'success': True,
            'results': results_json,
            'summary': calculate_summary_from_df(df),
            'report_date': report_date_str
        })
        
    except Exception as e:
        return jsonify({'error': f'Analysis failed due to: {str(e)}'}), 500
    
@app.route('/api/generate-pdf', methods=['POST'])
def generate_pdf():
    """ Endpoint de PDF: Recibe JSON y devuelve un PDF """
    try:
        data = request.json
        report_type = data.get('type', 'patient')
        analysis_results_json = data.get('results', [])
        
        df = pd.DataFrame(analysis_results_json)
        
        if df.empty:
            return jsonify({'error': 'No results to generate report from'}), 400

        # 1. Generar texto con IA
        report_text = generar_reporte_ia(df, report_type)
        
        # 2. Crear el archivo PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
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

if __name__ == '__main__':
    # Ya no necesitamos 'with app.app_context(): db.create_all()'
    app.run(debug=True, port=5000)