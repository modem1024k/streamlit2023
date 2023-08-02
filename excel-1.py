import pandas as pd
import streamlit as st
import xlrd

st.set_page_config(page_title="My App", page_icon=":smiley:", layout="wide")
rq = st.text_input('查询日期',"202307")

file = pd.ExcelFile("data"+rq+".xlsx")
print('表名',file.sheet_names)

col1, col2 = st.columns([1,99])
if st.button(' 业 务 查  询'):
    #result = c.execute(sql)
    
    with col1:
        pass
        

    with col2:
        for sheet in file.sheet_names:
            df = file.parse(sheet)  #表名
            st.write(df,width=500, height=500, scrolling=True)

