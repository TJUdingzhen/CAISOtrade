"""
CAISO 市场监控 Dashboard
使用 Streamlit 构建实时数据可视化界面
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import os
import time

# 配置
API_URL = os.getenv("API_URL", "http://localhost:8000")
REFRESH_INTERVAL = 30  # 秒

# 页面配置
st.set_page_config(
    page_title="CAISO 电力市场监控",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 样式
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }
    .stMetric {
        background-color: #1e2329;
        border-radius: 10px;
        padding: 15px;
    }
    .price-up {
        color: #00cc00;
    }
    .price-down {
        color: #ff4444;
    }
</style>
""", unsafe_allow_html=True)

# 侧边栏
def sidebar():
    st.sidebar.title("⚡ CAISO 监控设置")
    
    # 节点选择
    nodes = ["SP15", "NP15", "ZP26", "PGEB-APND", "SDGE-APND", "SCE-APND"]
    node = st.sidebar.selectbox("选择节点", nodes, index=0)
    
    # 市场选择
    markets = {"RTM": "实时市场", "DAM": "日前市场", "RTPD": "实时15分钟"}
    market = st.sidebar.selectbox("市场类型", list(markets.keys()), 
                                   format_func=lambda x: markets[x], index=0)
    
    # 时间范围
    hours = st.sidebar.slider("历史数据范围（小时）", 1, 168, 24)
    
    # 自动刷新
    auto_refresh = st.sidebar.checkbox("自动刷新", value=True)
    
    st.sidebar.divider()
    st.sidebar.info(f"API: {API_URL}")
    
    return node, market, hours, auto_refresh

# 获取数据
def fetch_latest(node, market):
    """获取最新价格"""
    try:
        resp = requests.get(f"{API_URL}/api/lmp/latest", 
                           params={"node": node, "market": market},
                           timeout=10)
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        st.error(f"获取最新价格失败: {e}")
        return None

def fetch_stats(node, market):
    """获取统计数据"""
    try:
        resp = requests.get(f"{API_URL}/api/lmp/stats",
                           params={"node": node, "market": market},
                           timeout=10)
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        st.error(f"获取统计失败: {e}")
        return None

def fetch_history(node, market, hours):
    """获取历史数据"""
    try:
        resp = requests.get(f"{API_URL}/api/lmp/history",
                           params={"node": node, "market": market, "hours": hours},
                           timeout=30)
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        st.error(f"获取历史数据失败: {e}")
        return None

def fetch_signals(hours=24):
    """获取交易信号"""
    try:
        resp = requests.get(f"{API_URL}/api/signals",
                           params={"hours": hours},
                           timeout=10)
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        return None

# 主页面
def main():
    node, market, hours, auto_refresh = sidebar()
    
    # 标题
    st.title(f"⚡ CAISO 电力市场实时监控")
    st.caption(f"节点: {node} | 市场: {market} | 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 获取数据
    latest = fetch_latest(node, market)
    stats = fetch_stats(node, market)
    history = fetch_history(node, market, hours)
    signals = fetch_signals()
    
    # 指标卡片行
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if latest:
            price = latest['price']
            st.metric(
                label="当前电价",
                value=f"${price:.2f}/MWh",
                delta=f"{stats['price_change_24h']:.1f}% (24h)" if stats and stats.get('price_change_24h') else None
            )
        else:
            st.metric(label="当前电价", value="N/A")
    
    with col2:
        if stats:
            st.metric(
                label="24h 均价",
                value=f"${stats['avg_price_24h']:.2f}" if stats.get('avg_price_24h') else "N/A"
            )
        else:
            st.metric(label="24h 均价", value="N/A")
    
    with col3:
        if stats:
            st.metric(
                label="24h 最高价",
                value=f"${stats['max_price_24h']:.2f}" if stats.get('max_price_24h') else "N/A"
            )
        else:
            st.metric(label="24h 最高价", value="N/A")
    
    with col4:
        if stats:
            st.metric(
                label="24h 最低价",
                value=f"${stats['min_price_24h']:.2f}" if stats.get('min_price_24h') else "N/A"
            )
        else:
            st.metric(label="24h 最低价", value="N/A")
    
    st.divider()
    
    # 图表区域
    col_chart, col_signals = st.columns([3, 1])
    
    with col_chart:
        st.subheader("📈 价格趋势")
        
        if history and history.get('data'):
            df = pd.DataFrame(history['data'])
            
            # 根据聚合类型处理数据
            if 'timestamp' in df.columns:
                df['time'] = pd.to_datetime(df['timestamp'])
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df['time'], y=df['avg_price'],
                    mode='lines', name='均价',
                    line=dict(color='#00ff88', width=2)
                ))
                fig.add_trace(go.Scatter(
                    x=df['time'], y=df['max_price'],
                    mode='lines', name='最高价',
                    line=dict(color='#ff6666', width=1, dash='dash')
                ))
                fig.add_trace(go.Scatter(
                    x=df['time'], y=df['min_price'],
                    mode='lines', name='最低价',
                    line=dict(color='#66aaff', width=1, dash='dash')
                ))
            else:
                df['time'] = pd.to_datetime(df['interval_start'])
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df['time'], y=df['price'],
                    mode='lines', name='电价',
                    line=dict(color='#00ff88', width=2)
                ))
            
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis_title="时间",
                yaxis_title="价格 ($/MWh)",
                height=500,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无历史数据")
    
    with col_signals:
        st.subheader("🔔 交易信号")
        
        if signals and signals.get('signals'):
            for sig in signals['signals'][:10]:  # 显示最近10条
                action_color = {
                    'CHARGE': '🟢',
                    'DISCHARGE': '🔴',
                    'HOLD': '⚪'
                }.get(sig['action'], '⚪')
                
                with st.container():
                    st.markdown(f"""
                    **{action_color} {sig['action']}**  
                    {sig['node_id']} @ ${sig['price']:.2f}  
                    <small>{sig['timestamp'][:16]}</small>
                    """, unsafe_allow_html=True)
                    if sig.get('reason'):
                        st.caption(sig['reason'][:50])
                    st.divider()
        else:
            st.info("暂无交易信号")
    
    # 详细数据表格
    with st.expander("📋 查看详细数据"):
        if history and history.get('data'):
            df_display = pd.DataFrame(history['data'])
            st.dataframe(df_display, use_container_width=True)
    
    # 系统状态
    col_status1, col_status2 = st.columns(2)
    
    with col_status1:
        st.subheader("🔌 系统状态")
        try:
            health = requests.get(f"{API_URL}/health", timeout=5).json()
            st.success(f"✅ API 服务正常 | {health['timestamp']}")
        except:
            st.error("❌ API 服务异常")
    
    with col_status2:
        st.subheader("📊 数据覆盖")
        try:
            nodes = requests.get(f"{API_URL}/api/nodes", timeout=5).json()
            st.info(f"已收录 {len(nodes.get('nodes', []))} 个节点数据")
        except:
            st.warning("无法获取节点信息")
    
    # 自动刷新
    if auto_refresh:
        time.sleep(REFRESH_INTERVAL)
        st.rerun()

if __name__ == "__main__":
    main()