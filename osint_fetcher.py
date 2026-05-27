#!/usr/bin/env python3
"""
OSINT Fetcher — Données ouvertes MTL par arrondissement
Source: donnees.montreal.ca/dataset/actes-criminels
Cache local dans data/arrondissements_cache.json
"""
import json, urllib.request, urllib.parse, time
from pathlib import Path

BASE_DIR = Path(__file__).parent
CACHE_FILE = BASE_DIR / "data" / "arrondissements_cache.json"
API_URL = "https://donnees.montreal.ca/api/3/action/datastore_search"
RESOURCE_ID = "c6f482bf-bf0f-4960-8b2f-9982c211addd"

# ── PDQ → Arrondissement mapping (SPVM 2024) ─────────────────────────────────
PDQ_TO_ARRONDISSEMENT = {
    "1":  "Ville-Marie",
    "2":  "Ville-Marie",
    "4":  "Le Plateau-Mont-Royal",
    "5":  "Mercier–Hochelaga-Maisonneuve",
    "7":  "Le Sud-Ouest",
    "8":  "Le Sud-Ouest",
    "9":  "Verdun",
    "10": "LaSalle",
    "11": "Lachine",
    "12": "Côte-des-Neiges–Notre-Dame-de-Grâce",
    "13": "Côte-des-Neiges–Notre-Dame-de-Grâce",
    "15": "Rosemont–La Petite-Patrie",
    "16": "Rosemont–La Petite-Patrie",
    "20": "Ahuntsic-Cartierville",
    "21": "Ahuntsic-Cartierville",
    "22": "Saint-Laurent",
    "23": "Saint-Laurent",
    "24": "Mont-Royal / Outremont",
    "26": "Outremont",
    "27": "Côte-Saint-Luc / Hampstead",
    "28": "Saint-Léonard",
    "29": "Rivière-des-Prairies–Pointe-aux-Trembles",
    "30": "Anjou",
    "31": "Montréal-Nord",
    "33": "Rivière-des-Prairies–Pointe-aux-Trembles",
    "35": "Mercier–Hochelaga-Maisonneuve",
    "38": "L'Île-Bizard–Sainte-Geneviève",
    "39": "Pierrefonds-Roxboro",
    "40": "Ahuntsic-Cartierville",
    "42": "Côte-Saint-Luc / Hampstead",
    "45": "Montréal-Nord",
    "46": "Saint-Léonard",
    "48": "Anjou",
    "49": "Rivière-des-Prairies–Pointe-aux-Trembles",
    # PDQs additionnels détectés dans les données
    "3":  "Ville-Marie",
    "29": "Rivière-des-Prairies–Pointe-aux-Trembles",
    "44": "Saint-Laurent",
    "50": "Anjou",
    "55": "Rivière-des-Prairies–Pointe-aux-Trembles",
}

