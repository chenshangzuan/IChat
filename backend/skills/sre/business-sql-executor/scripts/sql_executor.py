#!/usr/bin/env python3
"""
Business SQL Executor
Usage: python sql_executor.py "SELECT ..."
Output: JSON {"columns": [...], "rows": [[...]], "count": N}
        or   {"error": "..."}
"""

import json
import sys

import pymysql
import pymysql.cursors

# ── 数据库连接配置（请替换为实际值）──────────────────────────────────────
DB_CONFIG: dict = {
    "host": "10.89.0.14",
    "port": 30602,
    "user": "root",
    "password": "uEXsn7NZrusBIGKe",
    # database 不设置，支持跨库联表查询；SQL 中使用 db.table 格式引用表
    "charset": "utf8mb4",
    "connect_timeout": 10,
    "cursorclass": pymysql.cursors.DictCursor,
}
# ─────────────────────────────────────────────────────────────────────────


def run_sql(sql: str) -> dict:
    sql = sql.strip()
    first_token = sql.split()[0].upper() if sql.split() else ""
    if first_token != "SELECT":
        return {"error": f"Only SELECT statements are allowed, got: {first_token}"}

    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            rows_raw = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = [[row[col] for col in columns] for row in rows_raw]
            return {"columns": columns, "rows": rows, "count": len(rows)}
    finally:
        conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: sql_executor.py <SQL>"}))
        sys.exit(1)

    result = run_sql(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, default=str))
    if "error" in result:
        sys.exit(1)
