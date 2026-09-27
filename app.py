import os
import pandas as pd
import plotly.express as px
import streamlit as st

# 1. Page Configuration Setup
st.set_page_config(page_title="NYT Interactive Chart", layout="wide")

st.title("The average of children born to a woman in select countries and regions")
st.write(
    "Adjust the slider on the left sidebar to scale the data view window."
)

CSV_FILE = "birthrates.csv"


# 2. Automated File Loading Pipeline
@st.cache_data
def load_and_clean_data(file_path):
  if not os.path.exists(file_path):
    return None

  # Read file with clean string formatting fallback
  df = pd.read_csv(file_path, names=["Date", "Value"])

  # Ensure types are perfectly cast
  df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
  df = df.dropna(subset=["Date"])

  # Clean values up
  df["Date"] = df["Date"].dt.round("D")
  df = df.sort_values("Date")
  df["Value"] = pd.to_numeric(df["Value"], errors="coerce").round(2)
  return df


df = load_and_clean_data(CSV_FILE)

# 3. Validation Boundary Check
if df is None or df.empty:
  st.error(f"Error: We found your file but couldn't parse rows from it!")
  st.stop()

# 4. Interactive Sidebar Setup
st.sidebar.header("Controls & Filters")
min_date = df["Date"].min().to_pydatetime()
max_date = df["Date"].max().to_pydatetime()

# Date slider handling a full start and finish tuple
selected_range = st.sidebar.slider(
    "Select Date Range",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="MMM YYYY",
)

# Fix: Split your active slider tuple into specific range targets
start_date, end_date = selected_range
filtered_df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

# 5. Graph Assembly
if not filtered_df.empty:
  fig = px.line(
      filtered_df,
      x="Date",
      y="Value",
      markers=True,
      title="Birthrate Trends Over Time",
  )

  fig.update_layout(
      plot_bgcolor="white",
      paper_bgcolor="white",
      font_family="Georgia",
      hovermode="x unified",
      xaxis=dict(showgrid=True, gridcolor="#f0f0f0", title_text=""),
      yaxis=dict(showgrid=True, gridcolor="#f0f0f0", title_text="Birth Rate"),
  )

  # Push visualization frame out
  st.plotly_chart(fig, use_container_width=True)
else:
  st.warning("No data points fit the current selected timeline threshold.")

# 6. Safety view of data
with st.expander("View Raw CSV Data Matrix"):
  st.dataframe(filtered_df, use_container_width=True)
