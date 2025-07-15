import pandas as pd
import sqlite3


def load_card_database(path: str = None) -> pd.DataFrame:
    db_file = path
    conn = sqlite3.connect(db_file)
    datas = pd.read_sql_query(
        "SELECT id, type, atk, def, level, race, attribute, category, setcode FROM datas",
        conn
    )
    texts = pd.read_sql_query(
        "SELECT id, name,desc FROM texts",
        conn
    )
    conn.close()

    # merge 按照 id 拼接
    df = pd.merge(datas, texts, on="id", how="inner")
    df = (
        df
        .sort_values("id")
        .drop_duplicates(subset="name", keep="first")
        .set_index("id")
    )
    return df


db_cn = load_card_database('./cdb_cn/cards.cdb')
db_jp = load_card_database('./cdb_jp/cards.cdb')
db_cn_renamed = db_cn.rename(columns={'name': 'name_cn', 'desc': 'desc_cn'}).reset_index()
db_jp_renamed = db_jp.rename(columns={'name': 'name_jp', 'desc': 'desc_jp'}).reset_index()

merged = pd.merge(
    db_cn_renamed,
    db_jp_renamed[['id', 'name_jp', 'desc_jp']],
    on='id',
    how='inner'
)

# 保留 id 为索引
merged = merged.set_index('id')
conn = sqlite3.connect('cards_all.cdb')

# 写入DataFrame（假设merged已经准备好，id为索引）
merged.to_sql('merged_cards', conn, if_exists='replace', index=True)

# 关闭连接
conn.close()
