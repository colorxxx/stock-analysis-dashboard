#!/usr/bin/env python3
"""캐시된 분석 결과를 삭제하는 스크립트"""

import sqlite3

DB_FILE = "stock_data.db"

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute("DELETE FROM perplexity_analysis")
deleted = cursor.rowcount

conn.commit()
conn.close()

print(f"✅ {deleted}개의 캐시된 분석 결과를 삭제했습니다.")
