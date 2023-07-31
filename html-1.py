import streamlit.components.v1 as components        #将要展示的 弄成html
import streamlit as st

st.set_page_config(page_title="My App", page_icon=":smiley:", layout="wide")

# 读取包含 Java 的 HTML 文件
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
#text=""
#with open("my_new_驾驶舱.html",encoding="utf-8",width=00, height=7200, scrolling=True) as fp: #如果遇到decode错误，就加上合适的encoding
    #text=fp.read()
#components.html(text)
