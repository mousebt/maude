import os
import sys
import json
import time
import pickle
import argparse
import numpy as np
import pandas as pd
import pymysql
import requests
from dotenv import load_dotenv

# 加载环境配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(BASE_DIR, ".env")
load_dotenv(env_path)

DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASSWORD', '123456')
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_NAME = os.getenv('DB_NAME') or 'maude_db'

DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')

OPENROUTER_KEY = os.getenv('OPENROUTER_KEY')
OPENROUTER_BASE_URL = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
OPENROUTER_EMBEDDING_MODEL = os.getenv('OPENROUTER_EMBEDDING_MODEL', 'openai/text-embedding-3-small')

def get_db_connection():
    """连接本地 MySQL 数据库"""
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        database=DB_NAME,
        charset='utf8mb4'
    )

def fetch_imdrf_dictionary():
    """从数据库中提取所有非空的官方 IMDRF 器械问题对照字典"""
    print(">>> 正在从本地数据库提取 IMDRF 官方字典 (fda_device_problem_mapping)...")
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """
        SELECT FDA_CODE, TERM, IMDRF_CODE 
        FROM fda_device_problem_mapping 
        WHERE IMDRF_CODE IS NOT NULL AND IMDRF_CODE != ''
    """
    cursor.execute(sql)
    rows = cursor.fetchall()
    conn.close()
    
    # 格式化为字典: {fda_code: {"term_en": term_en, "imdrf_code": imdrf_code}}
    imdrf_dict = {}
    for row in rows:
        fda_code, term_en, imdrf_code = row
        imdrf_dict[fda_code] = {
            "term_en": term_en.strip(),
            "imdrf_code": imdrf_code.strip()
        }
    print(f"  [完成] 共加载 {len(imdrf_dict)} 条有效 IMDRF 字典映射。")
    return imdrf_dict

def translate_imdrf_terms_batch(imdrf_dict, batch_size=50):
    """使用 DeepSeek-Chat 大模型批量将字典中的英文术语翻译成中文，以减少 API 请求次数"""
    print(f"\n>>> 正在使用大模型批量翻译字典术语 (每批 {batch_size} 条)...")
    if not DEEPSEEK_API_KEY:
        raise ValueError("未在环境变量中配置 DEEPSEEK_API_KEY")
        
    items = list(imdrf_dict.items())
    translated_dict = {}
    
    # 每次翻译 batch_size 条
    for i in range(0, len(items), batch_size):
        chunk = items[i:i+batch_size]
        payload_list = [{"fda_code": fda_code, "term_en": data["term_en"]} for fda_code, data in chunk]
        
        prompt = """你是一个专业的医疗器械监管与临床医学翻译专家。
下面是一个 JSON 数组，包含英文的医疗器械故障/不良事件术语（term_en）和其对应代码（fda_code）。
请将这些英文术语翻译为精确、地道且符合中国医疗器械警戒规范的中文术语。
不要对术语进行任何额外的长篇大论或解释，直接返回翻译。
必须且只能返回以下格式的 JSON 对象，包含 "translations" 数组，无须任何 markdown 标记或前后文字：
{
  "translations": [
    {"fda_code": "代码", "term_zh": "中文术语"}
  ]
}"""

        url = f"{DEEPSEEK_BASE_URL.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a professional medical translator. Always output strict JSON format."},
                {"role": "user", "content": f"{prompt}\n\n【待翻译术语】:\n{json.dumps(payload_list, ensure_ascii=False)}"}
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }
        
        print(f"  正在翻译第 {i+1} 至 {min(i+batch_size, len(items))} 条术语...")
        retry = 3
        while retry > 0:
            try:
                response = requests.post(url, headers=headers, json=data, timeout=30)
                if response.status_code == 200:
                    res_json = response.json()
                    content = json.loads(res_json['choices'][0]['message']['content'])
                    for item in content.get("translations", []):
                        fda_code = item["fda_code"]
                        term_zh = item["term_zh"]
                        if fda_code in imdrf_dict:
                            translated_dict[fda_code] = {
                                "imdrf_code": imdrf_dict[fda_code]["imdrf_code"],
                                "term_en": imdrf_dict[fda_code]["term_en"],
                                "term_zh": term_zh.strip()
                            }
                    break
                else:
                    print(f"    [警告] 调用翻译接口失败 (HTTP {response.status_code}): {response.text}，正在重试...")
            except Exception as e:
                print(f"    [警告] 翻译异常: {e}，正在重试...")
            retry -= 1
            time.sleep(1)
            
        time.sleep(0.5) # 适当限频
        
    print(f"  [完成] 翻译完成，共成功翻译 {len(translated_dict)} 条术语。")
    return translated_dict

