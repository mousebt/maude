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

    print(">>> 正在查询当前数据库各表的实际物理行数与存储空间...")
    
    # 从 information_schema 查询表大小和行数
    sql = """
        SELECT 
            TABLE_NAME, 
            TABLE_ROWS, 
            ROUND((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2) AS TOTAL_MB,
            ROUND(DATA_LENGTH / 1024 / 1024, 2) AS DATA_MB,
            ROUND(INDEX_LENGTH / 1024 / 1024, 2) AS INDEX_MB
        FROM information_schema.TABLES 
        WHERE TABLE_SCHEMA = %s
        ORDER BY TOTAL_MB DESC
    """
    cursor.execute(sql, (DB_NAME,))
    rows = cursor.fetchall()
    
    print("\n数据库表信息明细：")
    for r in rows:
        print(f"  表名: {r[0]:<25} | 预估行数: {r[1]:,>12} | 总空间: {r[2]:>8} MB (数据: {r[3]:>8} MB, 索引: {r[4]:>8} MB)")
        
    conn.close()

if __name__ == '__main__':
    main()
