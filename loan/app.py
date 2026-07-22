"""
贷款借据余额可视化看板
=======================
Tab1: 个人贷款 - 按别名/所属部门HR筛选，展示月度借据余额汇总
Tab2: 公司贷款 - 按业务品种细分/所属部门HR筛选，展示月度借据余额汇总
"""

import streamlit as st
import pandas as pd
import toml
from pathlib import Path
import re
import io
import json
import time
import uuid
from typing import List
from datetime import datetime

# pyecharts 驾驶舱依赖
import pyecharts.options as opts
from pyecharts.charts import Line, Pie, Bar, Grid, Timeline
from streamlit.components.v1 import html as st_html

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="贷款借据余额看板",
    page_icon="📊",
    layout="wide",
)

# ==================== 常量 ====================
DATA_DIR = Path(__file__).parent
YUAN_TO_WAN = 10000

# ==================== 用户管理（基于 secrets.toml） ====================

SECRETS_FILE = DATA_DIR / ".streamlit" / "secrets.toml"


def read_users() -> list:
    """从 secrets.toml 读取所有用户（含密码）。"""
    data = toml.load(str(SECRETS_FILE))
    return data.get("auth", {}).get("users", [])


def write_users(users: list):
    """将用户列表写回 secrets.toml，保留注释。"""
    data = toml.load(str(SECRETS_FILE))
    data["auth"]["users"] = users
    with open(str(SECRETS_FILE), "w", encoding="utf-8") as f:
        toml.dump(data, f)


def verify_user(username: str, password: str) -> bool:
    """验证用户名密码。"""
    users = read_users()
    return any(u["username"] == username and u["password"] == password for u in users)


def get_all_users() -> list:
    """查询所有用户（隐藏密码）。"""
    users = read_users()
    return [(u["username"],) for u in users]


def add_user(username: str, password: str) -> tuple:
    """新增用户，返回 (success, message)。"""
    users = read_users()
    if any(u["username"] == username for u in users):
        return False, f"用户名 {username} 已存在"
    users.append({"username": username, "password": password})
    write_users(users)
    return True, f"用户 {username} 新增成功"


def delete_user(username: str) -> tuple:
    """删除用户，返回 (success, message)。"""
    users = read_users()
    new_users = [u for u in users if u["username"] != username]
    if len(new_users) == len(users):
        return False, f"用户 {username} 不存在"
    write_users(new_users)
    return True, f"用户 {username} 已删除"


def update_password(username: str, new_password: str) -> tuple:
    """修改用户密码，返回 (success, message)。"""
    users = read_users()
    for u in users:
        if u["username"] == username:
            u["password"] = new_password
            write_users(users)
            return True, f"用户 {username} 密码已更新"
    return False, f"用户 {username} 不存在"

# ==================== 用户登录 ====================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    # 居中布局
    _, center_col, _ = st.columns([1, 1, 1])
    with center_col:
        st.markdown(
            """<div style="text-align:center;font-size:2.5rem;margin-top:2rem;">📊</div>
            <h3 style="text-align:center;margin-bottom:1.5rem;">贷款借据余额看板</h3>""",
            unsafe_allow_html=True,
        )
        username = st.text_input("用户名", placeholder="请输入用户名")
        password = st.text_input("密码", type="password", placeholder="请输入密码")
        if st.button("登 录"):
            if verify_user(username, password):
                st.session_state.authenticated = True
                st.session_state.current_user = username
                #st.experimental_rerun()
                st.rerun()
            else:
                st.error("用户名或密码错误")
    st.stop()

# ==================== session_state 初始化 ====================

