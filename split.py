from datasets import load_dataset
import pandas as pd

# 1. 加载jsonl数据
dataset = load_dataset('json', data_files='finetune_data_both.jsonl', split='train')

# 2. 划分train/test
split_dataset = dataset.train_test_split(test_size=0.1, shuffle=True, seed=42)
train_dataset = split_dataset['train']
test_dataset = split_dataset['test']

# 3. 保存为jsonl（先保存，内容是unicode编码）
train_dataset.to_json('train_tmp.jsonl', orient='records', lines=True)
test_dataset.to_json('test_tmp.jsonl', orient='records', lines=True)

# 4. 用pandas重新保存为可读汉字
for in_file, out_file in [('train_tmp.jsonl', 'train_both.jsonl'), ('test_tmp.jsonl', 'test_both.jsonl')]:
    df = pd.read_json(in_file, lines=True)
    df.to_json(out_file, force_ascii=False, orient='records', lines=True)
