import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import math
from pyathena import connect

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="VentureScope",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #060B14;
    color: #CBD5E1;
}

h1 {
    font-size: 2.8rem !important;
    font-weight: 700 !important;
    background: linear-gradient(135deg, #38BDF8 0%, #818CF8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.03em;
    margin-bottom: 0.2rem !important;
}

h2, h3 {
    color: #F1F5F9 !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em;
}

/* Metric cards */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
    border: 1px solid #1E3A5F;
    border-top: 3px solid #38BDF8;
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
}

div[data-testid="stMetricLabel"] p {
    font-size: 0.78rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #64748B !important;
    font-weight: 500 !important;
}

div[data-testid="stMetricValue"] > div {
    font-size: 1.9rem !important;
    font-weight: 700 !important;
    color: #F8FAFC !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #0A1628 !important;
    border-right: 1px solid #1E293B;
}

section[data-testid="stSidebar"] label {
    color: #94A3B8 !important;
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

/* Divider */
hr { border-color: #1E293B !important; margin: 1.5rem 0 !important; }

/* Info box */
div[data-testid="stAlert"] {
    background-color: #0F2137 !important;
    border: 1px solid #1E3A5F !important;
    border-left: 4px solid #38BDF8 !important;
    border-radius: 8px;
    color: #CBD5E1 !important;
}

/* Section label */
.section-label {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #38BDF8;
    font-weight: 600;
    margin-bottom: 0.3rem;
}

/* ISI badge */
.isi-badge {
    display: inline-block;
    padding: 0.4rem 1rem;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 600;
    margin-top: 0.3rem;
}
</style>
""", unsafe_allow_html=True)


# ── Athena Connection ──────────────────────────────────────────────────────────
def get_connection():
    return connect(
        aws_access_key_id=st.secrets["aws_access_key_id"],
        aws_secret_access_key=st.secrets["aws_secret_access_key"],
        region_name=st.secrets["region_name"],
        s3_staging_dir=st.secrets["s3_staging_dir"],
        schema_name="venturescope"
    )


# ── Data Loaders (separate queries — no broken JOIN) ──────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def load_funding_data():
    """Load startup funding data from Athena."""
    query = """
    SELECT
        sector,
        country_code,
        COUNT(DISTINCT name)            AS startup_count,
        SUM(funding_total_usd)          AS total_funding,
        ROUND(AVG(funding_total_usd),2) AS avg_funding,
        SUM(seed)                       AS total_seed,
        SUM(round_A)                    AS total_series_a,
        SUM(round_B)                    AS total_series_b,
        SUM(round_C)                    AS total_series_c,
        SUM(round_D)                    AS total_series_d
    FROM startup_funding
    WHERE country_code IS NOT NULL
      AND country_code <> ''
      AND sector IS NOT NULL
      AND funding_total_usd > 0
    GROUP BY sector, country_code
    """
    conn = get_connection()
    return pd.read_sql(query, conn)


@st.cache_data(ttl=3600, show_spinner=False)
def load_sentiment_data():
    """Load sentiment data from Athena."""
    query = """
    SELECT
        sentiment_label,
        COUNT(*)                        AS headline_count,
        ROUND(AVG(sentiment_score), 4)  AS avg_score
    FROM news_sentiment
    GROUP BY sentiment_label
    """
    conn = get_connection()
    return pd.read_sql(query, conn)


@st.cache_data(ttl=3600, show_spinner=False)
def load_sector_trends():
    """Load year-over-year sector funding trends."""
    query = """
    SELECT
        founded_year,
        sector,
        SUM(funding_total_usd) AS total_funding
    FROM startup_funding
    WHERE founded_year BETWEEN 2000 AND 2015
      AND sector IS NOT NULL
      AND sector <> 'Other'
      AND funding_total_usd > 0
    GROUP BY founded_year, sector
    ORDER BY founded_year
    """
    conn = get_connection()
    return pd.read_sql(query, conn)


@st.cache_data(ttl=3600, show_spinner=False)
def load_funnel_data():
    """Load funding stage funnel data."""
    query = """
    SELECT
        COUNT(CASE WHEN seed > 0 THEN 1 END)    AS seed_count,
        COUNT(CASE WHEN round_A > 0 THEN 1 END) AS series_a_count,
        COUNT(CASE WHEN round_B > 0 THEN 1 END) AS series_b_count,
        COUNT(CASE WHEN round_C > 0 THEN 1 END) AS series_c_count,
        COUNT(CASE WHEN round_D > 0 THEN 1 END) AS series_d_count
    FROM startup_funding
    """
    conn = get_connection()
    return pd.read_sql(query, conn)


@st.cache_data(ttl=3600, show_spinner=False)
def load_total_headlines():
    """Load total headlines count to prove live updates."""
    query = "SELECT COUNT(*) AS total FROM news_sentiment"
    conn = get_connection()
    return pd.read_sql(query, conn)


# ── ISI Calculation ────────────────────────────────────────────────────────────
def calculate_isi(df_sentiment):
    """Calculate Investor Sentiment Index from sentiment distribution."""
    if df_sentiment.empty:
        return 0.0, "Neutral"
    total = df_sentiment["headline_count"].sum()
    if total == 0:
        return 0.0, "Neutral"
    pos = df_sentiment.loc[df_sentiment["sentiment_label"] == "positive", "headline_count"].sum()
    neg = df_sentiment.loc[df_sentiment["sentiment_label"] == "negative", "headline_count"].sum()
    isi = round(((pos - neg) / total) * 100, 2)
    if isi > 5:
        label = "Bullish 📈"
    elif isi < -5:
        label = "Bearish 📉"
    else:
        label = "Neutral ➡️"
    return isi, label


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown('<p class="section-label">Live Intelligence Platform</p>', unsafe_allow_html=True)
st.title("VentureScope")
st.markdown("Startup Ecosystem Analytics — Historical Funding × Live Market Sentiment")
st.markdown("---")


# ── Load Data ──────────────────────────────────────────────────────────────────
with st.spinner("Loading data from AWS Athena..."):
    try:
        df_funding    = load_funding_data()
        df_sentiment  = load_sentiment_data()
        df_trends     = load_sector_trends()
        df_funnel_raw = load_funnel_data()
        df_headlines  = load_total_headlines()
        data_ok = True
    except Exception as e:
        data_ok = False
        st.error("Failed to connect to AWS Athena. Check your credentials in Streamlit secrets.")
        st.exception(e)

if not data_ok:
    st.stop()

# ── Sidebar Filters ────────────────────────────────────────────────────────────
st.sidebar.markdown("### 🔭 VentureScope")
st.sidebar.markdown("---")
st.sidebar.markdown("**Filters**")

all_sectors = sorted([s for s in df_funding["sector"].unique() if s != "Other"])
selected_sectors = st.sidebar.multiselect(
    "Sectors",
    options=all_sectors,
    default=all_sectors
)

if not selected_sectors:
    st.sidebar.warning("Select at least one sector.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.markdown("**About**")
st.sidebar.caption("Pipeline refreshes every 3 hours via AWS Lambda → Glue → Athena.")
st.sidebar.caption("Built on AWS S3, Glue, Lambda, EventBridge, Athena.")

# ── Apply Filters ──────────────────────────────────────────────────────────────
df_filtered   = df_funding[df_funding["sector"].isin(selected_sectors)]
df_trends_f   = df_trends[df_trends["sector"].isin(selected_sectors)]

# ── Aggregations ───────────────────────────────────────────────────────────────
df_sector = df_filtered.groupby("sector").agg(
    startup_count=("startup_count", "sum"),
    total_funding=("total_funding", "sum"),
    avg_funding=("avg_funding", "mean")
).reset_index()

df_geo = df_filtered.groupby("country_code").agg(
    startup_count=("startup_count", "sum"),
    total_funding=("total_funding", "sum")
).reset_index()
df_geo["log_funding"] = df_geo["total_funding"].apply(lambda x: math.log10(x) if x > 0 else 0)

# ── ISI & Sentiment ────────────────────────────────────────────────────────────
isi_score, isi_label = calculate_isi(df_sentiment)
total_headlines = int(df_headlines["total"].iloc[0]) if not df_headlines.empty else 0

# ── Summary Banner ─────────────────────────────────────────────────────────────
if not df_sector.empty:
    top_funded = df_sector.loc[df_sector["total_funding"].idxmax(), "sector"]
    isi_desc = "slightly positive" if isi_score > 0 else "slightly negative" if isi_score < 0 else "neutral"
    st.info(
        f"**Market Snapshot** — Tracking **{df_sector['startup_count'].sum():,} startups** across "
        f"**{len(df_sector)} sectors**. **{top_funded}** leads in total capital raised. "
        f"Live news sentiment is **{isi_desc}** (ISI: {isi_score:+.1f}%), "
        f"based on **{total_headlines:,} headlines** processed by the pipeline."
    )

# ── KPI Row ────────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Startups", f"{df_sector['startup_count'].sum():,}")
k2.metric("Total Funding", f"${df_sector['total_funding'].sum()/1e9:.1f}B")
k3.metric("Avg Deal Size", f"${df_sector['avg_funding'].mean():,.0f}")
k4.metric("ISI Score", f"{isi_score:+.1f}%", delta=isi_label)
k5.metric("Headlines Processed", f"{total_headlines:,}")

st.markdown("---")

# ── Chart 1: Global Funding Map ────────────────────────────────────────────────
st.markdown("### 🗺️ Global Capital Deployment")
fig_map = px.choropleth(
    df_geo,
    locations="country_code",
    color="log_funding",
    hover_name="country_code",
    hover_data={
        "log_funding": False,
        "total_funding": ":$,.0f",
        "startup_count": True,
        "country_code": False
    },
    color_continuous_scale="Blues",
    template="plotly_dark"
)
fig_map.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=10, b=10),
    coloraxis_colorbar=dict(title="Funding (log scale)")
)
st.plotly_chart(fig_map, use_container_width=True)

st.markdown("---")

# ── Charts 2 & 3: Trends + Sector Bar ─────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📈 Funding Trends by Sector (2000–2015)")
    if df_trends_f.empty:
        st.info("No trend data available for selected sectors.")
    else:
        fig_line = px.line(
            df_trends_f,
            x="founded_year",
            y="total_funding",
            color="sector",
            template="plotly_dark",
            labels={"founded_year": "Year", "total_funding": "Total Funding (USD)", "sector": "Sector"}
        )
        fig_line.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_line, use_container_width=True)

with col2:
    st.markdown("### 🏆 Sector Funding Distribution")
    fig_bar = px.bar(
        df_sector.sort_values("total_funding", ascending=True),
        x="total_funding",
        y="sector",
        orientation="h",
        template="plotly_dark",
        color="total_funding",
        color_continuous_scale="Blues",
        labels={"total_funding": "Total Funding (USD)", "sector": ""}
    )
    fig_bar.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# ── Charts 4 & 5: Funnel + Sentiment ──────────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.markdown("### 🔻 Startup Funding Stage Funnel")
    if df_funnel_raw.empty:
        st.info("No funnel data available.")
    else:
        row = df_funnel_raw.iloc[0]
        funnel_df = pd.DataFrame({
            "Stage": ["Seed", "Series A", "Series B", "Series C", "Series D"],
            "Count": [
                int(row["seed_count"]),
                int(row["series_a_count"]),
                int(row["series_b_count"]),
                int(row["series_c_count"]),
                int(row["series_d_count"])
            ]
        })
        fig_funnel = go.Figure(go.Funnel(
            y=funnel_df["Stage"],
            x=funnel_df["Count"],
            textinfo="value+percent initial",
            marker=dict(color=["#38BDF8", "#60A5FA", "#818CF8", "#A78BFA", "#C084FC"])
        ))
        fig_funnel.update_layout(
            template="plotly_dark",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=10, b=10)
        )
        st.plotly_chart(fig_funnel, use_container_width=True)

with col4:
    st.markdown("### 📰 Live Investor Sentiment")
    if df_sentiment.empty:
        st.info("No sentiment data available yet. Pipeline may still be processing.")
    else:
        color_map = {
            "positive": "#10B981",
            "neutral": "#64748B",
            "negative": "#EF4444"
        }
        fig_sent = px.pie(
            df_sentiment,
            values="headline_count",
            names="sentiment_label",
            template="plotly_dark",
            hole=0.55,
            color="sentiment_label",
            color_discrete_map=color_map
        )
        fig_sent.update_traces(textinfo="percent+label")
        fig_sent.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=20, b=20),
            showlegend=False,
            annotations=[dict(
                text=f"ISI<br><b>{isi_score:+.1f}%</b>",
                x=0.5, y=0.5,
                font_size=18,
                font_color="#F8FAFC",
                showarrow=False
            )]
        )
        st.plotly_chart(fig_sent, use_container_width=True)

st.markdown("---")

# ── Sentiment Polarity Bar ─────────────────────────────────────────────────────
st.markdown("### 📊 Sentiment Distribution")
if not df_sentiment.empty:
    col_sent1, col_sent2, col_sent3 = st.columns(3)
    for _, row in df_sentiment.iterrows():
        label = row["sentiment_label"].title()
        count = int(row["headline_count"])
        score = float(row["avg_score"])
        if row["sentiment_label"] == "positive":
            col_sent1.metric(f"✅ {label}", f"{count:,} headlines", f"Avg score: {score:+.3f}")
        elif row["sentiment_label"] == "neutral":
            col_sent2.metric(f"➡️ {label}", f"{count:,} headlines", f"Avg score: {score:+.3f}")
        elif row["sentiment_label"] == "negative":
            col_sent3.metric(f"🔴 {label}", f"{count:,} headlines", f"Avg score: {score:+.3f}")

st.markdown("---")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.caption("VentureScope · Built on AWS S3 · Glue · Lambda · EventBridge · Athena · Streamlit · Data: Crunchbase via Kaggle + NewsAPI")