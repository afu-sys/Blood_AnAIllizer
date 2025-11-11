import re
import pandas as pd

def parsear_lineas_a_dataframe(lines):
    """
    Aplica Regex a las líneas de texto y las convierte en un DataFrame.
    Toma la lógica de la celda 3.
    """
    
    # Patrón para rangos normales (bajo - alto)
    pattern_range = (
        r"([A-Za-z0-9ÁÉÍÓÚÜáéíóúüñ\(\)/\\-\\s\\*\\.]+?)"  # test name
        r"\s+H?([\d.,]+(?:E\d+)?)"                   # value
        r"\s*([a-zA-Z0-9/%µ\\.\\*]*)?"                 # unit
        r"\s+([\d.,]+)\s*(?:-|\\s)\s*([\d.,]+)"       # ref low and high
    )

    # Patrón para umbrales (< o >)
    pattern_threshold = (
        r"([A-Za-z0-9ÁÉÍÓÚÜáéíóúüñ\(\)/\\-\\s\\*\\.]+?)"
        r"\s*([<>])?\s*([\d.,]+(?:E\d+)?)"
        r"\s*([a-zA-Z0-9/%µ\\.\\,\\^]*\s*m2|[a-zA-Z0-9/%µ\\.\\,\\^]*)?"
        r"\s*([<>])\s*([\d.,]+)"
    )

    data = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith(("Page", "Página")) or not any(c.isdigit() for c in line):
            continue
        
        # --- AÑADE ESTA LIMPIEZA MÁS FUERTE ---
        # 1. Eliminar caracteres que no sean espacio, letra o número de base
        # Se asegura de que no haya basura en la línea que rompa el Regex
        line = re.sub(r'[^\w\s\.\,\-\+\(\)/\\*<>\[\]]', '', line, flags=re.UNICODE) 
        
        # 2. Normalizar números y símbolos de unidad
        line = line.replace(",", ".").replace("[", "").replace("]", "").replace("*", "")

        # Caso 1: rangos normales
        for match in re.finditer(pattern_range, line):
            test, value, unit, ref_low, ref_high = match.groups()
            data.append([
                test.strip(),
                float(value),
                unit if unit else "",
                float(ref_low),
                float(ref_high)
            ])

        # Caso 2: umbrales
        for match in re.finditer(pattern_threshold, line):
            test, _, value, unit, sign_ref, limit = match.groups()
            value = float(value.replace(",", ".")) if value else None
            limit = float(limit.replace(",", ".")) if limit else None

            ref_low, ref_high = (0.0, limit) if sign_ref == "<" else (limit, float("inf"))
            
            data.append([
                test.strip(),
                value,
                unit if unit else "",
                ref_low,
                ref_high
            ])

    return pd.DataFrame(data, columns=["Test", "Value", "Unit", "Ref Low", "Ref High"])

def clasificar_resultados(df):
    """
    Añade la columna 'Status' al DataFrame.
    Toma la lógica de la celda 4.
    """
    df["Status"] = df.apply(
        lambda row: (
            "Normal"
            if row["Ref Low"] <= row["Value"] <= row["Ref High"]
            else (
                "Near"
                if (
                    (row["Ref High"] == float("inf") and abs(row["Value"] - row["Ref Low"]) <= 0.25 * row["Ref Low"])
                    or (row["Ref Low"] == float("-inf") and abs(row["Value"] - row["Ref High"]) <= 0.25 * row["Ref High"])
                    or (
                        row["Ref High"] != float("inf")
                        and row["Ref Low"] != float("-inf")
                        and (row["Ref High"] - row["Ref Low"]) > 0
                        and abs(row["Value"] - max(min(row["Value"], row["Ref High"]), row["Ref Low"]))
                        <= 0.25 * (row["Ref High"] - row["Ref Low"])
                    )
                )
                else ("Low" if row["Value"] < row["Ref Low"] else "High")
            )
        ),
        axis=1,
    )
    return df