import os
import csv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dataset_dir = os.path.join(BASE_DIR, "reports", "davinci_death_dataset")

def classify_text(m_key, text):
    text_lower = text.lower().strip()
    
    # 1. 结构问题/数据缺失判断 (Structural Issues)
    # - 长度小于 50 个字符
    # - 或者是典型的 FDA 删除说明，或是只有 (B)(4)
    is_structural_template = (
        "product code has been removed" in text_lower or
        "information is currently unknown" in text_lower or
        text_lower == "(b)(4)." or
        text_lower == "(b)(4)" or
        text_lower == "(b)(6)" or
        text_lower == "\\n" or
        text_lower == "none"
    )
    if len(text) < 55 or is_structural_template:
        return "Structural_Issue", "数据缺失/被FDA删除/仅含脱敏掩码"

    # 2. 惊悚/异常事件判断 (Shocking/Weird)
    # 细分子类关键字，以便给出判定原因
    weird_rules = {
        "机器不受控/自主乱动": ["uncontrolled", "drift", "spontaneous", "by itself", "automatically", "erratic"],
        "起火/冒烟/漏电灼伤": ["fire", "spark", "smoke", "burn", "explosion", "arcing", "arc", "insulation failure", "leakage"],
        "零件断裂/遗留人体内/丢针": ["left inside", "lost inside", "fell into", "retained", "dropped into", "broken tip", "missing needle", "broken piece"],
        "诉讼黑幕/做空指控/瞒报曝光": ["lawsuit", "legal dispute", "litigation", "citron", "attorney", "court", "complaint filed"]
    }
    
    for reason, kw_list in weird_rules.items():
        for kw in kw_list:
            if kw in text_lower:
                return "Shocking", f"触发[{reason}]关键字: '{kw}'"

    # 3. 常规报告 (Normal)
    return "Normal", "常规临床并发症/正常手术意外描述"

def main():
    input_file = os.path.join(BASE_DIR, "reports", "davinci_death_events.csv")
    output_file = os.path.join(dataset_dir, "davinci_death_classified.csv")
    
    if not os.path.exists(input_file):
        print("未找到源达芬奇致死病例 CSV 文件。")
        return

    classified_records = []
    stats = {"Normal": 0, "Shocking": 0, "Structural_Issue": 0}
    
    # 用来记录各个分类的典型示例
    samples = {"Normal": [], "Shocking": [], "Structural_Issue": []}

    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        
        # 确定列索引
        key_idx = headers.index("MDR_REPORT_KEY")
        num_idx = headers.index("REPORT_NUMBER")
        brand_idx = headers.index("BRAND_NAME")
        text_idx = headers.index("FOI_TEXT")

        for row in reader:
            if not row or len(row) <= text_idx:
                continue
            
            m_key = row[key_idx]
            rep_num = row[num_idx]
            brand = row[brand_idx]
            text = row[text_idx]
            
            category, reason = classify_text(m_key, text)
            stats[category] += 1
            
            record = [m_key, rep_num, brand, category, reason, text]
            classified_records.append(record)
            
            # 收集样本（最多保留 3 个典型示例）
            if len(samples[category]) < 3:
                samples[category].append((m_key, brand, reason, text))

    # 写入分类结果 CSV
    new_headers = ["MDR_REPORT_KEY", "REPORT_NUMBER", "BRAND_NAME", "CLASSIFICATION", "REASON", "FOI_TEXT"]
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(new_headers)
        writer.writerows(classified_records)

    total = sum(stats.values())
    print(">>> 720 条达芬奇致死病案例行初筛分类完成！")
    print(f"    总记录数: {total} 条")
    print("-" * 50)
    for cat, count in stats.items():
        pct = (count / total) * 100
        print(f"    - 分类: {cat:<20} | 数量: {count:>3} 条 | 占比: {pct:.2f}%")
    print("-" * 50)
    print(f"    分类明细已导出至: {output_file}\n")

    # 打印典型样本供分析
    for cat in ["Structural_Issue", "Shocking", "Normal"]:
        print("=" * 80)
        print(f"【分类典型示例】: {cat}")
        print("=" * 80)
        for idx, (m_key, brand, reason, text) in enumerate(samples[cat], 1):
            print(f"  示例 {idx} | MDR: {m_key} | 器械: {brand}")
            print(f"  判定依据: {reason}")
            # 截取前 250 字符展示
            snippet = text.replace('\n', ' ').strip()
            if len(snippet) > 250:
                snippet = snippet[:250] + "..."
            print(f"  内容片段: {snippet}")
            print("-" * 80)
        print()

if __name__ == '__main__':
    main()
