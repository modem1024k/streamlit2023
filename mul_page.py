import streamlit as st
import numpy as np
import math
import pandas as pd
from io import BytesIO
import time
import streamlit.components.v1 as components        #将要展示的 弄成html
import xlrd
#二分法求解
def cal_rate2(money1,month,month2,rate,money2):  #money:贷款总额，month:还款月数，month2:爬坡期，rate:利息总额
    r1=10000
    r2=300000
    i=0
    while i<150000:
        r=(r1+r2)/2
        x=0.0000001*r
        money=money1-money2
        b=(money*x*month2+(money * x * month * (1 + x) ** month) / ((1 + x) ** month - 1) - money-rate)
        if abs(b)<2:
            print(x*12,b)
            break
        elif b>0:
            r2=r
        else:
            r1=r
        i=i+1    
    #print(x*12,b) 
    if i>=150000:
        x=0
    return x*12

# Main function
def IRR():
    st.title("IRR计算器")
    num1 = st.number_input("贷款本金:",value=1000000,disabled=True)
    num2 = st.number_input("还款期数:",value=12)
    num3 = st.number_input("爬坡期:",value=0)
    num4 = st.number_input("利息总额:",value=30000,step=10000)
    num5 =st.number_input("砍头金额", value=0)
    #st.write("贷款利率:",cal_rate(num1,num2,num3,num4))

    operation = st.selectbox("Select operation:", ("计算", "放弃"))
#
    if st.button("Calculate"):
        if operation == "计算":
            result = cal_rate2(num1,num2,num3,num4,num5)
    
        st.success(f"IRR: {str(round(result*100,3))+'%'}")


#酒店测算
def cal_hotel(money,month,month2,rate1):  #money:贷款总额，month:还款月数，month2:爬坡期，rate:利息总额
    rate=(rate1/100)/12
    print('利率',rate)
    b=money * rate *  (1 + rate) ** month / ((1 + rate) ** month - 1)
    #payment = principal * monthly_rate * (1 + monthly_rate)**term / ((1 + monthly_rate)**term - 1)

    print('每月',b)
    b1=money*rate
    row=[]
    header=['期数','每月还款']
    #row.append(header)
    for i in range(month+month2):
        if i < month2:
            row.append(['第'+str(i+1)+'期',round(b1,2)])
        else:    
            row.append(['第'+str(i+1)+'期',round(b,2)])
    

    df=pd.DataFrame(row,columns=header)  #生成新的Dataframe
    print(df)
    return df,b

