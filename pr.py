import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

# ====================== 网页全局设置 (企业级UI注入) ======================
st.set_page_config(page_title="企业风库存看板", layout="wide", page_icon="🏢")

# 核心 CSS 注入：复刻设计图的白蓝高级质感
st.markdown("""
<style>
    /* 调整主页面顶部留白 */
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    /* 全局字体和标题颜色 */
    h1, h2, h3 { color: #1E3A8A !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    /* 重写指标卡片样式 (复刻第二张图顶部的白底卡片) */
    div[data-testid="metric-container"] {
        background-color: #FFFFFF; border: 1px solid #E5E7EB; padding: 15px 20px;
        border-radius: 10px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        border-left: 5px solid #3B82F6;
    }
    div[data-testid="metric-container"] label { color: #6B7280 !important; font-size: 14px !important; }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] { color: #111827 !important; font-size: 28px !important; font-weight: bold;}
    /* 隐藏原生的 DataFrame 索引 */
    .row_heading.level0 {display:none}
    .blank {display:none}
</style>
""", unsafe_allow_html=True)

# ====================== 数据底表加载 ======================
FILE_PATH = r"H:\Dept\HzP_LOG\05_MSE-LOP\11_PP&MP\XSU3HZ\coding\AI\final_model\Non_FG\finally\Dashboard_Master_Data.xlsx"

@st.cache_data
def load_data():
    if not os.path.exists(FILE_PATH):
         st.error(f"找不到数据总表，请确认 prepare_data.py 已成功运行！路径：{FILE_PATH}")
         st.stop()
    df = pd.read_excel(FILE_PATH)
    df['date'] = pd.to_datetime(df['date'])
    df.replace([np.inf, -np.inf], 0, inplace=True)
    df.fillna(0, inplace=True)
    return df

df = load_data()

# ====================== 左侧侧边栏 (原汁原味保留) ======================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/dashboard-layout.png", width=60)
    st.title("决策看板中心")
    menu = st.radio("请选择功能模块", [
        "1️⃣ 12个月资金占用走势", 
        "2️⃣ 月末资金全量明细表", 
        "3️⃣ 每日排库库位预警", 
        "4️⃣ 单日精准预测查询"
    ])
    st.markdown("---")
    st.caption("AI 驱动型供应链中枢 v2.0")

# =====================================================================
# 模块 1: 12个月资金占用走势 (👉 完美复刻图1：左表右图)
# =====================================================================
if menu == "1️⃣ 12个月资金占用走势":
    st.title(" 月度预测库存资金走势看板")
    st.caption("基于 AI 预测月底结余库存 × 采购单价测算")
    
    df_end = df[df['is_month_end'] == 1].copy()
    if not df_end.empty:
        trend = df_end.groupby('年月').agg({'总金额': 'sum', 'item_id': 'nunique'}).reset_index()
        trend.columns = ['月份', '预测总金额', '涉及物料数']
        
        # 👑 核心排版：左边放汇总表，右边放渐变面积图
        c1, c2 = st.columns([1, 1.8])
        
        with c1:
            st.subheader(" 资金月度汇总清单")
            # 采用交互式 dataframe 方便看，设置高度与右侧图表齐平
            st.dataframe(
                trend.style.format({'预测总金额': '¥ {:,.2f}'}).background_gradient(cmap='Blues', subset=['预测总金额']),
                use_container_width=True, height=380
            )
            
        with c2:
            st.subheader(" 资金占用金额趋势 (RMB)")
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(
                x=trend['月份'], y=trend['预测总金额'],
                fill='tozeroy', # 填充渐变色，复刻设计图的阴影效果
                mode='lines+markers',
                line=dict(color='#3B82F6', width=3),
                marker=dict(size=8, color='#1E3A8A'),
                name='总金额'
            ))
            fig1.update_layout(
                margin=dict(l=0, r=0, t=20, b=0),
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=True, gridcolor='#E5E7EB'),
                yaxis=dict(showgrid=True, gridcolor='#E5E7EB', tickformat=",.0f")
            )
            st.plotly_chart(fig1, use_container_width=True)
            
        st.markdown("---")
        # 底部展示当年最需要关注的 Top 物料预警
        st.subheader(" 当月高金额预警清单")
        sel_m = st.selectbox("选择查看月份:", trend['月份'].tolist(), index=len(trend)-1)
        df_m = df_end[df_end['年月'] == sel_m].sort_values('总金额', ascending=False).head(20)
        df_m_show = df_m[['item_id', 'price', 'safety_stock', 'AI预测库存', '总金额']].copy()
        df_m_show.columns = ['物料号', '单价', '安全库存', '月末结余量', '资金总计']
        st.dataframe(df_m_show.style.format({
            '单价': '¥ {:.2f}', '月末结余量': '{:.0f} 件', '资金总计': '¥ {:,.2f}', '安全库存': '{:.0f} 件'
        }), use_container_width=True)

# =====================================================================
# 模块 2: 月末资金全量明细表 (原汁原味平铺)
# =====================================================================
elif menu == "2️⃣ 月末资金全量明细表":
    st.title(" 全景：12个月月末金额明细清单")
    df_end = df[df['is_month_end'] == 1].copy()
    if not df_end.empty:
        df_show = df_end[['年月', 'item_id', 'price', 'AI预测库存', '总金额']].copy()
        df_show.columns = ['归属月份', '料号 (Item ID)', '单价', '月末AI预测库存', '结算金额(×30)']
        df_show = df_show.sort_values(by=['归属月份', '结算金额(×30)'], ascending=[True, False])
        st.dataframe(df_show.style.format({
            '单价': '¥ {:.2f}', '月末AI预测库存': '{:.0f} 件', '结算金额(×30)': '¥ {:,.2f}'
        }), use_container_width=True, height=700)