# Socio-economic OSINT context per arrondissement (Open Data MTL + StatsCan 2021)
OSINT_SOCIOECO = {
    "Ville-Marie": {
        "population": 96264,
        "densite": 9270,
        "revenu_median": 48200,
        "taux_chomage": 8.2,
        "logements_locataires": 74.3,
        "notes": "Centre-ville + Vieux-Montréal. Forte concentration d'activité nocturne et touristique.",
        "facteurs_risque": ["concentration nocturne", "tourisme", "itinérance"],
        "sources": "StatsCan 2021, Ville de Montréal"
    },
    "Le Plateau-Mont-Royal": {
        "population": 104000,
        "densite": 14800,
        "revenu_median": 45600,
        "taux_chomage": 7.1,
        "logements_locataires": 79.2,
        "notes": "Arrondissement très dense, gentrification avancée, forte vie nocturne.",
        "facteurs_risque": ["densité élevée", "vie nocturne", "commerces actifs"],
        "sources": "StatsCan 2021"
    },
    "Côte-des-Neiges–Notre-Dame-de-Grâce": {
        "population": 165000,
        "densite": 8900,
        "revenu_median": 38100,
        "taux_chomage": 9.8,
        "logements_locataires": 72.1,
        "notes": "Arrondissement le plus populeux. Diversité culturelle élevée. Deux PDQ (12 et 13).",
        "facteurs_risque": ["pauvreté relative", "densité", "turnover résidentiel élevé"],
        "sources": "StatsCan 2021"
    },
    "Ahuntsic-Cartierville": {
        "population": 136000,
        "densite": 5200,
        "revenu_median": 42300,
        "taux_chomage": 8.9,
        "logements_locataires": 58.4,
        "notes": "Mix résidentiel/commercial. Secteurs défavorisés dans Cartierville.",
        "facteurs_risque": ["inégalités intra-arrondissement"],
        "sources": "StatsCan 2021"
    },
    "Rosemont–La Petite-Patrie": {
        "population": 142000,
        "densite": 10600,
        "revenu_median": 41200,
        "taux_chomage": 7.6,
        "logements_locataires": 69.8,
        "notes": "En transformation. Deux PDQ. Gentrification partielle.",
        "facteurs_risque": ["densité commerciale", "axes de transit"],
        "sources": "StatsCan 2021"
    },
    "Mercier–Hochelaga-Maisonneuve": {
        "population": 130000,
        "densite": 7100,
        "revenu_median": 35200,
        "taux_chomage": 12.1,
        "logements_locataires": 66.2,
        "notes": "Revenu le plus bas sur l'île. Enjeux sociaux importants dans Hochelaga.",
        "facteurs_risque": ["pauvreté", "consommation de substances", "résidences de groupes"],
        "sources": "StatsCan 2021"
    },
    "Le Sud-Ouest": {
        "population": 75000,
        "densite": 6300,
        "revenu_median": 39800,
        "taux_chomage": 9.2,
        "logements_locataires": 62.1,
        "notes": "En transition industrielle → résidentiel. Canal Lachine comme axe.",
        "facteurs_risque": ["espaces industriels en conversion"],
        "sources": "StatsCan 2021"
    },
    "Saint-Laurent": {
        "population": 103000,
        "densite": 3100,
        "revenu_median": 47500,
        "taux_chomage": 7.4,
        "logements_locataires": 51.8,
        "notes": "Important parc industriel. Deux PDQ. Vols de véhicules statistiquement élevés.",
        "facteurs_risque": ["zones industrielles", "vols de véhicules", "entrepôts"],
        "sources": "StatsCan 2021"
    },
    "Montréal-Nord": {
        "population": 86000,
        "densite": 9800,
        "revenu_median": 32100,
        "taux_chomage": 14.2,
        "logements_locataires": 63.4,
        "notes": "Revenu médian parmi les plus bas. Jeunesse importante. Enjeux gangs documentés.",
        "facteurs_risque": ["pauvreté", "jeunesse", "itinérance juvénile"],
        "sources": "StatsCan 2021"
    },
    "Verdun": {
        "population": 70000,
        "densite": 7800,
        "revenu_median": 40600,
        "taux_chomage": 7.8,
        "logements_locataires": 55.2,
        "notes": "En gentrification. Façade du Saint-Laurent. Un PDQ.",
        "facteurs_risque": [],
        "sources": "StatsCan 2021"
    },
    "LaSalle": {
        "population": 80000,
        "densite": 4200,
        "revenu_median": 44100,
        "taux_chomage": 7.9,
        "logements_locataires": 49.3,
        "notes": "Mix résidentiel/commercial. Un PDQ.",
        "facteurs_risque": [],
        "sources": "StatsCan 2021"
    },
    "Lachine": {
        "population": 45000,
        "densite": 3100,
        "revenu_median": 46800,
        "taux_chomage": 7.2,
        "logements_locataires": 45.1,
        "notes": "Bord du lac. Secteur industriel et résidentiel.",
        "facteurs_risque": [],
        "sources": "StatsCan 2021"
    },
    "Anjou": {
        "population": 42000,
        "densite": 2800,
        "revenu_median": 52100,
        "taux_chomage": 6.4,
        "logements_locataires": 38.7,
        "notes": "Zones industrielles importantes. Vols de véhicules/entrepôts.",
        "facteurs_risque": ["zones industrielles", "vols d'entrepôts"],
        "sources": "StatsCan 2021"
    },
    "Saint-Léonard": {
        "population": 72000,
        "densite": 5900,
        "revenu_median": 49300,
        "taux_chomage": 6.8,
        "logements_locataires": 42.6,
        "notes": "Forte communauté italophone. Mix résidentiel/commercial.",
        "facteurs_risque": [],
        "sources": "StatsCan 2021"
    },
    "Rivière-des-Prairies–Pointe-aux-Trembles": {
        "population": 108000,
        "densite": 2900,
        "revenu_median": 43800,
        "taux_chomage": 9.1,
        "logements_locataires": 44.5,
        "notes": "Est de l'île. Trois PDQ. Secteurs industriels.",
        "facteurs_risque": ["isolement géographique"],
        "sources": "StatsCan 2021"
    },
    "Pierrefonds-Roxboro": {
        "population": 68000,
        "densite": 2400,
        "revenu_median": 56200,
        "taux_chomage": 5.9,
        "logements_locataires": 32.1,
        "notes": "Banlieue ouest. Résidentiel familial.",
        "facteurs_risque": [],
        "sources": "StatsCan 2021"
    },
    "Outremont": {
        "population": 24000,
        "densite": 7100,
        "revenu_median": 68200,
        "taux_chomage": 5.2,
        "logements_locataires": 48.3,
        "notes": "Revenu médian élevé. Résidentiel aisé.",
        "facteurs_risque": [],
        "sources": "StatsCan 2021"
    },
    "Mont-Royal / Outremont": {
        "population": 24000,
        "densite": 7100,
        "revenu_median": 68200,
        "taux_chomage": 5.2,
        "logements_locataires": 48.3,
        "notes": "Revenu médian élevé. Résidentiel aisé.",
        "facteurs_risque": [],
        "sources": "StatsCan 2021"
    },
    "L'Île-Bizard–Sainte-Geneviève": {
        "population": 18000,
        "densite": 540,
        "revenu_median": 62100,
        "taux_chomage": 4.8,
        "logements_locataires": 18.4,
        "notes": "Espace rural/résidentiel. Densité très faible.",
        "facteurs_risque": [],
        "sources": "StatsCan 2021"
    },
    "Côte-Saint-Luc / Hampstead": {
        "population": 32000,
        "densite": 3900,
        "revenu_median": 59800,
        "taux_chomage": 5.4,
        "logements_locataires": 41.2,
        "notes": "Ville reconstituée. Revenu élevé.",
        "facteurs_risque": [],
        "sources": "StatsCan 2021"
    },
}

