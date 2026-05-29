# Programmatic Intelligence

**DV360 Benchmark Platform** – ML-powered pricing & performance intelligence for YouTube and Display campaigns.

## Features
- 📊 DV360 data ingestion (YouTube + Non-YouTube)
- 🤖 LightGBM-based CPM/CPV predictions
- 📈 Interactive dashboard with WPP Media design
- 🚀 Free, GitHub Pages hosted
- 📡 Model Context Protocol (MCP) API

## Data Source
- **YouTube**: Complete Views, Starts, Clicks, Impressions, Media Cost
- **Non-YouTube (Display/Video)**: Same metrics + Creative, Placement data
- **Dimensions**: Device Type, Month/Quarter, Advertiser, IO, Line Item, Creative

## Project Structure
```
├── etl/                      # Data ingestion & normalization
│   ├── ingest.py            # CSV → DuckDB pipeline
│   ├── schema.sql           # Canonical fact table
│   └── requirements.txt
├── models/                  # ML models
│   ├── train.py            # LightGBM training
│   └── [trained models]
├── api/                     # Flask MCP server
│   ├── app.py              # /predict endpoint
│   └── requirements.txt
├── docs/                    # Static site (GitHub Pages)
│   ├── index.html          # Dashboard
│   ├── css/
│   └── js/
├── .github/workflows/       # CI/CD
│   └── etl-train-deploy.yml
└── README.md
```

## Quick Start

### Local Setup
```bash
# 1. Clone repo
git clone https://github.com/kknman944-design/programmatic-intelligence.git
cd programmatic-intelligence

# 2. Install dependencies
pip install -r etl/requirements.txt
pip install -r api/requirements.txt

# 3. Ingest data
python etl/ingest.py --input data/youtube.csv --input data/nonyt.csv

# 4. Train model
python models/train.py

# 5. Run API
python api/app.py

# 6. Visit http://localhost:8000
```

## Data Format

### Input (YouTube & Non-YouTube CSVs)
See `docs/SCHEMA.md` for full column mapping.

### Canonical Fact Table (DuckDB)
```
fact_daily: 
  date, channel, advertiser_id, advertiser, io_id, io_name, 
  li_id, li_name, creative_id, creative, device_type, 
  impressions, measurable_impr, viewable_impr, clicks, 
  complete_views, starts, cost, currency, 
  cpm, vcpm, cpv, cpc, ctr, vr, cr
```

## Metrics (Calculated)
- **CPM** = Cost / Impressions * 1000
- **vCPM** = Cost / Viewable Impressions * 1000
- **CPV** = Cost / Complete Views
- **CPC** = Cost / Clicks
- **CTR** = Clicks / Impressions
- **View Rate (VR)** = Complete Views / Impressions
- **Completion Rate (CR)** = Complete Views / Starts

## Deployment

### GitHub Actions (Automated)
- **Daily ETL**: Ingest new DV360 exports
- **Weekly Model Training**: Retrain LightGBM on latest data
- **Auto-Deploy**: Push site to GitHub Pages

## Notes
- **Extensible**: Add dimensions in `schema.sql`, update `ingest.py` mapping
- **Scalable**: DuckDB handles ~1M+ rows; move to BigQuery if needed
- **API-First**: MCP endpoint supports external tools & notebooks

## License
MIT
