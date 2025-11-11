import os
import re
# Usaremos el import que Railway parece preferir de tu log:
import google.genai as genai
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

def _configurar_cliente_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("No se encontró la GEMINI_API_KEY.")
    
    # Esta línea asegura que la clave se establezca para la API de Gemini
    os.environ["GEMINI_API_KEY"] = api_key 
    return genai.Client()

def _lab_results_to_text(df):
    lines = []
    # Aquí es donde aplicamos la seguridad: usamos .to_dict() para la fila si fuera necesario, 
    # pero el código que tienes es estable si las filas contienen los tipos esperados.
    for _, row in df.iterrows():
        line = (
            f"{row['Test']}: {row['Value']} {row['Unit']} "
            f"(reference range {row['Ref Low']}–{row['Ref High']}). "
            f"Status: {row['Status']}."
        )
        lines.append(line)
    return "Here are the patient's laboratory results:\n\n" + "\n".join(lines)

def _generate_doctor_prompt(content):
    # Prompt de doctor
    return f"""
You are a licensed medical doctor specializing in clinical laboratory interpretation.
Below are the patient's blood test results:

{content}

Please write a concise medical report that follows these guidelines:
1. Summarize all normal findings briefly.
2. Describe in more detail the parameters marked as “Near” or “High”.
3. If any abnormal or borderline values could be associated with physiological changes
   or potential medical conditions, mention them as possible interpretations —
   but make it clear that these are hypotheses, not diagnoses.
4. If all values are within normal ranges, state that explicitly.
5. Use clear, professional medical language in English.
6. Organize the report into 2–4 coherent paragraphs.
7. End with this disclaimer:
   “This report is for informational purposes only and does not replace professional medical evaluation.”
"""

def _generate_patient_prompt(content):
    # Prompt de paciente
    return f"""
You are a friendly and empathetic health advisor. Your goal is to help a person
understand their lab results in a simple, clear, and positive way.
Use everyday language and a relatable tone.

Here are the person's lab results:

{content}

Please write a summary for the patient following these guidelines:

1.  Simple Language: Explain the results as if you were talking to a friend.
    Avoid medical jargon completely.
2.  Normal Results: Start by congratulating the person for the results
    that are within the normal range. Briefly and simply explain
    what it means to have those values at a healthy level.
3.  Areas for Improvement: For each value marked as "High",
    "Low", or "Near", do the following:
    a. Explain very simply what that parameter measures.
    b. Without being alarming, mention why it's a good idea to pay attention to that value.
    c. Offer 2-3 practical and actionable lifestyle recommendations to help
       improve that value. They should be easy tips to incorporate into daily life.
4.  Positive and Motivational Tone.
5.  Clear Structure: Organize the report into short, easy-to-read paragraphs. The formatting must be simple, containing only explanatory text without bolding, symbols, or lists.
6.  Final Disclaimer: You must end with the following text:
    "Remember, this is an interpretation to help you understand your results.
    It does not replace a consultation with your doctor, who knows your history
    and will give you the best recommendations. Always talk to your doctor!"
"""

def generar_reporte_ia(df, tipo_prompt):
    client = _configurar_cliente_gemini()
    # Usamos la versión de prompt que se adapte al tipo
    content = _lab_results_to_text(df) 
    
    if tipo_prompt == "doctor":
        prompt = _generate_doctor_prompt(content)
    elif tipo_prompt == "paciente":
        prompt = _generate_patient_prompt(content)
    else:
        raise ValueError("Tipo de prompt no válido. Debe ser 'doctor' o 'paciente'.")
        
    response = client.models.generate_content(
        model="gemini-2.5-flash",  
        contents=prompt
    )

    return response.text

def create_medical_report_pdf(output_filename, report_text, image_path=None):
    # Lógica de Reportlab para crear el PDF final
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        topMargin=inch, bottomMargin=inch,
        leftMargin=inch, rightMargin=inch
    )
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(name="Normal_Justified", parent=styles["Normal"], alignment=TA_JUSTIFY, spaceAfter=12, leading=14))
    styles.add(ParagraphStyle(name="Bold_Disclaimer", parent=styles["Normal_Justified"], fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name="Bullet_Style", parent=styles["Normal_Justified"], leftIndent=20, spaceAfter=6))

    Story = []

    # Se mantiene la traducción de **Markdown** a etiquetas <b>HTML para Reportlab
    report_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', report_text)
    blocks = report_text.strip().split('\n\n')

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        
        if "Remember, this is an interpretation" in block or "This report is for informational" in block:
            Story.append(Paragraph(block, styles["Bold_Disclaimer"]))
            continue
        
        if block.startswith('* '):
            list_items = block.split('\n')
            for item in list_items:
                item_clean = item.strip().lstrip('* ').strip()
                if item_clean:
                    Story.append(Paragraph(item_clean, styles["Bullet_Style"]))
            Story.append(Spacer(1, 0.1 * inch))
        else:
            Story.append(Paragraph(block, styles["Normal_Justified"]))
            
    try:
        doc.build(Story)
    except Exception as e:
        print(f"Error construyendo el PDF: {e}")