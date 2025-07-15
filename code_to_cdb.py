import json
import pandas as pd
import sqlite3

input_json = "filtered.json"      # 原始文件


with open(input_json, "r", encoding="utf-8") as f:
    lua = json.load(f)

conn = sqlite3.connect('cards_all.cdb')
db = pd.read_sql_query(
        "SELECT * FROM merged_cards",
        conn
    )
if 'code' not in db.columns:
    db['code'] = ''

for item in lua:
    mask = db['id'].astype(str) == str(item['id'])
    db.loc[mask, 'code'] = item['code']

db.to_sql('all', conn, if_exists='replace', index=True)
# 关闭连接
conn.close()