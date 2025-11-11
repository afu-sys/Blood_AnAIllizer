import re
import pandas as pd
from math import inf

def parsear_lineas_a_dataframe(lines):
    pattern_range = (
        r"([A-Za-z0-9\s()/.\*]+?)" 
        r"\s+H?([\d.,]+(?:E\d+)?)"
        r"\s*([a-zA-Z0-9/%µ.*]*)?"
        r"\s+([\d.,]+)\s*(?:-|\s)\s*([\d.,]+)"
    )

    pattern_threshold = (
        r"([A-Za-z0-9\s()/.\*]+?)" 
        r"\s*([<>])?\s*([\d.,]+(?:E\d+)?)"
        r"\s*([a-zA-Z0-9/%µ,^]*\s*m2|[a-zA-Z0-9/%µ,^]*)?"
        r"\s*([<>])\s*([\d.,]+)"
    )

    data = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith(("Page", "Página")) or not any(c.isdigit() for c in line):
            continue
        
        line = line.replace(",", ".").replace("[", "").replace("]", "").replace("*", "")

        for match in re.finditer(pattern_range, line):
            test, value, unit, ref_low, ref_high = match.groups()
            if not value: continue
            data.append([test.strip(), float(value), unit if unit else "", float(ref_low), float(ref_high)])

        for match in re.finditer(pattern_threshold, line):
            test, sign_val, value, unit, sign_ref, limit = match.groups()
            if not value or not limit: continue 

            value = float(value) if value else None
            limit = float(limit) if limit else None

            ref_low, ref_high = (0.0, limit) if sign_ref == "<" else (limit, inf)
            
            data.append([test.strip(), value, unit if unit else "", ref_low, ref_high])

    return pd.DataFrame(data, columns=["Test", "Value", "Unit", "Ref Low", "Ref High"])

def clasificar_resultados(df):
    if df.empty:
        return df
        
    df["Status"] = df.apply(
        lambda row: ("Normal" if row["Ref Low"] <= row["Value"] <= row["Ref High"] else ("Near"
            if ((row["Ref High"] == inf and row["Ref Low"] > 0 and abs(row["Value"] - row["Ref Low"]) <= 0.25 * row["Ref Low"])
                or (row["Ref Low"] == -inf and row["Ref High"] > 0 and abs(row["Value"] - row["Ref High"]) <= 0.25 * row["Ref High"])
                or (row["Ref High"] != inf and row["Ref Low"] != -inf and (row["Ref High"] - row["Ref Low"]) > 0
                    and abs(row["Value"] - max(min(row["Value"], row["Ref High"]), row["Ref Low"])) <= 0.25 * (row["Ref High"] - row["Ref Low"])
                )
            )
            else ("Low" if row["Value"] < row["Ref Low"] else "High")
        )
    ),
    axis=1,
    )
    return df