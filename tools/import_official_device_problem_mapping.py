import os
import csv
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

CSV_PATH = os.path.join(BASE_DIR, "data", "raw", "deviceproblemcodes2025.csv")

def main():
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        database=DB_NAME
    )
    cursor = conn.cursor()

    # 1. 创建官方映射对照表
    print(">>> 正在创建官方对照表 fda_device_problem_mapping...", flush=True)
    cursor.execute("DROP TABLE IF EXISTS fda_device_problem_mapping")
    create_sql = """
        CREATE TABLE fda_device_problem_mapping (
            FDA_CODE VARCHAR(50) PRIMARY KEY,
            TERM VARCHAR(255),
            NCIT_CODE VARCHAR(50),
            IMDRF_CODE VARCHAR(50)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    cursor.execute(create_sql)

    # 2. 读取并导入 CSV 数据
    print(f">>> 正在从 {CSV_PATH} 读取映射关系...", flush=True)
    rows_to_insert = []
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)  # 跳过表头 FDA_CODE,TERM,NCIT_CODE,IMDRF_CODE
        for row in reader:
            if len(row) >= 4:
                fda_code = row[0].strip()
                term = row[1].strip()
                ncit_code = row[2].strip()
                imdrf_code = row[3].strip()
                # 过滤空的 fda_code
                if fda_code:
                    rows_to_insert.append((fda_code, term, ncit_code, imdrf_code))

    print(f"    共解析出 {len(rows_to_insert)} 条有效记录，正在插入数据库...", flush=True)
    insert_sql = """
        INSERT INTO fda_device_problem_mapping (FDA_CODE, TERM, NCIT_CODE, IMDRF_CODE)
        VALUES (%s, %s, %s, %s)
    """
    cursor.executemany(insert_sql, rows_to_insert)
    conn.commit()
    print(">>> 官方器械故障编码映射对照表导入完成！\n", flush=True)

    # 3. 统计 2020 年以后吻合器不良事件，通过官方映射表转换成 IMDRF
    print(">>> 正在分步创建 2020 年以后吻合器不良事件临时表...", flush=True)
    
    # 筛选全量吻合器报告主键
    cursor.execute("DROP TEMPORARY TABLE IF EXISTS temp_all_staplers")
    cursor.execute("""
        CREATE TEMPORARY TABLE temp_all_staplers AS
        SELECT DISTINCT MDR_REPORT_KEY
        FROM device
        WHERE GENERIC_NAME LIKE '%stapler%' OR BRAND_NAME LIKE '%stapler%'
    """)
    cursor.execute("ALTER TABLE temp_all_staplers ADD PRIMARY KEY (MDR_REPORT_KEY)")
    
    # 筛选 2020 年以后的唯一吻合器不良事件报告主键
    cursor.execute("DROP TEMPORARY TABLE IF EXISTS temp_stapler_2020")
    cursor.execute("""
        CREATE TEMPORARY TABLE temp_stapler_2020 AS
        SELECT t.MDR_REPORT_KEY
        FROM temp_all_staplers t
        JOIN mdr_report m ON t.MDR_REPORT_KEY = m.MDR_REPORT_KEY
        WHERE m.DATE_RECEIVED LIKE '%/%/%'
          AND RIGHT(m.DATE_RECEIVED, 4) >= '2020'
    """)
    cursor.execute("ALTER TABLE temp_stapler_2020 ADD PRIMARY KEY (MDR_REPORT_KEY)")
    
    cursor.execute("SELECT COUNT(*) FROM temp_stapler_2020")
    total_events = cursor.fetchone()[0]
    print(f"    2020年以后吻合器不良事件总数 (唯一报告数): {total_events:,} 起。\n", flush=True)

    # 4. 执行 SQL JOIN 联表查询：统计最频繁的器械故障对应的官方 IMDRF_CODE 及其官方描述
    print(">>> 正在执行 SQL JOIN 获取前 15 大 IMDRF 器械故障分布 (使用官方对照表)...", flush=True)
    query_imdrf = """
        SELECT 
            m.IMDRF_CODE,
            m.TERM as official_term,
            dpc.DEVICE_PROBLEM_CODE as fda_code,
            COUNT(*) as event_count
        FROM temp_stapler_2020 t
        JOIN device_problem_code dpc ON t.MDR_REPORT_KEY = dpc.MDR_REPORT_KEY
        LEFT JOIN fda_device_problem_mapping m ON dpc.DEVICE_PROBLEM_CODE = m.FDA_CODE
        GROUP BY m.IMDRF_CODE, m.TERM, dpc.DEVICE_PROBLEM_CODE
        ORDER BY event_count DESC
        LIMIT 15
    """
    cursor.execute(query_imdrf)
    results = cursor.fetchall()

    print("\n[表 1] 2020 年以后吻合器不良事件 IMDRF 官方映射统计结果 (前 15 大故障模式)：")
    print("-" * 125)
    print(f"{'排名':<4} | {'IMDRF 代码':<12} | {'官方英文描述 (TERM)':<45} | {'FDA 代码':<10} | {'事件数':<10} | {'占比':<8}")
    print("-" * 125)
    for idx, row in enumerate(results, 1):
        imdrf = row[0] or 'Pending/None'
        term = row[1] or 'Unknown Device Problem'
        fda = row[2] or 'N/A'
        cnt = row[3]
        pct = (cnt / total_events) * 100 if total_events > 0 else 0
        # 截断太长的 TERM 方便显示
        if len(term) > 43:
            term = term[:40] + "..."
        print(f"{idx:<4} | {imdrf:<12} | {term:<45} | {fda:<10} | {cnt:<10,} | {pct:.2f}%")
    print("-" * 125)

    conn.close()

if __name__ == '__main__':
    main()
