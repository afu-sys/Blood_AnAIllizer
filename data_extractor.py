import re
import pandas as pd

# Adaptación de la celda 54 (Regex)
def parsear_lineas_a_dataframe(lines):
    pattern_range = (
        r"([A-Za-z0-9ÁÉÍÓÚÜáéíóúüñ\(\)/\\-\\s\\*\\.]+?)"
        r"\s+H?([\d.,]+(?:E\d+)?)"
        r"\s*([a-zA-Z0-9/%µ\\.\\*]*)?"
        r"\s+([\d.,]+)\s*(?:-|\\s)\s*([\d.,]+)"
    )

    pattern_threshold = (
        r"([A-Za-z0-9ÁÉÍÓÚÜáéíóúüñ\(\)/\\-\\s\\*\\.]+?)"
        r"\s*([<>])?\s*([\d.,]+(?:E\d+)?)"
        r"\s*([a-Za-z0-9/%µ\\.\\,\\^]*\s*m2|[a-zA-Z0-9/%µ\\.\\,\\^]*)?"
        r"\s*([<>])\s*([\d.,]+)"
    )

    data = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith(("Page", "Página")) or not any(c.isdigit() for c in line):
            continue
        
        # Corrección: Quitar los puntos y comas que rompen el Regex.
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
            test, sign_val, value, unit, sign_ref, limit = match.groups()
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

# Adaptación de la celda 55 (Clasificación de Status)
def clasificar_resultados(df):
    df["Status"] = df.apply(
        lambda row: (
            "Normal"
            if row["Ref Low"] <= row["Value"] <= row["Ref High"]
            else (
                "Near"
                if (
                    (   # Case 1, we only have the higher ref (<X)
                        row["Ref High"] == float("inf")
                        and abs(row["Value"] - row["Ref Low"]) <= 0.25 * row["Ref Low"]
                    )
                    or ( # Case 2, we only have the lower ref (>X)
                        row["Ref Low"] == float("-inf")
                        and abs(row["Value"] - row["Ref High"]) <= 0.25 * row["Ref High"]
                    )
                    or ( # Case 3, we have the range
                        row["Ref High"] != float("inf")
                        and row["Ref Low"] != float("-inf")
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