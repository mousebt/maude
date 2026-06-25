import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
csv_path = os.path.join(BASE_DIR, "reports", "maude_global_hierarchy_analysis.csv")

def main():
    if not os.path.exists(csv_path):
        print(f"文件不存在: {csv_path}")
        return
        
    print(f">>> 正在读取 {csv_path} 的前 15 行...")
    with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
        for i in range(15):
            line = f.readline()
            if not line:
                break
            # 使用 repr 打印，防止控制台编码报错
            print(f"Line {i+1}: {repr(line.strip())}")

if __name__ == '__main__':
    main()
