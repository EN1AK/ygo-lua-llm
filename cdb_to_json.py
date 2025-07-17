import pandas as pd
import sqlite3
import json

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
    output_cn = f"{row['code']}"
    records.append(json.dumps({"instruction": instruction_cn, "output": output_cn}, ensure_ascii=False))

    # 日文
    instruction_jp = f"下面是卡片的信息，请根据这些信息生成lua脚本：\nカード名：{row['name_jp']},効果：{row['desc_jp']},{tag},卡密为{row['id']}"
    output_jp = f"{row['code']}"
    records.append(json.dumps({"instruction": instruction_jp, "output": output_jp}, ensure_ascii=False))


def replace_circled_numbers(text):
    circled_map = {
        '①': '1', '②': '2', '③': '3', '④': '4', '⑤': '5',
        '⑥': '6', '⑦': '7', '⑧': '8', '⑨': '9', '⑩': '10',
    }
    for k, v in circled_map.items():
        text = text.replace(k, v)
    return text


new_records = []
for line in records:
    obj = json.loads(line)
    if "instruction" in obj:
        obj["instruction"] = replace_circled_numbers(obj["instruction"])
    # 如果你想处理多个字段，可以在这里加
    new_records.append(json.dumps(obj, ensure_ascii=False))

with open('finetune_data.jsonl', 'w', encoding='utf-8') as f:
    for line in new_records:
        f.write(line + '\n')
