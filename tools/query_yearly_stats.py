import os
import re
import pymysql
from dotenv import load_dotenv

env_path = r"e:\pythonProject\MAUDE\.env"
load_dotenv(env_path)

DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASSWORD', '123456')
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_NAME = os.getenv('DB_NAME') or 'maude_db'

OUTPUT_FILE = r"e:\pythonProject\MAUDE\MAUDE各年份数据记录统计报告.md"

def extract_year_from_filename(filename):
    # 提取文件名中的4位数字
    match = re.search(r'\d{4}', filename)
    if match:
        return match.group(0)
    # 处理类似 foitextthru1995.txt 或者是 patientThru2025.txt
    if 'thru' in filename.lower():
        match_thru = re.search(r'thru(\d{4})', filename, re.IGNORECASE)
        if match_thru:
            return f"Thru {match_thru.group(1)}"
    return "Unknown"

def main():
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        database=DB_NAME
    )
    cursor = conn.cursor()

    print(">>> 正在从 _import_progress 统计各个数据文件的导入行数...")
    cursor.execute("SELECT file_name, processed_rows FROM _import_progress ORDER BY file_name;")
    progress_rows = cursor.fetchall()
    
    file_stats = []
    for fname, rows in progress_rows:
        year = extract_year_from_filename(fname)
        file_stats.append({
            'file_name': fname,
            'year': year,
            'rows': rows
        })

    # 分类汇总设备（device）和描述文本（foi_text）的按年份/文件记录数
    device_files = [f for f in file_stats if 'device' in f['file_name'].lower() or 'foidev' in f['file_name'].lower()]
    foi_files = [f for f in file_stats if 'foitext' in f['file_name'].lower()]

    print(">>> 正在统计 mdr_report 主表各年份的记录数（按收到日期 DATE_RECEIVED 年份）...")
    cursor.execute("""
        SELECT RIGHT(DATE_RECEIVED, 4) as yr, COUNT(*) as cnt 
        FROM mdr_report 
        GROUP BY yr 
        ORDER BY yr;
    """)
    mdr_yearly = cursor.fetchall()

    print(">>> 正在统计 patient 表各年份的记录数（按收到日期 DATE_RECEIVED 年份）...")
    cursor.execute("""
        SELECT RIGHT(DATE_RECEIVED, 4) as yr, COUNT(*) as cnt 
        FROM patient 
        GROUP BY yr 
        ORDER BY yr;
    """)
    patient_yearly = cursor.fetchall()

    conn.close()

    # 格式化输出为 Markdown
    md_content = []
    md_content.append("# FDA MAUDE 数据库各年份记录数统计报告\n")
    md_content.append("> 本报告数据直接查询自 MySQL `maude_db` 数据库中的全量落盘数据，涵盖主表、患者表、设备表、描述文本表的年度明细。\n")
    md_content.append("## 一、 核心总表年度记录数统计 (按 DATE_RECEIVED)\n")
    md_content.append("以下数据为通过解析 `DATE_RECEIVED` 字段中的收到年份，对主表和患者表进行的聚合统计。展示了各年度的不良事件发生趋势。\n")
    
    md_content.append("| 收到年份 | 主表 (mdr_report) 记录数 | 患者表 (patient) 记录数 |")
    md_content.append("| :--- | :--- | :--- |")
    
    # 将主表和患者表按年份对齐
    mdr_dict = {row[0]: row[1] for row in mdr_yearly if row[0] and row[0].isdigit()}
    patient_dict = {row[0]: row[1] for row in patient_yearly if row[0] and row[0].isdigit()}
    
    all_years = sorted(list(set(mdr_dict.keys()) | set(patient_dict.keys())))
    
    for yr in all_years:
        m_cnt = mdr_dict.get(yr, 0)
        p_cnt = patient_dict.get(yr, 0)
        md_content.append(f"| {yr} 年 | {m_cnt:,} | {p_cnt:,} |")
        
    md_content.append("\n## 二、 历史设备文件导入明细统计 (按原始数据源年份)\n")
    md_content.append("设备表（`device` 及 `device_baseline_legacy`）的原始数据源为按年度拆分的文件。以下为各个设备文件实际清洗并载入数据库的记录数明细：\n")
    md_content.append("| 对应年份 | 原始数据文件名 | 成功导入记录数 |")
    md_content.append("| :--- | :--- | :--- |")
    
    # 按照年份对设备文件进行排序
    def sort_key(x):
        yr_str = x['year']
        if yr_str.startswith('Thru '):
            return int(yr_str.replace('Thru ', '')) - 100
        elif yr_str.isdigit():
            return int(yr_str)
        return 9999
        
    device_files.sort(key=sort_key)
    for f in device_files:
        md_content.append(f"| {f['year']} 年 | {f['file_name']} | {f['rows']:,} |")

    md_content.append("\n## 三、 自由描述文本文件导入明细统计 (按原始数据源年份)\n")
    md_content.append("事件描述文本表（`foi_text` 及溢出表 `foi_text_overflow`）原始数据同样按照年份分割。以下为各个文本文件实际清洗导入的行数统计明细：\n")
    md_content.append("| 对应年份 | 原始数据文件名 | 成功导入记录数 |")
    md_content.append("| :--- | :--- | :--- |")
    
    foi_files.sort(key=sort_key)
    for f in foi_files:
        md_content.append(f"| {f['year']} 年 | {f['file_name']} | {f['rows']:,} |")

    md_content.append("\n---\n*报告生成时间: 2026-06-10 | 数据底座优化技术支持: Antigravity*")

    # 写入文件
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_content))
        
    print(f"\n>>> 报告已成功输出至: {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
