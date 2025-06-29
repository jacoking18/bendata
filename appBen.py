import csv
import streamlit as st

st.title("Search Results Viewer")

uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"]) 

if uploaded_file is not None:
    try:
        decoded = uploaded_file.read().decode('utf-8').splitlines()
        csv_reader = csv.reader(decoded)
        
        header = next(csv_reader, None)
        if header:
            st.write("### File Header:", header)

            rows = []
            for row in csv_reader:
                if not row or len(row) < len(header):
                    continue  # Skip empty or malformed rows
                rows.append(row)

            if rows:
                st.write("### First 5 Rows:")
                for r in rows[:5]:
                    st.write(r)
            else:
                st.warning("The file appears to have no readable data rows.")
        else:
            st.error("The uploaded file has no header.")
    
    except Exception as e:
        st.error(f"⚠️ Error reading file: {str(e)}")
