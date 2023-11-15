'''
1、2023-9-18 中登-修改表头[凭证编号]
2、增加用户登录
3、9-21增加aggrid
4、9-22增加供应链下载
5、10-10增加普惠报表
6、10-19增加日报处理
'''

import streamlit as st
import numpy as np
import math
import pandas as pd
from io import BytesIO
import time
import streamlit.components.v1 as components        #将要展示的 弄成html
import xlrd
import re
import datetime
from st_aggrid import AgGrid
import numpy as np
import webbrowser

#供应链日报处理
def pd_merge(df_1,df_2,*args):
    print (args[0])
    df = pd.merge(df_1,df_2,left_on=args[0][0],right_on=args[0][1])
    print(df)

def pd_merge_lr(df_1,df_2,*args):
    print (args[0])
    l1=len(args[0])
    print('长度',l1)
    df = pd.merge(df_1,df_2,on=args[0][0:l1-1],how=args[0][l1-1])
    print(df)
    

#聚合连接text
def join_text(df_1,k1,k2):
    grouped = df_1.groupby(k1)[k2].agg(lambda x: ','.join(x))
    return grouped

#供应链台账生成
def taizh(df_1,df_2):
    #df_1.loc[df_1['客户经理'].str.contains('（客户经理）'), '客户经理'].str.replace('（客户经理）','')
    df_1.loc[df_1['客户经理'].str.contains('（客户经理）'), '客户经理'] = df_1.loc[df_1['客户经理'].str.contains('（客户经理）'), '客户经理'].str.replace('（客户经理）', '')

    print(df_1[0:3])

    merged_table = pd.merge(df_1, df_2, left_on=['产品名称', '平台名称'], right_on=['产品名称2', '平台名称2'], how='left')
    merged_table.loc[merged_table['备注2'].notna(), '备注'] = merged_table['备注2']
    updated_table = merged_table.drop(columns=['产品名称2', '平台名称2', '备注2'])
    updated_table = updated_table.drop(columns=['企业规模','产品子名称','平台名称'])
    updated_table['业务发生日'] = pd.to_datetime(updated_table['业务发生日']).dt.strftime('%Y/%m/%d')
    #df['日期列名'] = pd.to_datetime(df['日期列名']).dt.strftime('%Y/%m/%d')
    #updated_table['业务发生日'] = updated_table['业务发生日'].dt.strftime('%Y/%m/%d')
    #updated_table['业务发生日'] = pd.to_datetime(updated_table['业务发生日'])
    updated_table['利率']=updated_table['利率']/100
    updated_table['币种']='人民币'
    updated_table = updated_table[updated_table['客户经理'] != '梅进健']
    updated_table = updated_table[updated_table['客户经理'] != '何洁']
    updated_table = updated_table[updated_table['客户经理'] != '徐晓光']
    updated_table = updated_table[updated_table['客户经理'] != '吴从宇']
    updated_table = updated_table[updated_table['客户经理'] != '闫晓英']
    updated_table = updated_table[updated_table['客户经理'] != '徐劲松']

    updated_table = updated_table.sort_values('业务发生日')
    print(updated_table[0:3])
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    yesterday = yesterday.strftime("%Y-%m-%d")
    #updated_table.to_excel('.\\excel\\temp'+yesterday+'.xlsx')


    return updated_table

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

    #pd.set_option('display.float_format', '{:,.0f}'.format)
    #pd.set_option('display.float_format', None)

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
            #pd.set_option('display.float_format', '{:,.0f}'.format)
            df2 = pd.read_excel(uploaded_file2)
            st.write("发票 Data:")
            #df2['发票号码']=df2['发票号码'].astype(np.object)   #超长号码转文本
            print(df2)
            st.write(df2)
        except Exception as e:
            st.error("Error reading the Excel file. Please upload a valid Excel file.") 


        if st.button("Calculate"):
            pd.set_option('display.float_format', '{:,.0f}'.format)
            df1['银票累计'] = df1['合同金额'].cumsum()
            df2['发票累计']=df2['发票金额'].cumsum()
            fp=0
            mark=[]
            yp=[]
            print(df2)
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
                        print('显示1',fphm)
                        fpje=str(df2['发票金额'][j])
                        row1=df1.iloc[i].tolist()
                        
                        row1.append(fphm)
                        row1.append(fpje)
                        #print(row1)
                        yp.append(row1)
                        fp=fp+1
                        #except :
                        #    fphm=fphm+df2['发票号码'][j]+';'
                        #    fp=fp+1    
                    else :
                        #try :
                        fphm1=str(df2['发票号码'][j])
                        print('显示2',fphm1)
                        fpje1=str(df2['发票金额'][j])
                        row1=df1.iloc[i].tolist()
                        #print(row1)
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
    rq = st.text_input('查询日期  贷款情况(万元)',"202310")
    
    file = pd.ExcelFile(".//excel//data"+rq+".xlsx")
    print('表名',file.sheet_names)
    
    col1, col2 = st.columns([1,99])
    if st.button(' 业 务 查  询'):
        #result = c.execute(sql)
        
        with col1:
            pass
            
    
        with col2:
            for sheet in file.sheet_names:
                df = file.parse(sheet)  #表名
                #df.set_index(df.columns[0], inplace=True)
                #st.write(df,width=500, height=500, scrolling=True)
                AgGrid(df,theme='blue', height=300,width=400) 


