# VentureScope Analytics Hub

An end-to-end serverless data pipeline and interactive analytics engine designed to cross-reference historical venture capital allocation with real-time market sentiment.

VentureScope serves as a leading indicator for capital rotation, identifying discrepancies between where venture money has historically flowed (Crunchbase data) and where public momentum is currently shifting (Live NLP News scraping).

### System Architecture

The project relies on a decoupled, serverless cloud architecture to ensure high availability and low compute costs:

* **Data Ingestion:** AWS EventBridge triggers AWS Lambda functions on 3-hour intervals to scrape live financial news and pull historical startup datasets.
* **Transformation & NLP:** AWS Glue processes the raw text, applying VADER Sentiment Analysis to score headlines across active venture sectors.
* **Storage Layer:** Processed data is partitioned and stored as Parquet files within an Amazon S3 Data Lake.
* **Query Engine:** Amazon Athena executes serverless SQL queries directly against S3. The dashboard utilizes an optimized direct hash-join to compile the cross-referenced data matrix in under 21 seconds.
* **Presentation Layer:** Streamlit handles the frontend, leveraging Plotly for advanced geospatial and multi-dimensional rendering.

### Core Features

* **Global Capital Deployment Map:** A choropleth visualization (log-scaled) mapping total historical funding across global ecosystems.
* **Market Divergence Matrix:** A multi-variable scatter plot isolating sectors with high media sentiment but low historical funding (emerging markets) versus highly funded sectors experiencing negative media headwinds.
* **Dynamic Executive Deduction:** An auto-generating text module that mathematically assesses the active filters to provide a plain-English summary of current macro conditions.
* **Interactive Control Panel:** User-defined parameters to filter the pipeline by capital requirements and sentiment polarity tolerances.

### Technology Stack

* **Cloud Infrastructure:** AWS (S3, Athena, IAM, Lambda, Glue)
* **Backend / Data Engineering:** Python, Pandas, PyAthena, SQL
* **Frontend / Visualization:** Streamlit, Plotly Express
* **Environment Management:** Python `venv`, Git

### Local Installation & Setup

To run this dashboard locally, ensure you have Python 3.11+ installed.

1. Clone the repository:

```powershell
git clone https://github.com/sammyyaakk/venturescope.git
cd venturescope

```

2. Create and activate a secure virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate

```

3. Install the required pipeline dependencies:

```powershell
pip install -r requirements.txt

```

4. Configure AWS Credentials. Create a hidden Streamlit directory and a secrets file:

```powershell
mkdir .streamlit
New-Item -Path .streamlit/secrets.toml -ItemType File

```

5. Add your AWS IAM Developer credentials to `.streamlit/secrets.toml`:

```toml
aws_access_key_id = "YOUR_ACCESS_KEY"
aws_secret_access_key = "YOUR_SECRET_KEY"
region_name = "us-east-1"
s3_staging_dir = "s3://your-athena-query-results-bucket/"

```

6. Launch the analytics engine:

```powershell
streamlit run app.py

```

### Future Roadmap

* Migrate the local Streamlit deployment to a fully hosted AWS EC2 instance or Streamlit Community Cloud.
* Implement predictive time-series forecasting to estimate sentiment trajectory over the next fiscal quarter.
* Integrate a secondary API for real-time macroeconomic indicators (Interest Rates, CPI) to add a third dimension to the divergence matrix.

### Author

Developed by Samyak Jain