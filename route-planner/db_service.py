# ================================================================
# MySQL数据库服务
#
# 职责：
# - 管理用户偏好和历史记录
# - 落地版POI数据存储（替换mock_data）
# ================================================================

import mysql.connector
import json
import os


def get_connection():
    """获取MySQL连接"""
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", 3306)),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DB", "route_planner")
    )


def get_user_preference(user_id: str) -> dict:
    """
    查询用户历史偏好。
    返回：{prefer: [], avoid: [], history: []}
    无记录返回空dict。
    """
    # TODO: 数据同学B实现
    # conn = get_connection()
    # cursor = conn.cursor(dictionary=True)
    # cursor.execute("SELECT * FROM user_preferences WHERE user_id = %s", (user_id,))
    # result = cursor.fetchone()
    # return result or {}
    return {}


def save_route_history(user_id: str, user_input: str, routes: list):
    """
    保存用户路线记录。
    供下次规划时参考用户偏好。
    """
    # TODO: 数据同学B实现
    # conn = get_connection()
    # cursor = conn.cursor()
    # cursor.execute(
    #     "INSERT INTO route_history (user_id, user_input, routes, created_at) VALUES (%s, %s, %s, NOW())",
    #     (user_id, user_input, json.dumps(routes, ensure_ascii=False))
    # )
    # conn.commit()
    pass


def get_pois_from_db(city: str, filters: dict) -> list:
    """
    从数据库查询POI（落地版，替换mock_data/pois.json）。
    """
    # TODO: 数据同学B实现
    # conn = get_connection()
    # cursor = conn.cursor(dictionary=True)
    # cursor.execute("SELECT * FROM pois WHERE city = %s", (city,))
    # return cursor.fetchall()
    return []


# ================================================================
# 建表SQL（首次部署时执行）
# ================================================================
CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id VARCHAR(64) PRIMARY KEY,
    prefer JSON,
    avoid JSON,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS route_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(64),
    user_input TEXT,
    routes JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pois (
    id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(128),
    city VARCHAR(32),
    category JSON,
    cost INT,
    duration INT,
    score FLOAT,
    tags JSON,
    open_time VARCHAR(32),
    lat DOUBLE,
    lng DOUBLE
);
"""