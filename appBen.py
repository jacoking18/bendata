# app.py

import streamlit as st
import pandas as pd
from geopy.distance import geodesic
from io import BytesIO

st.set_page_config(page_title="📍 Lead Proximity Sorter", layout="centered")
st.title("📍 Lead Proximity Sorter")
st.markdown("""
Upload your **CSV or Excel** file and this app will:
- Reorder rows based on geographic proximity
- Leave un-sortable addresses at the bottom
- Preview the sorted list
- Let you download the optimized result

**Must contain:** `LATITUDE` and `LONGITUDE` (or similar variants)
""")

uploaded_file = st.file_uploader("📁 Upload your file", type=["csv", "xlsx"])

def standardize_columns(df):
    df.columns = df.columns.str.upper().str.strip()
    column_map = {
        'LAT': 'LATITUDE',
        'LNG': 'LONGITUDE',
        'LONG': 'LONGITUDE',
        'LON': 'LONGITUDE'
    }
    df.rename(columns=column_map, inplace=True)
    return df

def sort_by_proximity(df):
    df_valid = df.dropna(subset=['LATITUDE', 'LONGITUDE']).copy()
    df_valid[['LATITUDE', 'LONGITUDE']] = df_valid[['LATITUDE', 'LONGITUDE']].astype(float)

    visited = [False] * len(df_valid)
    order = []

    current_index = 0
    visited[current_index] = True
    order.append(current_index)

    for _ in range(len(df_valid) - 1):
        current_location = (
            df_valid.iloc[current_index]['LATITUDE'],
            df_valid.iloc[current_index]['LONGITUDE']
        )
        min_dist = float('inf')
        next_index = None

        for i, row in df_valid.iterrows():
            if not visited[i]:
                target_location = (row['LATITUDE'], row['LONGITUDE'])
                dist = geodesic(current_location, target_location).meters
                if dist < min_dist:
                    min_dist = dist
                    next_index = i

        if next_index is not None:
            visited[next_index] = True
            order.append(next_index)
            current_index = next_index

    sorted_valid = df_valid.iloc[order].copy()
    sorted_valid.insert(0, 'SortOrder', range(1, len(sorted_valid) + 1))

    df_missing = df[df['LATITUDE'].isna() | df['LONGITUDE'].isna()].copy()
    df_missing.insert(0, 'SortOrder', ['Unsorted'] * len(df_missing))

    final = pd.concat([sorted_valid, df_missing], ignore_index=True)
    return final

if uploaded_file:
    file_ext = uploaded_file.name.split(".")[-1].lower()
    try:
        if file_ext == "csv":
            df = pd.read_csv(uploaded_file, on_bad_lines='skip', engine='python', skip_blank_lines=True)
        else:
            df = pd.read_excel(uploaded_file, engine='openpyxl')

        if df.empty:
            st.error("❌ Uploaded file is empty or unreadable.")
            st.stop()

        df = standardize_columns(df)

        if 'LATITUDE' in df.columns and 'LONGITUDE' in df.columns:
            sorted_df = sort_by_proximity(df)

            st.subheader("📊 Sorted Preview (First 25 Rows)")
            st.dataframe(sorted_df.head(25), use_container_width=True)

            def convert_df_to_csv(df):
                buffer = BytesIO()
                df.to_csv(buffer, index=False)
                return buffer.getvalue()

            st.download_button(
                label="⬇️ Download Sorted CSV",
                data=convert_df_to_csv(sorted_df),
                file_name="sorted_leads_by_proximity.csv",
                mime="text/csv"
            )
        else:
            st.error("❌ No `LATITUDE` and `LONGITUDE` fields found. Please check your file headers.")

    except Exception as e:
        st.error(f"❌ Error reading file: {str(e)}")
