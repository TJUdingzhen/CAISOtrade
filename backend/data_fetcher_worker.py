"""
CAISO 数据获取 Worker - 接入真实 CAISO OASIS API
支持代理配置和模拟数据模式（国内网络环境适用）
"""

import os
import time
import random
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from loguru import logger
import requests
import zipfile
import io

# 配置
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://caiso:caiso_password@db:5432/caiso_market")
CAISO_NODE = os.getenv("CAISO_NODE", "SP15")
CAISO_MARKET = os.getenv("CAISO_MARKET", "RTM")
FETCH_INTERVAL = int(os.getenv("FETCH_INTERVAL", "300"))

# 代理配置
HTTP_PROXY = os.getenv("HTTP_PROXY", "")
HTTPS_PROXY = os.getenv("HTTPS_PROXY", "")
USE_PROXY = os.getenv("USE_PROXY", "false").lower() == "true"

# 模拟数据模式（国内网络无法访问 CAISO 时使用）
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "false").lower() == "true"

engine = create_engine(DATABASE_URL)

# CAISO OASIS API 配置
OASIS_BASE_URL = "http://oasis.caiso.com/oasisapi"

# 节点名称映射
NODE_MAPPING = {
    "SP15": "TH_SP15_GEN-APND",
    "NP15": "TH_NP15_GEN-APND", 
    "ZP26": "TH_ZP26_GEN-APND",
}

def get_proxy_dict():
    """获取代理配置"""
    if not USE_PROXY:
        return None
    
    proxies = {}
    if HTTP_PROXY:
        proxies['http'] = HTTP_PROXY
    if HTTPS_PROXY:
        proxies['https'] = HTTPS_PROXY
    
    return proxies if proxies else None

def generate_mock_data(node_name: str, market: str, start: datetime, end: datetime) -> pd.DataFrame:
    """
    生成模拟 CAISO 数据（用于国内无法访问 CAISO API 时测试系统）
    模拟真实电价特征：日内波动、早晚高峰
    """
    logger.info(f"Generating mock data for {node_name} ({market}) from {start} to {end}")
    
    # 生成5分钟间隔的时间序列
    intervals = []
    current = start
    while current < end:
        intervals.append(current)
        current += timedelta(minutes=5)
    
    data = []
    base_time = datetime.now()
    
    for i, ts in enumerate(intervals):
        # 模拟日内电价曲线特征
        hour = ts.hour + ts.minute / 60
        
        # 基础价格 $30-50/MWh
        base_price = 40
        
        # 早高峰 (7-10点): +$20-40
        if 7 <= hour <= 10:
            peak_add = random.uniform(20, 40)
        # 晚高峰 (17-21点): +$30-80
        elif 17 <= hour <= 21:
            peak_add = random.uniform(30, 80)
        # 凌晨 (0-6点): -$10-20
        elif 0 <= hour < 6:
            peak_add = random.uniform(-15, -5)
        else:
            peak_add = random.uniform(-5, 15)
        
        # 随机波动
        noise = random.uniform(-5, 5)
        
        price = base_price + peak_add + noise
        
        # 偶尔出现负电价（加州太阳能过剩时常见）
        if random.random() < 0.02:  # 2% 概率
            price = random.uniform(-20, 0)
        
        # 偶尔出现极高价（供需紧张时）
        if random.random() < 0.01:  # 1% 概率
            price = random.uniform(200, 400)
        
        data.append({
            'INTERVALSTARTTIME_GMT': ts,
            'INTERVALENDTIME_GMT': ts + timedelta(minutes=5),
            'MW': round(price, 2),
            'GROUP': 1,
            'NODE': node_name,
            'MARKET': market
        })
    
    df = pd.DataFrame(data)
    logger.info(f"Generated {len(df)} mock records")
    return df

def fetch_caiso_data_direct(node_name: str, market: str, start: datetime, end: datetime) -> pd.DataFrame:
    """
    直接调用 CAISO OASIS API 获取数据
    支持代理配置
    """
    # 如果使用模拟数据模式，直接返回模拟数据
    if USE_MOCK_DATA:
        logger.warning("MOCK DATA MODE: Using simulated data instead of real CAISO API")
        return generate_mock_data(node_name, market, start, end)
    
    node_id = NODE_MAPPING.get(node_name.upper(), node_name)
    
    market_map = {
        "DAM": "DAM",
        "RTM": "RTM", 
        "RTPD": "RTPD"
    }
    
    params = {
        "queryname": "PRC_INTVL_LMP",
        "market_run_id": market_map.get(market, "RTM"),
        "node": node_id,
        "startdatetime": start.strftime("%Y%m%dT%H:%M-0000"),
        "enddatetime": end.strftime("%Y%m%dT%H:%M-0000"),
        "version": "1",
        "resultformat": "6"
    }
    
    proxies = get_proxy_dict()
    
    try:
        logger.info(f"Fetching CAISO data: {node_id} ({market}) from {start} to {end}")
        if proxies:
            logger.info(f"Using proxy: {proxies}")
        
        url = f"{OASIS_BASE_URL}/SingleZip"
        
        response = requests.get(
            url, 
            params=params, 
            proxies=proxies,
            timeout=60
        )
        response.raise_for_status()
        
        # 处理 ZIP 响应
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            csv_files = [f for f in z.namelist() if f.endswith('.csv')]
            if not csv_files:
                logger.warning("No CSV file in ZIP response")
                return pd.DataFrame()
            
            with z.open(csv_files[0]) as f:
                df = pd.read_csv(f)
        
        # 列名标准化
        if 'INTERVALSTARTTIME_GMT' in df.columns:
            df['INTERVALSTARTTIME_GMT'] = pd.to_datetime(df['INTERVALSTARTTIME_GMT'])
        if 'INTERVALENDTIME_GMT' in df.columns:
            df['INTERVALENDTIME_GMT'] = pd.to_datetime(df['INTERVALENDTIME_GMT'])
        if 'MW' in df.columns:
            df['MW'] = pd.to_numeric(df['MW'], errors='coerce')
        
        logger.info(f"Fetched {len(df)} records from CAISO")
        return df
        
    except requests.exceptions.ProxyError as e:
        logger.error(f"Proxy error: {e}")
        logger.warning("Falling back to mock data...")
        return generate_mock_data(node_name, market, start, end)
    except requests.exceptions.Timeout:
        logger.error("Request timeout - CAISO API may be unreachable from your location")
        logger.warning("Falling back to mock data...")
        return generate_mock_data(node_name, market, start, end)
    except Exception as e:
        logger.error(f"Error fetching from CAISO: {e}")
        logger.warning("Falling back to mock data...")
        return generate_mock_data(node_name, market, start, end)

