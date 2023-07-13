import streamlit as st
import numpy as np
import math

def cal_rate(money1,month,month2,rate,money2):  #money:贷款总额，month:还款月数，month2:爬坡期，rate:利息总额
    
    for r in range(50000,300000):
        x=0.0000001*r
        money=money1-money2
        b=(money*x*month2+(money * x * month * (1 + x) ** month) / ((1 + x) ** month - 1) - money-rate)
        if abs(b)<2:
            print(x*12,b)
            break
        
    return x*12

#二分法求解
def cal_rate2(money1,month,month2,rate,money2):  #money:贷款总额，month:还款月数，month2:爬坡期，rate:利息总额
    r1=50000
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
    return x*12

# Main function
def main():
    st.title("IRR计算器")
    num1 = st.number_input("贷款本金:",value=1000000,disabled=True)
    num2 = st.number_input("还款期数:",value=30)
    num3 = st.number_input("爬坡期:",value=6)
    num4 = st.number_input("利息总额:",value=200000)
    num5 =st.number_input("砍头金额", value=0)
    #st.write("贷款利率:",cal_rate(num1,num2,num3,num4))

    operation = st.selectbox("Select operation:", ("计算", "放弃"))
#
    if st.button("Calculate"):
        if operation == "计算":
            result = cal_rate2(num1,num2,num3,num4,num5)
    #    elif operation == "Subtraction":
    #        result = subtract(num1, num2)
    #    elif operation == "Multiplication":
    #        result = multiply(num1, num2)
    #    elif operation == "Division":
    #        result = divide(num1, num2)
    #
        st.success(f"IRR: {str(round(result*100,3))+'%'}")

if __name__ == "__main__":
    #cal_rate2(1000000,54,6,500000,0)
    main()
