# Yu-Gi-Oh! Lua Script Generation 微调项目

本项目旨在基于 DeepSeek Coder 1.3B-Instruct 模型，实现“根据卡片信息自动生成 Yu-Gi-Oh! 卡牌 Lua 脚本”的指令微调流程。

模型链接：https://huggingface.co/en1ak/ygo-lua-coder

---

## 目录

- [数据构建](#数据构建)
    - [获取原始数据](#获取原始数据)
    - [数据处理与格式](#数据处理与格式)
- [模型微调](#模型微调)
    - [训练环境](#训练环境)
    - [训练参数](#训练参数)
- [性能评测](#性能评测)
- [小记](#小记)
---

## 数据构建

### 获取原始数据

1. **下载中/日文卡片数据库：**
    ```bash
    cd ./cdb_cn
    wget -O cards.cdb https://cdn02.moecube.com:444/ygopro-database/zh-CN/cards.cdb

    cd ./cdb_jp
    wget -O cards.cdb https://cdn02.moecube.com:444/ygopro-database/ja_JP/cards.cdb
    ```

2. **下载lua脚本：**
    ```bash
    git clone https://github.com/mycard/ygopro-scripts.git
    ```

### 数据处理与格式

3. **运行数据构造脚本：**
    ```bash
    python all_in_one.py
    ```

4. **最终生成的训练数据格式如下（JSONL，每行为一条训练样本）：**

    - `instruction`：  
      ```
      下面是卡片的信息，请根据这些信息生成lua脚本：{name},{desc},{tag},卡密为{id}
      ```
    - `output`：  
      ```
      {code}
      ```
训练集token总数约为20m，平均每条1k，最大token数3019

这里也提供可以直接使用的数据集：https://huggingface.co/datasets/en1ak/ygo_lua

---

## 模型微调

### 训练环境

- **基座模型**： [deepseek-coder-1.3b-instruct](https://huggingface.co/deepseek-ai/deepseek-coder-1.3b-instruct)
- **训练脚本**：官方 `finetune_deepseekcoder.py`
- **GPU**：NVIDIA RTX 5090

### 训练参数

```bash
deepspeed finetune.py \
    --model_name_or_path $MODEL_PATH \
    --data_path $DATA_PATH \
    --output_dir $OUTPUT_PATH \
    --num_train_epochs 3 \
    --model_max_length 4096 \
    --per_device_train_batch_size 8 \
    --per_device_eval_batch_size 1 \
    --gradient_accumulation_steps 4 \
    --evaluation_strategy "no" \
    --save_strategy "epoch" \
    --save_total_limit 5 \
    --learning_rate 2e-5 \
    --warmup_steps 10 \
    --logging_steps 100 \
    --lr_scheduler_type "cosine" \
    --gradient_checkpointing True \
    --report_to "tensorboard" \
    --deepspeed configs/ds_config_zero3.json \
    --bf16 True
```

## 性能评测

| 模型路径       | ROUGE-1 | ROUGE-2 | ROUGE-L | BLEU   | BERTScore Precision | BERTScore Recall | BERTScore F1 |
|------------|---------|---------|---------|--------|---------------------|------------------|--------------|
| base model | 0.0753  | 0.0125  | 0.0539  | 0.0010 | 0.6216              | 0.6621           | 0.6400       |
| on_cn+jp   | 0.4603  | 0.4214  | 0.4302  | 0.1183 | 0.8841              | 0.8541           | 0.8673       |
| on_cn      | 0.3042  | 0.2610  | 0.2750  | 0.0769 | 0.7955              | 0.7647           | 0.7767       |


## 小记
一次小小的练手项目，熟悉了大模型微调的流程。


1：我进行了两次训练，第一次是双语资料，没有去除特殊字符（如①/「/α/●等），与此同时，我还发现deepseek-coder没有日语能力（仅在英语以及中文语料上训练）

意识到这一点后，第二次训练仅用了中文语料，且去除并替代了一部分特殊字符（如①替换为1），尽管如此，如表格所示，使用了双语训练的模型表现更好

2：实际上，deepseek等ai的能力可以非常轻松地从lua脚本翻译为k语言，正确率也非常高（主要问题在编造卡名和字段上），但是反向操作却非常困难


### 可以改进的地方：
完整效果及其对应的lua脚本比较长，学习起来可能比较困难，可以通过人为构造一些简单的效果及其对应的lua脚本作为训练数据，如：
```bash
这张卡召唤/特殊召唤/反转成功时 丢弃/送墓/除外/送回一张手卡可以发动 破坏/表侧除外/里侧除外/送入墓地/弹回手卡/卡组对手场上一张盖放的/表侧表示的怪兽卡/魔法陷阱卡
```