def get_openrouter_embeddings(texts, batch_size=100):
    """通过 OpenRouter 计算文本列表的 Embedding 向量"""
    if not OPENROUTER_KEY:
        raise ValueError("未在环境变量中配置 OPENROUTER_KEY")
        
    url = f"{OPENROUTER_BASE_URL.rstrip('/')}/embeddings"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json"
    }
    
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        chunk = texts[i:i+batch_size]
        payload = {
            "model": OPENROUTER_EMBEDDING_MODEL,
            "input": chunk
        }
        
        retry = 3
        while retry > 0:
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                if response.status_code == 200:
                    res_json = response.json()
                    embeddings = [item['embedding'] for item in res_json['data']]
                    all_embeddings.extend(embeddings)
                    break
                else:
                    print(f"    [警告] 计算 Embedding 失败 (HTTP {response.status_code}): {response.text}，正在重试...")
            except Exception as e:
                print(f"    [警告] 计算 Embedding 异常: {e}，正在重试...")
            retry -= 1
            time.sleep(1)
            
        time.sleep(0.5)
        
    return all_embeddings

def build_dictionary_embeddings(translated_dict, cache_path):
    """为字典中的中英文术语计算向量表示，并持久化缓存起来"""
    print("\n>>> 正在构建字典的语义 Embedding 缓存...")
    
    fda_codes = list(translated_dict.keys())
    en_texts = [translated_dict[code]["term_en"] for code in fda_codes]
    zh_texts = [translated_dict[code]["term_zh"] for code in fda_codes]
    
    print(f"  正在计算 {len(en_texts)} 个英文术语的 Embedding...")
    en_embeddings = get_openrouter_embeddings(en_texts)
    
    print(f"  正在计算 {len(zh_texts)} 个中文术语的 Embedding...")
    zh_embeddings = get_openrouter_embeddings(zh_texts)
    
    # 组装缓存
    embedding_cache = {}
    for idx, fda_code in enumerate(fda_codes):
        embedding_cache[fda_code] = {
            "imdrf_code": translated_dict[fda_code]["imdrf_code"],
            "term_en": translated_dict[fda_code]["term_en"],
            "term_zh": translated_dict[fda_code]["term_zh"],
            "emb_en": en_embeddings[idx],
            "emb_zh": zh_embeddings[idx]
        }
        
    # 保存缓存文件
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, 'wb') as f:
        pickle.dump(embedding_cache, f)
        
    print(f"  [完成] 语义 Embedding 缓存构建完毕并保存至: {cache_path}")
    return embedding_cache

def extract_entities_with_llm(text, model="deepseek-chat"):
    """使用大语言模型从中文描述中提取关键实体"""
    url = f"{DEEPSEEK_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = """你是一个专业的医疗器械不良事件警戒分析专家。请仔细阅读给出的吻合器不良事件中文描述，从中提取出其中的结构化实体。
请严格按照给出的 JSON 格式返回以下三个字段，无需任何多余的解释或 markdown 块：
1. "device_failure_phrases": 提取文本中描述的器械故障或物理异常表现（如“卡钉”、“无法击发”、“缝合线呈扁平状”、“组件脱落”等，用列表表示，若无则为空列表）。
2. "patient_consequence_phrases": 提取文本中描述的患者临床后果或伤害表现（如“出血”、“大出血”、“吻合口瘘”、“吻合口狭窄”、“组织撕裂”等，用列表表示，若无则为空列表）。
3. "surgical_context_phrases": 提取文本中描述的手术背景信息（如“腹腔镜直肠前切除术”、“肺癌根治术”、“吻合器切除”、“开腹”等，用列表表示，若无则为空列表）。

