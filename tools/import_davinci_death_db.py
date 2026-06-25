import os
import pymysql
import csv
import time
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(BASE_DIR, ".env")
load_dotenv(env_path)

DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASSWORD', '123456')
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', 3306))
NEW_DB_NAME = 'davinci_death_db'

def create_and_import(csv_path, table_name, cursor, conn):
    t_start = time.time()
    
    # 1. 读取 CSV 头部获取字段名称
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        
    # 2. 动态构造建表语句
    col_defs = []
    for h in headers:
        # 智能判定主外键和整数字段为 BIGINT，其余为 LONGTEXT 保证兼容性
        if h in ('MDR_REPORT_KEY', 'MDR_TEXT_KEY', 'EVENT_KEY', 'DEVICE_EVENT_KEY', 'PATIENT_SEQUENCE_NUMBER'):
            col_defs.append(f"`{h}` BIGINT")
        else:
            col_defs.append(f"`{h}` LONGTEXT")
            
    create_sql = f"CREATE TABLE `{table_name}` ({', '.join(col_defs)}) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"
    
    cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
    cursor.execute(create_sql)
    
    # 3. 自动建立物理索引以支持后续多表关联
    if 'MDR_REPORT_KEY' in headers:
        cursor.execute(f"ALTER TABLE `{table_name}` ADD INDEX `idx_mdr_key` (`MDR_REPORT_KEY`)")
    if 'MDR_TEXT_KEY' in headers:
        cursor.execute(f"ALTER TABLE `{table_name}` ADD INDEX `idx_text_key` (`MDR_TEXT_KEY`)")
        
    conn.commit()

    # 4. 读取数据并批量插入
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # 跳过表头
        rows = [list(row) for row in reader]

    if rows:
        placeholders = ', '.join(['%s'] * len(headers))
        insert_sql = f"INSERT INTO `{table_name}` ({', '.join([f'`{h}`' for h in headers])}) VALUES ({placeholders})"
        
        # 精细化清洗数据：处理整数类型的 \N, 空字符, 浮点数；处理文本类型的 \N
        rows_cleaned = []
        for row in rows:
            cleaned_row = []
            for col_idx, col in enumerate(row):
                h_name = headers[col_idx]
                is_int_col = h_name in ('MDR_REPORT_KEY', 'MDR_TEXT_KEY', 'EVENT_KEY', 'DEVICE_EVENT_KEY', 'PATIENT_SEQUENCE_NUMBER')
                
                if is_int_col:
                    if not col or col == '\\N' or col.strip() == '':
                        cleaned_row.append(None)
                    else:
                        try:
                            # 兼容 "1.0" 这种浮点字符串转 int 的情况
                            cleaned_row.append(int(float(col)))
                        except ValueError:
                            cleaned_row.append(None)
                else:
                    if col == '\\N':
                        cleaned_row.append(None)
                    else:
                        cleaned_row.append(None if col == '' else col)
            cleaned_row_item = cleaned_row
            rows_cleaned.append(cleaned_row_item)

        
        # 分批写入
        batch_size = 500
        for i in range(0, len(rows_cleaned), batch_size):
            batch = rows_cleaned[i : i + batch_size]
            cursor.executemany(insert_sql, batch)
            
        conn.commit()

        
    print(f"  [成功] 表 `{table_name}` 导入完毕，共 {len(rows)} 行记录 (耗时: {time.time() - t_start:.2f} 秒)")

def main():
    # 1. 先连接本地 MySQL 实例（不指定数据库）以创建新数据库
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )
    cursor = conn.cursor()

    print(f">>> 正在创建全新的专有数据库 `{NEW_DB_NAME}`...")
    cursor.execute(f"DROP DATABASE IF EXISTS `{NEW_DB_NAME}`")
    cursor.execute(f"CREATE DATABASE `{NEW_DB_NAME}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    conn.commit()
    conn.close()

    # 2. 重新连接新创建的数据库
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        database=NEW_DB_NAME
    )
    cursor = conn.cursor()

    dataset_dir = os.path.join(BASE_DIR, "reports", "davinci_death_dataset")
    print(f"源 CSV 文件夹路径: {dataset_dir}\n")

    # 定义要导入的表与其对应的 CSV 文件名
    tables_config = {
        "mdr_report": "davinci_death_mdr_report.csv",
        "device": "davinci_death_device.csv",
        "patient": "davinci_death_patient.csv",
        "foi_text": "davinci_death_foi_text.csv",
        "foi_text_overflow": "davinci_death_foi_text_overflow.csv"
    }

    # 遍历并导入
    for table_name, csv_file in tables_config.items():
        csv_path = os.path.join(dataset_dir, csv_file)
        if os.path.exists(csv_path):
            create_and_import(csv_path, table_name, cursor, conn)
        else:
            print(f"  [跳过] 未找到对应的 CSV 文件: {csv_path}")

    # 3. 验证数据库中的表和总记录数
    print("\n>>> 正在验证新数据库的导入状态...")
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print("当前数据库中的表：")
    for t in tables:
        cursor.execute(f"SELECT COUNT(*) FROM `{t[0]}`")
        count = cursor.fetchone()[0]
        print(f"  表: {t[0]:<20} | 导入行数: {count}")

    conn.close()
    print(f"\n>>> 专有分析库 `{NEW_DB_NAME}` 关系型数据集导入工作全部完成！")

if __name__ == '__main__':
    main()
