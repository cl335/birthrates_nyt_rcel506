import os
import re
import pandas as pd
import plotly.express as px
import streamlit as st

# 1. Page Layout Customization
st.set_page_config(page_title="NYT Interactive Chart", layout="wide")

st.title("The average number of children born to a woman in select countries and regions ")


CSV_FILE = "birthrates.csv"

# 2. Wide-Matrix Multi-Line Parser Pipeline
@st.cache_data
def load_and_clean_data(file_path):
    if not os.path.exists(file_path):
        return None
    
    with open(file_path, "r", encoding="utf-8") as f:
        first_line = f.readline()
    countries = [c.strip() for c in re.split(r'[\t,]', first_line) if c.strip()]
    
    df_data = pd.read_csv(file_path, skiprows=2, header=None, sep=None, engine='python')
    long_form_list = []
    
    for i, country_name in enumerate(countries):
        x_column_index = i * 2
        y_column_index = i * 2 + 1
        
        if y_column_index < df_data.shape[1]:
            sub_df = df_data[[x_column_index, y_column_index]].dropna()
            sub_df.columns = ["Date", "Value"]
            
            sub_df["Date"] = pd.to_datetime(sub_df["Date"], errors='coerce')
            sub_df["Value"] = pd.to_numeric(sub_df["Value"], errors='coerce')
            sub_df = sub_df.dropna(subset=["Date", "Value"])
            
            sub_df["Country"] = country_name
            long_form_list.append(sub_df)
            
    if not long_form_list:
        return None
        
    combined_df = pd.concat(long_form_list, ignore_index=True)
    combined_df["Date"] = combined_df["Date"].dt.round("D")
    return combined_df.sort_values("Date")

df = load_and_clean_data(CSV_FILE)

# 3. Validation Boundary Check
if df is None or df.empty:
    st.error("Error: Could not format the matrix columns from your dataset. Double-check your file upload.")
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
    format="MMM YYYY"
)

start_date, end_date = selected_range
filtered_df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

# 5. Define Custom Journalistic Colors
# You can customize these hex codes to any shades you want.
# NYT charts often use a signature bold primary highlight paired with muted grays/blues.
nyt_palette = [
    "#815d7b", "#e3d2df", "#3b64a1", "#ce503a", "#f7e183", 
    "#889092", "#d37d7d", "#adadad", "#d3d3d3", "#d3d3d3",
    "#d3d3d3", "#d3d3d3", "#d3d3d3", "#d3d3d3"
]
# Map every unique country to a specific color from our palette array
unique_countries = df["Country"].unique()
country_color_map = {
    country: nyt_palette[i % len(nyt_palette)]
    for i, country in enumerate(unique_countries)
}

# 6. Render Multi-Line Plotly Chart
if not filtered_df.empty:
  # Add a text label column that is empty for all points except the very last one
  # This displays the country name cleanly at the end of each trace line
  filtered_df = filtered_df.sort_values("Date")
  filtered_df["Label"] = ""

  for country in filtered_df["Country"].unique():
    mask = filtered_df["Country"] == country
    if mask.any():
      last_index = filtered_df[mask].index[-1]
      filtered_df.at[last_index, "Label"] = country

  # Build line chart using Plotly's native line tracking mode
  fig = px.line(
      filtered_df,
      x="Date",
      y="Value",
      color="Country",
      text="Label",  # Use the column we just created
      color_discrete_map=country_color_map,
      title="Birth Rates per Woman (1960 - Present)",
  )

  # Style the text positioning natively so it stays on the right side of the endpoints
  fig.update_traces(
      textposition="middle right", font=dict(family="Georgia", size=11)
  )

  # 7. Apply Minimalist Layout & Injection
  fig.update_layout(
      plot_bgcolor="white",
      paper_bgcolor="white",
      font_family="Georgia",
      hovermode="x unified",
      showlegend=False,  # Completely disables the default sidebar color key boxes
      margin=dict(
          l=40, r=220, t=40, b=40
      ),  # High right margin ('r=220') gives labels room to display
      xaxis=dict(showgrid=True, gridcolor="#f5f5f5", title_text=""),
      yaxis=dict(
          showgrid=True, gridcolor="#f5f5f5", title_text="Fertility Rate"
      ),
  )

  st.plotly_chart(fig, use_container_width=True)
else:
  st.warning("No information exists for this window selection.")
