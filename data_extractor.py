import re
import pandas as pd
from math import inf # Necesario para usar inf

# ==========================================================
# Adaptación de la celda 54 (Regex)
# NOTA: Se usa una expresión más segura para el nombre de la prueba
# para evitar problemas de codificación de caracteres acentuados (ñ, á) en Railway/scripts.
# ==========================================================
def parsear_lineas_a_dataframe(lines):
    
    # FIX: Se usa una expresión más segura para el nombre de la prueba
    # Se eliminan los caracteres acentuados y se simplifica la clase de caracteres.
    
    # PATRÓN 1: RANGOS NORMALES
    pattern_range = (
        r"([A-Za-z0-9\s()/.\*]+?)" # Nombre de la prueba simplificado (solo caracteres ASCII seguros)
        r"\s+H?([\d.,]+(?:E\d+)?)"
        r"\s*([a-zA-Z0-9/%µ.*]*)?"
        r"\s+([\d.,]+)\s*(?:-|\s)\s*([\d.,]+)"
    )

    # PATRÓN 2: UMBRALES (< o >)
    pattern_threshold = (
        r"([A-Za-z0-9\s()/.\*]+?)" # Nombre de la prueba simplificado
        r"\s*([<>])?\s*([\d.,]+(?:E\d+)?)"
        r"\s*([a-zA-Z0-9/%µ,^]*\s*m2|[a-zA-Z0-9/%µ,^]*)?"
        r"\s*([<>])\s*([\d.,]+)"
    )

    data = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith(("Page", "Página")) or not any(c.isdigit() for c in line):
            continue
        
        # Pre-procesamiento de la línea
        line = line.replace(",", ".").replace("[", "").replace("]", "").replace("*", "")

        # Caso 1: rangos normales
        for match in re.finditer(pattern_range, line):
            test, value, unit, ref_low, ref_high = match.groups()
            
            if not value: continue
            
            data.append([
                test.strip(),
                float(value),
                unit if unit else "",
                float(ref_low),
                float(ref_high)
            ])

        # Caso 2: umbrales
        for match in re.finditer(pattern_threshold, line):
            test, sign_val, value, unit, sign_ref, limit = match.groups()
            
            if not value or not limit: continue 

            value = float(value) if value else None
            limit = float(limit) if limit else None

            # Ajustar el rango según el umbral (< o >)
            ref_low, ref_high = (0.0, limit) if sign_ref == "<" else (limit, inf)
            
            data.append([
                test.strip(),
                value,
                unit if unit else "",
                ref_low,
                ref_high
            ])

    return pd.DataFrame(data, columns=["Test", "Value", "Unit", "Ref Low", "Ref High"])

# Adaptación de la celda 55 (Clasificación de Status)
def clasificar_resultados(df):
    if df.empty:
        return df
        
    df["Status"] = df.apply(
        lambda row: (
            "Normal"
            if row["Ref Low"] <= row["Value"] <= row["Ref High"]
            else (
                "Near"
                if (
                    (   # Caso 1: Rango alto (<X) - Proximidad al límite inferior
                        row["Ref High"] == inf
                        and row["Ref Low"] > 0
                        and abs(row["Value"] - row["Ref Low"]) <= 0.25 * row["Ref Low"]
                    )
                    or ( # Caso 2: Rango bajo (>X) - Proximidad al límite superior
                        row["Ref Low"] == -inf
                        and row["Ref High"] > 0
                        and abs(row["Value"] - row["Ref High"]) <= 0.25 * row["Ref High"]
                    )
                    or ( # Caso 3: Rango definido [Low, High] - Proximidad al rango
                        row["Ref High"] != inf
                        and row["Ref Low"] != -inf
                        and (row["Ref High"] - row["Ref Low"]) > 0
                        and abs(
                            row["Value"]
                            - max(min(row["Value"], row["Ref High"]), row["Ref Low"])
                        )
                        <= 0.25 * (row["Ref High"] - row["Ref Low"])
                    )
                )
                else ("Low" if row["Value"] < row["Ref Low"] else "High")
            )
        ),
        axis=1,
    )
    return df