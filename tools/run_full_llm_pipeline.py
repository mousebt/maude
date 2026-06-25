import os
import csv
import json
import time
import pymysql
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(BASE_DIR, ".env")
load_dotenv(env_path)

DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASSWORD', '123456')
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_NAME = 'davinci_death_db'

DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')

PROMPTS = {
    "Shocking": """你是一名资深的医疗器械安全与取证专家。请分析以下达芬奇手术机器人的致死事故长文本。
你的目标是提取并梳理致命性故障的物理因果链。请必须以严格的 JSON 格式输出，不要包含任何 markdown 标记或前后文字，字段如下：
{
  "hazard_category": "必须且只能为以下选项之一：能量器械漏电/电弧/击穿/灼伤、机械臂/器械部件弯曲/断裂/脱落遗留、系统死机/软件错误/黑屏/紧急报错卡死、机械臂锁死无法拔出/无法撤除、医生操作不当/经验不足/学习曲线阶段、气腹故障、起火冒烟、诉讼瞒报/做空曝光、其他机器物理故障、其他",
  "fault_component": "故障发生的手术附件或整机组件精确名称，必须精确指明涉事器械组件或耗材的完整英文/中文官方名称（如 Maryland Clamp, Hot Shears, SureForm Stapler, Vessel Sealer, Camera 等，若无提及则填'未知'）",
  "causal_chain": "事故发生的步骤演化顺序时序描述（100字内）",
  "root_cause": "引发致命伤的底层原因（例如：电刀电路短路自动放电、医生视野外盲操割裂血管、系统故障被迫紧急中转导致大出血）",
  "factual_summary": "一句话精炼事实总结（80字内）"
}""",

    "Normal": """你是一名临床医学专家，专门分析手术警戒与并发症。请分析以下达芬奇辅助手术的致死病例长文本。
你的目标是确认达芬奇系统是否在事故中充当了无辜者，并识别临床意外的真实本质。请必须以严格的 JSON 格式输出，不要包含任何 markdown 标记或前后文字，字段如下：
{
  "clinical_complication": "必须且只能为以下选项之一或其实时精炼词：大出血、吻合口漏、术后感染、脏器并发症、癌症进展恶化、术后肺栓塞、麻醉意外、术后肠梗阻、其他（若为其他，请用2-4字精准提取，如'吸入性肺炎'）",
  "robot_involvement": "无关联（机器工作完好且无阻碍） / 间接关联（如手术时间长导致患者体弱衰竭，但机器无物理故障）",
  "surgeon_decision": "医生在出血或发生并发症时是否进行了中转开腹/开胸？（YES / NO / 未提及）",
  "clinical_summary": "临床事实与致死机理解析总结（80字内）"
}""",

    "Structural_Issue": """你是一名数据挖掘与隐私清洗工程师。请分析以下达芬奇机器人事故文本。
这篇文本可能因为 FDA 删除或严重的商业和隐私脱敏而丢失了大部分内容。请帮我评估其受损情况并提取残存线索。请必须以严格的 JSON 格式输出，不要包含任何 markdown 标记或前后文字，字段如下：
{
  "data_loss_type": "被FDA要求删除 / 仅含商业脱敏掩码B4 / 仅含患者隐私掩码B6 / 极度敷衍字数不足",
  "extracted_clues": "从中能提取出的极少数线索（如涉及的特定手术名称、医院、或诉讼信息，若无则填'无'）",
  "can_be_repaired": "是否有可能通过交叉检索修复数据？（YES / NO）"
}"""
}

