import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Performance Monitoring Dashboard",
    layout="wide"
)

# --------------------------------------------------
# TITLE & INTRO
# --------------------------------------------------
st.title("📊 Performance Monitoring Dashboard")

st.write(
    "This dashboard helps you **understand how your customer support or business system "
    "is performing over time**. Upload your data, select a date, and quickly see whether "
    "everything is **On Track**, needs **Monitoring**, or requires **Action**."
)

# --------------------------------------------------
# USER GUIDE
# --------------------------------------------------
with st.expander("👋 New here? Click to see how this works (1-minute guide)"):
    st.markdown(
        """
        **How to use this dashboard:**
        1. Upload your customer support CSV file from the left sidebar  
        2. Choose how many days you want to view  
        3. Select a specific date to inspect  
        4. Review the status message to know if action is needed  
        5. Use the chart to easily see trends over time  

        This dashboard is designed so **anyone can understand it**, even without technical knowledge.
        """
    )

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
st.sidebar.header("Controls")

view_days = st.sidebar.selectbox(
    "View window (days)",
    [7, 14, 30, 60, 90],
    index=0
)

uploaded_file = st.sidebar.file_uploader(
    "Upload performance CSV",
    type=["csv"]
)

st.sidebar.markdown("### CSV format expected")
st.sidebar.markdown(
    """
    Your CSV should contain **customer support data**, such as:
    - Ticket creation date  
    - Ticket resolution date (if available)  
    - Ticket status or priority  

    The dashboard will automatically **clean and convert** it into business metrics.
    """
)

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
if uploaded_file:
    raw_df = pd.read_csv(uploaded_file)
else:
    # Demo fallback
    dates = pd.date_range(end=datetime.today(), periods=60)
    raw_df = pd.DataFrame({
        "created_date": dates,
        "resolved_date": dates + pd.to_timedelta(np.random.randint(30, 300, size=len(dates)), unit="m"),
        "status": np.random.choice(["Resolved", "Open", "Pending"], size=len(dates))
    })

# --------------------------------------------------
# DATA CLEANING & TRANSFORMATION
# --------------------------------------------------
df = raw_df.copy()

# Detect date column
date_col = None
for col in df.columns:
    if "date" in col.lower():
        date_col = col
        break

if date_col is None:
    st.error("No date column found in uploaded file.")
    st.stop()

df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
df = df.dropna(subset=[date_col])

df["date"] = df[date_col].dt.date

# Processing time
processing_time = None
if "resolved_date" in df.columns:
    df["resolved_date"] = pd.to_datetime(df["resolved_date"], errors="coerce")
    df["processing_time"] = (
        (df["resolved_date"] - pd.to_datetime(df[date_col]))
        .dt.total_seconds() / 60
    )
else:
    df["processing_time"] = np.random.uniform(5, 10, size=len(df))

# Error definition
if "status" in df.columns:
    df["is_error"] = df["status"].str.lower().isin(["open", "pending"])
else:
    df["is_error"] = np.random.choice([0, 1], size=len(df), p=[0.9, 0.1])

# --------------------------------------------------
# AGGREGATION
# --------------------------------------------------
daily = df.groupby("date").agg(
    daily_tickets=("date", "count"),
    avg_processing_time=("processing_time", "mean"),
    error_rate=("is_error", "mean")
).reset_index()

daily["error_rate"] = daily["error_rate"] * 100
daily = daily.sort_values("date").tail(view_days)

# --------------------------------------------------
# STATUS LOGIC
# --------------------------------------------------
def classify(row):
    if row["error_rate"] > 5 or row["avg_processing_time"] > 8:
        return "Action Required"
    elif row["error_rate"] > 2:
        return "Monitoring"
    return "On Track"

daily["status"] = daily.apply(classify, axis=1)

# --------------------------------------------------
# DATE SELECTION
# --------------------------------------------------
selected_date = st.selectbox(
    "📅 Select a date to inspect",
    daily["date"].astype(str)
)

selected_row = daily[daily["date"].astype(str) == selected_date].iloc[0]

# --------------------------------------------------
# KPI METRICS
# --------------------------------------------------
c1, c2, c3, c4 = st.columns(4)

c1.metric("Daily Tickets", int(selected_row["daily_tickets"]))
c2.metric("Avg Processing Time", f"{selected_row['avg_processing_time']:.2f} min")
c3.metric("Error Rate", f"{selected_row['error_rate']:.2f}%")
c4.metric("Current Status", selected_row["status"])

# --------------------------------------------------
# CHART (SIMPLE & BUSINESS FRIENDLY)
# --------------------------------------------------
st.subheader("📈 Performance Trends")

fig = px.line(
    daily,
    x="date",
    y=["daily_tickets", "avg_processing_time", "error_rate"],
    labels={
        "value": "Value",
        "variable": "Metric",
        "daily_tickets": "Daily Tickets",
        "avg_processing_time": "Avg Processing Time (min)",
        "error_rate": "Error Rate (%)"
    }
)

st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.markdown("---")
st.markdown(
    "<center>Built by Nandini Matta · AI / ML & Data Engineering</center>",
    unsafe_allow_html=True
)
