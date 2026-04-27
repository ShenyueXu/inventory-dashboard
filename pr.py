import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

# ====================== 页面配置 ======================
st.set_page_config(page_title="智能库存监控中心", layout="wide", page_icon="")

# ====================== 深色LED霓虹样式 ======================
st.markdown("""
<style>
    .stApp { background-color: #0B1020; color: #E6E9F7; }
    h1, h2, h3 { color: #00F0FF !important; text-shadow: 0 0 6px #00F0FF; }
    section[data-testid="sidebar"] { background-color: #101830; }
    div[data-testid="metric-container"] {
        background: #121A33;
        border: 1px solid #00F0FF;
        border-radius: 12px;
        box-shadow: 0 0 12px #00F0FF55;
        padding: 16px;
    }
    div[data-testid="stMetricValue"] {
        color: #00FFEA !important;
        font-size: 30px !important;
        font-weight: bold;
        text-shadow: 0 0 8px #00FFEA;
    }
    div[data-testid="metric-container"] label {
        color: #A9B7E7 !important;
    }
    .stDataFrame { background-color: #0E162D; }
</style>
""", unsafe_allow_html=True)

# ====================== 固定绝对路径 ======================
MAIN_XLSX = r"H:\Dept\HzP_LOG\05_MSE-LOP\11_PP&MP\XSU3HZ\coding\AI\final_model\Non_FG\finally\Dashboard_Master_Data.xlsx"
PLAN_XLSX = r"H:\Dept\HzP_LOG\05_MSE-LOP\11_PP&MP\XSU3HZ\coding\AI\final_model\Non_FG\finally\计划员-价值流信息xlsx.xlsx"

@st.cache_data(ttl=3600)
def load_data():
    df_main = pd.read_excel(MAIN_XLSX)
    df_main["date"] = pd.to_datetime(df_main["date"], errors="coerce")

    df_plan = pd.read_excel(PLAN_XLSX)
    df_plan.rename(columns={
        "Material": "item_id",
        "MRP ctrlr": "planner",
        "Value stream": "value_stream"
    }, inplace=True)

    df_merge = pd.merge(
        df_main,
        df_plan[["item_id", "Material Description", "Vendor", "Vendor name", "planner", "value_stream"]],
        on="item_id",
        how="left"
    )

    df_merge["planner"] = df_merge["planner"].fillna("未分配")
    df_merge["value_stream"] = df_merge["value_stream"].fillna("未分配")
    df_merge = df_merge.fillna(0)
    return df_merge

df = load_data()

# ====================== 侧边栏筛选 ======================
with st.sidebar:
    st.title("智能监控中心")
    st.subheader("全局筛选")

    vs_list = ["全部"] + sorted(df["value_stream"].dropna().unique().tolist())
    planner_list = ["全部"] + sorted(df["planner"].dropna().unique().tolist())

    sel_vs = st.selectbox("Value stream 价值流", vs_list)
    sel_planner = st.selectbox("MRP ctrlr 计划员", planner_list)

    st.markdown("---")
    menu = st.radio("功能模块", [
        "12个月资金走势",
        "月末资金明细表",
        "库位预警监控",
        "物料精准查询"
    ])
    st.caption("AI 供应链决策系统 v3.0")

# 全局筛选逻辑
df_filtered = df.copy()
if sel_vs != "全部":
    df_filtered = df_filtered[df_filtered["value_stream"] == sel_vs]
if sel_planner != "全部":
    df_filtered = df_filtered[df_filtered["planner"] == sel_planner]

# =====================================================================
# 12个月资金走势
# =====================================================================
if menu == "12个月资金走势":
    st.title("月度资金占用 LED 看板")
    df_month = df_filtered[df_filtered["is_month_end"] == 1].copy()
    if not df_month.empty:
        df_group = df_month.groupby("年月").agg(
            预测总金额=("总金额", "sum"),
            物料数量=("item_id", "nunique")
        ).reset_index()
        c1, c2 = st.columns([1, 1.8])
        with c1:
            st.subheader("月度资金汇总")
            st.dataframe(df_group.style.format({"预测总金额":"¥ {:,.0f}"}), height=380)
        with c2:
            st.subheader("资金趋势图表")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_group["年月"],
                y=df_group["预测总金额"],
                fill="tozeroy",
                line=dict(color="#00F0FF", width=3),
                marker=dict(color="#00FFEA", size=6)
            ))
            fig.update_layout(template="plotly_dark", paper_bgcolor="#0B1020", plot_bgcolor="#0B1020")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("当前筛选条件无数据")

