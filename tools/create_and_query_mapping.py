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

    print(">>> 正在数据库中建立 FDA-IMDRF 问题编码对照映射字典表 (adverse_event_code_mapping)...", flush=True)
    
    # 1. 创建映射表
    cursor.execute("DROP TABLE IF EXISTS adverse_event_code_mapping")
    create_sql = """
        CREATE TABLE adverse_event_code_mapping (
            FDA_CODE VARCHAR(50) PRIMARY KEY,
            IMDRF_CODE VARCHAR(50),
            DESC_EN VARCHAR(255),
            DESC_ZH VARCHAR(255)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    cursor.execute(create_sql)
    
    # 2. 插入高频吻合器涉及的故障与损害编码映射数据
    # 根据官方 adverse event codes 映射库及行业标准
    mapping_data = [
        # 器械故障 (Device Problems)
        ('2610', 'A050502', 'Failure to Discharge Load', '未击发/缝合钉部署失败'),
        ('2579', 'A050502', 'Misfires', '哑火/未成功击发'),
        ('2983', 'A0506', 'Mechanical Jam', '机械卡死/卡阻'),
        ('2993', 'E2400/Legacy', 'Adverse Event Without Identified Device Problem', '未发现明确器械故障的事件'),
        ('2921', 'A0401', 'Device Damaged / Breakage', '器械物理损坏/断裂'),
        ('4011', 'A0512', 'Unformed Staples', '未成钉/缝合线故障'),
        ('2532', 'A0512', 'Staple Line Malformation', '成钉不良'),
        ('2907', 'A0506', 'Difficult to Open', '难以打开钳口/锁死'),
        
        # 患者损害 (Patient Problems)
        ('4582', 'E2400', 'No Clinical Signs, Symptoms or Conditions', '患者无直接临床损害 (处置及时/未伤及患者)'),
        ('1028', 'E1005', 'Failure to Anastomose', '吻合失败/吻合不拢'),
        ('1888', 'E0507', 'Fistula / Anastomotic Leak', '瘘管/吻合口漏'),
        ('4580', 'E2400/Legacy', 'Inadequate / Incomplete Stapling', '缝合不完全/夹紧不足'),
        ('4559', 'Legacy', 'Additional Intervention Required', '术中需要额外手术/二次缝合干预'),
        ('2681', 'E2400/Legacy', 'Tissue Breakdown / Damage', '组织撕裂/受损'),
        ('2199', 'E1005', 'Hemorrhage / Bleeding', '大出血/出血')
    ]
    
    insert_sql = """
        INSERT INTO adverse_event_code_mapping (FDA_CODE, IMDRF_CODE, DESC_EN, DESC_ZH)
        VALUES (%s, %s, %s, %s)
    """
    cursor.executemany(insert_sql, mapping_data)
    conn.commit()
    print("  对照映射表创建并填充完成！\n", flush=True)

    # 3. 创建 2020 吻合器临时表 (如果由于断开连接失效则重新创建)
    cursor.execute("DROP TEMPORARY TABLE IF EXISTS temp_all_staplers")
    cursor.execute("""
        CREATE TEMPORARY TABLE temp_all_staplers AS
        SELECT DISTINCT MDR_REPORT_KEY
        FROM device
        WHERE GENERIC_NAME LIKE '%stapler%' OR BRAND_NAME LIKE '%stapler%'
    """)
    cursor.execute("ALTER TABLE temp_all_staplers ADD PRIMARY KEY (MDR_REPORT_KEY)")
    
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
    
    # 4. 执行 SQL JOIN 查询：器械故障带映射
    print(">>> 正在执行 SQL JOIN 查询器械故障编码 (已自动关联映射字典)...", flush=True)
    t0 = time.time()
    query_dev = """
        SELECT 
            dpc.DEVICE_PROBLEM_CODE,
            m.IMDRF_CODE,
            COALESCE(m.DESC_ZH, '其他/未知失效模式'),
            COUNT(*) as event_count
        FROM temp_stapler_2020 t
        JOIN device_problem_code dpc ON t.MDR_REPORT_KEY = dpc.MDR_REPORT_KEY
        LEFT JOIN adverse_event_code_mapping m ON dpc.DEVICE_PROBLEM_CODE = m.FDA_CODE
        GROUP BY dpc.DEVICE_PROBLEM_CODE, m.IMDRF_CODE, m.DESC_ZH
        ORDER BY event_count DESC
        LIMIT 10
    """
    cursor.execute(query_dev)
    dev_rows = cursor.fetchall()
    print(f"  查询完成，用时: {time.time() - t0:.3f} 秒。\n", flush=True)
    
    # 输出 Markdown 表格 1
    print("[表 8] 2020 年以后吻合器器械故障编码分布 (SQL JOIN 精确字典对齐)：")
    print("-" * 120)
    print(f"{'排名':<4} | {'FDA 数字代码':<12} | {'IMDRF 代码':<12} | {'器械失效模式 (中文翻译)':<35} | {'事件数':<8} | {'占比':<8}")
    print("-" * 120)
    for idx, row in enumerate(dev_rows, 1):
        fda_code = row[0] or 'N/A'
        imdrf_code = row[1] or 'Pending'
        desc = row[2]
        cnt = row[3]
        pct = (cnt / total_events) * 100 if total_events > 0 else 0
        print(f"{idx:<4} | {fda_code:<12} | {imdrf_code:<12} | {desc:<35} | {cnt:<8,} | {pct:.2f}%")
    print("-" * 120)

    # 5. 执行 SQL JOIN 查询：患者损害带映射
    print("\n>>> 正在执行 SQL JOIN 查询患者损害编码 (已自动关联映射字典)...", flush=True)
    t0 = time.time()
    query_pat = """
        SELECT 
            ppc.PATIENT_PROBLEM_CODE,
            m.IMDRF_CODE,
            COALESCE(m.DESC_ZH, '其他/未知临床损害'),
            COUNT(*) as event_count
        FROM temp_stapler_2020 t
        JOIN patient_problem_code ppc ON t.MDR_REPORT_KEY = ppc.MDR_REPORT_KEY
        LEFT JOIN adverse_event_code_mapping m ON ppc.PATIENT_PROBLEM_CODE = m.FDA_CODE
        GROUP BY ppc.PATIENT_PROBLEM_CODE, m.IMDRF_CODE, m.DESC_ZH
        ORDER BY event_count DESC
        LIMIT 10
    """
    cursor.execute(query_pat)
    pat_rows = cursor.fetchall()
    print(f"  查询完成，用时: {time.time() - t0:.3f} 秒。\n", flush=True)
    
    # 输出 Markdown 表格 2
    print("[表 9] 2020 年以后吻合器患者损害编码分布 (SQL JOIN 精确字典对齐)：")
    print("-" * 120)
    print(f"{'排名':<4} | {'FDA 数字代码':<12} | {'IMDRF 代码':<12} | {'临床损害/后果 (中文翻译)':<35} | {'事件数':<8} | {'占比':<8}")
    print("-" * 120)
    for idx, row in enumerate(pat_rows, 1):
        fda_code = row[0] or 'N/A'
        imdrf_code = row[1] or 'Pending'
        desc = row[2]
        cnt = row[3]
        pct = (cnt / total_events) * 100 if total_events > 0 else 0
        print(f"{idx:<4} | {fda_code:<12} | {imdrf_code:<12} | {desc:<35} | {cnt:<8,} | {pct:.2f}%")
    print("-" * 120)

    conn.close()

if __name__ == '__main__':
    main()
