import os
import csv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dataset_dir = os.path.join(BASE_DIR, "reports", "davinci_death_dataset")

def main():
    csv_path = os.path.join(dataset_dir, "davinci_death_foi_text.csv")
    
    target_keys = ["2803906", "2965986"]
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        key_idx = headers.index("MDR_REPORT_KEY")
        text_idx = headers.index("FOI_TEXT")
        
        for row in reader:
            if not row or len(row) <= text_idx:
                continue
            m_key = row[key_idx]
            if m_key in target_keys:
                print("="*80)
                print(f"奇怪案例 MDR_REPORT_KEY : {m_key}")
                print("-"*80)
                print(row[text_idx])
                print("="*80 + "\n")

if __name__ == '__main__':
    main()