def hotel():
    #st.set_page_config(page_title="My App", page_icon=":smiley:", layout="wide")
    st.title("酒店贷测算表")
    col1, col2 ,col3 = st.columns([30,30,30])

    with col1:
        num1 = st.number_input("贷款本金:",value=5000000)
        num2 = st.number_input("还本金期数:",value=54,)
        num3 = st.number_input("爬坡期:",value=6)
        num4 = st.number_input("年利率:",value=10.00,step=0.01)
        num5 =st.number_input("砍头金额", value=0)
        num0 = st.number_input("店长工资:",value=35000)
        #st.write("贷款利率:",cal_rate(num1,num2,num3,num4))
    
        operation = st.selectbox("Select operation:", ("计算", "放弃"))
    #
        #if st.button("Calculate"):
        #    if operation == "计算":
        #        result = cal_rate2(num1,num2,num3,num4)
        #        st.write(result)
    with col2:
        num6 = st.number_input("单间REVPAR:",value=300)
        num7 = st.number_input("房间数:",value=120)
        num8 = st.number_input("年房租金额:",value=3000000)
        num9 = st.number_input("员工平均工资:",value=5000)
        num10 = st.number_input("OTA费用占比:",value=0.23)
        num11 = st.number_input("品牌方管理费:",value=0.06)
        num12 = st.number_input("品牌方系统费:",value=0.035,format="%.3f")


    with col1:
        if st.button("开始测算"):
            if operation == "计算":
                result,payment = cal_hotel(num1,num2,num3,num4)
                st.write(result)
                
                with col2:
                    row1=[]
                    mon_sr = num6 * num7 * 30
                    row1.append(['月收入',mon_sr,'REVP*房间数*30'])
                    rent_room= num8 / 12
                    row1.append(['房租',rent_room,'每月房租'])
                    human_fee = round(num9 * num7/4,2,)
                    row1.append(['人力成本',human_fee,'员工数(房间数/4)*工资'])
                    row1.append(['店长工资',num0,'品牌方指定'])
                    food_fee = num7*20*30
                    row1.append(["餐饮成本", food_fee,'房间数*20*30'])
                    hotel_name_fee = num6*num7*num11*30
                    row1.append(["品牌方收费",hotel_name_fee,'月收入*规定比例'])
                    water_fee = num7*10*30
                    row1.append(["水电费", water_fee,'房间数*10*30天'])
                    hotel_room_ser = num7*15*30
                    row1.append(["布草费用",hotel_room_ser,'房间数*15*30天'])
                    phone_fee =5000
                    row1.append(['通讯费',phone_fee,'固定5000'])
                    hotel_sys = num6*num7*num12*30
                    row1.append(['品牌方系统费',hotel_sys,'月收入*规定比例'])
                    ota_fee = num6*num7*num10*0.05*30
                    row1.append(["OTA渠道费", ota_fee,'月收入*规定比例'])
                    other_fee = num7*10*30
                    row1.append(["其他费用", other_fee,'房间数*10*30'])
                    cash = mon_sr
                    for item in row1:
                        if item[0] == row1[0][0]:
                            pass

                        else:    
                            cash=cash-round(item[1],2)
                    
                    row1.append(["现金结余", round(cash*0.94,20),'净现金剩余税率0.06'])        
                    
                    st.write('    ')
                    st.write('    ')
                    st.write('    ')
                    df1=pd.DataFrame(row1,columns=['项目名称','项目金额','备注'])
                    st.write(df1)

                    with col1:
                        
                        st.write('还款保障倍数',round(round(cash*0.94,20)/payment,4),font_size=30)
                        #pass
                    with col3:
                        pass  


#银票EAST报送
def yinpeast():
    st.title("银票发票匹配EAST报送")

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
            df3['单据编号']=df3['发票号码']
            df3['单据金额']=df3['发票金额']

            st.write(df3)    

            output = BytesIO()
            excel_writer = pd.ExcelWriter(output, engine='openpyxl')
            df3.to_excel(excel_writer, sheet_name='Sheet1', index=False)
            excel_writer.save()
            output.seek(0)
        
            st.download_button(label="Download Excel", data=output, file_name='bank'+time.strftime("%Y%m%d", time.localtime())+'.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

#驾驶舱展示

def html_driver():
    with open("my_new_驾驶舱.html", "r",encoding="utf-8") as f:
        page_html = f.read()
    # 在HTML中加入样式调整宽度    
    page_html = f"""
    <div style="width:50vw;">
    {page_html}
    </div>
    """
    
    # 将 HTML 页面作为组件显示在 Streamlit 上
    #st.components.v1.html(page_html, width=700, height=500, scrolling=True)
    components .html(page_html, width=2400, height=5500, scrolling=True)

#统计报表展示
def html_report():
    rq = st.text_input('查询日期  贷款情况(万元)',"202307")
    
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
                df.set_index(df.columns[0], inplace=True)
                st.write(df,width=500, height=500, scrolling=True)    


if __name__ == "__main__":

    st.set_page_config(page_title="My App", page_icon=":smiley:", layout="wide")
    
    
    
        # 创建侧边栏
    st.sidebar.title("公司部业务工具")
    
    # 创建页面列表
    pages = ["IRR计算器", "酒店贷测算器", "银票贴现EAST","供应链驾驶舱","统计报表展示"]
    
    # 显示页面列表
    for page in pages:
        st.sidebar.write(page)
    
    # 选择要查看的页面
    page = st.sidebar.selectbox("Choose a page", pages)
    
    # 显示选定的页面
    if page == "IRR计算器":
        IRR()
    elif page == "酒店贷测算器":
        hotel()
    elif page == "银票贴现EAST":
        yinpeast()
    elif page == "供应链驾驶舱":
        html_driver()
    else:
        html_report()
        #st.write("This is page 5")


   


