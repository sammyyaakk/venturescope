# VentureScope Analytics Hub

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)](https://venturescope.streamlit.app)
[![AWS](https://img.shields.io/badge/Cloud-AWS-FF9900?style=for-the-badge&logo=amazonaws)](https://aws.amazon.com)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python)](https://python.org)

> **Live App:** [venturescope.streamlit.app](https://venturescope.streamlit.app)

An end-to-end serverless data pipeline and interactive analytics dashboard that cross-references historical venture capital allocation with real-time investor sentiment from live news.

VentureScope identifies discrepancies between where venture money has historically flowed (54,294 Crunchbase startup records) and where public momentum is currently shifting (live NLP-scored news headlines ingested every 3 hours automatically).

---

## System Architecture

```
EventBridge (every 3 hours)
        ↓
AWS Lambda — fetches live VC/startup headlines from NewsAPI
        ↓
Amazon S3 — Raw Data Lake (JSON headlines + CSV funding data)
        ↓
AWS Glue — PySpark ETL + VADER NLP Sentiment Scoring
        ↓
Amazon S3 — Processed Data Lake (Parquet format)
        ↓
Amazon Athena — Serverless SQL Query Engine
        ↓
Streamlit Dashboard — Live Interactive Visualizations
```

The pipeline is fully automated — no manual steps after deployment. Every 3 hours, Lambda ingests fresh headlines, Glue scores them with NLP, and the dashboard reflects the updated data on the next visit.

---

## Features

- **Global Capital Deployment Map** — Choropleth visualization (log-scaled) mapping total historical funding across 115 countries
- **Sector Funding Trends** — Year-over-year funding analysis across 8 sectors from 2000–2015
- **Startup Funding Stage Funnel** — Tracks the drop-off rate from Seed through Series D across 17,000+ startups
- **Live Investor Sentiment Index (ISI)** — Aggregated NLP sentiment score derived from live news headlines, updated every 3 hours
- **Sentiment Distribution** — Real-time breakdown of positive, neutral, and negative market coverage
- **Market Divergence Matrix** — Scatter plot isolating sectors with high sentiment but low historical funding (emerging opportunities)
- **Dynamic Executive Summary** — Auto-generated plain-English market snapshot based on live pipeline data

---

## Technology Stack

| Layer | Technology |
|---|---|
| Cloud Infrastructure | AWS S3, Lambda, Glue, Athena, EventBridge, IAM |
| Data Processing | PySpark (AWS Glue), Pandas |
| NLP / Sentiment | VADER (vaderSentiment) |
| Query Engine | Amazon Athena (serverless SQL on Parquet) |
| Dashboard | Streamlit, Plotly Express |
| Data Sources | Crunchbase via Kaggle, NewsAPI |
| Language | Python 3.12 |
| Storage Format | Apache Parquet (Snappy compression) |

---

## Data Sources

- **Startup Funding:** [Crunchbase dataset via Kaggle](https://www.kaggle.com/datasets/arindam235/startup-investments-crunchbase) — 54,294 records across 115 countries
- **Live News:** [NewsAPI](https://newsapi.org) — startup and VC headlines fetched automatically every 3 hours

---

## Free Tier Cost

This entire project runs at **~$0/month** on AWS free tier:

| Service | Monthly Usage | Free Limit |
|---|---|---|
| AWS Lambda | ~240 invocations | 1,000,000 |
| AWS Glue | ~7.2 DPU-hours | 10 DPU-hours |
| Amazon S3 | ~100MB | 5GB |
| Amazon Athena | ~250MB scanned | 5TB |
| Amazon EventBridge | ~240 events | 14,000,000 |

---

## Local Setup

To run this dashboard locally, ensure you have Python 3.11+ installed.

**1. Clone the repository:**
```bash
git clone https://github.com/sammyyaakk/venturescope.git
cd venturescope
```

**2. Create and activate a virtual environment:**
```bash
python -m venv venv
.\venv\Scripts\Activate     # Windows
source venv/bin/activate    # Mac/Linux
```

**3. Install dependencies:**
```bash
pip install -r requirements.txt
```

**4. Configure AWS credentials:**
```bash
mkdir .streamlit
```

Create `.streamlit/secrets.toml` and add:
```toml
aws_access_key_id = "YOUR_ACCESS_KEY"
aws_secret_access_key = "YOUR_SECRET_KEY"
region_name = "us-east-1"
s3_staging_dir = "s3://your-curated-bucket/"
```

**5. Run the dashboard:**
```bash
streamlit run app.py
```

---

## Future Roadmap

- Sector-level sentiment mapping — join news sentiment with funding data by matching sector tags for deeper correlation analysis
- FinBERT integration — replace VADER with a domain-specific financial NLP model for higher sentiment accuracy
- Real-time streaming — upgrade Lambda to Kinesis Data Firehose for sub-minute data refresh
- Macroeconomic indicators — integrate interest rate and CPI data as a third analytical dimension

---

## Author

Developed by **Samyak Rajesh Jain**
B.Tech Information Technology

---

*Pipeline runs automatically on AWS. Data refreshes every 3 hours.*
