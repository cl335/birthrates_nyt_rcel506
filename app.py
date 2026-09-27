import os
import re
import pandas as pd
import plotly.express as px
import streamlit as st

# 1. Page Layout Customization
st.set_page_config(page_title="NYT Interactive Chart", layout="wide")

st.title("The average number of children born to a woman in select countries and regions")
st.write(
    "Replicating the multi-line New York Times time series dashboard. Select specific regions using the legend."
)

CSV_FILE = "birthrates.csv"


# 2. Wide-Matrix Multi-Line Parser Pipeline
@st.cache_data
def load_and_clean_data(file_path):
  if not os.path.exists(file_path):
    return None

  # Read raw lines to extract country headers reliably from row 0
  with open(file_path, "r", encoding="utf-8") as f:
    first_line = f.readline()
  # Split columns cleanly by detecting tab spacing or commas
  countries = [
      c.strip() for c in re.split(r"[\t,]", first_line) if c.strip()
  ]

  # Load all data values starting from row 2 (skipping names and X/Y labels)
  df_data = pd.read_csv(
      file_path, skiprows=2, header=None, sep=None, engine="python"
  )

  long_form_list = []

  # Loop through each country pair block sequentially
  for i, country_name in enumerate(countries):
    x_column_index = i * 2
    y_column_index = i * 2 + 1

    # Ensure we don't look past the boundaries of the file width
    if y_column_index < df_data.shape[1]:
      # Extract just this country's specific X and Y columns
      sub_df = df_data[[x_column_index, y_column_index]].dropna()
      sub_df.columns = ["Date", "Value"]

      # Clean dates and numbers for this specific slice
      sub_df["Date"] = pd.to_datetime(sub_df["Date"], errors="coerce")
      sub_df["Value"] = pd.to_numeric(sub_df["Value"], errors="coerce")
      sub_df = sub_df.dropna(subset=["Date", "Value"])

      # Tag it with the country identifier label
      sub_df["Country"] = country_name
      long_form_list.append(sub_df)

  # Combine all isolated countries into a uniform long-form DataFrame
  if not long_form_list:
    return None

  combined_df = pd.concat(long_form_list, ignore_index=True)
  combined_df["Date"] = combined_df["Date"].dt.round("D")
  return combined_df.sort_values("Date")


df = load_and_clean_data(CSV_FILE)

# 3. Dynamic Application Safety Checks
if df is None or df.empty:
  st.error(
      "Error: Could not format the matrix columns from your dataset. Double-check your file upload."
  )
  st.stop()

# 4. Interactive Sidebar Controls
st.sidebar.header("Filter Timeline View")
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

# 5. Render Multi-Line Plotly Chart
if not filtered_df.empty:
  # Crucial adjustment: Adding color="Country" plots all timelines simultaneously
  fig = px.line(
      filtered_df,
      x="Date",
      y="Value",
      color="Country",
      markers=True,
      title="Birth Rates per Woman (1960 - Present)",
  )

  # Journalistic styling adjustments to mimic NYT layout guidelines
  fig.update_layout(
      plot_bgcolor="white",
      paper_bgcolor="white",
      font_family="Georgia",  # Editorial text styling
      hovermode="x unified",  # Compiles all overlapping metrics into one clean comparison card
      margin=dict(l=40, r=40, t=40, b=40),
      xaxis=dict(showgrid=True, gridcolor="#f5f5f5", title_text=""),
      yaxis=dict(
          showgrid=True, gridcolor="#f5f5f5", title_text="Fertility Rate"
      ),
      legend=dict(
          title_text="Regions", orientation="h", yanchor="bottom", y=1.02, x=0
      ),
  )

  st.plotly_chart(fig, use_container_width=True)
else:
  st.warning("No information exists for this window selection.")

# 6. Preview Raw Processing Stacks
with st.expander("🔍 View Restructured Data Spreadsheet"):
  st.dataframe(filtered_df, use_container_width=True)
