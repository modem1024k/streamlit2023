import streamlit as st
import numpy as np
import math

def cal_rate(money,month,month2,rate):  #money:贷款总额，month:还款月数，month2:爬坡期，rate:利息总额
    
    for r in range(50000,300000):
        x=0.0000001*r
        b=(money*x*month2+(money * x * month * (1 + x) ** month) / ((1 + x) ** month - 1) - money-rate)
        if abs(b)<2:
            print(x*12,b)
            break
        
    return x*12

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    return a / b

# Main function
def main():
    st.title("IRR计算器")
    num1 = st.number_input("贷款本金:",value=1000000)
    num2 = st.number_input("还款期数:",value=30)
    num3 = st.number_input("爬坡期:",value=6)
    num4 = st.number_input("利息总额:",value=200000)
    #st.write("贷款利率:",cal_rate(num1,num2,num3,num4))

    operation = st.selectbox("Select operation:", ("计算", "放弃"))
#
    if st.button("Calculate"):
        if operation == "计算":
            result = cal_rate(num1,num2,num3,num4)
    #    elif operation == "Subtraction":
    #        result = subtract(num1, num2)
    #    elif operation == "Multiplication":
    #        result = multiply(num1, num2)
    #    elif operation == "Division":
    #        result = divide(num1, num2)
    #
        st.success(f"IRR: {str(round(result*100,3))+'%'}")

if __name__ == "__main__":
    main()
