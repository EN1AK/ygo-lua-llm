import pandas as pd
import sqlite3
import json
import os
from map import RACE_MAP, TYPE_MAP, CATEGORY_TAGS, TYPE_LINK, LINK_MARKERS, SETNAME_MAP, ATTR_MAP, TYPE_PENDULUM,TYPE_MONSTER

folder_path = "./ygopro-scripts"
output_json = "lua.json"
result_list = []

for root, dirs, files in os.walk(folder_path):
    for file in files:
        if file.endswith(".lua"):
            file_path = os.path.join(root, file)
            with open(file_path, "r", encoding="utf-8") as f:
                code_lines = f.readlines()
                # id: 文件名去掉第一个c
                id_val = file
                if id_val.startswith('c'):
                    id_val = id_val[1:-4]
                # name: 第一行注释去掉--
                if code_lines:
                    first_line = code_lines[0].strip()
                    if first_line.startswith('--'):
                        name_val = first_line.lstrip('-').strip()
                        code_body = "".join(code_lines[1:])  # 去掉第一行
                    else:
                        name_val = ""
                        code_body = "".join(code_lines)      # 不去掉
                else:
                    name_val = ""
                    code_body = ""
                result_list.append({
                    "id": id_val,
                    "name": name_val,
                    "code": code_body
                })

with open(output_json, "w", encoding="utf-8") as out_f:
    json.dump(result_list, out_f, ensure_ascii=False, indent=2)


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

input_json = "lua.json"      # 原始文件

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

conn = sqlite3.connect('cards_all.cdb')
df = pd.read_sql_query(
    "SELECT * FROM 'all'",
    conn
)
print(df.shape)

df= df.replace("", pd.NA).dropna()

print(df.shape)

def parse_flags(value, mapping):
    return [name for bit, name in mapping.items() if value & bit]


def parse_category(cat):
    return [CATEGORY_TAGS[1100 + i] for i in range(64) if (cat >> i) & 1 and (1100 + i) in CATEGORY_TAGS]


def parse_setcode(setcode, name_map):
    # 1. 转成大写十六进制字符串
    hex_str = f"{setcode:X}"
    # 2. 左侧补零，使长度成为 4 的倍数
    pad_len = (-len(hex_str)) % 4
    if pad_len:
        hex_str = hex_str.zfill(len(hex_str) + pad_len)
    # 3. 每 4 位一组
    names = []
    for i in range(0, len(hex_str), 4):
        segment = hex_str[i:i + 4]
        # 全 0 的段跳过
        if segment == "0000":
            continue
        code = int(segment, 16)
        if code in name_map:
            names.append(name_map[code])
    return names
def extract_arrows(def_value):
    """
    从 link_marker 的整数值中提取出 所有 生效的箭头符号，返回一个列表。
    """
    return [sym for bit, sym in LINK_MARKERS.items() if def_value & bit]

def card_to_tags(row):
    type_names = parse_flags(row["type"], TYPE_MAP)
    is_link = bool(row["type"] & TYPE_LINK)
    is_pendulum = bool(row["type"] & TYPE_PENDULUM)
    is_monster = bool(row["type"] & TYPE_MONSTER)
    if not is_monster:
        atk_val = ""
        def_val = ""
        level = ""
        scale = ""
        attr = ""
        race = ""
    else:
        # 怪兽卡才处理 -2 → “？”
        atk_val = "？" if row["atk"] == -2 else row["atk"]
        # 链接怪兽没有守备，其它怪兽按 -2 转换
        if is_link:
            def_val = ""
        else:
            def_val = "？" if row["def"] == -2 else row["def"]
        # 等级/阶级
        level = row["level"] & 0xFF
        # 刻度只有灵摆怪兽才有
        scale = (row["level"] >> 24) & 0xFF if is_pendulum else ""
        attr = ATTR_MAP.get(row["attribute"], f"0x{row['attribute']:X}")
        race = RACE_MAP.get(row["race"], f"0x{row['race']:X}")
    arrows = extract_arrows(row["def"]) if is_link else []

    result = {
        "中文卡名": row["name_cn"],
        "日文卡名": row["name_jp"],
        "攻击": atk_val,
        "守备": def_val,
        "等级/阶级/link值": level,
        "箭头": arrows,
        "刻度": scale,
        "类型": type_names,
        "属性": attr,
        "种族": race,
        "效果标签": parse_category(row["category"]),
        "系列": parse_setcode(row["setcode"], SETNAME_MAP),
    }
    # 仅保留值非空的字段
    filtered = {k: v for k, v in result.items() if v not in ("", [], None)}
    return filtered


