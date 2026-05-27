# SPVM INSIGHT

Dashboard analytique des incidents criminels SPVM 2015-2024.

- **152K incidents** — données ouvertes MTL (donnees.montreal.ca)
- **19 arrondissements** — carte interactive + tendances
- **Panel IA** — 12 spécialistes intégrés (criminologie, GRC, spatial, UX)
- **OSINT socio-éco** — corrélations données ouvertes par quartier

## Stack

- Backend: Flask + Anthropic Claude (panel d'experts)
- Frontend: HTML/JS/CSS (statique servi par Flask)
- Data: JSON pré-processé 2015-2024
- Deploy: Fly.io (yyz)

## Run local

```bash
pip install -r requirements.txt
ANTHROPIC_API_KEY=sk-... python app.py
```

## Deploy Fly.io

```bash
fly apps create spvm-insight
fly secrets set ANTHROPIC_API_KEY=sk-...
fly deploy --remote-only
```

## Structure

```
app.py              # Flask backend + panel IA
osint_fetcher.py    # Données ouvertes MTL par arrondissement
build_dataset.py    # ETL datasets SPVM
data/               # dataset.json + tables par année
static/             # assets CSS/JS
index.html          # Frontend
```
