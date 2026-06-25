import os
import time
import pymysql
from dotenv import load_dotenv

# 获取基准目录并加载环境配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(BASE_DIR, ".env")
load_dotenv(env_path)

DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASSWORD', '123456')
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', 3306))
SRC_DB = os.getenv('DB_NAME', 'maude_db')
DST_DB = 'maude_stapler_db'

def get_connection(db_name=None):
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        database=db_name,
        charset='utf8mb4',
        autocommit=True
    )

def main():
    t_total_start = time.time()
    print("==================================================", flush=True)
    print(">>> 开始执行 FDA MAUDE 吻合器专有数据库导出任务...", flush=True)
    print("==================================================", flush=True)

    # 1. 建立无特定库的连接，用以创建/重构新库
    print(f"\n1. 连接 MySQL 实例并重构专有分析库 `{DST_DB}`...", flush=True)
    t0 = time.time()
    conn = get_connection()
    cursor = conn.cursor()
    
    # 强制清理老库并建新库
    cursor.execute(f"DROP DATABASE IF EXISTS `{DST_DB}`")
    cursor.execute(f"CREATE DATABASE `{DST_DB}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    print(f"   [成功] 数据库 `{DST_DB}` 创建成功，耗时: {time.time() - t0:.2f} 秒。", flush=True)
    conn.close()

    # 2. 重新连接到新数据库，准备进行克隆与搬运
    conn = get_connection(DST_DB)
    cursor = conn.cursor()

    # 3. 克隆源表物理表结构
    tables_to_clone = [
        "mdr_report",
        "device",
        "patient",
        "foi_text",
        "foi_text_overflow",
        "patient_problem_code",
        "device_problem_code"
    ]
    
    dict_tables_to_clone = [
        "device_hierarchy_mapping",
        "fda_device_problem_mapping"
    ]

    print("\n2. 克隆源数据库的数据表定义 (保留全部主外键和索引)...", flush=True)
    t0 = time.time()
    for table in tables_to_clone + dict_tables_to_clone:
        cursor.execute(f"CREATE TABLE `{DST_DB}`.`{table}` LIKE `{SRC_DB}`.`{table}`")
        print(f"   - 表结构克隆完成: {table}", flush=True)
    print(f"   [成功] 所有表定义克隆完毕，耗时: {time.time() - t0:.2f} 秒。", flush=True)

    # 4. 在原数据库提取吻合器唯一 MDR_REPORT_KEY，写入临时表
    print("\n3. 在源库匹配吻合器唯一 MDR_REPORT_KEY 并建立临时映射表...", flush=True)
    t0 = time.time()
    
    # 在新库中创建实体临时表方便全局 JOIN
    cursor.execute(f"CREATE TABLE `{DST_DB}`.`temp_stapler_keys` AS SELECT DISTINCT MDR_REPORT_KEY FROM `{SRC_DB}`.`device` WHERE GENERIC_NAME LIKE '%stapler%' OR BRAND_NAME LIKE '%stapler%'")
    cursor.execute(f"ALTER TABLE `{DST_DB}`.`temp_stapler_keys` ADD PRIMARY KEY (MDR_REPORT_KEY)")
    
    # 获取总数
    cursor.execute(f"SELECT COUNT(*) FROM `{DST_DB}`.`temp_stapler_keys`")
    total_keys = cursor.fetchone()[0]
    print(f"   [成功] 匹配提取完毕。共锁定 {total_keys:,} 起吻合器不良事件报告，耗时: {time.time() - t0:.2f} 秒。", flush=True)

    # 5. 分表进行跨库 INSERT INTO SELECT 搬运动作
    print("\n4. 开始执行跨库物理搬运关系型数据...", flush=True)
    
    for table in tables_to_clone:
        t_sub = time.time()
        print(f"   正在搬运表 `{table}` ... ", end="", flush=True)
        
        if table == "device":
            sql = f"""
                INSERT INTO `{DST_DB}`.`{table}`
                SELECT d.* FROM `{SRC_DB}`.`{table}` d
                JOIN `{DST_DB}`.`temp_stapler_keys` k ON d.MDR_REPORT_KEY = k.MDR_REPORT_KEY
            """
        else:
            sql = f"""
                INSERT INTO `{DST_DB}`.`{table}`
                SELECT x.* FROM `{SRC_DB}`.`{table}` x
                JOIN `{DST_DB}`.`temp_stapler_keys` k ON x.MDR_REPORT_KEY = k.MDR_REPORT_KEY
            """
            
        cursor.execute(sql)
        rows_inserted = cursor.rowcount
        print(f"完成。成功写入 {rows_inserted:,} 行记录 (耗时: {time.time() - t_sub:.2f} 秒)", flush=True)

    # 6. 复制轻量分类映射字典数据 (全量复制)
    print("\n5. 复制分类和问题映射字典数据...", flush=True)
    for table in dict_tables_to_clone:
        t_sub = time.time()
        print(f"   正在全量复制字典表 `{table}` ... ", end="", flush=True)
        sql = f"INSERT INTO `{DST_DB}`.`{table}` SELECT * FROM `{SRC_DB}`.`{table}`"
        cursor.execute(sql)
        rows_inserted = cursor.rowcount
        print(f"完成。成功写入 {rows_inserted:,} 行记录 (耗时: {time.time() - t_sub:.2f} 秒)", flush=True)

    # 7. 清理临时表
    print("\n6. 物理清理临时匹配键表...", flush=True)
    cursor.execute(f"DROP TABLE IF EXISTS `{DST_DB}`.`temp_stapler_keys`")
    print("   [完成] 临时匹配表已安全删除。", flush=True)

    print("\n==================================================", flush=True)
    print(f">>> 导出工作全部顺利完成！总计用时: {time.time() - t_total_start:.2f} 秒。", flush=True)
    print("==================================================", flush=True)

    conn.close()

if __name__ == '__main__':
    main()
