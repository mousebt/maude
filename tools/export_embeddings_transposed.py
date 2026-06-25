import os
import csv
import numpy as np
from dotenv import load_dotenv
from zhipuai import ZhipuAI

# 加载配置
load_dotenv()
api_key = os.getenv("ZHIPU_API_KEY")

if not api_key:
    print("未找到 ZHIPU_API_KEY，请检查 .env 文件。")
    exit(1)

# 初始化客户端
client = ZhipuAI(api_key=api_key)

# 单词列表
words = ["国王", "男性", "女性", "王后", "医疗", "器械", "苹果", "Apple"]
print(f"正在获取词向量并准备转置输出...")

# 获取 Embedding
response = client.embeddings.create(
    model="embedding-3",
    input=words
)

# 提取所有单词的向量并组织成 2D 数组 (8 words x 2048 dims)
all_embeddings = [data.embedding for data in response.data]

# 转置操作: 将其变为 (2048 dims x 8 words)
# 使用 zip(*list) 是 Python 中转置矩阵的简洁写法
transposed_data = list(zip(*all_embeddings))

csv_path = "e:\\pythonProject\\MAUDE\\word_embeddings_2048_transposed.csv"

try:
    with open(csv_path, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        
        # 第一行是表头: Dimension, 国王, 男性, 女性, 王后, ...
        header = ["Dimension"] + words
        writer.writerow(header)
        
        # 写入 2048 行数据
        for i, dim_values in enumerate(transposed_data):
            row = [f"Dim_{i}"] + list(dim_values)
            writer.writerow(row)
            
    print(f"成功将转置后的向量数据保存至: {csv_path}")
    print("现在每一列代表一个词，每一行代表一个维度，Excel 计算公式会更方便（如：=B2-C2+D2）。")

except Exception as e:
    print(f"保存文件时出错: {e}")
