import streamlit as st
import time

# Create an empty slot
empty_slot = st.empty()

# Simulate a loading process
with st.spinner("Loading data..."):
    time.sleep(3)  # Simulating data loading

# Update the empty slot with content
for i in range(3):
    empty_slot.text("Data loaded successfully!"+str(i))
    time.sleep(2)


placeholder = st.empty()
placeholder.text("Hello World")
time.sleep(2) 
placeholder.empty() # 清空容器
for i in range(5):
    with placeholder.container():
        placeholder.text("占位空"+str(i))
        time.sleep(2)
