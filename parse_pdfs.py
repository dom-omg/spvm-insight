#!/usr/bin/env python3
"""
Extrait le texte complet + tableaux de chaque rapport PDF SPVM.
Sauvegarde tout en JSON pour l'assistant IA et le dashboard.
"""
import pdfplumber, json, os, re

def clean(s):
    if s is None: return ""
    return re.sub(r'\s+', ' ', str(s)).strip()

def extract_report(year, path):
    print(f"\n{'='*50}\nRapport {year} — {path}")
    result = {"year": year, "pages": [], "tables": [], "full_text": ""}
    full_text = []
    try:
        with pdfplumber.open(path) as pdf:
            print(f"  {len(pdf.pages)} pages")
            for i, page in enumerate(pdf.pages):
                # Texte
                txt = page.extract_text() or ""
                if txt.strip():
                    full_text.append(f"\n--- PAGE {i+1} ---\n{txt}")
                    result["pages"].append({"page": i+1, "text": txt[:2000]})

                # Tableaux
                tables = page.extract_tables()
                for t_idx, table in enumerate(tables):
                    if not table: continue
                    clean_table = [[clean(cell) for cell in row] for row in table if any(cell for cell in row)]
                    if len(clean_table) > 1:
                        result["tables"].append({
                            "year": year, "page": i+1, "table_idx": t_idx,
                            "data": clean_table[:30]  # max 30 lignes
                        })

    except Exception as e:
        print(f"  ERREUR: {e}")

    result["full_text"] = "\n".join(full_text)[:150000]  # max 150k chars
    print(f"  Texte: {len(result['full_text'])} chars | Tableaux: {len(result['tables'])}")
    return result

# Extraire tous les rapports
all_reports = {}
for year in [2024,2023,2022,2021,2020,2019,2018,2017,2016,2015]:
    path = f"pdfs/spvm_{year}.pdf"
    if not os.path.exists(path): continue
    data = extract_report(year, path)
    all_reports[str(year)] = data
    # Sauvegarder le texte complet séparément
    with open(f"data/text_{year}.txt", "w", encoding="utf-8") as f:
        f.write(data["full_text"])
    # Version light pour le dashboard (sans full_text)
    light = {k:v for k,v in data.items() if k != "full_text"}
    with open(f"data/tables_{year}.json", "w", encoding="utf-8") as f:
        json.dump(light, f, ensure_ascii=False, indent=2)

print(f"\n✓ Extraction complète — {len(all_reports)} rapports")

# Index des rapports disponibles
index = {yr: {"pages": len(d["pages"]), "tables": len(d["tables"]),
               "text_size": len(d["full_text"])}
         for yr, d in all_reports.items()}
with open("data/index.json", "w") as f:
    json.dump(index, f, indent=2)
print(json.dumps(index, indent=2))
