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

def main():
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        database=DB_NAME
    )
    cursor = conn.cursor()
    
    # 1. 查询表结构
    print(">>> 正在查看 mdr_report 表的结构中关于日期字段的信息...")
    cursor.execute("DESCRIBE mdr_report")
    for row in cursor.fetchall():
        if 'DATE' in row[0] or 'date' in row[0].lower():
            print(f"字段名: {row[0]}, 类型: {row[1]}, 是否为空: {row[2]}, 键: {row[3]}, 默认值: {row[4]}")
            
    # 2. 查询前几条数据的实际日期值
    print("\n>>> 正在查看 mdr_report 表前 10 条记录的日期实际值...")
    cursor.execute("SELECT MDR_REPORT_KEY, DATE_RECEIVED, DATE_REPORT, DATE_OF_EVENT FROM mdr_report LIMIT 10")
    for row in cursor.fetchall():
        print(f"MDR_REPORT_KEY: {row[0]} | DATE_RECEIVED: {row[1]} | DATE_REPORT: {row[2]} | DATE_OF_EVENT: {row[3]}")
        
    conn.close()

if __name__ == '__main__':
    main()
