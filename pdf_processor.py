import pdfplumber
import fitz  # PyMuPDF
import unicodedata
import re

def extraer_texto_de_pdf(ruta_pdf):
    """
    Extrae todo el texto de un archivo PDF.
    Toma la lógica de la celda 2.
    """
    all_text = ""
    with pdfplumber.open(ruta_pdf) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_text += text + "\n"
    
    return all_text.split("\n")

def _generate_variants(name: str):
    """
    Crea variantes de un nombre para buscar en el PDF.
    Toma la lógica de la celda 5.
    """
    def deaccent(s):
        s2 = unicodedata.normalize("NFKD", s)
        return "".join(c for c in s2 if not unicodedata.combining(c))

    base = re.sub(r"\s+", " ", name).strip()
    no_accent = re.sub(r"\s+", " ", deaccent(name)).strip()

    variants = {
        base,
        no_accent,
        base.replace(".", ","),
        base.replace(",", "."),
        no_accent.replace(".", ","),
        no_accent.replace(",", "."),
        " ".join(base.split()),
        " ".join(no_accent.split()),
    }
    return [v for v in variants if v]

def pintar_pdf(pdf_in_path, pdf_out_path, df):
    """
    Crea un nuevo PDF con los resultados resaltados.
    Toma la lógica de la celda 5.
    """
    doc = fitz.open(pdf_in_path)
    highlighted_tests = set()

    for page in doc:
        for _, row in df.iterrows():
            test = str(row["Test"])
            status = row["Status"]

            if test not in highlighted_tests:
                found = []
                for variante in _generate_variants(test):
                    if len(variante) > 1:
                        inst = page.search_for(variante)
                        if inst:
                            found = inst
                            break

                for rect in found:
                    annot = page.add_rect_annot(rect)
                    if status == "Normal":
                        annot.set_colors(stroke=(0, 1, 0), fill=(0, 1, 0))  # Verde
                    elif status == "Near":
                        annot.set_colors(stroke=(1, 0.65, 0), fill=(1, 0.65, 0))  # Naranja
                    else:
                        annot.set_colors(stroke=(1, 0, 0), fill=(1, 0, 0))  # Rojo
                    annot.set_opacity(0.5)
                    annot.set_border(width=1.5)
                    annot.update()

                if found:
                    highlighted_tests.add(test)

    doc.save(pdf_out_path, deflate=True)
    doc.close()