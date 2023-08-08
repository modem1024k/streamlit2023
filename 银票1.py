import streamlit as st
import pandas as pd

def main():
    st.title("Excel File Uploader")

    uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx", "xls"])

    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            st.write("Uploaded Excel Data:")
            st.write(df)
        except Exception as e:
            st.error("Error reading the Excel file. Please upload a valid Excel file.")

if __name__ == "__main__":
    main()
