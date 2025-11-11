import os
import json
import tempfile
import pandas as pd
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager
from datetime import datetime, timezone

# Grabbing our own logic files
from pdf_processor import extraer_texto_de_pdf
from data_extractor import parsear_lineas_a_dataframe, clasificar_resultados
from report_generator import generar_reporte_ia, create_medical_report_pdf

import fitz

load_dotenv()
app = Flask(__name__)
CORS(app)

# Setting up all the config for Flask, JWT, and the DB
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# This is our User table for the database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    timelines = db.relationship('Timeline', backref='user', lazy=True)

# This is our Timeline table
class Timeline(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    results = db.Column(db.JSON, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'results': self.results,
            'user_id': self.user_id
        }

# API endpoint for making a new account
@app.route('/api/users/register', methods=['POST'])
def register_user():
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        name = data.get('name')
        password = data.get('password')

        if not username or not email or not password:
            return jsonify({'error': 'Missing required fields'}), 400
        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            return jsonify({'error': 'User or email already exists'}), 409

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, name=name, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        access_token = create_access_token(identity={'id': new_user.id, 'username': new_user.username})
        return jsonify({
            'success': True,
            'user': {'id': new_user.id, 'username': new_user.username, 'email': new_user.email},
            'access_token': access_token
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# API endpoint for logging in
@app.route('/api/users/login', methods=['POST'])
def login_user():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            access_token = create_access_token(identity={'id': user.id, 'username': user.username})
            return jsonify({
                'success': True,
                'user': {'id': user.id, 'username': user.username, 'email': user.email},
                'access_token': access_token
            })
        
        return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API endpoint to get timeline data. Protected!
@app.route('/api/timeline', methods=['GET'])
@jwt_required() # You need a valid token to get in
def get_timeline():
    current_user_identity = get_jwt_identity()
    user_id = current_user_identity['id']
    timeline_entries = Timeline.query.filter_by(user_id=user_id).order_by(Timeline.date.asc()).all()
    timeline_data = [entry.to_dict() for entry in timeline_entries]
    return jsonify({'success': True, 'timeline': timeline_data})

# API endpoint to save a new timeline entry. Also protected!
@app.route('/api/save-timeline', methods=['POST'])
@jwt_required()
def save_timeline():
    try:
        current_user_identity = get_jwt_identity()
        user_id = current_user_identity['id']
        data = request.json
        
        new_entry = Timeline(
            date=datetime.fromisoformat(data.get('date')),
            results=data.get('results'),
            user_id=user_id
        )
        db.session.add(new_entry)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Timeline saved', 'entry': new_entry.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# The main event! This is the REAL analyze endpoint
@app.route('/api/analyze', methods=['POST'])
@jwt_required()
def analyze_reports():
    # Eliminamos el logger.setLevel('DEBUG') para evitar logs excesivos en producción
    
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        report_date_str = request.form.get('date', datetime.now(timezone.utc).strftime('%Y-%m-%d'))
        file = files[0] # Just grab the first file
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = os.path.join(tmp_dir, secure_filename(file.filename))
            file.save(pdf_path)
            
            # --- Lógica de Extracción Única y Robustez ---
            # Llamamos a la función única. El manejo de errores (fitz/pdfplumber)
            # ahora está 100% dentro de pdf_processor.py.
            lineas = extraer_texto_de_pdf(pdf_path) 
            
            # Step 2: Turn text into data (pandas)
            df = parsear_lineas_a_dataframe(lineas)
            
            # Step 3: Classify the data (High, Low, etc.)
            if not df.empty:
                df = clasificar_resultados(df)
            else:
                return jsonify({'error': 'No data could be extracted from this PDF.'}), 400
        
        # Convert the data to JSON for our frontend
        results_json = json.loads(df.to_json(orient='records'))
        
        return jsonify({
            'success': True,
            'results': results_json,
            'summary': calculate_summary_from_df(df),
            'report_date': report_date_str
        })
        
    except Exception as e:
        # Esto es lo que verá el usuario, si algo falla
        return jsonify({'error': f'Analysis failed due to: {str(e)}'}), 500

# The REAL PDF generator endpoint
@app.route('/api/generate-pdf', methods=['POST'])
@jwt_required()
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
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)