# =====================================================================
# 模块 3: 每日排库库位预警 (👉 完美复刻图2：卡片+双图+明细)
# =====================================================================
elif menu == "3️⃣ 每日排库库位预警":
    st.title(" 库位监控总览看板")
    
    # 顶部日期筛选
    min_date = df['date'].min().date()
    max_date = df['date'].max().date()
    sel_date = st.date_input("🔍 选择排产监控日期:", value=min_date, min_value=min_date, max_value=max_date)
    df_day = df[df['date'] == pd.to_datetime(sel_date)].copy()
    
    if not df_day.empty:
        # 👑 顶层：4 个指标卡片
        total_bins = int(df_day['需求库位数'].sum())
        active_items = int(df_day[df_day['需求库位数'] > 0]['item_id'].nunique())
        max_item = df_day.loc[df_day['需求库位数'].idxmax(), 'item_id'] if total_bins > 0 else "无"
        max_bins = int(df_day['需求库位数'].max())
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(" 总库位需求数", f"{total_bins:,} 托")
        m2.metric(" 需排库物料种类", f"{active_items} 种")
        m3.metric(" 预警/最大占用物料", f"{max_item}")
        m4.metric(" 单物料最高库位数", f"{max_bins} 托")
        st.markdown("<br>", unsafe_allow_html=True)

        # 👑 中间：左边环形图，右边7天走势图
        c_mid1, c_mid2 = st.columns([1, 1.8])
        
        with c_mid1:
            st.subheader("▍ 库位占用分布")
            df_pie = df_day[['item_id', '需求库位数']].sort_values('需求库位数', ascending=False)
            top5 = df_pie.head(5)
            others = pd.DataFrame([{'item_id': '其它', '需求库位数': df_pie.iloc[5:]['需求库位数'].sum()}])
            df_pie_final = pd.concat([top5, others], ignore_index=True) if len(df_pie)>5 else top5
            
            fig2 = px.pie(df_pie_final, values='需求库位数', names='item_id', hole=0.5, 
                          color_discrete_sequence=px.colors.qualitative.Set2)
            fig2.update_layout(margin=dict(l=20, r=20, t=20, b=20), showlegend=True, 
                               legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
            st.plotly_chart(fig2, use_container_width=True)

        with c_mid2:
            st.subheader("▍ 近7天库位库存趋势")
            end_d = pd.to_datetime(sel_date) + pd.Timedelta(days=7)
            trend_7d = df[(df['date'] >= pd.to_datetime(sel_date)) & (df['date'] <= end_d)]
            trend_agg = trend_7d.groupby('date')['需求库位数'].sum().reset_index()
            
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(
                x=trend_agg['date'].dt.strftime('%m-%d'), y=trend_agg['需求库位数'],
                fill='tozeroy', mode='lines+markers',
                line=dict(color='#0EA5E9', width=3), marker=dict(size=8, color='#0284C7')
            ))
            fig3.update_layout(margin=dict(l=0, r=0, t=20, b=0), plot_bgcolor='rgba(0,0,0,0)',
                               xaxis=dict(showgrid=True, gridcolor='#E5E7EB'), yaxis=dict(showgrid=True, gridcolor='#E5E7EB'))
            st.plotly_chart(fig3, use_container_width=True)

        # 👑 底部：明细数据表
        st.subheader("▍ 排库作业清单")
        df_show = df_day[df_day['需求库位数'] > 0][['item_id', 'AI预测库存', 'rounding_qty', '需求库位数']].copy()
        df_show.columns = ['物料号', '库存数量', '标准容量(件/托)', '占用托数']
        df_show = df_show.sort_values(by=['占用托数'], ascending=False)
        df_show.insert(0, '序号', range(1, len(df_show) + 1))
        
        st.dataframe(df_show.style.format({
            '库存数量': '{:.0f}', '标准容量(件/托)': '{:.0f}', '占用托数': '{:.0f}'
        }), use_container_width=True, height=400)

# =====================================================================
# 模块 4: 单日精准预测查询 (增加样式美化)
# =====================================================================
elif menu == "4️⃣ 单日精准预测查询":
    st.title(" 物料单点精准核对")
    
    c1, c2 = st.columns(2)
    with c1: sel_d = st.date_input("步骤1：选择日期", value=df['date'].min())
    with c2: sel_i = st.selectbox("步骤2：输入/选择料号", df['item_id'].unique())
        
    res = df[(df['date'] == pd.to_datetime(sel_d)) & (df['item_id'] == sel_i)]
    
    if not res.empty:
        v_ai = res['AI预测库存'].values[0]
        v_sys = res['pred_stock'].values[0]
        v_safe = res['safety_stock'].values[0]
        
        st.markdown("### 📊 核心指标对比")
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric(" AI 修正后库存", f"{int(v_ai)} 件")
        mc2.metric(" ERP 原始预测", f"{int(v_sys)} 件")
        mc3.metric(" 安全库存标准", f"{int(v_safe)} 件")
    else:
        st.warning("⚠️ 该料号在选定日期下没有预测记录。")