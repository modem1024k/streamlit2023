import pandas as pd
import streamlit as st
import xlrd



st.set_page_config(page_title="My App", page_icon=":smiley:", layout="wide")
rq = st.text_input('查询日期',"202306")

file = pd.ExcelFile("data"+rq+".xlsx")
print('表名',file.sheet_names)

col1, col2 = st.columns([1,99])
if st.button(' 业 务 查  询'):
    #result = c.execute(sql)
    
    with col1:
        pass
        

    with col2:
        df1 = file.parse(file.sheet_names[0])  #表名
        st.write(df1,width=500, height=500, scrolling=True)

        df2 = file.parse(file.sheet_names[1])  #表名
        st.write(df2,width=500, height=500, scrolling=True)

        df3 = file.parse(file.sheet_names[2])  #表名
        st.write(df3,width=500, height=500, scrolling=True)

        df4 = file.parse(file.sheet_names[3])  #表名
        st.write(df4,width=500, height=500, scrolling=True)

