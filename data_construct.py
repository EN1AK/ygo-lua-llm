import pandas as pd
import sqlite3

conn = sqlite3.connect('cards_all.cdb')
df = pd.read_sql_query(
    "SELECT * FROM 'all'",
    conn
)
print(df.shape)

df= df.replace("", pd.NA).dropna()

print(df.shape)

