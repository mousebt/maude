# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import pickle
import argparse
import pandas as pd
import requests
from dotenv import load_dotenv

# 获取基准目录并加载环境配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(BASE_DIR, ".env")
load_dotenv(env_path)

DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')

# Unicode 列名定义，彻底免疫 Windows 环境乱码
ZH_MODEL = '\u578b\u53f7'        # 型号
ZH_SPEC = '\u89c4\u683c'         # 规格
ZH_ID = '\u62a5\u544a\u7f16\u7801' # 报告编码

def check_missing(val):
    """判断一个值是否缺失"""
    if pd.isna(val):
        return True
    val_str = str(val).strip()
    if val_str == '' or val_str.lower() in ['nan', 'null', 'none']:
        return True
    return False

def extract_model_from_text(text, model="deepseek-chat"):
    """调用大语言模型从中文自述文本中提取明确提到的型号和规格"""
    url = f"{DEEPSEEK_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = """你是一个专业的医疗器械数据清洗与信息提取专家。
请仔细阅读给出的吻合器不良事件中文描述，并从中提取文本中【明确提及】的器械型号和规格参数。
注意：
1. 必须是文本中显式写出来的（例如提到“型号：CDH29”、“使用EC60A吻合器”、“蓝色钉仓”等）。
2. 绝对不能凭空推测或臆造！如果文本中没有明确提到，请在 JSON 中对应字段返回 null。
3. 请将提取结果规范化：型号应提取为器械字母+数字组合（如 CDH29, EC60A 等），规格应提取为具体参数（如 29mm, 60mm 等）。

请严格按照以下 JSON 格式返回，不要包含任何 markdown 块或解释性前言后语：
{
  "extracted_model": "提取的具体型号 (若无则为 null)",
  "extracted_spec": "提取的规格参数 (若无则为 null)"
}"""

    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a professional medical data extractor. Always output strict JSON format."},
            {"role": "user", "content": f"{prompt}\n\n【不良事件文本描述】:\n{text}"}
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=20)
        if response.status_code == 200:
            res_json = response.json()
            content = json.loads(res_json['choices'][0]['message']['content'])
            return content
        else:
            print(f"    [LLM-ERR] HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"    [LLM-ERR] 异常: {e}")
    return {"extracted_model": None, "extracted_spec": None}

def main():
    parser = argparse.ArgumentParser(description="Extract missing model and spec from narrative texts")
    parser.add_argument("--test-limit", type=int, default=None, help="限制处理的缺失记录条数")
    args = parser.parse_args()
    
    data_dir = os.path.join(BASE_DIR, "stapler_research", "data")
    aligned_pkl = os.path.join(data_dir, "target_aligned.pkl")
    progress_pkl = os.path.join(data_dir, "model_filling_progress.pkl")
    
    if not os.path.exists(aligned_pkl):
        print(f"❌ 错误: 未找到对齐后的数据集: {aligned_pkl}")
        sys.exit(1)
        
    # 1. 加载对齐数据
    df = pd.read_pickle(aligned_pkl)
    
    # 动态匹配列名以防万一
    col_id = [c for c in df.columns if ZH_ID in c][0]
    col_model = [c for c in df.columns if ZH_MODEL in c][0]
    col_spec = [c for c in df.columns if ZH_SPEC in c][0]
    
    # 2. 筛选出型号或规格缺失的记录
    df_missing = df[df[col_model].apply(check_missing) | df[col_spec].apply(check_missing)]
    
    total_missing = len(df_missing)
    print(f">>> 大盘中共有 {total_missing} 条记录缺失 [型号] 或 [规格] 字段 (共 {len(df)} 条)。")
    
    if total_missing == 0:
        print("  所有记录的型号和规格均已完整，无须填补。")
        return
        
    # 3. 读取已填补进度 (支持断点续传)
    if os.path.exists(progress_pkl):
        print(f"  发现已有填补进度备份，正在加载: {progress_pkl}")
        with open(progress_pkl, 'rb') as f:
            filled_records = pickle.load(f)
        print(f"  已成功加载 {len(filled_records)} 条已填补记录。")
    else:
        filled_records = {}
        
    # 4. 开始提取并填补
    unprocessed_df = df_missing[~df_missing[col_id].isin(filled_records.keys())]
    if args.test_limit:
        unprocessed_df = unprocessed_df.head(args.test_limit)
        print(f"  [测试模式] 仅处理前 {args.test_limit} 条缺失记录。")
        
    to_process_count = len(unprocessed_df)
    print(f"  本次待处理缺失记录: {to_process_count} 条。")
    
    if to_process_count == 0:
        print("  待处理数据已在进度中全部完成，直接写入大盘...")
    else:
        count = 0
        t_start = time.time()
        for idx, row in unprocessed_df.iterrows():
            report_id = row[col_id]
            text = row["nanjing_text_combined"]
            
            # 调用大模型提取
            res = extract_model_from_text(text)
            
            filled_records[report_id] = {
                "extracted_model": res.get("extracted_model"),
                "extracted_spec": res.get("extracted_spec")
            }
            
            count += 1
            # 实时备份防止崩溃
            if count % 10 == 0 or count == to_process_count:
                with open(progress_pkl, 'wb') as f:
                    pickle.dump(filled_records, f)
                avg_speed = (time.time() - t_start) / count
                print(f"  [填补进度] 已处理 {count}/{to_process_count} 条... 均速: {avg_speed:.2f}秒/条，已持久化备份。")
                
            time.sleep(0.5)
            
        print(f"\n>>> 文本提取处理结束，共耗时: {time.time() - t_start:.2f} 秒。")
        
    # 5. 将结果回填写入大盘 DataFrame
    print("\n>>> 正在将提取到的型号/规格回填写入 target_aligned.pkl ...")
    model_fill_count = 0
    spec_fill_count = 0
    
    for idx, row in df.iterrows():
        report_id = row[col_id]
        if report_id in filled_records:
            ext_model = filled_records[report_id]["extracted_model"]
            ext_spec = filled_records[report_id]["extracted_spec"]
            
            # 回填型号
            if check_missing(row[col_model]) and ext_model:
                df.at[idx, col_model] = ext_model
                model_fill_count += 1
                
            # 回填规格
            if check_missing(row[col_spec]) and ext_spec:
                df.at[idx, col_spec] = ext_spec
                spec_fill_count += 1
                
    # 6. 保存最终对齐大盘
    with open(aligned_pkl, 'wb') as f:
        pickle.dump(df, f)
        
    # 7. 统计最终填补覆盖率
    final_null_model = df[col_model].apply(check_missing).sum()
    final_null_spec = df[col_spec].apply(check_missing).sum()
    
    print("\n================== 描述性文本填补成果汇总 ==================")
    print(f"  - 从自述文本中成功填补的 [型号] 数量: {model_fill_count} 条")
    print(f"  - 从自述文本中成功填补的 [规格] 数量: {spec_fill_count} 条")
    print(f"  - 填补后 [型号] 剩余缺失数          : {final_null_model} 条 (总数 {len(df)})")
    print(f"  - 填补后 [规格] 剩余缺失数          : {final_null_spec} 条 (总数 {len(df)})")
    print("==========================================================")

if __name__ == '__main__':
    main()
