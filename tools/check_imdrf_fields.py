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
    
    # 1. 获取所有表
    cursor.execute("SHOW TABLES")
    tables = [t[0] for t in cursor.fetchall()]
    
    print(f"数据库 '{DB_NAME}' 中共有 {len(tables)} 张表：{tables}\n")
    
    found_imdrf = False
    all_fields = {}
    
    for table in tables:
        print(f">>> 正在检查表: {table} 的字段...")
        cursor.execute(f"DESCRIBE {table}")
        columns = cursor.fetchall()
        table_fields = []
        for col in columns:
            col_name = col[0]
            col_type = col[1]
            table_fields.append(col_name)
            if "imdrf" in col_name.lower():
                print(f"  [发现 IMDRF] 表: {table} | 字段名: {col_name} | 类型: {col_type}")
                found_imdrf = True
        all_fields[table] = table_fields
        
    if not found_imdrf:
        print("\n[结果] 没有在字段名中直接发现包含 'IMDRF' 的列。")
        print("\n为了方便您分析类似的编码字段，下面列出各个表中的核心编码/分类相关字段：")
        for table, fields in all_fields.items():
            print(f"\n表名: {table}")
            relevant_fields = [f for f in fields if any(kw in f.lower() for kw in ['code', 'type', 'problem', 'class', 'method', 'result', 'eval'])]
            for rf in relevant_fields:
                print(f"  - {rf}")
                
    conn.close()

if __name__ == '__main__':
    main()
