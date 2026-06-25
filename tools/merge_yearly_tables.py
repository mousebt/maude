import os
import re
import pymysql
import pandas as pd
from dotenv import load_dotenv

# 动态获取根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env_path = os.path.join(BASE_DIR, ".env")
load_dotenv(env_path)

DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASSWORD', '123456')
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_NAME = os.getenv('DB_NAME') or 'maude_db'

REPORT_PATH = os.path.join(BASE_DIR, "reports", "MAUDE各年份数据记录统计报告.md")

def extract_year_from_filename(filename):
    match = re.search(r'\d{4}', filename)
    if match:
        return int(match.group(0))
    # 处理类似 foitextthru1995.txt
    if 'thru' in filename.lower():
        match_thru = re.search(r'thru(\d{4})', filename, re.IGNORECASE)
        if match_thru:
            return int(match_thru.group(1))
    return None

def main():
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        database=DB_NAME
    )
    cursor = conn.cursor()

    # 1. 统计 mdr_report 和 patient 按 DATE_RECEIVED 年份的记录数
    print(">>> 正在统计 mdr_report 按年份的记录数...")
    cursor.execute("""
        SELECT RIGHT(DATE_RECEIVED, 4) AS yr, COUNT(*) 
        FROM mdr_report 
        GROUP BY yr
    """)
    mdr_data = cursor.fetchall()
    
    print(">>> 正在统计 patient 按年份的记录数...")
    cursor.execute("""
        SELECT RIGHT(DATE_RECEIVED, 4) AS yr, COUNT(*) 
        FROM patient 
        GROUP BY yr
    """)
    patient_data = cursor.fetchall()

    # 转化为 dict
    mdr_dict = {}
    for yr, cnt in mdr_data:
        try:
            yr_int = int(yr)
            mdr_dict[yr_int] = cnt
        except ValueError:
            # 比如含有非数字
            mdr_dict[yr] = cnt

    patient_dict = {}
    for yr, cnt in patient_data:
        try:
            yr_int = int(yr)
            patient_dict[yr_int] = cnt
        except ValueError:
            patient_dict[yr] = cnt

    # 2. 从 _import_progress 提取 device 和 foi_text 文件对应的行数并按年份合并
    print(">>> 正在从 _import_progress 汇总文件级导入行数...")
    cursor.execute("SELECT file_name, processed_rows FROM _import_progress")
    progress_rows = cursor.fetchall()

    device_dict = {}
    foi_dict = {}

    for fname, rows in progress_rows:
        yr = extract_year_from_filename(fname)
        if yr is None:
            continue
        fname_lower = fname.lower()
        if 'device' in fname_lower or 'foidev' in fname_lower:
            device_dict[yr] = device_dict.get(yr, 0) + rows
        elif 'foitext' in fname_lower:
            foi_dict[yr] = foi_dict.get(yr, 0) + rows

    conn.close()

    # 3. 汇总所有的年份 key
    all_years = set()
    all_years.update(mdr_dict.keys())
    all_years.update(patient_dict.keys())
    all_years.update(device_dict.keys())
    all_years.update(foi_dict.keys())

    # 将年份排序：把数字年份放在前面排好序，非数字（如未识别、异常年份）放在最后
    numeric_years = sorted([y for y in all_years if isinstance(y, int)])
    str_years = sorted([y for y in all_years if isinstance(y, str)])
    sorted_years = numeric_years + str_years

    # 4. 构建统一 DataFrame
    merged_rows = []
    for yr in sorted_years:
        mdr_cnt = mdr_dict.get(yr, 0)
        pat_cnt = patient_dict.get(yr, 0)
        dev_cnt = device_dict.get(yr, 0)
        foi_cnt = foi_dict.get(yr, 0)
        
        # 显示年份格式
        yr_label = f"{yr} 年" if isinstance(yr, int) else str(yr)
        
        merged_rows.append({
            "年份": yr_label,
            "主表 (mdr_report)": mdr_cnt,
            "患者表 (patient)": pat_cnt,
            "设备数据 (device)": dev_cnt,
            "描述文本 (foi_text)": foi_cnt
        })

    df = pd.DataFrame(merged_rows)

    # 5. 生成 Markdown 宽表
    table_lines = []
    table_lines.append("| 年份 | 主表 (mdr_report) 记录数 | 患者表 (patient) 记录数 | 历史设备文件 (device) 导入行数 | 自由描述文本 (foi_text) 导入行数 |")
    table_lines.append("| :--- | :--- | :--- | :--- | :--- |")
    for _, r in df.iterrows():
        # 格式化数字，0 替换为 -
        mdr_str = f"{r['主表 (mdr_report)']:,}" if r['主表 (mdr_report)'] > 0 else "-"
        pat_str = f"{r['患者表 (patient)']:,}" if r['患者表 (patient)'] > 0 else "-"
        dev_str = f"{r['设备数据 (device)']:,}" if r['设备数据 (device)'] > 0 else "-"
        foi_str = f"{r['描述文本 (foi_text)']:,}" if r['描述文本 (foi_text)'] > 0 else "-"
        table_lines.append(f"| {r['年份']} | {mdr_str} | {pat_str} | {dev_str} | {foi_str} |")

    merged_table_text = "\n".join(table_lines)

    # 6. 读取原有报告，并重构前三节
    if os.path.exists(REPORT_PATH):
        with open(REPORT_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 寻找原本“四、”或“## 四、”的开始位置
        # 我们用正则来找，把前三节用一张汇总表代替
        pattern = r"(## 四、.*)"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            # 获取四节及以后的全部内容，并将标题序号做升华
            remaining_content = match.group(1)
            # 标题序号替换：四->二，五->三，六->四，七->五
            remaining_content = remaining_content.replace("## 四、", "## 二、")
            remaining_content = remaining_content.replace("## 五、", "## 三、")
            remaining_content = remaining_content.replace("## 六、", "## 四、")
            remaining_content = remaining_content.replace("## 七、", "## 五、")
        else:
            remaining_content = ""
            print("警告：未在原报告中定位到“## 四、”章节，保留后半部可能失败。")

        # 重构头部和第一节
        header = """# FDA MAUDE 数据库各年份全量记录汇总统计报告

> 本报告数据直接查询自 MySQL `maude_db` 数据库中的全量落盘数据。为便于直观比对，我们已将主表、患者表、历史设备文件及自由描述文本文件的按年度数据整理成一张统一的“年度数据底座汇总表”。

## 一、 MAUDE 年度数据导入与大盘记录数汇总表

以下表格完整对齐了各个年份的记录数。其中，主表与患者表的数据依据收到日期（`DATE_RECEIVED`）年份聚合，历史设备数据与描述文本数据则依据其原始年份文件的清洗载入行数进行汇总。

"""
        
        final_report_content = header + merged_table_text + "\n\n" + remaining_content
        
        with open(REPORT_PATH, 'w', encoding='utf-8') as f:
            f.write(final_report_content)
        print(f"\n>>> 成功将所有年份统计表合并到一张宽表中，并重新输出了报告：{REPORT_PATH}")
    else:
        print(f"未找到原始报告 {REPORT_PATH}")

if __name__ == '__main__':
    main()
