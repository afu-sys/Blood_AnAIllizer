import os
import re
import google.genai as genai
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

def _configurar_cliente_gemini():
    API_KEY = os.getenv("GEMINI_API_KEY")
    if not API_KEY:
        raise ValueError("No se encontró la GEMINI_API_KEY.")
    genai.configure(api_key=API_KEY)

def _lab_results_to_text(df):
    lines = []
    for _, row in df.iterrows():
        row_dict = row.to_dict()
        # --- ¡ESTA ES LA CORRECCIÓN DEL KEYERROR! ---
        # Usamos las claves en minúscula/camelCase que app.py define
        line = (
            f"{row_dict['test']}: {row_dict['value']} {row_dict['unit']} "
            f"(reference range {row_dict['refLow']}–{row_dict['refHigh']}). "
            f"Status: {row_dict['status']}."
        )
        lines.append(line)
    return "Here are the patient's laboratory results:\n\n" + "\n".join(lines)

def _generate_prompt(content, tipo_prompt):
    if tipo_prompt == "doctor":
        return f"Actúa como un médico. Analiza estos resultados y haz un breve resumen profesional de 3 párrafos. {content}"
    if tipo_prompt == "paciente":
        return f"Actúa como un asesor de salud. Analiza estos resultados y da un consejo amigable de 3 párrafos. {content}"
    return ""

def generar_reporte_ia(df, tipo_prompt):
    _configurar_cliente_gemini()
    content = _lab_results_to_text(df)
    prompt = _generate_prompt(content, tipo_prompt)

    model = genai.GenerativeModel("gemini-1.5-flash") 
    response = model.generate_content(contents=prompt)
    return response.text

def create_medical_report_pdf(output_filename, report_text):
    doc = SimpleDocTemplate(output_filename, pagesize=letter, topMargin=inch, bottomMargin=inch, leftMargin=inch, rightMargin=inch)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Normal_Justified", parent=styles["Normal"], alignment=TA_JUSTIFY, spaceAfter=12, leading=14))
    
    Story = []
    blocks = report_text.strip().split('\n\n')

    for block in blocks:
        if block.strip():
            # --- ¡ESTA ES LA CORRECCIÓN DEL TYPO! ---
            Story.append(Paragraph(block.strip(), styles["Normal_Justified"]))
            
    doc.build(Story)
    