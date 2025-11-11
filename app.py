import os
import json
import tempfile
import pandas as pd
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from datetime import datetime, timezone
import traceback

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
    # Asegúrate de usar la columna 'status' (minúscula) que acabamos de renombrar
    status_counts = df['status'].value_counts()
    return {
        'normal': int(status_counts.get('Normal', 0)),
        'near': int(status_counts.get('Near', 0)),
        'abnormal': int(status_counts.get('Low', 0) + status_counts.get('High', 0)),
        'total': int(len(df))
    }

@app.route('/api/analyze', methods=['POST'])
#@jwt_required() # <--- ¡RECUERDA QUITAR EL '#' CUANDO TERMINES DE PROBAR!
def analyze_reports():
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        report_date_str = request.form.get('date', datetime.now(timezone.utc).strftime('%Y-%m-%d'))
        file = files[0]
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = os.path.join(tmp_dir, secure_filename(file.filename))
            file.save(pdf_path)
            
            lineas = extraer_texto_de_pdf(pdf_path) 
            
            df = parsear_lineas_a_dataframe(lineas)
            
            if not df.empty:
                df = clasificar_resultados(df)
            else:
                return jsonify({'error': 'No data could be extracted from this PDF.'}), 400
        
        # --- ¡AQUÍ ESTÁ LA SOLUCIÓN! ---
        # Renombramos las columnas del DataFrame para que coincidan con el JS
        df = df.rename(columns={
            'Test': 'test',
            'Value': 'value',
            'Unit': 'unit',
            'Ref Low': 'refLow',
            'Ref High': 'refHigh',
            'Status': 'status'
        })
        
        # Convertimos a JSON (usando el fix de int64)
        results_json = json.loads(df.to_json(orient='records'))
        
        return jsonify({
            'success': True,
            'results': results_json,
            'summary': calculate_summary_from_df(df), # Pasamos el df renombrado
            'report_date': report_date_str
        })
        
    except Exception as e:
        return jsonify({'error': f'Analysis failed due to: {str(e)}'}), 500
    
@app.route('/api/generate-pdf', methods=['POST'])
#@jwt_required()
def generate_pdf():
    try:
        data = request.json
        report_type = data.get('type', 'patient')
        analysis_results_json = data.get('results', [])
        
        df = pd.DataFrame(analysis_results_json)
        
        if df.empty:
            return jsonify({'error': 'No results to generate report from'}), 400

        report_text = generar_reporte_ia(df, report_type)
        
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
        # --- ¡ESTE ES EL CÓDIGO DE DEBUG! ---
        # 1. Imprime el error completo en los logs de Railway
        app.logger.error(f"¡FALLO AL GENERAR PDF! Error: {e}")
        app.logger.error(traceback.format_exc()) # Imprime el Traceback completo
        
        # 2. Devuelve un error al frontend
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    # Ya no necesitamos 'with app.app_context(): db.create_all()'
    app.run(debug=True, port=5000)