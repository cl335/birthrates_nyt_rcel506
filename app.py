import os
import re
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# 1. Page Configuration Setup
st.set_page_config(page_title="NYT Interactive Chart", layout="wide")

st.title("📉 Global Birthrate Trends Over Time")
st.write(
    "Replicating the New York Times time series layout with explicit multi-line labeling."
)

CSV_FILE = "birthrates.csv"


# 2. Dataset Processing Pipeline
@st.cache_data
def load_and_clean_data(file_path):
  if not os.path.exists(file_path):
    return None

  with open(file_path, "r", encoding="utf-8") as f:
    first_line = f.readline()
  countries = [
      c.strip() for c in re.split(r"[\t,]", first_line) if c.strip()
  ]

  df_data = pd.read_csv(
      file_path, skiprows=2, header=None, sep=None, engine="python"
  )
  long_form_list = []

  for i, country_name in enumerate(countries):
    x_column_index = i * 2
    y_column_index = i * 2 + 1

    if y_column_index < df_data.shape[1]:
      sub_df = df_data[[x_column_index, y_column_index]].dropna()
      sub_df.columns = ["Date", "Value"]

      sub_df["Date"] = pd.to_datetime(sub_df["Date"], errors="coerce")
      sub_df["Value"] = pd.to_numeric(sub_df["Value"], errors="coerce")
      sub_df = sub_df.dropna(subset=["Date", "Value"])

      sub_df["Country"] = country_name
      long_form_list.append(sub_df)

  if not long_form_list:
    return None

  combined_df = pd.concat(long_form_list, ignore_index=True)
  combined_df["Date"] = combined_df["Date"].dt.round("D")
  return combined_df.sort_values("Date")


df = load_and_clean_data(CSV_FILE)

if df is None or df.empty:
  st.error(
      "Error: Could not format the matrix columns from your dataset. Double-check your file upload."
  )
  st.stop()

# 3. Interactive Date Sidebar Slider
st.sidebar.header("Filter Timeline")
min_date = df["Date"].min().to_pydatetime()
max_date = df["Date"].max().to_pydatetime()

selected_range = st.sidebar.slider(
    "Select Date Range",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="MMM YYYY",
)

start_date, end_date = selected_range
filtered_df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

# 4. Define Color List
nyt_palette = [
    "#22415e",
    "#b83227",
    "#1b8a5a",
    "#d9822b",
    "#6c5ce7",
    "#006266",
    "#1289A7",
    "#A3CB38",
    "#ED4C67",
    "#485460",
    "#5758BB",
    "#FDA7DF",
    "#D980FA",
    "#5f27cd",
]

# 5. Build Graph Using Explicit Loops (Bypasses layout annotation bugs entirely)
if not filtered_df.empty:
  fig = go.Figure()

  unique_countries = filtered_df["Country"].unique()

  for idx, country in enumerate(unique_countries):
    country_data = filtered_df[filtered_df["Country"] == country].sort_values(
        "Date"
    )

    if not country_data.empty:
      color = nyt_palette[idx % len(nyt_palette)]

      # Add the continuous timeline line trace
      fig.add_trace(
          go.Scatter(
              x=country_data["Date"],
              y=country_data["Value"],
              mode="lines",
              name=country,
              line=dict(width=2.5, color=color),
          )
      )

      # Grab only the very last row coordinates to pin the text label
      last_row = country_data.iloc[-1]

      # Add a tiny standalone text marker right at the end of the line
      fig.add_trace(
          go.Scatter(
              x=[last_row["Date"]],
              y=[last_row["Value"]],
              mode="text",
              text=[f"  {country}"],
              textposition="middle right",
              showlegend=False,
              hoverinfo="skip",
              textfont=dict(family="Georgia", size=11, color=color),
          )
      )

  # 6. Global Minimalist Layout
  fig.update_layout(
      plot_bgcolor="white",
      paper_bgcolor="white",
      font_family="Georgia",
      hovermode="x unified",
      showlegend=False,
      margin=dict(l=40, r=200, t=40, b=40),  # Room on the right for labels
      xaxis=dict(
          showgrid=True,
          gridcolor="#f5f5f5",
          zeroline=False,
          type="date",
      ),
      yaxis=dict(
          showgrid=True,
          gridcolor="#f5f5f5",
          zeroline=False,
          title_text="Fertility Rate",
      ),
  )

  st.plotly_chart(fig, use_container_width=True)
else:
  st.warning("No data points fit the current selected timeline threshold.")
