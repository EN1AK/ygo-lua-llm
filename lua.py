import os
import json

folder_path = "./ygopro-scripts"  # 替换为你的文件夹路径
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

print(f"已保存到 {output_json}")
