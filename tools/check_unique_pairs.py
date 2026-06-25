import os
import pymysql
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(BASE_DIR, ".env")
load_dotenv(env_path)

DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASSWORD', '123456')
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_NAME = os.getenv('DB_NAME') or 'maude_db'

def main():
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        database=DB_NAME
    )
    cursor = conn.cursor()

    print(">>> 正在从 device_unique_pairs 缓存表中模糊检索包含达芬奇名称的唯一键对...")
    sql = """
        SELECT BRAND_NAME, GENERIC_NAME, CNT 
        FROM device_unique_pairs 
        WHERE BRAND_NAME LIKE '%da vinci%' OR BRAND_NAME LIKE '%davinci%'
        ORDER BY CNT DESC
    """
    cursor.execute(sql)
    rows = cursor.fetchall()
    
    print(f"找到 {len(rows)} 个唯一的达芬奇设备品牌-通用名称组合：")
    for idx, r in enumerate(rows[:20], 1):
        print(f"  {idx}. Brand: {r[0]} | Generic: {r[1]} | Count: {r[2]}")
        
    conn.close()

if __name__ == '__main__':
    main()
