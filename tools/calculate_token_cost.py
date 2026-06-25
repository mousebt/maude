import os
import csv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
csv_path = os.path.join(BASE_DIR, "reports", "davinci_death_events.csv")

def main():
    if not os.path.exists(csv_path):
        print("未找到 davinci_death_events.csv 文件。")
        return
        
    total_chars = 0
    total_words = 0
    record_count = 0
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        text_idx = headers.index("FOI_TEXT")
        
        for row in reader:
            if not row or len(row) <= text_idx:
                continue
            text = row[text_idx].strip()
            if text:
                total_chars += len(text)
                total_words += len(text.split())
                record_count += 1
                
    # 纯英文 Token 计算粗略估算：1 个单词约等于 1.3 个 Token
    # 或者用字符数估算：1 个 Token 约等于 4 个字符
    est_tokens_by_words = int(total_words * 1.35)
    est_tokens_by_chars = int(total_chars / 4)
    
    # 我们取两者的平均值作为稳妥的文本本体 Token 数
    base_tokens = int((est_tokens_by_words + est_tokens_by_chars) / 2)
    
    print(f"统计结果：")
    print(f"  总病例记录数     : {record_count} 条")
    print(f"  总字符数 (Chars) : {total_chars:,} 个字符")
    print(f"  总英文单词数      : {total_words:,} 个单词")
    print(f"  自述文本本体估算 : {base_tokens:,} Tokens")
    
if __name__ == '__main__':
    main()
