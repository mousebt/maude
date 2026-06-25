import os
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

    print(">>> 正在检测 device_problem_code 中是否存在字母开头的 IMDRF/NCI 编码...")
    
    # 查询包含字母的故障代码
    query = """
        SELECT DEVICE_PROBLEM_CODE, COUNT(1) as cnt 
        FROM device_problem_code 
        WHERE DEVICE_PROBLEM_CODE REGEXP '^[A-Za-z]' 
        GROUP BY DEVICE_PROBLEM_CODE 
        ORDER BY cnt DESC
        LIMIT 10
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    
    if rows:
        print("  发现以下字母开头的故障编码：")
        for r in rows:
            print(f"    代码: {r[0]:<15} | 频数: {r[1]:,}")
    else:
        print("  没有发现任何以字母开头的故障编码。")

    print("\n>>> 正在检测 patient_problem_code 中是否存在字母开头的 IMDRF/NCI 编码...")
    query_pat = """
        SELECT PATIENT_PROBLEM_CODE, COUNT(1) as cnt 
        FROM patient_problem_code 
        WHERE PATIENT_PROBLEM_CODE REGEXP '^[A-Za-z]' 
        GROUP BY PATIENT_PROBLEM_CODE 
        ORDER BY cnt DESC
        LIMIT 10
    """
    cursor.execute(query_pat)
    rows_pat = cursor.fetchall()
    
    if rows_pat:
        print("  发现以下字母开头的患者损害编码：")
        for r in rows_pat:
            print(f"    代码: {r[0]:<15} | 频数: {r[1]:,}")
    else:
        print("  没有发现任何以字母开头的患者损害编码。")

    conn.close()

if __name__ == '__main__':
    main()
