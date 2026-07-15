import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pyathena import connect

# 1. Page Configuration & Dark Theme Aesthetic
st.set_page_config(
    page_title="VentureScope Hub Engine",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling to enforce a clean interface
st.markdown("""
    <style>
        .block-container { padding-top: 2rem; }
        div[data-testid="stMetric"] {
            background-color: #1E2633;
            padding: 20px;
            border-radius: 8px;
            border-left: 5px solid #00D2FF;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 VentureScope Analytics Hub")
st.subheader("Live Market Sentiment Signals Unified with Historical Venture Benchmarks")
st.markdown("---")

# 2. Data Retrieval Layer (Cached)
@st.cache_data(ttl=3600)
def load_linked_sector_data():
    conn = connect(
        aws_access_key_id=st.secrets["aws_access_key_id"],
        aws_secret_access_key=st.secrets["aws_secret_access_key"],
        region_name=st.secrets["region_name"],
        s3_staging_dir=st.secrets["s3_staging_dir"]
    )
    
    query = """
    SELECT 
        c.sector AS venture_sector,
        COUNT(DISTINCT c.name) AS historical_startup_count,
        ROUND(AVG(c.funding_total_usd), 2) AS historical_avg_funding,
        ROUND(AVG(n.sentiment_score), 4) AS live_market_sentiment,
        COUNT(n.title) AS total_live_headlines_analyzed
    FROM 
        venturescope.startup_funding c
    JOIN 
        venturescope.news_sentiment n ON n.sector = c.sector
    WHERE 
        n.sector <> 'other'
    GROUP BY 
        c.sector
    ORDER BY 
        historical_startup_count DESC;
    """
    return pd.read_sql(query, conn)

# Execution Flow
try:
    with st.spinner("Compiling aggregated metrics from AWS Athena..."):
        df_sector = load_linked_sector_data()

    # Convert numeric fields to clean types just in case
    df_sector["historical_startup_count"] = df_sector["historical_startup_count"].astype(int)
    df_sector["historical_avg_funding"] = df_sector["historical_avg_funding"].astype(float)
    df_sector["live_market_sentiment"] = df_sector["live_market_sentiment"].astype(float)
    df_sector["total_live_headlines_analyzed"] = df_sector["total_live_headlines_analyzed"].astype(int)

    # 3. Interactive Sidebar Controls
    st.sidebar.header("🎛️ Control Panel")
    st.sidebar.markdown("Filter and isolate portfolio dynamics.")
    
    all_sectors = sorted(df_sector["venture_sector"].unique())
    selected_sectors = st.sidebar.multiselect(
        "Isolate Target Sectors",
        options=all_sectors,
        default=all_sectors
    )
    
    # Filter dataset based on selection
    df_filtered = df_sector[df_sector["venture_sector"].isin(selected_sectors)]

    if df_filtered.empty:
        st.warning("Please select at least one sector in the control panel sidebar.")
    else:
        # 4. KPI Metrics Ribbon
        total_startups = df_filtered["historical_startup_count"].sum()
        overall_avg_funding = df_filtered["historical_avg_funding"].mean()
        overall_sentiment = df_filtered["live_market_sentiment"].mean()
        total_headlines = df_filtered["total_live_headlines_analyzed"].sum()

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Total Tracked Ventures", f"{total_startups:,}")
        with m2:
            st.metric("Avg Capital Allocation", f"${overall_avg_funding:,.2f}")
        with m3:
            st.metric("Composite Sentiment Index", f"{overall_sentiment:+.4f}")
        with m4:
            st.metric("Scraped News Corpus", f"{total_headlines:,}")

        st.markdown("---")

        # 5. Row 1: Divergence & Correlation Breakdown
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📊 Market Divergence Matrix")
            st.caption("Juxtaposing historical capitalization frequency against real-time media sentiment trajectory.")
            
            # Dual-axis or clean combined plot using Plotly Express
            fig_diverge = px.scatter(
                df_filtered,
                x="historical_startup_count",
                y="live_market_sentiment",
                size="historical_avg_funding",
                color="venture_sector",
                hover_name="venture_sector",
                labels={
                    "historical_startup_count": "Historical Venture Abundance (Count)",
                    "live_market_sentiment": "Live Sentiment Index",
                    "historical_avg_funding": "Avg Funding (USD)"
                },
                template="plotly_dark",
                size_max=50
            )
            st.plotly_chart(fig_diverge, use_container_width=True)

        with col2:
            st.markdown("### 💰 Historic Capital Allocation Intensity")
            st.caption("Evaluating historical funding scale across active industrial channels.")
            
            fig_funding = px.bar(
                df_filtered.sort_values(by="historical_avg_funding", ascending=True),
                x="historical_avg_funding",
                y="venture_sector",
                orientation="h",
                labels={"historical_avg_funding": "Average Funding (USD)", "venture_sector": "Sector"},
                template="plotly_dark",
                color="historical_avg_funding",
                color_continuous_scale=px.colors.sequential.Viridis
            )
            st.plotly_chart(fig_funding, use_container_width=True)

        st.markdown("---")

        # 6. Row 2: Media Volume vs. Data View
        col3, col4 = st.columns([1, 1])

        with col3:
            st.markdown("### 📰 Media Signals Contribution")
            st.caption("Proportion of live public news volume backing each sector.")
            
            fig_pie = px.pie(
                df_filtered,
                values="total_live_headlines_analyzed",
                names="venture_sector",
                template="plotly_dark",
                hole=0.4
            )
            fig_pie.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)

        with col4:
            st.markdown("### 📋 Aggregated Engineering Data Stream")
            st.caption("The raw multi-dimensional matrix delivered instantly via your optimized Athena query layer.")
            st.dataframe(
                df_filtered.style.format({
                    "historical_avg_funding": "${:,.2f}",
                    "live_market_sentiment": "{:+.4f}"
                }),
                use_container_width=True,
                hide_index=True
            )

except Exception as e:
    st.error("Failed to compile Amazon Athena pipeline components.")
    st.exception(e)