import pdfplumber

def extraer_texto_de_pdf(ruta_pdf):
    all_text = ""
    try:
        with pdfplumber.open(ruta_pdf) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    all_text += text + "\n"
        return all_text.split("\n")
    except Exception as e:
        print(f"ERROR: Fallo al abrir o extraer el PDF: {e}")
        return []