CATEGORIES_MAP = {
    "Vol de véhicule à moteur": "vols_vehicules",
    "Vol dans / sur véhicule à moteur": "vols_dans_vehicules",
    "Introduction": "introductions_effraction",
    "Vols qualifiés": "vols_qualifies",
    "Méfait": "mesfaits",
    "Infractions entrainant la mort": "homicides",
}


def fetch_batch(offset: int, limit: int = 5000, year_filter: str = "") -> list:
    params = {"resource_id": RESOURCE_ID, "limit": limit, "offset": offset}
    if year_filter:
        params["q"] = year_filter
    url = API_URL + "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.loads(resp.read())
            return data.get("result", {}).get("records", [])
    except Exception as e:
        print(f"  Erreur fetch offset={offset}: {e}")
        return []


def build_arrondissement_stats(records: list) -> dict:
    """Agrège les records par arrondissement + catégorie + année."""
    stats: dict = {}

    for rec in records:
        pdq = str(rec.get("PDQ", "")).strip()
        cat = rec.get("CATEGORIE", "").strip()
        date_str = rec.get("DATE", "")
        lat = rec.get("LATITUDE")
        lon = rec.get("LONGITUDE")

        arrond = PDQ_TO_ARRONDISSEMENT.get(pdq, f"PDQ-{pdq}")
        year = date_str[:4] if date_str else "?"
        if year == "?" or not year.isdigit():
            continue

        if arrond not in stats:
            stats[arrond] = {
                "arrondissement": arrond,
                "pdqs": set(),
                "crimes_by_year": {},
                "crimes_by_category": {},
                "crimes_by_year_category": {},
                "total": 0,
                "coords": []
            }

        a = stats[arrond]
        a["pdqs"].add(pdq)
        a["total"] += 1

        # Par année
        a["crimes_by_year"][year] = a["crimes_by_year"].get(year, 0) + 1

        # Par catégorie
        short = CATEGORIES_MAP.get(cat, cat)
        a["crimes_by_category"][short] = a["crimes_by_category"].get(short, 0) + 1

        # Par année + catégorie
        key = f"{year}_{short}"
        a["crimes_by_year_category"][key] = a["crimes_by_year_category"].get(key, 0) + 1

        # Coordonnées (sample pour centroïde)
        if lat and lon and len(a["coords"]) < 100:
            try:
                a["coords"].append([float(lat), float(lon)])
            except Exception:
                pass

    # Convertir sets en listes + calculer centroïdes
    result = {}
    for arrond, data in stats.items():
        data["pdqs"] = sorted(list(data["pdqs"]))
        if data["coords"]:
            lats = [c[0] for c in data["coords"]]
            lons = [c[1] for c in data["coords"]]
            data["centroid"] = [sum(lats)/len(lats), sum(lons)/len(lons)]
        else:
            data["centroid"] = [45.53, -73.65]
        del data["coords"]
        # Ajouter OSINT socio-éco
        data["osint"] = OSINT_SOCIOECO.get(arrond, {})
        result[arrond] = data

    return result


