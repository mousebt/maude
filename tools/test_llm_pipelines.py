import os
import csv
import json
import time
import requests
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(BASE_DIR, ".env")
load_dotenv(env_path)

DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')

# 各分类的整理管道 System Prompt
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
这篇文本可能因为 FDA 删除或严重的商业和隐私脱敏而丢失了大部分内容。请帮我评估其受损情况并提取残存线索。请必须以严格的 JSON 格式输出，不要包含 any markdown 标记或前后文字，字段如下：
{
  "data_loss_type": "被FDA要求删除 / 仅含商业脱敏掩码B4 / 仅含患者隐私掩码B6 / 极度敷衍字数不足",
  "extracted_clues": "从中能提取出的极少数线索（如涉及的特定手术名称、医院、或诉讼信息，若无则填'无'）",
  "can_be_repaired": "是否有可能通过交叉检索修复数据？（YES / NO）"
}"""
}

def call_deepseek_api(prompt, case_text):
    """
    调用官方 DeepSeek-Chat API。
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
    
    try:
        response = requests.post(
            f"{DEEPSEEK_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            res_json = response.json()
            content = res_json['choices'][0]['message']['content']
            usage = res_json.get('usage', {})
            return content, usage
        else:
            return f"Error: HTTP {response.status_code} - {response.text}", {}
    except Exception as e:
        return f"Error: {e}", {}

def main():
    if not DEEPSEEK_API_KEY:
        print("错误: 未配置 DEEPSEEK_API_KEY 环境变量！")
        return

    classified_csv = os.path.join(BASE_DIR, "reports", "davinci_death_dataset", "davinci_death_classified.csv")
    if not os.path.exists(classified_csv):
        print("错误: 未找到分类 CSV 文件！")
        return

    # 1. 抽取测试样本（Normal 10份, Shocking 10份, Structural 7份）
    test_cases = {"Normal": [], "Shocking": [], "Structural_Issue": []}
    
    with open(classified_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        key_idx = headers.index("MDR_REPORT_KEY")
        class_idx = headers.index("CLASSIFICATION")
        text_idx = headers.index("FOI_TEXT")
        
        for row in reader:
            if not row:
                continue
            cat = row[class_idx]
            m_key = row[key_idx]
            text = row[text_idx]
            
            # 各分类控制抽取数量
            limit = 10 if cat in ("Normal", "Shocking") else 7
            if len(test_cases[cat]) < limit:
                test_cases[cat].append((m_key, text))

    print(">>> 正在启动不同类别的 AI 整理管道测试...")
    print(f"    计划测试: Shocking (10) | Normal (10) | Structural_Issue (7)")
    print(f"    调用模型: deepseek-chat (基于官方 API: {DEEPSEEK_BASE_URL})")
    print("-" * 60)

    test_results = []
    total_input_tokens = 0
    total_output_tokens = 0

    # 2. 遍历执行 AI 整理
    for cat, cases in test_cases.items():
        print(f"\n[管道启动] 正在处理类别: {cat} (共 {len(cases)} 份样例)...")
        prompt = PROMPTS[cat]
        
        for idx, (m_key, text) in enumerate(cases, 1):
            print(f"  ({idx}/{len(cases)}) 正在处理 MDR: {m_key} ...")
            
            t0 = time.time()
            api_res, usage = call_deepseek_api(prompt, text)
            duration = time.time() - t0
            
            # 统计 tokens
            in_t = usage.get('prompt_tokens', 0)
            out_t = usage.get('completion_tokens', 0)
            total_input_tokens += in_t
            total_output_tokens += out_t
            
            # 解析结果
            try:
                parsed_res = json.loads(api_res)
            except Exception:
                parsed_res = {"raw_response": api_res}
                
            test_results.append({
                "mdr_report_key": m_key,
                "category": cat,
                "duration_seconds": round(duration, 2),
                "tokens_used": {"input": in_t, "output": out_t},
                "structured_data": parsed_res
            })
            
            # 适当延时防止限流
            time.sleep(0.5)

    # 3. 物理保存测试结果 JSON
    output_path = os.path.join(BASE_DIR, "reports", "davinci_death_dataset", "llm_test_results.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)

    # 4. 打印统计报告
    print("\n" + "=" * 60)
    print(">>> 大模型整理管道测试完成！")
    print("=" * 60)
    print(f"  - 成功处理测试样例 : {len(test_results)} 份")
    print(f"  - 消耗 Input Tokens: {total_input_tokens:,}")
    print(f"  - 消耗 Output Tokens: {total_output_tokens:,}")
    print(f"  - 估算 API 总成本  : ${((total_input_tokens * 0.14 + total_output_tokens * 0.28) / 1000000):.5f} (约 ¥{((total_input_tokens * 0.14 + total_output_tokens * 0.28) / 1000000) * 7.2:.4f} 元)")
    print(f"  - 测试结果已保存至 : {output_path}")
    print("=" * 60)

if __name__ == '__main__':
    main()
