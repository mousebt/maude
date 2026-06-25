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
    
    print(">>> 正在查看 foi_text_knowledge 表的列名...")
    cursor.execute("DESCRIBE foi_text_knowledge")
    for row in cursor.fetchall():
        print(f"字段: {row[0]:<30} | 类型: {row[1]:<20}")
        
    print("\n>>> 正在查看 foi_text_knowledge 表的行数...")
    cursor.execute("SELECT COUNT(*) FROM foi_text_knowledge")
    print(f"行数: {cursor.fetchone()[0]:,}")
    
    print("\n>>> 查看前 5 行示例数据...")
    cursor.execute("SELECT * FROM foi_text_knowledge LIMIT 5")
    for row in cursor.fetchall():
        print(row)
        
    conn.close()

if __name__ == '__main__':
    main()
