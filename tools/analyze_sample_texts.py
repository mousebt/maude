import os
import csv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dataset_dir = os.path.join(BASE_DIR, "reports", "davinci_death_dataset")

def main():
    csv_path = os.path.join(dataset_dir, "davinci_death_foi_text.csv")
    device_path = os.path.join(dataset_dir, "davinci_death_device.csv")
    
    if not os.path.exists(csv_path):
        print("未找到致死病例文本 CSV 文件。")
        return

    # 1. 加载设备信息，建立 MDR_REPORT_KEY -> BRAND_NAME 的映射
    device_map = {}
    with open(device_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        # 字段索引
        key_idx = headers.index("MDR_REPORT_KEY")
        brand_idx = headers.index("BRAND_NAME") if "BRAND_NAME" in headers else -1
        generic_idx = headers.index("GENERIC_NAME") if "GENERIC_NAME" in headers else -1
        
        for row in reader:
            if not row:
                continue
            m_key = row[key_idx]
            brand = row[brand_idx] if brand_idx != -1 else "Unknown"
            generic = row[generic_idx] if generic_idx != -1 else "Unknown"
            device_map[m_key] = f"{brand} ({generic})"

    # 2. 读取文本记录，按长度降序排列，以便抓取“信息量最大”的复杂长文本
    text_records = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        key_idx = headers.index("MDR_REPORT_KEY")
        text_idx = headers.index("FOI_TEXT")
        
        for row in reader:
            if not row or len(row) <= text_idx:
                continue
            m_key = row[key_idx]
            text = row[text_idx]
            text_records.append((m_key, text))

    # 按文本长度排序
    text_records.sort(key=lambda x: len(x[1]), reverse=True)

    print(">>> 正在提取长度排名前 3 的典型达芬奇致死病案描述进行显微分析...\n")

    # 抓取前 3 个做展示
    count = 0
    for m_key, text in text_records:
        if len(text) < 1000: # 确保是有深度内容的文本
            continue
        
        dev_info = device_map.get(m_key, "未知达芬奇设备")
        print("="*80)
        print(f"病案样本 {count+1}")
        print(f"  MDR_REPORT_KEY : {m_key}")
        print(f"  涉及设备信息   : {dev_info}")
        print(f"  文本总长度     : {len(text)} 字符")
        print("-"*80)
        
        # 打印部分文本，换行美化
        # 如果文本过长，打印前 1500 字符和后 500 字符
        if len(text) > 2000:
            print(text[:1500] + "\n\n... [此处省略部分中间调查记录] ...\n\n" + text[-500:])
        else:
            print(text)
        print("="*80 + "\n")
        
        count += 1
        if count >= 3:
            break

if __name__ == '__main__':
    main()
