import os
import time
import pymysql
from dotenv import load_dotenv

# Load env file from the parent directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(BASE_DIR, ".env")
load_dotenv(env_path)

DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASSWORD', '123456')
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_NAME = os.getenv('DB_NAME') or 'maude_db'

def get_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        database=DB_NAME
    )

def main():
    conn = get_connection()
    cursor = conn.cursor()

    print(">>> 正在分步创建 2020 年以后吻合器不良事件临时表...", flush=True)
    t_start = time.time()
    
    # 1. 筛选全量吻合器报告主键
    cursor.execute("DROP TEMPORARY TABLE IF EXISTS temp_all_staplers")
    t0 = time.time()
    cursor.execute("""
        CREATE TEMPORARY TABLE temp_all_staplers AS
        SELECT DISTINCT MDR_REPORT_KEY
        FROM device
        WHERE GENERIC_NAME LIKE '%stapler%' OR BRAND_NAME LIKE '%stapler%'
    """)
    cursor.execute("ALTER TABLE temp_all_staplers ADD PRIMARY KEY (MDR_REPORT_KEY)")
    print(f"  [1/2] 全量吻合器报告过滤完成，用时: {time.time() - t0:.2f} 秒。", flush=True)
    
    # 2. 筛选 2020 年以后的唯一吻合器不良事件报告主键
    cursor.execute("DROP TEMPORARY TABLE IF EXISTS temp_stapler_2020")
    t0 = time.time()
    cursor.execute("""
        CREATE TEMPORARY TABLE temp_stapler_2020 AS
        SELECT t.MDR_REPORT_KEY
        FROM temp_all_staplers t
        JOIN mdr_report m ON t.MDR_REPORT_KEY = m.MDR_REPORT_KEY
        WHERE m.DATE_RECEIVED LIKE '%/%/%'
          AND RIGHT(m.DATE_RECEIVED, 4) >= '2020'
    """)
    cursor.execute("ALTER TABLE temp_stapler_2020 ADD PRIMARY KEY (MDR_REPORT_KEY)")
    
    # 统计 2020 年以后的唯一报告总数
    cursor.execute("SELECT COUNT(*) FROM temp_stapler_2020")
    total_events = cursor.fetchone()[0]
    print(f"  [2/2] 2020 年以后唯一报告过滤完成，当前共有 {total_events:,} 起事件。用时: {time.time() - t0:.2f} 秒。", flush=True)
    print(f"临时表分步筛选全部完成，总共用时: {time.time() - t_start:.2f} 秒。\n", flush=True)

    # 3. 关联 device_problem_code 统计高频故障编码 (对应 IMDRF Annex A)
    print(">>> 正在直接关联字段统计高频器械故障编码 (对应 IMDRF Annex A)...", flush=True)
    t0 = time.time()
    query_dev_problems = """
        SELECT 
            dpc.DEVICE_PROBLEM_CODE,
            COUNT(*) as event_count
        FROM temp_stapler_2020 t
        JOIN device_problem_code dpc ON t.MDR_REPORT_KEY = dpc.MDR_REPORT_KEY
        GROUP BY dpc.DEVICE_PROBLEM_CODE
        ORDER BY event_count DESC
        LIMIT 15
    """
    cursor.execute(query_dev_problems)
    dev_rows = cursor.fetchall()
    print(f"  器械故障统计完成，用时: {time.time() - t0:.2f} 秒。", flush=True)
    
    print("\n[表 6] 2020 年以后吻合器高频器械故障编码统计 (直接字段提取)：")
    print("-" * 65)
    print(f"{'序号':<4} | {'故障代码':<12} | {'关联事件数':<12} | {'事件占比':<8}")
    print("-" * 65)
    for idx, row in enumerate(dev_rows, 1):
        code = row[0] or 'Unknown'
        cnt = row[1]
        pct = (cnt / total_events) * 100 if total_events > 0 else 0
        print(f"{idx:<4} | {code:<12} | {cnt:<12,} | {pct:.2f}%")
    print("-" * 65)

    # 4. 关联 patient_problem_code 统计高频临床伤害编码 (对应 IMDRF Annex E)
    print("\n>>> 正在直接关联字段统计高频患者临床损害编码 (对应 IMDRF Annex E)...", flush=True)
    t0 = time.time()
    query_pat_problems = """
        SELECT 
            ppc.PATIENT_PROBLEM_CODE,
            COUNT(*) as event_count
        FROM temp_stapler_2020 t
        JOIN patient_problem_code ppc ON t.MDR_REPORT_KEY = ppc.MDR_REPORT_KEY
        GROUP BY ppc.PATIENT_PROBLEM_CODE
        ORDER BY event_count DESC
        LIMIT 15
    """
    cursor.execute(query_pat_problems)
    pat_rows = cursor.fetchall()
    print(f"  患者损害统计完成，用时: {time.time() - t0:.2f} 秒。", flush=True)
    
    print("\n[表 7] 2020 年以后吻合器高频患者临床损害编码统计 (直接字段提取)：")
    print("-" * 65)
    print(f"{'序号':<4} | {'损害代码':<12} | {'关联事件数':<12} | {'事件占比':<8}")
    print("-" * 65)
    for idx, row in enumerate(pat_rows, 1):
        code = row[0] or 'Unknown'
        cnt = row[1]
        pct = (cnt / total_events) * 100 if total_events > 0 else 0
        print(f"{idx:<4} | {code:<12} | {cnt:<12,} | {pct:.2f}%")
    print("-" * 65)

    conn.close()

if __name__ == '__main__':
    main()