for key, default in [
    ("selected_alias", []),
    ("selected_dept", []),
    ("selected_biz_type", []),
    ("selected_dept_comp", []),
    ("selected_offsheet", []),
    ("selected_biz", []),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ==================== 活跃用户心跳 ====================

HEARTBEAT_FILE = DATA_DIR / "_active_sessions.json"
HEARTBEAT_TIMEOUT = 120  # 超过2分钟视为离线

# 为每个浏览器标签页生成唯一会话 token
if "session_token" not in st.session_state:
    st.session_state.session_token = uuid.uuid4().hex


def heartbeat():
    """记录当前用户心跳到共享文件。"""
    try:
        if HEARTBEAT_FILE.exists():
            data = json.loads(HEARTBEAT_FILE.read_text(encoding="utf-8"))
        else:
            data = {}
        data[st.session_state.session_token] = {
            "username": st.session_state.get("current_user", "未知"),
            "last_seen": time.time(),
        }
        # 清理过期会话
        now = time.time()
        data = {k: v for k, v in data.items()
                if now - v["last_seen"] < HEARTBEAT_TIMEOUT}
        HEARTBEAT_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass  # 心跳失败不影响主流程


def get_active_users():
    """获取当前活跃用户列表（用户名 + 最近活跃时间）。"""
    try:
        if not HEARTBEAT_FILE.exists():
            return []
        data = json.loads(HEARTBEAT_FILE.read_text(encoding="utf-8"))
        now = time.time()
        active = []
        for token, info in data.items():
            if now - info["last_seen"] < HEARTBEAT_TIMEOUT:
                active.append({
                    "username": info["username"],
                    "last_seen": datetime.fromtimestamp(info["last_seen"]).strftime("%H:%M:%S"),
                    "token": token[:8],
                })
        # 按最近活跃时间倒序
        active.sort(key=lambda x: x["last_seen"], reverse=True)
        return active
    except Exception:
        return []


# 每次页面加载时记录心跳
heartbeat()

# ==================== 工具函数 ====================


def smart_read_csv(filepath: Path) -> pd.DataFrame:
    """
    智能读取 CSV 文件，自动处理编码问题。

    先用 utf-8-sig 尝试读取；若失败则用 errors='replace' 容错，
    将不可解码字节替换为占位符，保证数据完整性。

    Args:
        filepath: CSV 文件路径

    Returns:
        读取成功后的 DataFrame，所有列为字符串类型

    Raises:
        UnicodeDecodeError: 两种方式均失败时抛出
    """
    # 尝试标准 UTF-8-SIG 编码
    try:
        return pd.read_csv(filepath, encoding="utf-8-sig", dtype=str)
    except UnicodeDecodeError:
        pass

    # 容错模式：用替换字符处理损坏字节
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()
    return pd.read_csv(io.StringIO(raw), dtype=str)


def parse_filename_month(filename: str) -> str:
    """
    从文件名中解析月份信息。

    例如:
        "个人2501.csv" -> "2025-01"
        "公司2604.csv" -> "2026-04"

    Args:
        filename: CSV 文件名

    Returns:
        格式化的月份字符串，如 "2025-01"
    """
    match = re.search(r"(\d{2})(\d{2})", filename)
    if match:
        yy, mm = match.groups()
        year = 2000 + int(yy)
        return f"{year}-{mm}"
    return "未知月份"


def parse_month_range(filename: str):
    """
    从文件名中解析月份标签和日期范围。

    Args:
        filename: CSV 文件名

    Returns:
        (month_label, month_start, month_end) 三元组，
        month_start/end 为 datetime 对象，范围左闭右开
    """
    match = re.search(r"(\d{2})(\d{2})", filename)
    if match:
        yy, mm = match.groups()
        year = 2000 + int(yy)
        month = int(mm)
        label = f"{year}-{month:02d}"
        start = datetime(year, month, 1)
        # 下月1号作为右边界
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)
        return label, start, end
    return "未知月份", None, None


def load_and_aggregate(csv_files: List[Path], group_cols: List[str]) -> pd.DataFrame:
    """
    批量加载 CSV 文件，按筛选维度同时聚合借据余额和放款金额。

    借据余额: 对文件中所有记录的借据余额求和（月末快照）。
    放款金额: 仅对起始日期在当月范围内的记录求和（当月新发放）。

    Args:
        csv_files: CSV 文件路径列表
        group_cols: 分组维度列名列表

    Returns:
        聚合后的 DataFrame，包含月份、分组列、借据余额汇总、放款金额汇总
    """
    frames = []
    for fp in csv_files:
        try:
            month_label, month_start, month_end = parse_month_range(fp.name)
            if month_start is None:
                continue
            df = smart_read_csv(fp)

            # 转换借据余额（全量）
            df["借据余额"] = pd.to_numeric(df["借据余额"], errors="coerce").fillna(0)

            # 转换放款金额和起始日期，仅起始日期在当月范围内的计入当月放款金额
            df["放款金额"] = pd.to_numeric(df["放款金额"], errors="coerce").fillna(0)
            df["起始日期"] = pd.to_datetime(df["起始日期"], errors="coerce")
            in_month = (df["起始日期"] >= month_start) & (df["起始日期"] < month_end)
            df["放款金额_当月"] = 0.0
            df.loc[in_month, "放款金额_当月"] = df.loc[in_month, "放款金额"]

            # 不良余额: 五级分类 开头为"3"/"4"/"5" 的借据余额
            df["不良余额"] = 0.0
            if "五级分类" in df.columns:
                bad_mask = df["五级分类"].astype(str).str.match(r"^[345]")
                df.loc[bad_mask, "不良余额"] = df.loc[bad_mask, "借据余额"]

            # 按分组维度聚合
            grouped = df.groupby(group_cols, dropna=False).agg(
                借据余额汇总=("借据余额", "sum"),
                放款金额汇总=("放款金额_当月", "sum"),
                不良余额汇总=("不良余额", "sum"),
            ).reset_index()
            grouped["月份"] = month_label
            frames.append(grouped)
        except Exception as e:
            st.warning(f"读取文件 {fp.name} 失败: {e}")

    if not frames:
        return pd.DataFrame()

    result = pd.concat(frames, ignore_index=True)
    # 按月份排序
    result["__sort"] = result["月份"].str.replace("-", "").astype(int)
    result = result.sort_values("__sort").drop(columns="__sort")
    return result


def safe_filter_options(df: pd.DataFrame, col: str) -> List[str]:
    """
    获取筛选列的可用选项，自动过滤空字符串和 NaN。

    Args:
        df: 聚合数据
        col: 列名

    Returns:
        去重、排序、过滤空值后的选项列表
    """
    values = df[col].dropna().astype(str).unique().tolist()
    return sorted(v for v in values if v.strip())


# ==================== 数据加载 ====================


@st.cache_data(show_spinner=False)
def load_personal_data() -> pd.DataFrame:
    """加载所有个人贷款 CSV 并聚合。"""
    files = sorted(DATA_DIR.glob("个人*.csv"))
    return load_and_aggregate(files, group_cols=["别名", "所属部门HR"])