# =====================================================================
# 月末资金明细表
# =====================================================================
elif menu == "月末资金明细表":
    st.title("全量月末资金明细")
    df_month = df_filtered[df_filtered["is_month_end"] == 1].copy()
    if not df_month.empty:
        cols = [
            "年月","item_id","Material Description","value_stream","planner",
            "Vendor name","price","AI预测库存","总金额"
        ]
        show_df = df_month[cols].copy()
        show_df.columns = ["月份","料号","物料描述","价值流","计划员","供应商","单价","月末库存","库存金额"]
        st.dataframe(show_df.style.format({"单价":"¥ {:.2f}","库存金额":"¥ {:,.0f}"}), height=700)
    else:
        st.info("当前筛选条件无数据")

# =====================================================================
# 库位预警监控
# =====================================================================
elif menu == "库位预警监控":
    st.title("库位占用实时监控")
    if df_filtered.empty:
        st.info("当前筛选无数据")
    else:
        d_min = df_filtered["date"].min().date()
        d_max = df_filtered["date"].max().date()
        sel_date = st.date_input("选择查询日期", d_max, d_min, d_max)
        df_day = df_filtered[df_filtered["date"] == pd.Timestamp(sel_date)]

        if not df_day.empty:
            total_bin = int(df_day["需求库位数"].sum())
            mat_cnt = df_day[df_day["需求库位数"] > 0]["item_id"].nunique()
            col1,col2,col3,col4 = st.columns(4)
            col1.metric("总占用库位", f"{total_bin} 托")
            col2.metric("涉及物料", mat_cnt)
            col3.metric("单物料最高占用", df_day.loc[df_day["需求库位数"].idxmax(), "item_id"])
            col4.metric("单物料最大托数", int(df_day["需求库位数"].max()))

            c1,c2 = st.columns(2)
            with c1:
                st.subheader("库位占用分布")
                top_mat = df_day.nlargest(5, "需求库位数")
                fig_pie = px.pie(top_mat, values="需求库位数", names="item_id", hole=0.5)
                fig_pie.update_layout(template="plotly_dark", paper_bgcolor="#0B1020")
                st.plotly_chart(fig_pie, use_container_width=True)
            with c2:
                st.subheader("近7日库位趋势")
                df_7d = df_filtered[(df_filtered["date"]>=pd.Timestamp(sel_date)) & (df_filtered["date"]<=pd.Timestamp(sel_date)+pd.Timedelta(days=7))]
                trend_7d = df_7d.groupby("date")["需求库位数"].sum()
                fig_line = go.Figure(go.Scatter(x=trend_7d.index, y=trend_7d.values, line=dict(color="#00FFEA",width=3)))
                fig_line.update_layout(template="plotly_dark", paper_bgcolor="#0B1020")
                st.plotly_chart(fig_line, use_container_width=True)

            st.subheader("当日物料库位清单")
            list_df = df_day[df_day["需求库位数"]>0][
                ["item_id","Material Description","value_stream","planner","Vendor name","AI预测库存","需求库位数"]
            ]
            list_df.columns = ["料号","物料描述","价值流","计划员","供应商","当前库存","占用托数"]
            st.dataframe(list_df, use_container_width=True)
        else:
            st.info("所选日期无库位数据")

# =====================================================================
# 物料精准查询
# =====================================================================
elif menu == "物料精准查询":
    st.title("物料单点精准查询")
    if df_filtered.empty:
        st.info("当前筛选无数据")
    else:
        c1,c2 = st.columns(2)
        with c1:
            q_date = st.date_input("选择查询日期", df_filtered["date"].max())
        with c2:
            q_mat = st.selectbox("选择物料料号", sorted(df_filtered["item_id"].unique()))

        res = df_filtered[(df_filtered["date"]==pd.Timestamp(q_date)) & (df_filtered["item_id"]==q_mat)]
        if not res.empty:
            row = res.iloc[0]
            st.markdown(f"""
            价值流：{row['value_stream']} &nbsp;&nbsp; 
            计划员：{row['planner']} &nbsp;&nbsp; 
            供应商：{row['Vendor name']}
            """)
            a,b,c = st.columns(3)
            a.metric("AI预测库存", f"{int(row['AI预测库存'])} 件")
            b.metric("ERP原始库存", f"{int(row['pred_stock'])} 件")
            c.metric("安全库存阈值", f"{int(row['safety_stock'])} 件")
        else:
            st.warning("该日期+料号无查询数据")