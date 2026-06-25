import os
import csv
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dataset_dir = os.path.join(BASE_DIR, "reports", "davinci_death_dataset")

def main():
    csv_path = os.path.join(dataset_dir, "davinci_death_foi_text.csv")
    
    if not os.path.exists(csv_path):
        print("未找到致死病例文本 CSV 文件。")
        return

    print(">>> 开始扫描 1767 条达芬奇致死病案描述文本中的『异常与奇怪』特征...\n")

    # 1. 扫描短文本奇怪现象（死亡病历为什么会极短？）
    short_weird_texts = []
    # 2. 扫描包含极端异常关键词的文本（如起火、火花、机器人失控自主运动、零件掉进人体等）
    weird_keywords = {
        "fire": ["fire", "spark", "burn", "smoke", "explosion"],
        "uncontrolled_movement": ["spontaneous", "by itself", "automatically", "uncontrolled", "drift", "erratic"],
        "foreign_body": ["left inside", "lost inside", "fell into", "retained", "dropped into", "broken tip"],
        "data_anomaly": ["garbage", "error", "corrupt", "unreadable", "html", "http"]
    }
    weird_matches = {k: [] for k in weird_keywords}

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        key_idx = headers.index("MDR_REPORT_KEY")
        text_idx = headers.index("FOI_TEXT")

        for row in reader:
            if not row or len(row) <= text_idx:
                continue
            m_key = row[key_idx]
            text = row[text_idx].strip()
            text_lower = text.lower()

            # 异常一：文本极短（小于 50 字符且不为空），说明死亡信息被严重隐瞒或敷衍登记
            if 0 < len(text) < 50:
                short_weird_texts.append((m_key, text))

            # 异常二：包含奇怪的业务事件
            for category, kw_list in weird_keywords.items():
                for kw in kw_list:
                    if kw in text_lower:
                        # 记录 MDR_REPORT_KEY 和匹配的片段
                        weird_matches[category].append((m_key, kw, text))
                        break

    # 报告一：超短/敷衍登记的死亡事件
    print(f"--- 1. 发现 {len(short_weird_texts)} 条『极其敷衍/简短』的致死事件描述（正常致死病例不应如此简短） ---")
    for m_key, text in short_weird_texts[:8]:
        print(f"  MDR: {m_key:<10} | 文本: {text}")
    print()

    # 报告二：设备起火/冒烟/火花等极端安全隐患
    print(f"--- 2. 发现 {len(weird_matches['fire'])} 条涉及『起火/火花/冒烟/灼伤』的案例 ---")
    for m_key, kw, text in weird_matches['fire'][:4]:
        snippet = text.replace('\n', ' ')[:130] + "..."
        print(f"  MDR: {m_key:<10} (关键字: {kw:<8}) | {snippet}")
    print()

    # 报告三：器械失控/自主乱动（Surgical Robot Uncontrolled Movement）—— 机器人自主运动最可怕
    print(f"--- 3. 发现 {len(weird_matches['uncontrolled_movement'])} 条涉及『不受控/自主异常乱动』的案例 ---")
    for m_key, kw, text in weird_matches['uncontrolled_movement'][:4]:
        snippet = text.replace('\n', ' ')[:130] + "..."
        print(f"  MDR: {m_key:<10} (关键字: {kw:<8}) | {snippet}")
    print()

    # 报告四：异物遗留体内（如机械臂尖端断裂并掉入患者体内）
    print(f"--- 4. 发现 {len(weird_matches['foreign_body'])} 条涉及『尖端断裂/零件遗留/掉入患者体内』的案例 ---")
    for m_key, kw, text in weird_matches['foreign_body'][:4]:
        snippet = text.replace('\n', ' ')[:130] + "..."
        print(f"  MDR: {m_key:<10} (关键字: {kw:<8}) | {snippet}")
    print()

if __name__ == '__main__':
    main()