#统计报表展示
def ph_report():
    rq = st.text_input('查询日期  普惠情况(万元)',"202310")
    
    file = pd.ExcelFile(".//excel//普惠"+rq+".xlsx")
    print('表名',file.sheet_names)
    
    col1, col2 = st.columns([1,99])
    if st.button(' 普 惠 查  询'):
        #result = c.execute(sql)
        
        with col1:
            pass
            
    
        with col2:
            for sheet in file.sheet_names:
                df = file.parse(sheet)  #表名
                #df.set_index(df.columns[0], inplace=True)
                st.write(df,width=500, height=500, scrolling=True)
                #AgGrid(df,theme='blue', height=300,width=400) 




#中登发票查重


def zdfp():
    st.title("中登在线") 
    uploaded_file1 = st.file_uploader("中登文件", type=["xlsx", "xls"],accept_multiple_files=True) 
    
    row_zd=[]
    data=[]
    dfs = []
    if uploaded_file1 is not None:
        for n in uploaded_file1:
            print(n)
            n.seek(0)
            try:
                #把多个excel文件合并为一个dataframe
                #data=pd.read_excel(n,sheet_name=0)
                #dfs.append(data)
                data=pd.read_excel(n,sheet_name=1)
                dfs.append(data)

            except Exception as e:
                st.error("Error reading the Excel file. Please upload a valid Excel file.")
        
        #data = pd.concat(dfs)
        try :
            data = pd.concat(dfs)
            #st.write(data)
            last_col = data.values[:, [1,4,6,12,-1]]
            #print(last_col)
            st.write(last_col)
            item_zd=[]
            result1=[]
            for item in last_col:
                result2=[]
                mark=item[4]
                #print(mark)
                owner=item[2]
                #print(mark)
                pattern1=re.compile(r'\d+|全部|所有|附件')  #寻出号码
                result2.append(pattern1.findall(mark))
                #print(result1)
                
                pattern = r'\d+-\d+'  #寻出连号发票号码
                match = re.findall(pattern,mark)
                if match:
                    #print('Matched:', match.group())
                    #print('Matched:', match)
                    for item_mark in match:
                        pattern2=r'\d+'
                        match2=re.findall(pattern2, item_mark)
                        #print(match2)
                        for fphm in range(int(match2[0]),int(match2[1])):
                            #print(fphm)
                            result2.append(str(fphm))        
                else:
                    print('No match.')
                    
                #print(result2)    
                for item2 in result2:
                    #print('发票号',item2)
                    for item3 in item2:
                        #print('item3发票',item3)
                        if (len(item3)<=5):
                            pass
                        else :
                            if item[2]!='上海华瑞银行股份有限公司':
                                item_zd.append([item[0],item[1],item[2],item[3],item3.lstrip('0')]) #去掉发票号码开头的0
                            else:
                                pass    

            df_zd=pd.DataFrame(item_zd,columns=['中登编号','到期日','企业开户行','企业账号','发票号码'])
            
            df_zd['发票号码'] = df_zd['发票号码'].astype(str)
            #去掉发票号码开头的0
            df_zd['发票号码'] = df_zd['发票号码'].str.lstrip('0')
            st.write(df_zd)
        except Exception as e:
            
            pass

    #dfzd=get_df_zd()
    #print(row_zd)
    #return data
    #上传发票文件
    uploaded_file2 = st.file_uploader("上传发票文件", type=["xls","xlsx"])
    if uploaded_file2 is not None:
        try :
            df_fp = pd.read_excel(uploaded_file2)
            time.sleep(1)
            #df_fp.rename(columns={'凭证编号':'发票号码'}) #修改表头
            df_fp['发票号码'] = df_fp['凭证编号'] #修改表头
            print(df_fp)
            df_fp['发票号码'] = df_fp['发票号码'].astype(str)
            df_fp['发票号码'] = df_fp['发票号码'].str.strip()
            df_fp['发票号码'] = df_fp['发票号码'].str.lstrip('0')
            st.write(df_fp)
            #join df_zd 和df_fp on 发票号码
            
            df=pd.merge(df_zd,df_fp,on='发票号码',how='left')
            st.write(df)
    
            #下载df的excel
            output = BytesIO()
            excel_writer = pd.ExcelWriter(output, engine='openpyxl')
            df.to_excel(excel_writer, sheet_name='Sheet1', index=False)
            excel_writer.save()
            output.seek(0)
        
            st.download_button(label="Download Excel", data=output, file_name='中登'+time.strftime("%Y%m%d", time.localtime())+'.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        except:
            print('error 发票文件')
            pass



#供应链每日更新
#dataframe添加汇总项
def df_sum(df_data,i,j):
#把datafram中的none替换为数值0
    df_data = df_data.fillna(0)
    #把dataframe中的nan替换为数值0
    df_data = df_data.replace(np.nan,0)
    
    #datafram中的第2列到第10列中的数字保留两位小数
    df_data.iloc[:,i:j] = df_data.iloc[:,i:j].applymap(lambda x: format(x, '.2f'))
    df_data.iloc[:,i:j] = df_data.iloc[:,i:j].astype(float)   #把dataframe中的字符型转换为浮点型
    #给dataframe中添加一行汇总，汇总第1列到第17列
            
    #print (df_data.columns[i:j])
    # 计算数值列的和  
    totals = df_data.iloc[: , i: j].sum()
    #print(list(totals))
    # 构建汇总行,text列使用'Total'文本 
    if i ==1:
        totals_row = pd.DataFrame([['Total'] + list(totals)+['']], columns=df_data.columns)
    if i==2:
        totals_row = pd.DataFrame([['Total',' '] + list(totals)], columns=df_data.columns)    
    df_data = df_data.append(totals_row)
    return df_data

def gyl_today():
    st.title("供应链每日更新")
    
    #显示前一天日期
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    #日期转字符
    yesterday = yesterday.strftime("%Y-%m-%d")
    print(yesterday.replace('-',''))

    rq = st.text_input('查询供应链最新余额',yesterday)
    
    file = pd.ExcelFile(".//excel//供应链汇总"+rq+".xlsx")
    print('表名',file.sheet_names)
    
    col1, col2 = st.columns([1,99])
    if st.button('查询(包含个人经营贷)'):
        #result = c.execute(sql)
        
        with col1:
            pass
            
    
        with col2:
            for sheet in file.sheet_names:
                pd.set_option('display.float_format', lambda x: '%.2f' % x)
                df = file.parse(sheet)  #表名

                #df.set_index(df.columns[0], inplace=True)
                AgGrid(df,theme='blue', height=400,width=400)
                #st.write(df,width=500, height=500, scrolling=True)
                output = BytesIO()
                excel_writer = pd.ExcelWriter(output, engine='openpyxl')
                df.to_excel(excel_writer, sheet_name='Sheet1', index=False)
                excel_writer.save()
                output.seek(0)
            
                st.download_button(label="Download Excel", data=output, file_name='供应链余额'+time.strftime("%Y%m%d", time.localtime())+'.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
 

    #if st.button('查询(不含个人经营贷)'):
    #    #result = c.execute(sql)
    #    
    #    with col1:
    #        pass
    #    
    #    with col2:
    #        for sheet in file.sheet_names:
    #            df = file.parse(sheet)  #表名
    #            df1=df[(df['备注']!='平安普惠')&(df['备注']!='磁金融')&(df['备注']!='Total')]
    #            df1=df_sum(df1,1,2)
    #            
    #            df1.set_index(df.columns[0], inplace=True)
    #            #st.write(df1,width=500, height=500, scrolling=True) 
    #            AgGrid(df,theme='blue', height=400,width=400)               
    
def gylrb():
    st.title("供应链日报")
    # 设置标题字体大小  
    css = """  
    <style>  
    .st-title {  
        font-size: 12px; /* 设置字体大小 */  
    }  
    </style>  
    """  
    st.markdown(css, unsafe_allow_html=True)
 
    
    uploaded_file1 = st.file_uploader("供应链台账", type=["xlsx", "xls"],accept_multiple_files=True) 
    
    data=[]
    col1, col2 ,col3 = st.columns([4,2,4])
    if uploaded_file1 is not None:
        for n in uploaded_file1:
            print(n)
            n.seek(0)
            try:
                
                gylbill=pd.read_excel(n,sheet_name=0,skiprows=3)
                #dfs.append(data)
                #st.write(gylbill)
                product=pd.read_excel('.//excel//产品-对应.xlsx',sheet_name=0)
                #st.write(product)

                gyltz1=taizh(gylbill,product)
                with col1:
                    st.write(gyltz1)

                #pandas不显示科学计数法
                yesterday = datetime.date.today() - datetime.timedelta(days=1)
                #日期转字符
                yesterday = yesterday.strftime("%Y-%m-%d")
                pd.set_option('display.float_format', lambda x: '%.2f' % x)

                group_sum=gyltz1.groupby(['备注'])['金额'].sum().rename('汇总金额').reset_index()
                group_sum['日期'] = yesterday

                sum_yesday=pd.read_excel('.//excel//汇总.xlsx',sheet_name=0)
                with col3:
                    st.write(sum_yesday)
                if st.button('生成汇总'):
                    result = pd.concat([group_sum,sum_yesday],axis=0,ignore_index=True)
                    result2 = result.groupby(['备注'])['汇总金额'].sum().rename('汇总金额').reset_index()
                    result2['日期'] = yesterday
                    result2 = result2.round(2)
                    #result2['汇总金额']=result2['汇总金额'].astype('float')
        
                    result2.to_excel('.//excel//供应链汇总'+yesterday+'.xlsx',index=False)
                    result2.to_excel('.//excel//汇总.xlsx',index=False)
                    with col1:
                        st.write(result2)



            except Exception as e:
                st.error("Error reading the Excel file. Please upload a valid Excel file.")


def fpyz():
    if st.button('发票验证(仅限行内机器使用)'):
        #components.html('<script> window.location.href = "http://10.130.134.79:8505" </script>',
        # width=1200,height=5500, scrolling=True)
        
       st.markdown("<a href='http://10.130.134.79:8505'>发票查验 仅限行内</a>",unsafe_allow_html=True)



def main():
    # 创建侧边栏
    st.sidebar.title("公司部业务工具")
    
    # 创建页面列表
    pages = ["IRR计算器", "酒店贷测算器", "银票贴现EAST","贷前中登发票查重","供应链驾驶舱",
             "供应链最新余额","普惠报表展示","发票验证","统计报表展示"]
    
    # 显示页面列表
    #for page in pages:
    #    st.sidebar.write(page)
    
    # 选择要查看的页面
    page = st.sidebar.selectbox("Choose a page", pages)
    
    # 显示选定的页面
    if page == "IRR计算器":
        IRR()
    elif page == "酒店贷测算器":
        hotel()
    elif page == "银票贴现EAST":
        yinpeast()
    elif page == "贷前中登发票查重":
        zdfp()
    elif page == "供应链驾驶舱":
        html_driver()
    elif page == "供应链最新余额":
        gyl_today()
    elif page =="普惠报表展示":
        ph_report()
    elif page == "发票验证":
        fpyz()        
    else:
        html_report()
        #st.write("This is page 5")

def login(user,pw):
    
    container = st.empty()     #登陆后清除登录界面
    container1 = st.empty()
    container2 = st.empty()
    container3 = st.empty()

    container.title("登录")
    
    username = container1.text_input("用户名")
    password = container2.text_input("密码",type='password')
    
    if container3.button("登录"):
        if username == user and password == pw:
            st.session_state["authenticated"] = True
            #st.success("登录成功")
            container.write("")
            container1.write("")
            container2.write("")
            container3.write("")
            
            home()
        else:
            st.error("用户名或密码错误")
            
# 主页面        
def home():
    st.title("公司部各项统计")
    
    if not st.session_state["authenticated"]:
        st.error("请先登录")
    else:
        #st.write("登录成功,欢迎访问主页!")
        main()


if __name__ == "__main__":

    st.set_page_config(page_title="My App", page_icon=":smiley:", layout="wide")
    #main()
    user = st.secrets["db_username"]
    pw = st.secrets["db_password"]
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    
    if not st.session_state["authenticated"]:
        login(user,pw)
    else:
        home()    
    
    
    
    


   



