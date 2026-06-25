import os
import csv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
csv_path = os.path.join(BASE_DIR, "reports", "davinci_death_dataset", "davinci_death_classified.csv")

def main():
    if not os.path.exists(csv_path):
        print("未找到分类后的 CSV。")
        return
        
    counts = {
        "机器不受控/自主乱动": 0,
        "起火/冒烟/漏电灼伤": 0,
        "零件断裂/遗留人体内/丢针": 0,
        "诉讼黑幕/做空指控/瞒报曝光": 0
    }
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        class_idx = headers.index("CLASSIFICATION")
        reason_idx = headers.index("REASON")
        
        for row in reader:
            if not row or len(row) <= reason_idx:
                continue
            classification = row[class_idx]
            reason = row[reason_idx]
            
            if classification == "Shocking":
                for cat in counts.keys():
                    if cat in reason:
                        counts[cat] += 1
                        break
                        
    print("惊悚报告细分统计：")
    for cat, cnt in counts.items():
        print(f"  - {cat:<20}: {cnt:>3} 条")
        
if __name__ == '__main__':
    main()