def init_knowledge_table():
    """
    初始化 MySQL 结构化知识表
    """
    conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, port=DB_PORT, database=DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS foi_text_knowledge (
            MDR_REPORT_KEY BIGINT PRIMARY KEY,
            CLASSIFICATION VARCHAR(50) NOT NULL,
            REASON VARCHAR(255),
            
            -- Shocking 惊悚类别专属字段
            HAZARD_CATEGORY VARCHAR(100) DEFAULT NULL,
            FAULT_COMPONENT VARCHAR(255) DEFAULT NULL,
            CAUSAL_CHAIN TEXT DEFAULT NULL,
            ROOT_CAUSE TEXT DEFAULT NULL,
            FACTUAL_SUMMARY TEXT DEFAULT NULL,
            
            -- Normal 常规类别专属字段
            CLINICAL_COMPLICATION VARCHAR(100) DEFAULT NULL,
            ROBOT_INVOLVEMENT TEXT DEFAULT NULL,
            SURGEON_DECISION VARCHAR(50) DEFAULT NULL,
            CLINICAL_SUMMARY TEXT DEFAULT NULL,
            
            -- Structural_Issue 结构问题专属字段
            DATA_LOSS_TYPE VARCHAR(100) DEFAULT NULL,
            EXTRACTED_CLUES TEXT DEFAULT NULL,
            CAN_BE_REPAIRED VARCHAR(10) DEFAULT NULL,
            
            -- API 开销度量字段
            INPUT_TOKENS INT DEFAULT 0,
            OUTPUT_TOKENS INT DEFAULT 0,
            DURATION_SECONDS FLOAT DEFAULT 0.0,
            CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    conn.commit()
    conn.close()

def call_api_with_retry(prompt, case_text, retries=3):
    """
    带指数退避重试的 API 调用
    """
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": case_text}
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }
    
    backoff = 1.0
    for attempt in range(retries):
        try:
            response = requests.post(
                f"{DEEPSEEK_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=35
            )
            if response.status_code == 200:
                res_json = response.json()
                content = res_json['choices'][0]['message']['content']
                usage = res_json.get('usage', {})
                return content, usage
            elif response.status_code == 429: # 限流
                time.sleep(backoff)
                backoff *= 2.0
            else:
                time.sleep(1.0)
        except Exception:
            time.sleep(backoff)
            backoff *= 1.5
            
    return None, {}

def process_single_case(record):
    """
    单条病案处理逻辑
    """
    m_key, rep_num, brand, cat, r_reason, text = record
    prompt = PROMPTS[cat]
    
    t0 = time.time()
    content, usage = call_api_with_retry(prompt, text)
    duration = time.time() - t0
    
    in_tokens = usage.get('prompt_tokens', 0)
    out_tokens = usage.get('completion_tokens', 0)
    
    result = {
        "mdr_key": m_key,
        "classification": cat,
        "reason": r_reason,
        "input_tokens": in_tokens,
        "output_tokens": out_tokens,
        "duration": round(duration, 2),
        "data": {}
    }
    
    if content:
        try:
            result["data"] = json.loads(content)
        except Exception:
            result["data"] = {"error_parsing": content}
    else:
        result["data"] = {"error_api": "API call failed after retries"}
        
    return result

def write_to_db(result, conn, cursor):
    """
    将处理结果持久化回 MySQL
    """
    m_key = int(result["mdr_key"])
    cat = result["classification"]
    reason = result["reason"]
    in_t = result["input_tokens"]
    out_t = result["output_tokens"]
    duration = result["duration"]
    data = result["data"]
    
    sql = """
        INSERT INTO foi_text_knowledge (
            MDR_REPORT_KEY, CLASSIFICATION, REASON,
            HAZARD_CATEGORY, FAULT_COMPONENT, CAUSAL_CHAIN, ROOT_CAUSE, FACTUAL_SUMMARY,
            CLINICAL_COMPLICATION, ROBOT_INVOLVEMENT, SURGEON_DECISION, CLINICAL_SUMMARY,
            DATA_LOSS_TYPE, EXTRACTED_CLUES, CAN_BE_REPAIRED,
            INPUT_TOKENS, OUTPUT_TOKENS, DURATION_SECONDS
        ) VALUES (
            %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s
        ) ON DUPLICATE KEY UPDATE
            CLASSIFICATION=VALUES(CLASSIFICATION),
            REASON=VALUES(REASON),
            HAZARD_CATEGORY=VALUES(HAZARD_CATEGORY),
            FAULT_COMPONENT=VALUES(FAULT_COMPONENT),
            CAUSAL_CHAIN=VALUES(CAUSAL_CHAIN),
            ROOT_CAUSE=VALUES(ROOT_CAUSE),
            FACTUAL_SUMMARY=VALUES(FACTUAL_SUMMARY),
            CLINICAL_COMPLICATION=VALUES(CLINICAL_COMPLICATION),
            ROBOT_INVOLVEMENT=VALUES(ROBOT_INVOLVEMENT),
            SURGEON_DECISION=VALUES(SURGEON_DECISION),
            CLINICAL_SUMMARY=VALUES(CLINICAL_SUMMARY),
            DATA_LOSS_TYPE=VALUES(DATA_LOSS_TYPE),
            EXTRACTED_CLUES=VALUES(EXTRACTED_CLUES),
            CAN_BE_REPAIRED=VALUES(CAN_BE_REPAIRED),
            INPUT_TOKENS=VALUES(INPUT_TOKENS),
            OUTPUT_TOKENS=VALUES(OUTPUT_TOKENS),
            DURATION_SECONDS=VALUES(DURATION_SECONDS)
    """
    
    # 填充对应分类的参数，其余为 None
    params = [
        m_key, cat, reason,
        
        # Shocking
        data.get("hazard_category") if cat == "Shocking" else None,
        data.get("fault_component") if cat == "Shocking" else None,
        data.get("causal_chain") if cat == "Shocking" else None,
        data.get("root_cause") if cat == "Shocking" else None,
        data.get("factual_summary") if cat == "Shocking" else None,
        
        # Normal
        data.get("clinical_complication") if cat == "Normal" else None,
        data.get("robot_involvement") if cat == "Normal" else None,
        data.get("surgeon_decision") if cat == "Normal" else None,
        data.get("clinical_summary") if cat == "Normal" else None,
        
        # Structural_Issue
        data.get("data_loss_type") if cat == "Structural_Issue" else None,
        data.get("extracted_clues") if cat == "Structural_Issue" else None,
        data.get("can_be_repaired") if cat == "Structural_Issue" else None,
        
        in_t, out_t, duration
    ]
    
    cursor.execute(sql, params)
    conn.commit()

