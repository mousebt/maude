import os
import pymysql
import csv
import time
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(BASE_DIR, ".env")
load_dotenv(env_path)

DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASSWORD', '123456')
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_NAME = os.getenv('DB_NAME') or 'maude_db'

def export_table_by_keys(cursor, table_name, keys, output_dir):
    """
    通过 keys 点查指定表的所有字段，并导出为 CSV 文件。
    """
    t_start = time.time()
    csv_file = os.path.join(output_dir, f"davinci_death_{table_name}.csv")
    print(f" 正在导出表 {table_name} ...")
    
    # 动态获取表字段，以支持 SELECT *
    # 为防 IN 条件过长，进行分批查询
    batch_size = 50000
    rows = []
    headers = []
    
    for i in range(0, len(keys), batch_size):
        sub_keys = keys[i : i + batch_size]
        format_strings = ','.join(['%s'] * len(sub_keys))
        sql = f"SELECT * FROM {table_name} WHERE MDR_REPORT_KEY IN ({format_strings})"
        
        cursor.execute(sql, tuple(sub_keys))
        if i == 0:
            headers = [desc[0] for desc in cursor.description]
        rows.extend(cursor.fetchall())
        
    if not rows:
        print(f"  [提示] 表 {table_name} 中未找到关联的数据。")
        return
        
    with open(csv_file, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
        
    print(f"  [完成] 成功写入 {len(rows)} 行记录，文件保存至: {csv_file} (耗时: {time.time() - t_start:.2f} 秒)")

def main():
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        database=DB_NAME
    )
    cursor = conn.cursor()

    print(">>> 正在检索达芬奇致死病例关联的 720 个核心 MDR_REPORT_KEY...")
    
    # 1. 捞取所有的达芬奇设备关联键
    sql_nay = "SELECT MDR_REPORT_KEY FROM device WHERE DEVICE_REPORT_PRODUCT_CODE = 'NAY'"
    cursor.execute(sql_nay)
    nay_keys = [r[0] for r in cursor.fetchall()]

    sql_non_nay_vinci = """
        SELECT MDR_REPORT_KEY FROM device 
        WHERE (BRAND_NAME LIKE '%da vinci%' OR BRAND_NAME LIKE '%davinci%')
          AND (DEVICE_REPORT_PRODUCT_CODE != 'NAY' OR DEVICE_REPORT_PRODUCT_CODE IS NULL)
    """
    cursor.execute(sql_non_nay_vinci)
    non_nay_keys = [r[0] for r in cursor.fetchall()]

    all_dev_keys = list(set(nay_keys + non_nay_keys))

    # 2. 筛选致死病例 (EVENT_TYPE = 'D') 的报告键值
    death_report_keys = []
    batch_size = 50000
    for idx in range(0, len(all_dev_keys), batch_size):
        sub_keys = all_dev_keys[idx : idx + batch_size]
        format_strings = ','.join(['%s'] * len(sub_keys))
        sql_deaths = f"SELECT MDR_REPORT_KEY FROM mdr_report WHERE MDR_REPORT_KEY IN ({format_strings}) AND EVENT_TYPE = 'D'"
        cursor.execute(sql_deaths, tuple(sub_keys))
        death_report_keys.extend([r[0] for r in cursor.fetchall()])

    print(f"共锁定 {len(death_report_keys)} 个达芬奇相关致死报告键值。")

    if not death_report_keys:
        print("未找到致死病例。")
        conn.close()
        return

    # 创建输出目录
    output_dir = os.path.join(BASE_DIR, "reports", "davinci_death_dataset")
    os.makedirs(output_dir, exist_ok=True)
    print(f"数据导出目标文件夹: {output_dir}\n")

    # 3. 遍历各个表进行完整导出
    tables_to_export = ["mdr_report", "device", "patient", "foi_text", "foi_text_overflow"]
    for table in tables_to_export:
        try:
            export_table_by_keys(cursor, table, death_report_keys, output_dir)
        except Exception as e:
            print(f"  [错误] 导出表 {table} 失败: {e}")

    print("\n>>> 所有关系型子集表格均已导出完成！")
    conn.close()

if __name__ == '__main__':
    main()
