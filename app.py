import streamlit as st
import pandas as pd
import plotly.express as px
import math
from pyathena import connect

# 1. Page Configuration
st.set_page_config(
    page_title="VentureScope Hub",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Refined Enterprise CSS
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', sans-serif;
            color: #E2E8F0;
        }
        
        h1 { font-weight: 700 !important; font-size: 3.8rem !important; letter-spacing: -0.02em; margin-bottom: 0.5rem !important; }
        h2 { font-weight: 600 !important; font-size: 1.8rem !important; letter-spacing: -0.01em; color: #F8FAFC !important; }
        h3 { font-weight: 600 !important; font-size: 1.2rem !important; color: #CBD5E1 !important; margin-top: 1rem !important; }
        
        /* Floating Animations */
        @keyframes floatUp {
            0% { opacity: 0; transform: translateY(15px); }
            100% { opacity: 1; transform: translateY(0); }
        }
        
        div[data-testid="stVerticalBlock"] > div {
            animation: floatUp 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
            opacity: 0;
        }
        
        div[data-testid="stVerticalBlock"] > div:nth-child(1) { animation-delay: 0.1s; }
        div[data-testid="stVerticalBlock"] > div:nth-child(2) { animation-delay: 0.2s; }
        div[data-testid="stVerticalBlock"] > div:nth-child(3) { animation-delay: 0.3s; }
        
        /* KPI Metric Styling */
        div[data-testid="stMetric"] {
            background-color: #0F172A;
            padding: 1.2rem;
            border-radius: 8px;
            border: 1px solid #1E293B;
            border-top: 4px solid #3B82F6;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        
        div[data-testid="stMetricValue"] > div {
            font-size: 2.0rem !important;
            font-weight: 700 !important;
        }
        
        /* Summary Box */
        div.stAlert {
            background-color: #1e293b;
            color: #f1f5f9;
            border: 1px solid #334155;
            border-left: 4px solid #10b981;
            padding: 1.2rem;
            font-size: 1.05rem !important;
            line-height: 1.6 !important;
        }
        
        hr { border-color: #334155; margin: 2rem 0; }
    </style>
""", unsafe_allow_html=True)

st.title("VentureScope Analytics")
st.markdown("Live Market Sentiment Signals Unified with Historical Venture Benchmarks")

# 3. Upgraded Data Engine
@st.cache_data(ttl=3600)
def load_linked_sector_data():
    conn = connect(
        aws_access_key_id=st.secrets["aws_access_key_id"],
        aws_secret_access_key=st.secrets["aws_secret_access_key"],
        region_name=st.secrets["region_name"],
        s3_staging_dir=st.secrets["s3_staging_dir"],
        schema_name="venturescope"  # ADD THIS LINE
    )
    
    # Now you can use simple table names because the connection is scoped
    query = """
    SELECT 
        c.sector AS venture_sector,
        c.country_code,
        COUNT(DISTINCT c.name) AS historical_startup_count,
        SUM(c.funding_total_usd) AS total_funding,
        ROUND(AVG(c.funding_total_usd), 2) AS historical_avg_funding,
        ROUND(AVG(n.sentiment_score), 4) AS live_market_sentiment,
        COUNT(n.title) AS total_live_headlines
    FROM 
        startup_funding c
    JOIN 
        news_sentiment n ON n.sector = c.sector
    WHERE 
        c.country_code IS NOT NULL AND c.country_code != ''
    GROUP BY 
        c.sector, c.country_code
    """
    return pd.read_sql(query, conn)

try:
    with st.spinner("Connecting to AWS Athena..."):
        df_raw = load_linked_sector_data()

    # 4. Sidebar Control Panel
    st.sidebar.markdown("### Parameters & Filters")
    
    all_sectors = sorted(df_raw["venture_sector"].unique())
    selected_sectors = st.sidebar.multiselect("Target Sectors", options=all_sectors, default=all_sectors)
    
    min_funding = float(df_raw["historical_avg_funding"].min())
    max_funding = float(df_raw["historical_avg_funding"].max())
    funding_range = st.sidebar.slider("Historical Avg Funding (USD)", min_funding, max_funding, (min_funding, max_funding))
    
    min_sent = float(df_raw["live_market_sentiment"].min())
    max_sent = float(df_raw["live_market_sentiment"].max())
    sentiment_range = st.sidebar.slider("Live Sentiment Tolerance", min_sent, max_sent, (min_sent, max_sent), step=0.01)

    # Apply Filters
    df_filtered = df_raw[
        (df_raw["venture_sector"].isin(selected_sectors)) &
        (df_raw["historical_avg_funding"] >= funding_range[0]) &
        (df_raw["historical_avg_funding"] <= funding_range[1]) &
        (df_raw["live_market_sentiment"] >= sentiment_range[0]) &
        (df_raw["live_market_sentiment"] <= sentiment_range[1])
    ]

    st.write(f"DEBUG: Raw data count: {len(df_raw)}")
    st.write(f"DEBUG: Filtered data count: {len(df_filtered)}")
    st.write(f"DEBUG: Selected sectors: {selected_sectors}")

    if df_filtered.empty:
        st.warning("Adjust your filter parameters to view data.")
    else:
        # Data Aggregation
        df_sector = df_filtered.groupby("venture_sector").agg(
            startup_count=("historical_startup_count", "sum"),
            avg_funding=("historical_avg_funding", "mean"),
            live_sentiment=("live_market_sentiment", "mean"),
            headlines=("total_live_headlines", "sum")
        ).reset_index()

        df_geo = df_filtered.groupby("country_code").agg(
            startup_count=("historical_startup_count", "sum"),
            total_funding=("total_funding", "sum")
        ).reset_index()
        
        # Apply logarithmic scale to handle data outliers like USA
        df_geo["log_funding"] = df_geo["total_funding"].apply(lambda x: math.log10(x) if x > 0 else 0)

        # 5. Direct Executive Summary
        total_startups = df_sector["startup_count"].sum()
        avg_sent = df_sector["live_sentiment"].mean()
        top_funding = df_sector.loc[df_sector['avg_funding'].idxmax()]['venture_sector']
        top_sentiment = df_sector.loc[df_sector['live_sentiment'].idxmax()]['venture_sector']

        status = "positive" if avg_sent > 0.05 else "negative" if avg_sent < -0.05 else "neutral"

        summary = (
            f"Market Summary: This dashboard currently tracks {total_startups:,} startups across "
            f"{len(df_sector)} active sectors. The overall media tone is {status} (Index: {avg_sent:+.2f}). "
            f"Historically, {top_funding.title()} requires the highest average capital, but {top_sentiment.title()} "
            f"is currently capturing the strongest positive media coverage."
        )
        st.info(summary)

        # 6. KPI Ribbon
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Tracked Ventures", f"{total_startups:,}")
        m2.metric("Mean Capital Need", f"${df_sector['avg_funding'].mean():,.0f}")
        m3.metric("Composite Sentiment", f"{avg_sent:+.2f}")
        m4.metric("Active Sectors", f"{len(df_sector)}")

        st.markdown("---")

        # 7. Chart 1: Global Map View
        st.markdown("### Global Capital Deployment")
        fig_map = px.choropleth(
            df_geo,
            locations="country_code",
            color="log_funding",
            hover_name="country_code",
            hover_data={"log_funding": False, "total_funding": ":$,.0f", "startup_count": True, "country_code": False},
            color_continuous_scale="Plasma",
            template="plotly_dark"
        )
        fig_map.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", 
            paper_bgcolor="rgba(0,0,0,0)", 
            margin=dict(t=10, b=10),
            coloraxis_colorbar=dict(title="Funding Intensity")
        )
        st.plotly_chart(fig_map, use_container_width=True)

        st.markdown("---")

        # 8. Charts 2 & 3: Hierarchy and Divergence
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Capital Distribution Hierarchy")
            fig_bar = px.bar(
                df_sector.sort_values(by="avg_funding", ascending=True),
                x="avg_funding",
                y="venture_sector",
                orientation="h",
                labels={"avg_funding": "Average Funding (USD)", "venture_sector": ""},
                template="plotly_dark",
                color="avg_funding",
                color_continuous_scale="Blues"
            )
            fig_bar.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_bar, use_container_width=True)

        with col2:
            st.markdown("### Market Divergence Matrix")
            fig_scatter = px.scatter(
                df_sector,
                x="startup_count",
                y="live_sentiment",
                size="avg_funding",
                color="venture_sector",
                hover_name="venture_sector",
                labels={"startup_count": "Venture Volume", "live_sentiment": "Sentiment Index"},
                template="plotly_dark",
                size_max=50
            )
            fig_scatter.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_scatter, use_container_width=True)

        st.markdown("---")
        
        # 9. Charts 4 & 5: Media Share and Sentiment Polarity
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown("### Media Signal Proportion")
            fig_pie = px.pie(
                df_sector,
                values="headlines",
                names="venture_sector",
                template="plotly_dark",
                hole=0.5
            )
            fig_pie.update_traces(textinfo='percent')
            fig_pie.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=20, b=20))
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col4:
            st.markdown("### Sentiment Polarity Variance")
            df_sector['polarity_color'] = df_sector['live_sentiment'].apply(lambda x: 'Positive' if x > 0 else 'Negative')
            fig_polarity = px.bar(
                df_sector.sort_values(by="live_sentiment"),
                x="live_sentiment",
                y="venture_sector",
                orientation="h",
                color="polarity_color",
                color_discrete_map={'Positive': '#10b981', 'Negative': '#ef4444'},
                labels={"live_sentiment": "Sentiment Score", "venture_sector": "", "polarity_color": "Trend"},
                template="plotly_dark"
            )
            fig_polarity.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
            st.plotly_chart(fig_polarity, use_container_width=True)

except Exception as e:
    st.error("Engine failed to compile Amazon Athena pipeline components.")
    st.exception(e)