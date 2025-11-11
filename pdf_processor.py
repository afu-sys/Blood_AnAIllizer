import pdfplumber
import fitz  # PyMuPDF
import unicodedata
import re
        

# Esta función de extracción ahora es mucho más robusta
def extraer_texto_de_pdf(ruta_pdf):
    """
    Extrae todo el texto de un archivo PDF usando PyMuPDF (fitz) por su robustez.
    Si falla, intenta con pdfplumber como respaldo.
    """
    all_text = ""
    
    # 1. Intento principal (PyMuPDF - más robusto para texto)
    try:
        doc = fitz.open(ruta_pdf)
        for page in doc:
            # Normalizar el texto (importante para que el regex funcione)
            text = unicodedata.normalize("NFKD", page.get_text()).strip()
            if text:
                all_text += text + "\n"
        doc.close()
        
        if len(all_text) < 50: # Si extrajo muy poco, es un fallo
            raise Exception("PyMuPDF extracted insufficient data.")
            
        return all_text.split("\n")

    except Exception as e:
        print(f"Alerta: PyMuPDF falló ({e}). Intentando con pdfplumber...")
        
        # 2. Intento de respaldo (pdfplumber)
        try:
            with pdfplumber.open(ruta_pdf) as pdf:
                for page in pdf.pages:
                    text = page.extract_text(x_tolerance=1, y_tolerance=1) # A veces mejoran la extracción
                    if text:
                        all_text += text + "\n"
            
            if len(all_text) < 50:
                raise Exception("Ambos extractores fallaron al obtener texto suficiente.")
                
            return all_text.split("\n")
            
        except Exception as e_final:
            print(f"Error final: Ambos métodos fallaron. {e_final}")
            raise e_final
            

def _generate_variants(name: str):
    """
    Crea variantes de un nombre para buscar en el PDF. (Lógica de pintar_pdf)
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
    Crea un nuevo PDF con los resultados resaltados. (Función de la celda 5)
    """
    # ... (código sin cambios, usa fitz y es solo para descargar) ...
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