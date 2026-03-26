"""
CAISO 市场数据监控后端 API
提供 RESTful API 接口供前端调用
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional
from loguru import logger
import os
import pandas as pd

# 配置
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://caiso:caiso_password@localhost:5432/caiso_market")

# 创建 FastAPI 应用
app = FastAPI(
    title="CAISO Market Monitor API",
    description="CAISO 电力市场实时数据监控 API",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据库连接
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Pydantic 模型
class LMPData(BaseModel):
    interval_start: datetime
    interval_end: datetime
    price: float
    mw: Optional[float] = None
    node_id: str
    market_type: str

class PriceStats(BaseModel):
    node_id: str
    market_type: str
    min_price: float
    max_price: float
    avg_price: float
    std_price: Optional[float] = None
    current_price: float
    price_change_24h: Optional[float] = None

class SignalRequest(BaseModel):
    node_id: str
    action: str
    price: float
    quantity_mw: float
    reason: str

# 健康检查
@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.now()}

# 获取最新电价
@app.get("/api/lmp/latest")
def get_latest_lmp(
    node: str = Query("SP15", description="节点名称"),
    market: str = Query("RTM", description="市场类型: DAM, RTM, RTPD")
):
    """获取指定节点的最新电价"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT interval_start, interval_end, price, mw, node_id, market_type
                FROM lmp_data
                WHERE node_id = :node AND market_type = :market
                ORDER BY interval_start DESC
                LIMIT 1
            """), {"node": node, "market": market})
            
            row = result.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="No data found")
            
            return {
                "interval_start": row[0],
                "interval_end": row[1],
                "price": float(row[2]),
                "mw": float(row[3]) if row[3] else None,
                "node_id": row[4],
                "market_type": row[5]
            }
    except Exception as e:
        logger.error(f"Error fetching latest LMP: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 获取历史数据
@app.get("/api/lmp/history")
def get_lmp_history(
    node: str = Query("SP15", description="节点名称"),
    market: str = Query("RTM", description="市场类型"),
    hours: int = Query(24, description="查询过去多少小时", ge=1, le=168),
    aggregation: str = Query("raw", description="聚合方式: raw, hour, day")
):
    """获取历史电价数据"""
    try:
        with engine.connect() as conn:
            start_time = datetime.now() - timedelta(hours=hours)
            
            if aggregation == "hour":
                query = """
                    SELECT 
                        time_bucket('1 hour', interval_start) as time_bucket,
                        AVG(price) as avg_price,
                        MIN(price) as min_price,
                        MAX(price) as max_price,
                        COUNT(*) as count
                    FROM lmp_data
                    WHERE node_id = :node 
                      AND market_type = :market
                      AND interval_start >= :start_time
                    GROUP BY time_bucket
                    ORDER BY time_bucket ASC
                """
            elif aggregation == "day":
                query = """
                    SELECT 
                        time_bucket('1 day', interval_start) as time_bucket,
                        AVG(price) as avg_price,
                        MIN(price) as min_price,
                        MAX(price) as max_price,
                        COUNT(*) as count
                    FROM lmp_data
                    WHERE node_id = :node 
                      AND market_type = :market
                      AND interval_start >= :start_time
                    GROUP BY time_bucket
                    ORDER BY time_bucket ASC
                """
            else:
                query = """
                    SELECT interval_start, interval_end, price, mw
                    FROM lmp_data
                    WHERE node_id = :node 
                      AND market_type = :market
                      AND interval_start >= :start_time
                    ORDER BY interval_start ASC
                """
            
            result = conn.execute(text(query), {
                "node": node, 
                "market": market, 
                "start_time": start_time
            })
            
            data = []
            for row in result:
                if aggregation in ["hour", "day"]:
                    data.append({
                        "timestamp": row[0],
                        "avg_price": float(row[1]),
                        "min_price": float(row[2]),
                        "max_price": float(row[3]),
                        "count": row[4]
                    })
                else:
                    data.append({
                        "interval_start": row[0],
                        "interval_end": row[1],
                        "price": float(row[2]),
                        "mw": float(row[3]) if row[3] else None
                    })
            
            return {
                "node": node,
                "market": market,
                "hours": hours,
                "aggregation": aggregation,
                "count": len(data),
                "data": data
            }
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 获取价格统计
@app.get("/api/lmp/stats")
def get_price_stats(
    node: str = Query("SP15", description="节点名称"),
    market: str = Query("RTM", description="市场类型")
):
    """获取价格统计信息（24小时）"""
    try:
        with engine.connect() as conn:
            # 当前价格
            current_result = conn.execute(text("""
                SELECT price, interval_start
                FROM lmp_data
                WHERE node_id = :node AND market_type = :market
                ORDER BY interval_start DESC
                LIMIT 1
            """), {"node": node, "market": market})
            current = current_result.fetchone()
            
            if not current:
                raise HTTPException(status_code=404, detail="No data found")
            
            current_price = float(current[0])
            
            # 24小时前的价格
            day_ago_result = conn.execute(text("""
                SELECT price
                FROM lmp_data
                WHERE node_id = :node 
                  AND market_type = :market
                  AND interval_start <= NOW() - INTERVAL '24 hours'
                ORDER BY interval_start DESC
                LIMIT 1
            """), {"node": node, "market": market})
            day_ago = day_ago_result.fetchone()
            
            price_change = None
            if day_ago:
                price_change = ((current_price - float(day_ago[0])) / float(day_ago[0])) * 100
            
            # 24小时统计
            stats_result = conn.execute(text("""
                SELECT 
                    MIN(price) as min_price,
                    MAX(price) as max_price,
                    AVG(price) as avg_price,
                    STDDEV(price) as std_price
                FROM lmp_data
                WHERE node_id = :node 
                  AND market_type = :market
                  AND interval_start >= NOW() - INTERVAL '24 hours'
            """), {"node": node, "market": market})
            stats = stats_result.fetchone()
            
            return {
                "node_id": node,
                "market_type": market,
                "current_price": current_price,
                "current_time": current[1],
                "price_change_24h": round(price_change, 2) if price_change else None,
                "min_price_24h": float(stats[0]) if stats[0] else None,
                "max_price_24h": float(stats[1]) if stats[1] else None,
                "avg_price_24h": float(stats[2]) if stats[2] else None,
                "std_price_24h": float(stats[3]) if stats[3] else None
            }
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 获取可用节点列表
@app.get("/api/nodes")
def get_nodes():
    """获取数据库中可用的节点列表"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT DISTINCT node_id, market_type, 
                       MAX(interval_start) as latest_data
                FROM lmp_data
                GROUP BY node_id, market_type
                ORDER BY node_id
            """))
            
            nodes = []
            for row in result:
                nodes.append({
                    "node_id": row[0],
                    "market_type": row[1],
                    "latest_data": row[2]
                })
            
            return {"nodes": nodes}
    except Exception as e:
        logger.error(f"Error fetching nodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 手动触发数据获取（用于测试）
@app.post("/api/fetch")
def trigger_fetch(
    node: str = Query("SP15"),
    market: str = Query("RTM"),
    hours: int = Query(1, ge=1, le=24)
):
    """手动触发数据获取"""
    try:
        from data_fetcher import fetch_and_store_data
        
        end = datetime.now()
        start = end - timedelta(hours=hours)
        
        count = fetch_and_store_data(node, market, start, end)
        
        return {
            "status": "success",
            "node": node,
            "market": market,
            "records_inserted": count
        }
    except Exception as e:
        logger.error(f"Error triggering fetch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 记录交易信号
@app.post("/api/signals")
def create_signal(signal: SignalRequest):
    """记录交易信号"""
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO trading_signals (timestamp, node_id, action, price, quantity_mw, reason)
                VALUES (NOW(), :node_id, :action, :price, :quantity_mw, :reason)
            """), {
                "node_id": signal.node_id,
                "action": signal.action,
                "price": signal.price,
                "quantity_mw": signal.quantity_mw,
                "reason": signal.reason
            })
            conn.commit()
            
            return {"status": "success", "message": "Signal recorded"}
    except Exception as e:
        logger.error(f"Error creating signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 获取交易信号历史
@app.get("/api/signals")
def get_signals(
    node: str = Query(None),
    hours: int = Query(24, ge=1, le=168)
):
    """获取交易信号历史"""
    try:
        with engine.connect() as conn:
            start_time = datetime.now() - timedelta(hours=hours)
            
            if node:
                query = """
                    SELECT timestamp, node_id, action, price, quantity_mw, reason, executed
                    FROM trading_signals
                    WHERE node_id = :node AND timestamp >= :start_time
                    ORDER BY timestamp DESC
                """
                params = {"node": node, "start_time": start_time}
            else:
                query = """
                    SELECT timestamp, node_id, action, price, quantity_mw, reason, executed
                    FROM trading_signals
                    WHERE timestamp >= :start_time
                    ORDER BY timestamp DESC
                """
                params = {"start_time": start_time}
            
            result = conn.execute(text(query), params)
            
            signals = []
            for row in result:
                signals.append({
                    "timestamp": row[0],
                    "node_id": row[1],
                    "action": row[2],
                    "price": float(row[3]),
                    "quantity_mw": float(row[4]),
                    "reason": row[5],
                    "executed": row[6]
                })
            
            return {"signals": signals, "count": len(signals)}
    except Exception as e:
        logger.error(f"Error fetching signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)