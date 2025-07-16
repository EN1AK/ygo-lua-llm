# Yu-Gi-Oh! Lua Script Generation 微调项目

本项目旨在基于 DeepSeek Coder 1.3B-Instruct 模型，实现“根据卡片信息自动生成 Yu-Gi-Oh! 卡牌 Lua 脚本”的指令微调流程。

---

## 目录

- [数据构建](#数据构建)
    - [获取原始数据](#获取原始数据)
    - [数据处理与格式](#数据处理与格式)
- [模型微调](#模型微调)
    - [训练环境](#训练环境)
    - [训练参数](#训练参数)
- [性能评测](#性能评测)

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

2. **下载脚本仓库：**
    ```bash
    git clone https://github.com/mycard/ygopro-scripts.git
    ```

### 数据处理与格式

3. **运行数据构造脚本：**
    ```bash
    python all_in_one.py
    ```

4. **最终生成的训练数据格式如下（JSONL，每行为一条训练样本）：**

    - `instruction` 示例：  
      ```
      下面是卡片的信息，请根据这些信息生成lua脚本：{name},{desc}，{tag},卡密为{id}
      ```
    - `output` 示例：  
      ```
      <cn/jp标识> {code}
      ```
（这里也提供可以直接使用的数据集：https://huggingface.co/datasets/en1ak/ygo_lua）

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
    --save_strategy "steps" \
    --save_steps 1000 \
    --save_total_limit 5 \
    --learning_rate 2e-5 \
    --warmup_steps 10 \
    --logging_steps 100 \
    --lr_scheduler_type "cosine" \
    --gradient_checkpointing True \
    --report_to "tensorboard" \
    --deepspeed configs/ds_config_zero3.json \
    --bf16 True
