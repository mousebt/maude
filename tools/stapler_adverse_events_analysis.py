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

    print(">>> 正在创建临时表匹配 'stapler' 相关的唯一报告键 (MDR_REPORT_KEY)...", flush=True)
    
    # 1. 创建临时表
    cursor.execute("DROP TEMPORARY TABLE IF EXISTS temp_stapler_keys")
    t0 = time.time()
    cursor.execute("""
        CREATE TEMPORARY TABLE temp_stapler_keys AS
        SELECT DISTINCT MDR_REPORT_KEY
        FROM device
        WHERE GENERIC_NAME LIKE '%stapler%' OR BRAND_NAME LIKE '%stapler%'
    """)
    print(f"临时表创建完成，耗时: {time.time() - t0:.2f} 秒。", flush=True)
    
    # 2. 为临时表添加主键索引
    print(">>> 正在为临时表添加主键索引...", flush=True)
    t0 = time.time()
    cursor.execute("ALTER TABLE temp_stapler_keys ADD PRIMARY KEY (MDR_REPORT_KEY)")
    print(f"主键索引添加完成，耗时: {time.time() - t0:.2f} 秒。", flush=True)
    
    # 3. 统计唯一不良事件报告总数
    cursor.execute("SELECT COUNT(*) FROM temp_stapler_keys")
    total_reports = cursor.fetchone()[0]
    print(f"唯一不良事件报告总数 (以 'stapler' 模糊匹配): {total_reports:,}", flush=True)

    # 4. 统计与 'stapler' 相关的产品代码和通用名称分布
    print(">>> 正在统计与 'stapler' 相关的产品代码和通用名称分布...", flush=True)
    query_codes = """
        SELECT 
            DEVICE_REPORT_PRODUCT_CODE,
            GENERIC_NAME,
            COUNT(*) as record_count
        FROM device d
        JOIN temp_stapler_keys t ON d.MDR_REPORT_KEY = t.MDR_REPORT_KEY
        GROUP BY DEVICE_REPORT_PRODUCT_CODE, GENERIC_NAME
        ORDER BY record_count DESC
        LIMIT 20
    """
    cursor.execute(query_codes)
    categories = cursor.fetchall()
    
    print("\n[表 1] 包含 'stapler' 关键字的前 20 个产品代码及通用名称：", flush=True)
    print("-" * 100, flush=True)
    print(f"{'产品代码':<10} | {'通用名称 (Generic Name)':<60} | {'报告记录数':<12}", flush=True)
    print("-" * 100, flush=True)
    for row in categories:
        code = row[0] or 'N/A'
        name = row[1].strip() if row[1] else 'Unknown'
        cnt = row[2]
        print(f"{code:<10} | {name[:60]:<60} | {cnt:<12,}", flush=True)
    print("-" * 100, flush=True)

    # 5. 严重度分类统计 (EVENT_TYPE: D-Death, IN-Injury, M-Malfunction, O-Other)
    print(">>> 正在统计不良事件的严重度分布 (根据 EVENT_TYPE)...", flush=True)
    query_severity = """
        SELECT 
            m.EVENT_TYPE,
            COUNT(*) as report_count
        FROM temp_stapler_keys t
        JOIN mdr_report m ON t.MDR_REPORT_KEY = m.MDR_REPORT_KEY
        GROUP BY m.EVENT_TYPE
        ORDER BY report_count DESC
    """
    cursor.execute(query_severity)
    severity_rows = cursor.fetchall()
    
    print("\n[表 2] 严重度分布：", flush=True)
    print("-" * 60, flush=True)
    print(f"{'事件类型代码':<15} | {'事件类型描述':<20} | {'报告数量':<12} | {'占比':<8}", flush=True)
    print("-" * 60, flush=True)
    
    event_type_desc = {
        'D': 'Death (死亡)',
        'IN': 'Injury (严重伤害)',
        'M': 'Malfunction (设备故障)',
        'O': 'Other (其他/未分类)',
        '*': 'Other (*)',
    }
    
    for row in severity_rows:
        code = row[0] or 'Unknown'
        cnt = row[1]
        desc = event_type_desc.get(code, code)
        pct = (cnt / total_reports) * 100 if total_reports > 0 else 0
        print(f"{code:<15} | {desc:<20} | {cnt:<12,} | {pct:.2f}%", flush=True)
    print("-" * 60, flush=True)

    # 6. 历年不良事件报告趋势
    print(">>> 正在统计历年不良事件报告趋势...", flush=True)
    query_yearly = """
        SELECT 
            CASE 
                WHEN m.DATE_RECEIVED LIKE '%/%/%' THEN RIGHT(m.DATE_RECEIVED, 4)
                ELSE 'Unknown'
            END as r_year,
            COUNT(*) as report_count
        FROM temp_stapler_keys t
        JOIN mdr_report m ON t.MDR_REPORT_KEY = m.MDR_REPORT_KEY
        GROUP BY r_year
        ORDER BY r_year ASC
    """
    cursor.execute(query_yearly)
    yearly_rows = cursor.fetchall()
    
    print("\n[表 3] 历年不良事件上报趋势：", flush=True)
    print("-" * 40, flush=True)
    print(f"{'年份':<10} | {'报告数量':<15} | {'占比':<8}", flush=True)
    print("-" * 40, flush=True)
    for row in yearly_rows:
        year = row[0] if row[0] is not None else 'Unknown'
        cnt = row[1]
        pct = (cnt / total_reports) * 100 if total_reports > 0 else 0
        print(f"{str(year):<10} | {cnt:<15,} | {pct:.2f}%", flush=True)
    print("-" * 40, flush=True)

    # 7. 主要制造商/品牌分布
    print(">>> 正在统计前 10 大相关制造商 (MANUFACTURER_D_NAME)...", flush=True)
    query_manufacturers = """
        SELECT 
            d.MANUFACTURER_D_NAME,
            COUNT(*) as report_count
        FROM temp_stapler_keys t
        JOIN device d ON t.MDR_REPORT_KEY = d.MDR_REPORT_KEY
        GROUP BY d.MANUFACTURER_D_NAME
        ORDER BY report_count DESC
        LIMIT 10
    """
    cursor.execute(query_manufacturers)
    mfg_rows = cursor.fetchall()
    
    print("\n[表 4] 前 10 大制造商品类报告统计：", flush=True)
    print("-" * 80, flush=True)
    print(f"{'制造商名称':<55} | {'报告数量':<12} | {'占比':<8}", flush=True)
    print("-" * 80, flush=True)
    for row in mfg_rows:
        mfg = row[0].strip() if row[0] else 'Unknown'
        cnt = row[1]
        pct = (cnt / total_reports) * 100 if total_reports > 0 else 0
        print(f"{mfg[:55]:<55} | {cnt:<12,} | {pct:.2f}%", flush=True)
    print("-" * 80, flush=True)

    conn.close()

if __name__ == '__main__':
    main()
