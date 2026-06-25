import os

def search_files():
    reports_dir = r"e:\pythonProjects\MAUDE\reports"
    keywords = ["da vinci", "davinci", "intuitive"]
    
    print(">>> 正在扫描 reports 目录下的报告文件...")
    for root, dirs, files in os.walk(reports_dir):
        for file in files:
            if file.endswith(('.md', '.html', '.csv', '.json')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().lower()
                        for kw in keywords:
                            if kw in content:
                                print(f"发现匹配文件: {file} (关键字: '{kw}')")
                                # 打印匹配行
                                f.seek(0)
                                lines = f.readlines()
                                match_count = 0
                                for i, line in enumerate(lines):
                                    if kw in line.lower():
                                        print(f"  第 {i+1} 行: {line.strip()[:150]}")
                                        match_count += 1
                                        if match_count >= 5:
                                            print("  ... (仅显示前 5 处匹配)")
                                            break
                                break
                except Exception as e:
                    print(f"读取文件 {file} 失败: {e}")

if __name__ == '__main__':
    search_files()
