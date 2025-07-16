import json
import os
import random
import sys
import argparse
import time

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pandas as pd
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained('Qwen/QwQ-32B')
print(f"正在加载模型分词器: Qwen/QwQ-32B")
filename = "finetune_data.jsonl"

token_counts = []
with open(filename, "r", encoding="utf-8") as f:
    for idx, line in enumerate(f, 1):
        obj = json.loads(line)
        # 你可以只统计instruction、output或合成后的文本
        text = obj.get("instruction", "") + obj.get("output", "")
        tokens = tokenizer.encode(text)
        token_counts.append(len(tokens))

print(f"平均token数: {sum(token_counts)/len(token_counts):.2f}")
print(f"最大token数: {max(token_counts)}")
print(f"最小token数: {min(token_counts)}")
print(f"总token数: {sum(token_counts)}")