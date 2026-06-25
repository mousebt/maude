import os
import time
import pymysql
from dotenv import load_dotenv

env_path = r"e:\pythonProjects\MAUDE\.env"
load_dotenv(env_path)

DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASSWORD', '123456')
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_NAME = os.getenv('DB_NAME') or 'maude_db'

def analyze():
    print("Connecting to database...")
    conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, port=DB_PORT, database=DB_NAME)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    print("Calculating total rows with non-empty BRAND_NAME and GENERIC_NAME...")
    t0 = time.time()
    
    # 统计总有效行数
    cursor.execute("""
        SELECT COUNT(*) as total_rows
        FROM device
        WHERE BRAND_NAME IS NOT NULL AND BRAND_NAME != ''
          AND GENERIC_NAME IS NOT NULL AND GENERIC_NAME != ''
          AND BRAND_NAME != '\\\\N' AND GENERIC_NAME != '\\\\N'
    """)
    total_rows = cursor.fetchone()['total_rows']
    print(f"Total valid device rows: {total_rows:,} (Calculated in {time.time() - t0:.2f}s)")
    
    # 获取所有的 unique pairs 按频次降序
    t0 = time.time()
    print("Fetching unique pairs with counts sorted by frequency...")
    sql = """
        SELECT BRAND_NAME, GENERIC_NAME, COUNT(*) as cnt
        FROM device
        WHERE BRAND_NAME IS NOT NULL AND BRAND_NAME != ''
          AND GENERIC_NAME IS NOT NULL AND GENERIC_NAME != ''
          AND BRAND_NAME != '\\\\N' AND GENERIC_NAME != '\\\\N'
        GROUP BY BRAND_NAME, GENERIC_NAME
        ORDER BY cnt DESC
    """
    cursor.execute(sql)
    rows = cursor.fetchall()
    print(f"Total unique pairs: {len(rows):,} (Fetched in {time.time() - t0:.2f}s)")
    
    # 计算累积覆盖率
    accumulated = 0
    coverage_80_count = None
    coverage_90_count = None
    coverage_95_count = None
    
    for idx, row in enumerate(rows, 1):
        accumulated += row['cnt']
        ratio = accumulated / total_rows
        
        if coverage_80_count is None and ratio >= 0.80:
            coverage_80_count = idx
        if coverage_90_count is None and ratio >= 0.90:
            coverage_90_count = idx
        if coverage_95_count is None and ratio >= 0.95:
            coverage_95_count = idx
            
    print("\n--- Coverage Analysis Results ---")
    print(f"To reach 80% coverage: {coverage_80_count:,} unique pairs")
    print(f"To reach 90% coverage: {coverage_90_count:,} unique pairs")
    print(f"To reach 95% coverage: {coverage_95_count:,} unique pairs")
    
    conn.close()

if __name__ == '__main__':
    analyze()