@st.cache_data(show_spinner=False)
def load_company_data() -> pd.DataFrame:
    """加载所有公司贷款 CSV 并聚合。"""
    files = sorted(DATA_DIR.glob("公司*.csv"))
    return load_and_aggregate(files, group_cols=["业务品种细分", "所属部门HR", "是否表外", "业务品种"])


# ==================== 页面布局 ====================

st.title("📊 贷款借据余额可视化看板")
st.caption("数据范围：2025年1月 ~ 2026年4月 | 按所选筛选条件展示月度借据余额汇总趋势")

tab1, tab2, tab3, tab4 = st.tabs(["🏠 个人贷款", "🏢 公司贷款", "🖥️ 驾驶舱", "🔧 管理员"])

# ==================== Tab1：个人贷款 ====================

with tab1:
    st.subheader("个人贷款 · 月度借据余额汇总")

    # 加载数据
    with st.spinner("正在加载个人贷款数据..."):
        personal_df = load_personal_data()

    if personal_df.empty:
        st.error("未找到个人贷款数据文件或文件为空。")
    else:
        # 筛选器（值通过 key 自动写入 st.session_state）
        col1, col2 = st.columns(2)
        with col1:
            all_aliases = safe_filter_options(personal_df, "别名")
            selected_alias = st.multiselect(
                "别名（可多选，留空表示全部）",
                options=all_aliases,
                key="selected_alias",
            )
        with col2:
            all_depts = safe_filter_options(personal_df, "所属部门HR")
            selected_dept = st.multiselect(
                "所属部门HR（可多选，留空表示全部）",
                options=all_depts,
                key="selected_dept",
            )

        # 应用筛选
        filtered = personal_df.copy()
        if selected_alias:
            filtered = filtered[filtered["别名"].isin(selected_alias)]
        if selected_dept:
            filtered = filtered[filtered["所属部门HR"].isin(selected_dept)]

        # 按月份汇总（同时汇总借据余额、放款金额和不良余额）
        monthly_summary = (
            filtered.groupby("月份").agg(
                借据余额汇总=("借据余额汇总", "sum"),
                放款金额汇总=("放款金额汇总", "sum"),
                不良余额汇总=("不良余额汇总", "sum"),
            )
            .reset_index()
            .sort_values("月份")
        )

        # ———— 借据余额 ————
        st.markdown("### 💰 借据余额")
        max_balance = monthly_summary["借据余额汇总"].max() / YUAN_TO_WAN
        avg_balance = monthly_summary["借据余额汇总"].mean() / YUAN_TO_WAN
        latest_balance = monthly_summary["借据余额汇总"].iloc[-1] / YUAN_TO_WAN if not monthly_summary.empty else 0

        m1, m2, m3 = st.columns(3)
        m1.metric("最大借据余额", f"{max_balance:,.2f} 万元")
        m2.metric("月均借据余额", f"{avg_balance:,.2f} 万元")
        m3.metric("最新月份余额", f"{latest_balance:,.2f} 万元")

        chart_data = monthly_summary.set_index("月份")[["借据余额汇总"]]
        chart_data["借据余额汇总"] = chart_data["借据余额汇总"] / YUAN_TO_WAN
        chart_data.columns = ["借据余额汇总（万元）"]
        st.line_chart(chart_data, use_container_width=True)

        # ———— 放款金额 ————
        st.markdown("### 💸 放款金额")
        total_loan = monthly_summary["放款金额汇总"].sum() / YUAN_TO_WAN
        avg_loan = monthly_summary["放款金额汇总"].mean() / YUAN_TO_WAN
        latest_loan = monthly_summary["放款金额汇总"].iloc[-1] / YUAN_TO_WAN if not monthly_summary.empty else 0

        k1, k2, k3 = st.columns(3)
        k1.metric("累计放款金额", f"{total_loan:,.2f} 万元")
        k2.metric("月均放款金额", f"{avg_loan:,.2f} 万元")
        k3.metric("最新月份放款金额", f"{latest_loan:,.2f} 万元")

        loan_chart = monthly_summary.set_index("月份")[["放款金额汇总"]]
        loan_chart["放款金额汇总"] = loan_chart["放款金额汇总"] / YUAN_TO_WAN
        loan_chart.columns = ["放款金额汇总（万元）"]
        st.line_chart(loan_chart, use_container_width=True)

        # ———— 不良余额 ————
        st.markdown("### ⚠️ 不良余额（五级分类为 3-次级 / 4-可疑 / 5-损失）")
        max_bad = monthly_summary["不良余额汇总"].max() / YUAN_TO_WAN
        avg_bad = monthly_summary["不良余额汇总"].mean() / YUAN_TO_WAN
        latest_bad = monthly_summary["不良余额汇总"].iloc[-1] / YUAN_TO_WAN if not monthly_summary.empty else 0

        b1, b2, b3 = st.columns(3)
        b1.metric("最大不良余额", f"{max_bad:,.2f} 万元")
        b2.metric("月均不良余额", f"{avg_bad:,.2f} 万元")
        b3.metric("最新月份不良余额", f"{latest_bad:,.2f} 万元")

        bad_chart = monthly_summary.set_index("月份")[["不良余额汇总"]]
        bad_chart["不良余额汇总"] = bad_chart["不良余额汇总"] / YUAN_TO_WAN
        bad_chart.columns = ["不良余额汇总（万元）"]
        st.line_chart(bad_chart, use_container_width=True)

        # 数据明细表（万元，按所属部门HR拆分，含借据余额、放款金额和不良余额）
        with st.expander("📋 查看数据明细", expanded=False):
            detail_df = (
                filtered.groupby(["月份", "所属部门HR"]).agg(
                    借据余额汇总=("借据余额汇总", "sum"),
                    放款金额汇总=("放款金额汇总", "sum"),
                    不良余额汇总=("不良余额汇总", "sum"),
                )
                .reset_index()
                .sort_values(["月份", "所属部门HR"])
            )
            display_df = detail_df.copy()
            display_df["借据余额汇总"] = (display_df["借据余额汇总"] / YUAN_TO_WAN).apply(
                lambda x: f"{x:,.2f}"
            )
            display_df["放款金额汇总"] = (display_df["放款金额汇总"] / YUAN_TO_WAN).apply(
                lambda x: f"{x:,.2f}"
            )
            display_df["不良余额汇总"] = (display_df["不良余额汇总"] / YUAN_TO_WAN).apply(
                lambda x: f"{x:,.2f}"
            )
            display_df.columns = ["月份", "所属部门HR", "借据余额汇总（万元）", "放款金额汇总（万元）", "不良余额汇总（万元）"]
            st.dataframe(display_df, use_container_width=True)

            # 导出Excel按钮
            export_df = detail_df.copy()
            export_df["借据余额汇总（万元）"] = (export_df["借据余额汇总"] / YUAN_TO_WAN).round(2)
            export_df["放款金额汇总（万元）"] = (export_df["放款金额汇总"] / YUAN_TO_WAN).round(2)
            export_df["不良余额汇总（万元）"] = (export_df["不良余额汇总"] / YUAN_TO_WAN).round(2)
            export_df = export_df[["月份", "所属部门HR", "借据余额汇总（万元）", "放款金额汇总（万元）", "不良余额汇总（万元）"]]
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                export_df.to_excel(writer, index=False, sheet_name="数据明细")
            st.download_button(
                label="📥 导出Excel",
                data=output.getvalue(),
                file_name=f"贷款数据明细_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

# ==================== Tab2：公司贷款 ====================

with tab2:
    st.subheader("公司贷款 · 月度借据余额汇总")

    # 加载数据
    with st.spinner("正在加载公司贷款数据..."):
        company_df = load_company_data()

    if company_df.empty:
        st.error("未找到公司贷款数据文件或文件为空。")
    else:
        # 筛选器（2行 x 2列，值通过 key 自动写入 st.session_state）
        col1, col2 = st.columns(2)
        with col1:
            all_biz_types = safe_filter_options(company_df, "业务品种细分")
            selected_biz_type = st.multiselect(
                "业务品种细分（可多选，留空表示全部）",
                options=all_biz_types,
                key="selected_biz_type",
            )
        with col2:
            all_depts_comp = safe_filter_options(company_df, "所属部门HR")
            selected_dept_comp = st.multiselect(
                "所属部门HR（可多选，留空表示全部）",
                options=all_depts_comp,
                key="selected_dept_comp",
            )

        col3, col4 = st.columns(2)
        with col3:
            all_offsheet = safe_filter_options(company_df, "是否表外")
            selected_offsheet = st.multiselect(
                "是否表外（可多选，留空表示全部）",
                options=all_offsheet,
                key="selected_offsheet",
            )
        with col4:
            all_biz = safe_filter_options(company_df, "业务品种")
            selected_biz = st.multiselect(
                "业务品种（可多选，留空表示全部）",
                options=all_biz,
                key="selected_biz",
            )

        # 应用筛选
        filtered = company_df.copy()
        if selected_biz_type:
            filtered = filtered[filtered["业务品种细分"].isin(selected_biz_type)]
        if selected_dept_comp:
            filtered = filtered[filtered["所属部门HR"].isin(selected_dept_comp)]
        if selected_offsheet:
            filtered = filtered[filtered["是否表外"].isin(selected_offsheet)]
        if selected_biz:
            filtered = filtered[filtered["业务品种"].isin(selected_biz)]

        # 按月份汇总（同时汇总借据余额、放款金额和不良余额）
        monthly_summary = (
            filtered.groupby("月份").agg(
                借据余额汇总=("借据余额汇总", "sum"),
                放款金额汇总=("放款金额汇总", "sum"),
                不良余额汇总=("不良余额汇总", "sum"),
            )
            .reset_index()
            .sort_values("月份")
        )

        # ———— 借据余额 ————
        st.markdown("### 💰 借据余额")
        max_balance = monthly_summary["借据余额汇总"].max() / YUAN_TO_WAN
        avg_balance = monthly_summary["借据余额汇总"].mean() / YUAN_TO_WAN
        latest_balance = monthly_summary["借据余额汇总"].iloc[-1] / YUAN_TO_WAN if not monthly_summary.empty else 0

        m1, m2, m3 = st.columns(3)
        m1.metric("最大借据余额", f"{max_balance:,.2f} 万元")
        m2.metric("月均借据余额", f"{avg_balance:,.2f} 万元")
        m3.metric("最新月份余额", f"{latest_balance:,.2f} 万元")

        chart_data = monthly_summary.set_index("月份")[["借据余额汇总"]]
        chart_data["借据余额汇总"] = chart_data["借据余额汇总"] / YUAN_TO_WAN
        chart_data.columns = ["借据余额汇总（万元）"]
        st.line_chart(chart_data, use_container_width=True)

        # ———— 放款金额 ————
        st.markdown("### 💸 放款金额")
        total_loan = monthly_summary["放款金额汇总"].sum() / YUAN_TO_WAN
        avg_loan = monthly_summary["放款金额汇总"].mean() / YUAN_TO_WAN
        latest_loan = monthly_summary["放款金额汇总"].iloc[-1] / YUAN_TO_WAN if not monthly_summary.empty else 0

        k1, k2, k3 = st.columns(3)
        k1.metric("累计放款金额", f"{total_loan:,.2f} 万元")
        k2.metric("月均放款金额", f"{avg_loan:,.2f} 万元")
        k3.metric("最新月份放款金额", f"{latest_loan:,.2f} 万元")

        loan_chart = monthly_summary.set_index("月份")[["放款金额汇总"]]
        loan_chart["放款金额汇总"] = loan_chart["放款金额汇总"] / YUAN_TO_WAN
        loan_chart.columns = ["放款金额汇总（万元）"]
        st.line_chart(loan_chart, use_container_width=True)

        # ———— 不良余额 ————
        st.markdown("### ⚠️ 不良余额（五级分类为 3-次级 / 4-可疑 / 5-损失）")
        max_bad = monthly_summary["不良余额汇总"].max() / YUAN_TO_WAN
        avg_bad = monthly_summary["不良余额汇总"].mean() / YUAN_TO_WAN
        latest_bad = monthly_summary["不良余额汇总"].iloc[-1] / YUAN_TO_WAN if not monthly_summary.empty else 0

        b1, b2, b3 = st.columns(3)
        b1.metric("最大不良余额", f"{max_bad:,.2f} 万元")
        b2.metric("月均不良余额", f"{avg_bad:,.2f} 万元")
        b3.metric("最新月份不良余额", f"{latest_bad:,.2f} 万元")

        bad_chart = monthly_summary.set_index("月份")[["不良余额汇总"]]
        bad_chart["不良余额汇总"] = bad_chart["不良余额汇总"] / YUAN_TO_WAN
        bad_chart.columns = ["不良余额汇总（万元）"]
        st.line_chart(bad_chart, use_container_width=True)

        # 数据明细表（万元，按所属部门HR拆分，含借据余额、放款金额和不良余额）
        with st.expander("📋 查看数据明细", expanded=False):
            detail_df = (
                filtered.groupby(["月份", "所属部门HR"]).agg(
                    借据余额汇总=("借据余额汇总", "sum"),
                    放款金额汇总=("放款金额汇总", "sum"),
                    不良余额汇总=("不良余额汇总", "sum"),
                )
                .reset_index()
                .sort_values(["月份", "所属部门HR"])
            )
            display_df = detail_df.copy()
            display_df["借据余额汇总"] = (display_df["借据余额汇总"] / YUAN_TO_WAN).apply(
                lambda x: f"{x:,.2f}"
            )
            display_df["放款金额汇总"] = (display_df["放款金额汇总"] / YUAN_TO_WAN).apply(
                lambda x: f"{x:,.2f}"
            )
            display_df["不良余额汇总"] = (display_df["不良余额汇总"] / YUAN_TO_WAN).apply(
                lambda x: f"{x:,.2f}"
            )
            display_df.columns = ["月份", "所属部门HR", "借据余额汇总（万元）", "放款金额汇总（万元）", "不良余额汇总（万元）"]
            st.dataframe(display_df, use_container_width=True)

            # 导出Excel按钮
            export_df = detail_df.copy()
            export_df["借据余额汇总（万元）"] = (export_df["借据余额汇总"] / YUAN_TO_WAN).round(2)
            export_df["放款金额汇总（万元）"] = (export_df["放款金额汇总"] / YUAN_TO_WAN).round(2)
            export_df["不良余额汇总（万元）"] = (export_df["不良余额汇总"] / YUAN_TO_WAN).round(2)
            export_df = export_df[["月份", "所属部门HR", "借据余额汇总（万元）", "放款金额汇总（万元）", "不良余额汇总（万元）"]]
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                export_df.to_excel(writer, index=False, sheet_name="数据明细")
            st.download_button(
                label="📥 导出Excel",
                data=output.getvalue(),
                file_name=f"贷款数据明细_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

# ==================== Tab3：驾驶舱 ====================

with tab3:
    st.subheader("🖥️ 贷款业务驾驶舱")
    st.caption("全局汇总视图 · 个人贷款 & 公司贷款 · pyecharts 渲染")

    with st.spinner("正在加载驾驶舱数据..."):
        p_df = load_personal_data()
        c_df = load_company_data()

    # 应用来自 Tab1/Tab2 的筛选条件
    p_filters_applied = []
    if st.session_state.get("selected_alias"):
        p_df = p_df[p_df["别名"].isin(st.session_state["selected_alias"])]
        p_filters_applied.append(f"别名({len(st.session_state['selected_alias'])})")
    if st.session_state.get("selected_dept"):
        p_df = p_df[p_df["所属部门HR"].isin(st.session_state["selected_dept"])]
        p_filters_applied.append(f"部门({len(st.session_state['selected_dept'])})")

    c_filters_applied = []
    if st.session_state.get("selected_biz_type"):
        c_df = c_df[c_df["业务品种细分"].isin(st.session_state["selected_biz_type"])]
        c_filters_applied.append(f"业务品种细分({len(st.session_state['selected_biz_type'])})")
    if st.session_state.get("selected_dept_comp"):
        c_df = c_df[c_df["所属部门HR"].isin(st.session_state["selected_dept_comp"])]
        c_filters_applied.append(f"部门({len(st.session_state['selected_dept_comp'])})")
    if st.session_state.get("selected_offsheet"):
        c_df = c_df[c_df["是否表外"].isin(st.session_state["selected_offsheet"])]
        c_filters_applied.append(f"是否表外({len(st.session_state['selected_offsheet'])})")
    if st.session_state.get("selected_biz"):
        c_df = c_df[c_df["业务品种"].isin(st.session_state["selected_biz"])]
        c_filters_applied.append(f"业务品种({len(st.session_state['selected_biz'])})")

    # 显示筛选状态
    if p_filters_applied or c_filters_applied:
        filter_status = []
        if p_filters_applied:
            filter_status.append("个人: " + ", ".join(p_filters_applied))
        if c_filters_applied:
            filter_status.append("公司: " + ", ".join(c_filters_applied))
        st.info("🔍 当前筛选: " + " | ".join(filter_status))

    if p_df.empty and c_df.empty:
        st.warning("当前筛选条件下无数据，请调整 Tab1/Tab2 的筛选项。")
    else:
        # 月度汇总
        p_monthly = (
            p_df.groupby("月份")[["借据余额汇总", "放款金额汇总"]]
            .sum().reset_index().sort_values("月份")
        )
        c_monthly = (
            c_df.groupby("月份")[["借据余额汇总", "放款金额汇总"]]
            .sum().reset_index().sort_values("月份")
        )
        p_latest = p_monthly.iloc[-1] if not p_monthly.empty else None
        c_latest = c_monthly.iloc[-1] if not c_monthly.empty else None

        # ===== KPI 指标卡 =====
        st.markdown("### 📈 关键指标总览")
        cp1, cp2, cp3, cc1, cc2, cc3 = st.columns(6)
        p_lb = p_latest["借据余额汇总"] / YUAN_TO_WAN / 10000 if p_latest is not None else 0
        p_cl = p_monthly["放款金额汇总"].sum() / YUAN_TO_WAN / 10000
        p_dc = p_df["所属部门HR"].astype(str).str.strip().replace("", pd.NA).dropna().nunique()
        c_lb = c_latest["借据余额汇总"] / YUAN_TO_WAN / 10000 if c_latest is not None else 0
        c_cl = c_monthly["放款金额汇总"].sum() / YUAN_TO_WAN / 10000
        c_dc = c_df["所属部门HR"].astype(str).str.strip().replace("", pd.NA).dropna().nunique()
        cp1.metric("个人·最新借据余额", f"{p_lb:,.2f} 亿")
        cp2.metric("个人·累计放款", f"{p_cl:,.2f} 亿")
        cp3.metric("个人·部门数", f"{p_dc} 个")
        cc1.metric("公司·最新借据余额", f"{c_lb:,.2f} 亿")
        cc2.metric("公司·累计放款", f"{c_cl:,.2f} 亿")
        cc3.metric("公司·部门数", f"{c_dc} 个")
        st.markdown("---")

        # ===== 月度趋势图 =====
        st.markdown("### 📈 月度趋势对比")
        cl1, cr1 = st.columns(2)

        with cl1:
            lp = (
                Line(init_opts=opts.InitOpts(width="100%", height="400px"))
                .add_xaxis(p_monthly["月份"].tolist())
                .add_yaxis("借据余额（亿元）",
                           (p_monthly["借据余额汇总"] / YUAN_TO_WAN / 10000).round(2).tolist(),
                           is_smooth=True, linestyle_opts=opts.LineStyleOpts(width=3),
                           label_opts=opts.LabelOpts(is_show=False))
                .add_yaxis("放款金额（亿元）",
                           (p_monthly["放款金额汇总"] / YUAN_TO_WAN / 10000).round(2).tolist(),
                           is_smooth=True, linestyle_opts=opts.LineStyleOpts(width=3),
                           label_opts=opts.LabelOpts(is_show=False))
                .set_global_opts(
                    title_opts=opts.TitleOpts(title="个人贷款 · 月度趋势"),
                    tooltip_opts=opts.TooltipOpts(trigger="axis"),
                    legend_opts=opts.LegendOpts(pos_bottom="0%"),
                    xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=45)),
                    yaxis_opts=opts.AxisOpts(name="亿元"),
                )
            )
            st_html(lp.render_embed(), height=450)

        with cr1:
            lc = (
                Line(init_opts=opts.InitOpts(width="100%", height="400px"))
                .add_xaxis(c_monthly["月份"].tolist())
                .add_yaxis("借据余额（亿元）",
                           (c_monthly["借据余额汇总"] / YUAN_TO_WAN / 10000).round(2).tolist(),
                           is_smooth=True, linestyle_opts=opts.LineStyleOpts(width=3),
                           label_opts=opts.LabelOpts(is_show=False))
                .add_yaxis("放款金额（亿元）",
                           (c_monthly["放款金额汇总"] / YUAN_TO_WAN / 10000).round(2).tolist(),
                           is_smooth=True, linestyle_opts=opts.LineStyleOpts(width=3),
                           label_opts=opts.LabelOpts(is_show=False))
                .set_global_opts(
                    title_opts=opts.TitleOpts(title="公司贷款 · 月度趋势"),
                    tooltip_opts=opts.TooltipOpts(trigger="axis"),
                    legend_opts=opts.LegendOpts(pos_bottom="0%"),
                    xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=45)),
                    yaxis_opts=opts.AxisOpts(name="亿元"),
                )
            )
            st_html(lc.render_embed(), height=450)

        st.markdown("---")

        # ===== 部门饼图（Timeline 时间轴） =====
        st.markdown("### 🍩 部门借据余额分布")
        all_months = sorted(p_df["月份"].unique().tolist())

        cl2, cr2 = st.columns(2)

        with cl2:
            tl_personal = Timeline(init_opts=opts.InitOpts(width="100%", height="450px"))
            tl_personal.add_schema(
                is_auto_play=True,
                play_interval=3000,
                is_loop_play=True,
                is_timeline_show=True,
            )
            for month in all_months:
                p_month_df = p_df[p_df["月份"] == month]
                pd_dept = p_month_df.groupby("所属部门HR")["借据余额汇总"].sum().sort_values(ascending=False)
                pd_dept = pd_dept[pd_dept > 0]
                if pd_dept.empty:
                    continue
                pp_data = [(k.strip() or "未知", round(v / YUAN_TO_WAN / 10000, 2))
                           for k, v in pd_dept.items()]
                pp = (
                    Pie()
                    .add("部门", pp_data, radius=["28%", "58%"], center=["35%", "50%"],
                         label_opts=opts.LabelOpts(formatter="{d}%"))
                    .set_global_opts(
                        title_opts=opts.TitleOpts(title=f"个人贷款 · {month} 部门借据余额分布"),
                        legend_opts=opts.LegendOpts(type_="scroll", orient="vertical", pos_right="0%", pos_top="5%"),
                    )
                )
                tl_personal.add(pp, month)
            st_html(tl_personal.render_embed(), height=520)

        with cr2:
            tl_company = Timeline(init_opts=opts.InitOpts(width="100%", height="450px"))
            tl_company.add_schema(
                is_auto_play=True,
                play_interval=3000,
                is_loop_play=True,
                is_timeline_show=True,
            )
            for month in all_months:
                c_month_df = c_df[c_df["月份"] == month]
                cd_dept = c_month_df.groupby("所属部门HR")["借据余额汇总"].sum().sort_values(ascending=False)
                cd_dept = cd_dept[cd_dept > 0]
                if cd_dept.empty:
                    continue
                pc_data = [(k.strip() or "未知", round(v / YUAN_TO_WAN / 10000, 2))
                           for k, v in cd_dept.items()]
                pc = (
                    Pie()
                    .add("部门", pc_data, radius=["28%", "58%"], center=["35%", "50%"],
                         label_opts=opts.LabelOpts(formatter="{d}%"))
                    .set_global_opts(
                        title_opts=opts.TitleOpts(title=f"公司贷款 · {month} 部门借据余额分布"),
                        legend_opts=opts.LegendOpts(type_="scroll", orient="vertical", pos_right="0%", pos_top="5%"),
                    )
                )
                tl_company.add(pc, month)
            st_html(tl_company.render_embed(), height=520)

        st.markdown("---")

        # ===== 不良余额部门饼图（Timeline 时间轴） =====
        st.markdown("### ⚠️ 不良余额部门分布")
        all_months_bad = sorted(p_df["月份"].unique().tolist())

        cl2b, cr2b = st.columns(2)

        with cl2b:
            tl_bad_personal = Timeline(init_opts=opts.InitOpts(width="100%", height="450px"))
            tl_bad_personal.add_schema(
                is_auto_play=True,
                play_interval=3000,
                is_loop_play=True,
                is_timeline_show=True,
            )
            for month in all_months_bad:
                p_month_df = p_df[p_df["月份"] == month]
                pd_bad_dept = p_month_df.groupby("所属部门HR")["不良余额汇总"].sum().sort_values(ascending=False)
                pd_bad_dept = pd_bad_dept[pd_bad_dept > 0]
                if pd_bad_dept.empty:
                    continue
                pp_bad_data = [(k.strip() or "未知", round(v / YUAN_TO_WAN / 10000, 2))
                               for k, v in pd_bad_dept.items()]
                pp_bad = (
                    Pie()
                    .add("部门", pp_bad_data, radius=["28%", "58%"], center=["35%", "50%"],
                         label_opts=opts.LabelOpts(formatter="{d}%"))
                    .set_global_opts(
                        title_opts=opts.TitleOpts(title=f"个人贷款 · {month} 不良余额部门分布"),
                        legend_opts=opts.LegendOpts(type_="scroll", orient="vertical", pos_right="0%", pos_top="5%"),
                    )
                )
                tl_bad_personal.add(pp_bad, month)
            st_html(tl_bad_personal.render_embed(), height=520)

        with cr2b:
            tl_bad_company = Timeline(init_opts=opts.InitOpts(width="100%", height="450px"))
            tl_bad_company.add_schema(
                is_auto_play=True,
                play_interval=3000,
                is_loop_play=True,
                is_timeline_show=True,
            )
            for month in all_months_bad:
                c_month_df = c_df[c_df["月份"] == month]
                cd_bad_dept = c_month_df.groupby("所属部门HR")["不良余额汇总"].sum().sort_values(ascending=False)
                cd_bad_dept = cd_bad_dept[cd_bad_dept > 0]
                if cd_bad_dept.empty:
                    continue
                pc_bad_data = [(k.strip() or "未知", round(v / YUAN_TO_WAN / 10000, 2))
                               for k, v in cd_bad_dept.items()]
                pc_bad = (
                    Pie()
                    .add("部门", pc_bad_data, radius=["28%", "58%"], center=["35%", "50%"],
                         label_opts=opts.LabelOpts(formatter="{d}%"))
                    .set_global_opts(
                        title_opts=opts.TitleOpts(title=f"公司贷款 · {month} 不良余额部门分布"),
                        legend_opts=opts.LegendOpts(type_="scroll", orient="vertical", pos_right="0%", pos_top="5%"),
                    )
                )
                tl_bad_company.add(pc_bad, month)
            st_html(tl_bad_company.render_embed(), height=520)

        st.markdown("---")

        # ===== TOP10 柱状图（按借据余额月均排名） =====
        st.markdown("### 🏆 TOP10 排行（月均借据余额）")
        cl3, cr3 = st.columns(2)

        with cl3:
            pa = p_df.groupby("别名")["借据余额汇总"].mean().sort_values(ascending=False).head(10)
            top_n_personal = len(pa)
            bp = (
                Bar(init_opts=opts.InitOpts(width="100%", height="400px"))
                .add_xaxis([str(k) for k in pa.index.tolist()])
                .add_yaxis("月均借据余额（亿元）",
                           (pa.values / YUAN_TO_WAN / 10000).round(2).tolist(),
                           label_opts=opts.LabelOpts(is_show=True, position="top", formatter="{c} 亿"))
                .set_global_opts(
                    title_opts=opts.TitleOpts(title=f"个人贷款 · 别名 TOP{top_n_personal}（月均借据余额）"),
                    xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=30, font_size=10)),
                    yaxis_opts=opts.AxisOpts(name="亿元"),
                )
                .reversal_axis()
            )
            st_html(bp.render_embed(), height=450)

        with cr3:
            cb = c_df.groupby("业务品种细分")["借据余额汇总"].mean().sort_values(ascending=False).head(10)
            top_n_company = len(cb)
            bc = (
                Bar(init_opts=opts.InitOpts(width="100%", height="400px"))
                .add_xaxis([str(k).strip() or "未知" for k in cb.index.tolist()])
                .add_yaxis("月均借据余额（亿元）",
                           (cb.values / YUAN_TO_WAN / 10000).round(2).tolist(),
                           label_opts=opts.LabelOpts(is_show=True, position="top", formatter="{c} 亿"))
                .set_global_opts(
                    title_opts=opts.TitleOpts(title=f"公司贷款 · 业务品种细分 TOP{top_n_company}（月均借据余额）"),
                    xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=30, font_size=10)),
                    yaxis_opts=opts.AxisOpts(name="亿元"),
                )
                .reversal_axis()
            )
            st_html(bc.render_embed(), height=450)

