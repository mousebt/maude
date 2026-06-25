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

# 定义要转换的单词列表
words = ["国王", "男性", "女性", "王后", "医疗", "器械", "苹果", "Apple"]
print(f"正在获取以下单词的 2048 维向量: {words}")

# 获取 Embedding
response = client.embeddings.create(
    model="embedding-3",
    input=words
)

# 准备写入 CSV
# 表头格式: Word, Dim_0, Dim_1, ..., Dim_2047
header = ["Word"] + [f"Dim_{i}" for i in range(2048)]
csv_path = "e:\\pythonProject\\MAUDE\\word_embeddings_2048.csv"

try:
    with open(csv_path, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        
        for i, data in enumerate(response.data):
            # 将单词和 2048 个浮点数拼接成一行
            row = [words[i]] + data.embedding
            writer.writerow(row)
            
    print(f"成功将向量数据保存至: {csv_path}")
    print("你可以直接用 Excel 打开该文件进行计算测试。")

except Exception as e:
    print(f"保存文件时出错: {e}")
