import os
import time
import requests
import pymysql
from dotenv import load_dotenv

env_path = r"e:\pythonProject\MAUDE\.env"
load_dotenv(env_path)

DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASSWORD', '123456')
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_NAME = os.getenv('DB_NAME') or 'maude_db'

DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL') or "https://api.deepseek.com"

def get_representative_samples():
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        database=DB_NAME
    )
    cursor = conn.cursor()
    
    print(">>> 正在从 foi_text_overflow 筛选具有高研究价值（字数>5000 且导致死亡/严重伤害）的样本...")
    
    # 联查 mdr_report 找出严重的不良事件后果的样本
    cursor.execute("""
        SELECT f.MDR_REPORT_KEY, m.EVENT_TYPE, CHAR_LENGTH(f.FOI_TEXT) as txt_len, f.FOI_TEXT
        FROM foi_text_overflow f
        JOIN mdr_report m ON f.MDR_REPORT_KEY = m.MDR_REPORT_KEY
        WHERE m.EVENT_TYPE IN ('D', 'IN') AND CHAR_LENGTH(f.FOI_TEXT) BETWEEN 5000 AND 10000
        LIMIT 2
    """)
    samples = cursor.fetchall()
    conn.close()
    return samples

def analyze_with_deepseek(report_key, event_type, text_len, narrative_text):
    print(f"\n=================== 开始调用 DeepSeek 挖掘分析病例 (ID: {report_key}) ===================")
    print(f"原始病例后果: {event_type} | 文本长度: {text_len} 字符")
    
    prompt = f"""
你是一名顶尖的医疗器械警戒专家与数据挖掘工程师。请分析下方这篇源自 FDA MAUDE 数据库中有关医疗器械不良事件的真实英文病例描述（叙述文本）。

请阅读并按以下结构，提取出其中的潜在器械问题、并发症关联以及根因分析。请使用【地道规范的中文】进行输出：

1. **核心医疗器械信息**：
   - 目标器械品牌/型号 (Primary Device Name/Model)
   - 伴随或同时使用的辅助设备/材料/耗材 (Associated Accessories/Materials)

2. **事件发生经过 (Timeline & Scenario)**：
   - 用简短几句话还原手术/使用现场发生了什么

3. **器械故障物理现象 (Root Cause & Device Failure)**：
   - 提取导致故障的物理/软件/操作原因（如电极断裂、阀门破裂、软件死机等）

4. **临床影响与患者结局 (Clinical Complication & Outcome)**：
   - 患者出现的临床症状、并发症（如失血、心率骤降、休克等）及最终的结局。

5. **LLM 挖掘到的“潜在隐患/警示点” (Potential Safety Hazards)**：
   - 深入挖掘此案例中隐藏的多器械串联失效隐患、临床操作盲区或厂商设计缺陷。

---
【原始病例叙述文本】：
{narrative_text}
---
"""

    # 接口地址通常为 BASE_URL/chat/completions 或 BASE_URL/v1/chat/completions
    # 智囊提示：deepseek-chat 背后就是最新的 DeepSeek V3/V4 模型
    api_url = f"{DEEPSEEK_BASE_URL.rstrip('/')}/chat/completions"
    if "/v1" not in api_url and not api_url.endswith("/v1/chat/completions"):
        # 有些环境喜欢加上 v1
        pass

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a professional medical data analyst and device safety expert. Always reply in Chinese."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "stream": False
    }
    
    print(f"正在向 DeepSeek 发起请求 (模型: deepseek-chat)...")
    t0 = time.time()
    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=60)
        # 如果 /chat/completions 报 404，尝试自动回退到 /v1/chat/completions
        if response.status_code == 404:
            print("  [尝试回退] 404 错误，尝试添加 /v1 路径...")
            fallback_url = f"{DEEPSEEK_BASE_URL.rstrip('/')}/v1/chat/completions"
            response = requests.post(fallback_url, headers=headers, json=data, timeout=60)

        response_json = response.json()
        if response.status_code == 200 and 'choices' in response_json:
            result = response_json['choices'][0]['message']['content']
            print(f"\n>>> DeepSeek 挖掘分析成功 (耗时: {time.time() - t0:.2f} 秒) <<<\n")
            print(result)
        else:
            print(f">>> DeepSeek 调用失败。HTTP 状态码: {response.status_code}。响应内容：", response_json)
    except Exception as e:
        print(">>> 调用 DeepSeek 发生异常：", e)

def main():
    if not DEEPSEEK_API_KEY:
        print("未检测到有效的 DeepSeek API 密钥，请在 .env 中设置 DEEPSEEK_API_KEY。")
        return
        
    samples = get_representative_samples()
    if not samples:
        print("未筛选到符合条件的超长病例描述样本。")
        return
        
    print(f"共筛选到 {len(samples)} 个极具代表性的高维案例。")
    
    # 依然对第 1 个样本运行挖掘测试
    key, event, length, text = samples[0]
    analyze_with_deepseek(key, event, length, text)

if __name__ == '__main__':
    main()
