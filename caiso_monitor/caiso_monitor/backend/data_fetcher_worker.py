"""
CAISO 数据获取 Worker - 接入真实 CAISO OASIS API
定时从 CAISO OASIS API 获取数据并存入数据库
"""

import os
import time
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from loguru import logger

# 尝试导入 pycaiso，如果失败则使用备用实现
try:
    from pycaiso.oasis import Node
    HAS_PYCAISO = True
    logger.info("使用 pycaiso 库")
except ImportError:
    HAS_PYCAISO = False
    logger.warning("pycaiso 未安装，将使用备用 HTTP 客户端")
    import requests
    import xml.etree.ElementTree as ET

# 配置
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://caiso:caiso_password@db:5432/caiso_market")
CAISO_NODE = os.getenv("CAISO_NODE", "SP15")
CAISO_MARKET = os.getenv("CAISO_MARKET", "RTM")
FETCH_INTERVAL = int(os.getenv("FETCH_INTERVAL", "300"))  # 默认5分钟

engine = create_engine(DATABASE_URL)

# CAISO OASIS API 配置
OASIS_BASE_URL = "http://oasis.caiso.com/oasisapi"

# 节点名称映射
NODE_MAPPING = {
    "SP15": "TH_SP15_GEN-APND",
    "NP15": "TH_NP15_GEN-APND",
    "ZP26": "TH_ZP26_GEN-APND",
}

def get_node_id(node_name: str) -> str:
    """获取完整的节点 ID"""
    return NODE_MAPPING.get(node_name.upper(), node_name)

def fetch_caiso_data_direct(node_name: str, market: str, start: datetime, end: datetime) -> pd.DataFrame:
    """
    直接调用 CAISO OASIS API 获取数据
    作为 pycaiso 的备用方案
    """
    node_id = get_node_id(node_name)
    
    # 市场类型映射
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
        "resultformat": "6"  # CSV 格式
    }
    
    try:
        logger.info(f"Fetching CAISO data: {node_id} ({market}) from {start} to {end}")
        
        url = f"{OASIS_BASE_URL}/SingleZip"
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        
        # 处理 ZIP 响应
        import zipfile
        import io
        
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            # 找到 CSV 文件
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
        
    except Exception as e:
        logger.error(f"Error fetching from CAISO: {e}")
        return pd.DataFrame()

def get_node_instance(node_name: str):
    """获取节点实例"""
    if HAS_PYCAISO and hasattr(Node, node_name.upper()):
        return getattr(Node, node_name.upper())()
    return None

def fetch_and_store_data(node_name: str, market: str, start: datetime, end: datetime) -> int:
    """
    从 CAISO 获取数据并存入数据库
    返回插入的记录数
    """
    try:
        # 优先使用 pycaiso，否则用直接 HTTP
        if HAS_PYCAISO:
            node = get_node_instance(node_name)
            if node:
                logger.info(f"Using pycaiso for {node_name}")
                df = node.get_lmps(start, end, market=market)
            else:
                df = fetch_caiso_data_direct(node_name, market, start, end)
        else:
            df = fetch_caiso_data_direct(node_name, market, start, end)
        
        if df.empty:
            logger.warning(f"No data returned for {node_name}")
            return 0
        
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
        
        # 批量插入（使用 ON CONFLICT 避免重复）
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
        logger.error(f"Error fetching data: {e}")
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
    
    # 分批获取（CAISO 限制每次最多30天）
    for i in range(days):
        batch_end = end - timedelta(days=i)
        batch_start = batch_end - timedelta(days=1)
        
        count = fetch_and_store_data(node_name, market, batch_start, batch_end)
        logger.info(f"Backfilled {count} records for {batch_start.date()}")
        
        # 避免请求过快
        time.sleep(2)

def main():
    """主循环 - 定时获取数据"""
    logger.info("="*50)
    logger.info("CAISO Data Fetcher Worker Starting")
    logger.info("="*50)
    logger.info(f"Node: {CAISO_NODE}")
    logger.info(f"Market: {CAISO_MARKET}")
    logger.info(f"Fetch Interval: {FETCH_INTERVAL}s")
    logger.info(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local'}")
    
    # 等待数据库就绪
    logger.info("Waiting for database...")
    time.sleep(10)
    
    # 首次启动时回填历史数据
    logger.info("Backfilling historical data...")
    try:
        backfill_data(CAISO_NODE, CAISO_MARKET, days=2)  # 先填2天，避免太久
    except Exception as e:
        logger.error(f"Backfill error: {e}")
    
    logger.info("Starting real-time data fetching loop...")
    
    while True:
        try:
            # 获取最近2小时的数据（重叠以确保不遗漏）
            count = fetch_recent_data(CAISO_NODE, CAISO_MARKET, hours=2)
            
            if count > 0:
                # 更新统计
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
            time.sleep(60)  # 出错后等待1分钟再试

if __name__ == "__main__":
    main()