# ==================== Tab4：管理员 ====================

with tab4:
    st.subheader("🔧 用户管理")

    if st.session_state.get("current_user") != "zhouxiang":
        st.error("您没有管理员权限，仅 zhouxiang 可访问此页面。")
    else:
        # ===== 当前在线用户 =====
        st.markdown("### 🟢 当前在线用户")
        active_users = get_active_users()
        if active_users:
            cols = st.columns(3)
            for i, u in enumerate(active_users):
                with cols[i % 3]:
                    st.metric(
                        label=u["username"],
                        value=f"🟢 在线",
                        delta=f"最近活跃 {u['last_seen']}",
                    )
            st.caption(f"共 {len(active_users)} 人在线（2 分钟内有操作视为在线）")
        else:
            st.info("当前无其他在线用户")
        st.markdown("---")

        # 查询所有用户
        st.markdown("### 📋 用户列表")
        all_users = get_all_users()
        if all_users:
            user_df = pd.DataFrame(all_users, columns=["用户名"])
            st.dataframe(user_df, use_container_width=True)
        else:
            st.info("暂无用户数据")

        st.markdown("---")

        # 新增用户
        st.markdown("### ➕ 新增用户")
        with st.form("add_user_form"):
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                new_username = st.text_input("用户名", key="add_username")
            with col_a2:
                new_password = st.text_input("密码", type="password", key="add_password")
            if st.form_submit_button("新增用户"):
                if not new_username or not new_password:
                    st.error("用户名和密码不能为空")
                else:
                    ok, msg = add_user(new_username, new_password)
                    if ok:
                        st.success(msg)
                        st.experimental_rerun()
                    else:
                        st.error(msg)

        st.markdown("---")

        # 修改密码
        st.markdown("### 🔑 修改密码")
        user_options = [u[0] for u in all_users] if all_users else []
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            target_user = st.selectbox("选择用户", options=user_options, key="pwd_user")
        with col_p2:
            new_pwd = st.text_input("新密码", type="password", key="new_pwd")
        if st.button("修改密码"):
            if not new_pwd:
                st.error("新密码不能为空")
            else:
                ok, msg = update_password(target_user, new_pwd)
                if ok:
                    st.success(msg)
                    st.experimental_rerun()
                else:
                    st.error(msg)

        st.markdown("---")

        # 删除用户
        st.markdown("### 🗑️ 删除用户")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            del_user = st.selectbox("选择用户", options=user_options, key="del_user")
        with col_d2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("确认删除"):
                if del_user == "zhouxiang":
                    st.error("不能删除管理员账户 zhouxiang")
                else:
                    ok, msg = delete_user(del_user)
                    if ok:
                        st.success(msg)
                        st.experimental_rerun()
                    else:
                        st.error(msg)