def fetch_and_store_data(node_name: str, market: str, start: datetime, end: datetime) -> int:
    """从 CAISO 获取数据并存入数据库"""
    df = fetch_caiso_data_direct(node_name, market, start, end)
    
    if df.empty:
        logger.warning(f"No data returned for {node_name}")
        return 0
    
    try:
        # 数据清洗和转换
        df['INTERVALSTARTTIME_GMT'] = pd.to_datetime(df['INTERVALSTARTTIME_GMT'])
        df['INTERVALENDTIME_GMT'] = pd.to_datetime(df['INTERVALENDTIME_GMT'])
        df = df.sort_values('INTERVALSTARTTIME_GMT')
        
        # 准备插入数据
        records = []
        for _, row in df.iterrows():
            records.append({
                'node_id': node_name,
                'market_type': market,
                'interval_start': row['INTERVALSTARTTIME_GMT'],
                'interval_end': row['INTERVALENDTIME_GMT'],
                'price': float(row['MW']) if pd.notna(row['MW']) else 0,
                'mw': float(row['MW']) if pd.notna(row['MW']) else None,
                'group_id': int(row['GROUP']) if 'GROUP' in row and pd.notna(row['GROUP']) else None
            })
        
        # 批量插入
        with engine.connect() as conn:
            for record in records:
                conn.execute(text("""
                    INSERT INTO lmp_data (node_id, market_type, interval_start, interval_end, price, mw, group_id)
                    VALUES (:node_id, :market_type, :interval_start, :interval_end, :price, :mw, :group_id)
                    ON CONFLICT DO NOTHING
                """), record)
            conn.commit()
        
        logger.info(f"Inserted {len(records)} records for {node_name}")
        return len(records)
        
    except Exception as e:
        logger.error(f"Error storing data: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 0

def fetch_recent_data(node_name: str, market: str, hours: int = 2) -> int:
    """获取最近 N 小时的数据"""
    end = datetime.utcnow()
    start = end - timedelta(hours=hours)
    return fetch_and_store_data(node_name, market, start, end)

def backfill_data(node_name: str, market: str, days: int = 7):
    """回填历史数据"""
    logger.info(f"Backfilling {days} days of data for {node_name}")
    
    end = datetime.utcnow()
    
    for i in range(days):
        batch_end = end - timedelta(days=i)
        batch_start = batch_end - timedelta(days=1)
        
        count = fetch_and_store_data(node_name, market, batch_start, batch_end)
        logger.info(f"Backfilled {count} records for {batch_start.date()}")
        
        time.sleep(1 if USE_MOCK_DATA else 2)  # 模拟数据不用等

def main():
    """主循环 - 定时获取数据"""
    logger.info("="*60)
    logger.info("CAISO Data Fetcher Worker Starting")
    logger.info("="*60)
    logger.info(f"Node: {CAISO_NODE}")
    logger.info(f"Market: {CAISO_MARKET}")
    logger.info(f"Fetch Interval: {FETCH_INTERVAL}s")
    logger.info(f"Mock Data Mode: {USE_MOCK_DATA}")
    logger.info(f"Use Proxy: {USE_PROXY}")
    if USE_PROXY:
        logger.info(f"HTTP_PROXY: {HTTP_PROXY}")
        logger.info(f"HTTPS_PROXY: {HTTPS_PROXY}")
    
    # 等待数据库就绪
    logger.info("Waiting for database...")
    time.sleep(10)
    
    # 首次启动时回填历史数据
    logger.info("Backfilling historical data...")
    try:
        backfill_data(CAISO_NODE, CAISO_MARKET, days=7)
    except Exception as e:
        logger.error(f"Backfill error: {e}")
    
    logger.info("Starting real-time data fetching loop...")
    
    while True:
        try:
            count = fetch_recent_data(CAISO_NODE, CAISO_MARKET, hours=2)
            
            if count > 0:
                try:
                    with engine.connect() as conn:
                        conn.execute(text("SELECT update_daily_stats()"))
                        conn.commit()
                except Exception as e:
                    logger.error(f"Stats update error: {e}")
            
            logger.info(f"Fetch cycle complete. Next fetch in {FETCH_INTERVAL}s")
            time.sleep(FETCH_INTERVAL)
            
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()