import streamlit as st
import numpy as np
import math
import pandas as pd
import os

def cal_rate(money1,month,month2,rate,money2):  #money:贷款总额，month:还款月数，month2:爬坡期，rate:利息总额
    
    for r in range(50000,300000):
        x=0.0000001*r
        money=money1-money2
        b=(money*x*month2+(money * x * month * (1 + x) ** month) / ((1 + x) ** month - 1) - money-rate)
        if abs(b)<2:
            print(x*12,b)
            break
        
    return x*12

#已知贷款本金，期数，利率，计算等额本息每月还款额
def cal_rate2(money,month,month2,rate1):  #money:贷款总额，month:还款月数，month2:爬坡期，rate:利息总额
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


#拼音排序
def pinyin_sort(list):
    import pypinyin
    import operator
    list_pinyin = []
    for i in list:
        list_pinyin.append(pypinyin.lazy_pinyin(i)[0])
    list_pinyin = list(zip(list_pinyin, list))
    list_pinyin.sort(key=operator.itemgetter(0))
    list = [x[1] for x in list_pinyin]
    return list


# Main function
def main():
    st.set_page_config(page_title="My App", page_icon=":smiley:", layout="wide")
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
                result,payment = cal_rate2(num1,num2,num3,num4)
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
    
    
    
    
    
    
    #    elif operation == "Subtraction":
    #        result = subtract(num1, num2)
    #    elif operation == "Multiplication":
    #        result = multiply(num1, num2)
    #    elif operation == "Division":
    #        result = divide(num1, num2)
    #
        #st.success(f"IRR: {str(round(result*100,3))+'%'}")
        

if __name__ == "__main__":
    st.write("DB username:", st.secrets["db_username"])
    st.write("DB password:", st.secrets["db_password"])
    st.write("My cool secrets:", st.secrets["my_cool_secrets"]["things_i_like"])

# And the root-level secrets are also accessible as environment variables:
    st.write(
        "Has environment variables been set:",
        os.environ["db_username"] == st.secrets["db_username"],
        )
    #cal_rate2(1000000,54,6,500000,0)
    main()
    #cal_rate2(1000000,54,6,10)