df['tag'] = df.apply(lambda row: json.dumps(card_to_tags(row), ensure_ascii=False), axis=1)
print(df.head)
df.to_sql('tag', conn, if_exists='replace', index=True)
# 关闭连接
conn.close()

conn = sqlite3.connect('cards_all.cdb')
df = pd.read_sql_query(
    "SELECT * FROM 'tag'",
    conn
)
print(df.shape)

records = []
def tag_to_nl(tag):
    if isinstance(tag, str):
        tag = json.loads(tag)

    parts = []
    if "攻击" in tag and tag["攻击"] not in ("", None):
        parts.append(f"攻击：{tag['攻击']}")
    if "守备" in tag and tag["守备"] not in ("", None):
        parts.append(f"守备：{tag['守备']}")
    if "等级/阶级/link值" in tag and tag["等级/阶级/link值"] not in ("", None):
        parts.append(f"等级/阶级/Link值：{tag['等级/阶级/link值']}")
    if "箭头" in tag and tag["箭头"]:
        if isinstance(tag["箭头"], list):
            parts.append(f"箭头：{','.join(str(a) for a in tag['箭头'])}")
        else:
            parts.append(f"箭头：{tag['箭头']}")
    if "刻度" in tag and tag["刻度"] not in ("", None):
        parts.append(f"刻度：{tag['刻度']}")
    if "类型" in tag and tag["类型"]:
        if isinstance(tag["类型"], list):
            parts.append(f"类型：{'、'.join(tag['类型'])}")
        else:
            parts.append(f"类型：{tag['类型']}")
    if "属性" in tag and tag["属性"]:
        parts.append(f"属性：{tag['属性']}")
    if "种族" in tag and tag["种族"]:
        parts.append(f"种族：{tag['种族']}")
    if "效果标签" in tag and tag["效果标签"]:
        if isinstance(tag["效果标签"], list):
            parts.append(f"效果标签：{'、'.join(tag['效果标签'])}")
        else:
            parts.append(f"效果标签：{tag['效果标签']}")
    if "系列" in tag and tag["系列"]:
        parts.append(f"系列：{tag['系列']}")
        # 你可以加入更多字段
    return '，'.join(parts)


for _, row in df.iterrows():
    tag = tag_to_nl(row['tag'])
    # 中文
    instruction_cn = f"下面是卡片的信息，请根据这些信息生成lua脚本：\n卡名：{row['name_cn']},效果文本：{row['desc_cn']},{tag},卡密为{row['id']}"
    output_cn = f"[CN] {row['code']}"
    records.append(json.dumps({"instruction": instruction_cn, "output": output_cn}, ensure_ascii=False))

    # 日文
    instruction_jp = f"下面是卡片的信息，请根据这些信息生成lua脚本：\nカード名：{row['name_jp']},効果：{row['desc_jp']},{tag},卡密为{row['id']}"
    output_jp = f"[JP] {row['code']}"
    records.append(json.dumps({"instruction": instruction_jp, "output": output_jp}, ensure_ascii=False))

# 写入文件，每行为一条训练数据
with open('finetune_data.jsonl', 'w', encoding='utf-8') as f:
    for line in records:
        f.write(line + '\n')