def main():
    if not DEEPSEEK_API_KEY:
        print("错误: 未配置 DEEPSEEK_API_KEY！")
        return
        
    classified_csv = os.path.join(BASE_DIR, "reports", "davinci_death_dataset", "davinci_death_classified.csv")
    if not os.path.exists(classified_csv):
        print("错误: 未找到分类 CSV 文件！")
        return

    print(">>> 正在初始化 foi_text_knowledge 知识库表...")
    init_knowledge_table()

    # 1. 加载所有 720 条分类记录
    records = []
    with open(classified_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        for row in reader:
            if row:
                records.append(row)
                
    total_records = len(records)
    print(f"载入成功，共计 {total_records} 条致死病例待跑批处理。")

    # 2. 数据库连接池（每个线程有独立的连接写入，或者统一在主线程队列写入）
    # 为保证连接安全，我们用主线程串行写入，工作线程负责高并发网络 API 请求。
    # 建立 20 个高并发工作线程
    max_workers = 20
    print(f"启动高并发线程池 (Workers: {max_workers}) 开始洗数据...")
    print("-" * 70)
    
    t_start = time.time()
    
    db_conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, port=DB_PORT, database=DB_NAME)
    db_cursor = db_conn.cursor()
    
    completed_cnt = 0
    total_in = 0
    total_out = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        futures = {executor.submit(process_single_case, rec): rec for rec in records}
        
        for future in as_completed(futures):
            rec = futures[future]
            try:
                res = future.result()
                write_to_db(res, db_conn, db_cursor)
                
                completed_cnt += 1
                total_in += res["input_tokens"]
                total_out += res["output_tokens"]
                
                # 打印实时进度
                if completed_cnt % 20 == 0 or completed_cnt == total_records:
                    pct = (completed_cnt / total_records) * 100
                    print(f"  [进度] 已完成 {completed_cnt}/{total_records} ({pct:.1f}%) | 耗时: {time.time() - t_start:.1f}s | 消耗 Token: In={total_in:,}, Out={total_out:,}")
            except Exception as e:
                print(f"  [异常] 病案 {rec[0]} 处理失败: {e}")

    # 3. 将全量知识库导出为一个 CSV，方便后续用户查看和备份
    output_csv = os.path.join(BASE_DIR, "reports", "davinci_death_dataset", "davinci_death_knowledge_base.csv")
    print(f"\n>>> 正在将全量结构化知识库导出至 CSV 文件: {output_csv}...")
    
    db_cursor.execute("SELECT * FROM foi_text_knowledge")
    rows = db_cursor.fetchall()
    headers = [desc[0] for desc in db_cursor.description]
    
    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    db_conn.close()
    
    total_duration = time.time() - t_start
    print(f"\n======================================================================")
    print(f">>> 全量 AI 洗盘与数据库持久化全部完成！")
    print(f"======================================================================")
    print(f"  - 成功清洗入库条数 : {completed_cnt} / {total_records} 条")
    print(f"  - 总运行时长 (秒)  : {total_duration:.2f} 秒 (平均每条约 {total_duration/total_records:.3f} 秒)")
    print(f"  - 累计消耗 Tokens  : Input={total_in:,} | Output={total_out:,}")
    print(f"  - 预估全量清洗成本 : {((total_in * 0.14 + total_out * 0.28) / 1000000) * 7.2:.4f} 元")
    print(f"  - 最终全量 CSV 导出: {output_csv}")
    print(f"======================================================================\n")

if __name__ == '__main__':
    main()
