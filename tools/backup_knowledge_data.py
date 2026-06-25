import os
import shutil
import pymysql
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(BASE_DIR, ".env")
load_dotenv(env_path)

DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASSWORD', '123456')
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_NAME = 'davinci_death_db'

def backup_files():
    dataset_dir = os.path.join(BASE_DIR, "reports", "davinci_death_dataset")
    csv_path = os.path.join(dataset_dir, "davinci_death_knowledge_base.csv")
    json_path = os.path.join(dataset_dir, "llm_test_results.json")
    
    if os.path.exists(csv_path):
        backup_csv = os.path.join(dataset_dir, "davinci_death_knowledge_base_backup.csv")
        shutil.copyfile(csv_path, backup_csv)
        print(f"[备份成功] 文件: {csv_path} -> {backup_csv}")
    else:
        print("[未发现文件] 无法备份 CSV 文件")
        
    if os.path.exists(json_path):
        backup_json = os.path.join(dataset_dir, "llm_test_results_backup.json")
        shutil.copyfile(json_path, backup_json)
        print(f"[备份成功] 文件: {json_path} -> {backup_json}")
    else:
        print("[未发现文件] 无法备份 JSON 结果")

def backup_db_table():
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT,
            database=DB_NAME
        )
        cursor = conn.cursor()
        
        # 备份表结构和数据
        cursor.execute("DROP TABLE IF EXISTS foi_text_knowledge_backup")
        cursor.execute("CREATE TABLE foi_text_knowledge_backup AS SELECT * FROM foi_text_knowledge")
        conn.commit()
        
        # 获取行数验证
        cursor.execute("SELECT COUNT(*) FROM foi_text_knowledge_backup")
        cnt = cursor.fetchone()[0]
        print(f"[备份成功] 数据库表: foi_text_knowledge -> foi_text_knowledge_backup (备份记录数: {cnt})")
        
        conn.close()
    except Exception as e:
        print(f"[数据库备份失败] 异常原因: {e}")

if __name__ == '__main__':
    print(">>> 正在启动数据备份流程...")
    backup_files()
    backup_db_table()
    print(">>> 备份工作全部完成！\n")
