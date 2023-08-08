import streamlit as st
import pandas as pd

pd.options.display.float_format = '{:.2f}'.format  #设置两位小数

def main():
    st.title("Excel File Uploader")

    uploaded_file1 = st.file_uploader("银票文件", type=["xlsx", "xls"])

    if uploaded_file1 is not None:
        try:
            df1 = pd.read_excel(uploaded_file1)
            st.write("银票 Data:")
            st.write(df1)
        except Exception as e:
            st.error("Error reading the Excel file. Please upload a valid Excel file.")

    uploaded_file2 = st.file_uploader("发票文件", type=["xlsx", "xls"])

    if uploaded_file2 is not None:
        try:
            df2 = pd.read_excel(uploaded_file2)
            st.write("发票 Data:")
            st.write(df2)
        except Exception as e:
            st.error("Error reading the Excel file. Please upload a valid Excel file.") 


        if st.button("Calculate"):
            df1['银票累计'] = df1['合同金额'].cumsum()
            df2['发票累计']=df2['发票金额'].cumsum()
            fp=0
            mark=[]
            yp=[]
            for i in range(len(df1)):
                fphm=''
                fphm1=''
                fpje=''
                fpje1=''
                for j in range(fp,len(df2)):
                    row1=[]
                    if df1['银票累计'][i]>=df2['发票累计'][j]:
                        #try :
                            #fphm=fphm+df2['发票号码'][j].astype(str)+';'
                        fphm=str(df2['发票号码'][j])
                        fpje=str(df2['发票金额'][j])
                        row1=df1.iloc[i].tolist()
                        
                        row1.append(fphm)
                        row1.append(fpje)
                        print(row1)
                        yp.append(row1)
                        fp=fp+1
                        #except :
                        #    fphm=fphm+df2['发票号码'][j]+';'
                        #    fp=fp+1    
                    else :
                        #try :
                        fphm1=str(df2['发票号码'][j])
                        fpje1=str(df2['发票金额'][j])
                        row1=df1.iloc[i].tolist()
                        print(row1)
                        row1.append(fphm1)
                        row1.append(fpje1)
                        yp.append(row1)
                        
                        #except :
                        #    fphm1=df2['发票号码'][j]    
                        break  


            headtitles = df1.columns.tolist()
            headtitles.append('发票号码')
            headtitles.append('发票金额')
            df3=pd.DataFrame(yp,columns=headtitles)  #生成新的DF

            st.write(df3)


if __name__ == "__main__":
    main()
