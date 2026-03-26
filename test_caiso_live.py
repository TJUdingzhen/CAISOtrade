#!/usr/bin/env python3
"""
CAISO 实时监控 - 本地快速启动脚本
无需 Docker，直接运行，接入真实 CAISO 数据
"""

import os
import sys
import time
import pandas as pd
from datetime import datetime, timedelta
import requests
import zipfile
import io

# 配置
CAISO_NODE = os.getenv("CAISO_NODE", "SP15")
CAISO_MARKET = os.getenv("CAISO_MARKET", "RTM")
OASIS_BASE_URL = "http://oasis.caiso.com/oasisapi"

# 节点映射
NODE_MAPPING = {
    "SP15": "TH_SP15_GEN-APND",
    "NP15": "TH_NP15_GEN-APND",
    "ZP26": "TH_ZP26_GEN-APND",
}

def fetch_caiso_lmp(node_name: str, market: str, start: datetime, end: datetime) -> pd.DataFrame:
    """从 CAISO OASIS API 获取实时电价数据"""
    node_id = NODE_MAPPING.get(node_name.upper(), node_name)
    
    params = {
        "queryname": "PRC_INTVL_LMP",
        "market_run_id": market,
        "node": node_id,
        "startdatetime": start.strftime("%Y%m%dT%H:%M-0000"),
        "enddatetime": end.strftime("%Y%m%dT%H:%M-0000"),
        "version": "1",
        "resultformat": "6"
    }
    
    print(f"📡 正在获取 {node_id} ({market}) 的数据...")
    print(f"   时间范围: {start} ~ {end}")
    
    try:
        url = f"{OASIS_BASE_URL}/SingleZip"
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        
        # 解压 ZIP
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            csv_files = [f for f in z.namelist() if f.endswith('.csv')]
            if not csv_files:
                print("❌ ZIP 中没有 CSV 文件")
                return pd.DataFrame()
            
            with z.open(csv_files[0]) as f:
                df = pd.read_csv(f)
        
        # 数据清洗
        df['INTERVALSTARTTIME_GMT'] = pd.to_datetime(df['INTERVALSTARTTIME_GMT'])
        df['INTERVALENDTIME_GMT'] = pd.to_datetime(df['INTERVALENDTIME_GMT'])
        df['MW'] = pd.to_numeric(df['MW'], errors='coerce')
        df = df.sort_values('INTERVALSTARTTIME_GMT')
        
        print(f"✅ 成功获取 {len(df)} 条数据")
        return df
        
    except Exception as e:
        print(f"❌ 获取数据失败: {e}")
        return pd.DataFrame()

def display_current_price(df: pd.DataFrame):
    """显示当前价格"""
    if df.empty:
        print("⚠️  暂无数据")
        return
    
    latest = df.iloc[-1]
    price = latest['MW']
    timestamp = latest['INTERVALSTARTTIME_GMT']
    
    print("\n" + "="*50)
    print(f"⚡ CAISO 实时电价 - {CAISO_NODE}")
    print("="*50)
    print(f"📍 节点: {CAISO_NODE}")
    print(f"📊 市场: {CAISO_MARKET}")
    print(f"⏰ 时间: {timestamp}")
    print(f"💰 电价: ${price:.2f}/MWh")
    
    # 计算 24h 统计
    if len(df) > 1:
        print(f"📈 24h 最高: ${df['MW'].max():.2f}")
        print(f"📉 24h 最低: ${df['MW'].min():.2f}")
        print(f"📊 24h 平均: ${df['MW'].mean():.2f}")
    print("="*50)

def simple_chart(df: pd.DataFrame, width: int = 80):
    """终端简单图表"""
    if df.empty or len(df) < 2:
        return
    
    print("\n📈 价格趋势 (最近24小时):")
    print("-" * width)
    
    prices = df['MW'].values
    min_p, max_p = prices.min(), prices.max()
    
    if max_p == min_p:
        print("价格无变化")
        return
    
    # 采样显示
    n_bars = min(24, len(prices))
    step = len(prices) // n_bars
    sample = prices[::step][-n_bars:]
    
    for i, price in enumerate(sample):
        bar_len = int((price - min_p) / (max_p - min_p) * 40)
        bar = "█" * bar_len
        print(f"${price:6.2f} | {bar}")
    
    print("-" * width)

def main():
    """主程序"""
    print("🚀 CAISO 实时数据监控")
    print(f"节点: {CAISO_NODE}, 市场: {CAISO_MARKET}")
    print("-" * 50)
    
    # 获取最近24小时数据
    end = datetime.utcnow()
    start = end - timedelta(hours=24)
    
    df = fetch_caiso_lmp(CAISO_NODE, CAISO_MARKET, start, end)
    
    if not df.empty:
        display_current_price(df)
        simple_chart(df)
        
        # 保存到 CSV
        filename = f"caiso_{CAISO_NODE}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        print(f"\n💾 数据已保存: {filename}")
    else:
        print("\n❌ 未能获取数据，请检查网络连接")
        sys.exit(1)

if __name__ == "__main__":
    main()