【输出格式例】
{
  "device_failure_phrases": ["卡钉", "无法击发"],
  "patient_consequence_phrases": ["大出血"],
  "surgical_context_phrases": ["腹腔镜直肠前切除术"]
}"""

    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a professional medical data extractor. Always output strict JSON."},
            {"role": "user", "content": f"{prompt}\n\n【事件中文描述】:\n{text}"}
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=20)
        if response.status_code == 200:
            res_json = response.json()
            return json.loads(res_json['choices'][0]['message']['content'])
        else:
            print(f"    [LLM-ERR] HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"    [LLM-ERR] 发生异常: {e}")
    return {"device_failure_phrases": [], "patient_consequence_phrases": [], "surgical_context_phrases": []}

def cosine_similarity(v1, v2):
    """计算两个向量的余弦相似度"""
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return float(dot_product / (norm_v1 * norm_v2))

def align_phrase_to_imdrf(phrase, phrase_emb, dict_cache, threshold=0.75):
    """将提取出的单个短语对齐到最匹配 of 官方 IMDRF Code (方案 A: 中英文双向匹配)"""
    best_code = None
    best_term_en = None
    best_term_zh = None
    max_sim = 0.0
    
    for fda_code, info in dict_cache.items():
        # 计算该短语与字典中英文的相似度
        sim_en = cosine_similarity(phrase_emb, info["emb_en"])
        # 计算该短语与字典中中文翻译的相似度
        sim_zh = cosine_similarity(phrase_emb, info["emb_zh"])
        
        # 取最大相似度，作为该词条的匹配度
        cur_sim = max(sim_en, sim_zh)
        if cur_sim > max_sim:
            max_sim = cur_sim
            best_code = info["imdrf_code"]
            best_term_en = info["term_en"]
            best_term_zh = info["term_zh"]
            
    # 阈值过滤
    if max_sim >= threshold:
        return {
            "imdrf_code": best_code,
            "term_en": best_term_en,
            "term_zh": best_term_zh,
            "similarity": round(max_sim, 4)
        }
    else:
        return {
            "imdrf_code": "Pending/Unknown",
            "term_en": "Unknown",
            "term_zh": phrase,
            "similarity": round(max_sim, 4)
        }

def process_nanjing_alignment(df_target, dict_cache, progress_path, limit=None, threshold=0.75):
    """核心执行循环：遍历南京数据进行 LLM 提取 + Embedding 对齐，支持断点续传"""
    print(f"\n>>> 正在启动目标域南京数据的实体提取与 IMDRF 编码对齐...")
    
    # 1. 尝试读取进度缓存以实现断点续传
    if os.path.exists(progress_path):
        print(f"  发现已有进度缓存，正在加载: {progress_path}")
        with open(progress_path, 'rb') as f:
            aligned_records = pickle.load(f)
        print(f"  已成功恢复 {len(aligned_records)} 条已处理记录。")
    else:
        aligned_records = []
        
    processed_keys = {r["报告编码"] for r in aligned_records}
    
    # 过滤出未处理的数据
    unprocessed_df = df_target[~df_target["报告编码"].isin(processed_keys)]
    if limit:
        unprocessed_df = unprocessed_df.head(limit)
        print(f"  [测试模式] 限制处理前 {limit} 条记录。")
        
    total_to_process = len(unprocessed_df)
    print(f"  待处理记录数: {total_to_process} 条 (大盘共 {len(df_target)} 条)。")
    
    if total_to_process == 0:
        print("  所有记录均已对齐完成！")
        return pd.DataFrame(aligned_records)
        
    # 2. 遍历提取
    count = 0
    t_start = time.time()
    
    for idx, row in unprocessed_df.iterrows():
        report_id = row["报告编码"]
        text_content = row["nanjing_text_combined"]
        
        # A. LLM 实体提取
        extracted = extract_entities_with_llm(text_content)
        dev_phrases = extracted.get("device_failure_phrases", [])
        pat_phrases = extracted.get("patient_consequence_phrases", [])
        surg_phrases = extracted.get("surgical_context_phrases", [])
        
        # B. 为器械故障短语计算 Embedding 并进行对齐
        aligned_codes = []
        aligned_details = []
        
        if dev_phrases:
            # 一次性计算该记录所有故障短语的 Embedding
            phrase_embs = get_openrouter_embeddings(dev_phrases)
            for phrase, p_emb in zip(dev_phrases, phrase_embs):
                aligned_res = align_phrase_to_imdrf(phrase, p_emb, dict_cache, threshold)
                aligned_details.append(aligned_res)
                if aligned_res["imdrf_code"] != "Pending/Unknown":
                    aligned_codes.append(aligned_res["imdrf_code"])
                    
        # 整合为逗号隔开的编码
        imdrf_codes_str = ",".join(list(set(aligned_codes))) if aligned_codes else "Pending"
        
        record = {
            "报告编码": report_id,
            "产品名称": row.get("产品名称", ""),
            "型号": row.get("型号", ""),
            "规格": row.get("规格", ""),
            "EVENT_TYPE": row.get("EVENT_TYPE", "M"),
            "device_failure_phrases": dev_phrases,
            "patient_consequence_phrases": pat_phrases,
            "surgical_context_phrases": surg_phrases,
            "imdrf_device_codes": imdrf_codes_str,
            "alignment_details": aligned_details,
            "nanjing_text_combined": text_content
        }
        
        aligned_records.append(record)
        count += 1
        
        # C. 实时持久化备份 (每 5 条写入一次，防止程序突发崩溃丢失进度)
        if count % 5 == 0 or count == total_to_process:
            with open(progress_path, 'wb') as f:
                pickle.dump(aligned_records, f)
            avg_speed = (time.time() - t_start) / count
            print(f"  [进度] 已处理 {count}/{total_to_process} 条... 均速: {avg_speed:.2f}秒/条，已持久化备份。")
            
        # 适当延时防限流
        time.sleep(0.5)
        
    print(f"\n>>> 提取与对齐计算完成！共耗时: {time.time() - t_start:.2f} 秒。")
    return pd.DataFrame(aligned_records)

def main():
    parser = argparse.ArgumentParser(description="Experiment Step 2: LLM-based Alignment")
    parser.add_argument("--build-cache", action="store_true", help="强制重新翻译字典并构建 Embedding 缓存")
    parser.add_argument("--test-limit", type=int, default=None, help="测试模式，限制提取的南京记录条数")
    parser.add_argument("--threshold", type=float, default=0.75, help="余弦相似度匹配过滤阈值")
    args = parser.parse_args()
    
    data_dir = os.path.join(BASE_DIR, "stapler_research", "data")
    os.makedirs(data_dir, exist_ok=True)
    
    cache_path = os.path.join(data_dir, "imdrf_embedding_cache.pkl")
    progress_path = os.path.join(data_dir, "nanjing_alignment_progress.pkl")
    final_output_path = os.path.join(data_dir, "target_aligned.pkl")
    
    # ----------------- Step 1: 字典翻译与嵌入初始化 -----------------
    dict_cache = None
    if not args.build_cache and os.path.exists(cache_path):
        print(f">>> [缓存就绪] 发现已有 IMDRF 字典 Embedding 缓存: {cache_path}")
        with open(cache_path, 'rb') as f:
            dict_cache = pickle.load(f)
    else:
        # 从数据库加载字典
        imdrf_dict = fetch_imdrf_dictionary()
        # 批量翻译
        translated_dict = translate_imdrf_terms_batch(imdrf_dict)
        # 计算 Embedding 并缓存
        dict_cache = build_dictionary_embeddings(translated_dict, cache_path)
        
    # ----------------- Step 2 & 3: 数据读取、LLM 提取与余弦对齐 -----------------
    target_path = os.path.join(data_dir, "target_standardized.pkl")
    if not os.path.exists(target_path):
        print(f"❌ 错误: 目标域特征视图 {target_path} 不存在，请先运行 standardize_data.py！")
        sys.exit(1)
        
    df_target = pd.read_pickle(target_path)
    
    # 执行主程序循环
    df_aligned = process_nanjing_alignment(
        df_target, 
        dict_cache, 
        progress_path, 
        limit=args.test_limit, 
        threshold=args.threshold
    )
    
    # ----------------- Step 4: 整合并生成最终落盘数据 -----------------
    # 保存对齐结果
    df_aligned.to_pickle(final_output_path)
    print(f"\n>>> [对齐完成] 最终的对齐标准化结果已成功保存至: {final_output_path}")
    
    # 简单统计分析
    total_records = len(df_aligned)
    aligned_count = len(df_aligned[df_aligned["imdrf_device_codes"] != "Pending"])
    aligned_rate = (aligned_count / total_records) * 100 if total_records > 0 else 0
    
    print("\n================== 实验步骤二对齐统计汇总 ==================")
    print(f"  - 目标域总记录数  : {total_records} 条")
    print(f"  - 成功映射到编码数: {aligned_count} 条")
    print(f"  - 编码对齐覆盖率  : {aligned_rate:.2f}%")
    print("==========================================================")

if __name__ == '__main__':
    main()