def fetch_and_cache(years: list = None, max_pages: int = 20) -> dict:
    """Fetch depuis MTL Open Data et cache localement."""
    if years is None:
        years = ["2020", "2021", "2022", "2023", "2024"]

    print(f"Fetching MTL Open Data — {len(years)} années...")
    all_records = []

    for year in years:
        print(f"  Année {year}...")
        offset = 0
        page = 0
        while page < max_pages:
            batch = fetch_batch(offset, limit=5000, year_filter=year)
            if not batch:
                break
            # Filter exact year (q= is broad match)
            filtered = [r for r in batch if r.get("DATE", "").startswith(year)]
            all_records.extend(filtered)
            if len(batch) < 5000:
                break
            offset += 5000
            page += 1
            time.sleep(0.2)
        print(f"    {len([r for r in all_records if r.get('DATE','').startswith(year)])} records pour {year}")

    print(f"Total: {len(all_records)} records")
    stats = build_arrondissement_stats(all_records)

    # Save cache
    cache = {
        "meta": {
            "source": "Ville de Montréal — données ouvertes (actes criminels)",
            "url": "https://donnees.montreal.ca/dataset/actes-criminels",
            "years": years,
            "total_records": len(all_records),
            "generated": time.strftime("%Y-%m-%d %H:%M")
        },
        "arrondissements": stats
    }

    CACHE_FILE.parent.mkdir(exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    print(f"✓ Cache sauvegardé: {len(stats)} arrondissements")
    return cache


def load_or_fetch(force_refresh: bool = False) -> dict:
    if not force_refresh and CACHE_FILE.exists():
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return fetch_and_cache()


if __name__ == "__main__":
    import sys
    force = "--refresh" in sys.argv
    data = load_or_fetch(force_refresh=force)
    arronds = data.get("arrondissements", {})
    print(f"\n{len(arronds)} arrondissements:")
    for name, d in sorted(arronds.items(), key=lambda x: x[1]["total"], reverse=True):
        print(f"  {name:45s} {d['total']:>8,} crimes | PDQs: {d['pdqs']}")
