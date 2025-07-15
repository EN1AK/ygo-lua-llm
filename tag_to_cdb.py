import pandas as pd
import sqlite3
from map import RACE_MAP, TYPE_MAP, CATEGORY_TAGS, TYPE_LINK, LINK_MARKERS, SETNAME_MAP, ATTR_MAP, TYPE_PENDULUM,TYPE_MONSTER
import json
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

