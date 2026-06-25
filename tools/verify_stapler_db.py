import os
import time
import random
import pymysql
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(BASE_DIR, ".env")
load_dotenv(env_path)

DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASSWORD', '123456')
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', 3306))
SRC_DB = os.getenv('DB_NAME', 'maude_db')
DST_DB = 'maude_stapler_db'

# 预期行数字典（根据之前精确探查的数据）
EXPECTED_COUNTS = {
    "mdr_report": 52250,
    "device": 52987,
    "patient": 52350,
    "foi_text": 94674,
    "foi_text_overflow": 175,
    "patient_problem_code": 18436,
    "device_problem_code": 17541
}

def get_connection(db_name):
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        database=db_name,
        charset='utf8mb4'
    )

def main():
    print("==================================================", flush=True)
    print(">>> 开始对专有分析库 `maude_stapler_db` 进行多维度校验...", flush=True)
    print("==================================================", flush=True)

    src_conn = get_connection(SRC_DB)
    dst_conn = get_connection(DST_DB)
    src_cursor = src_conn.cursor()
    dst_cursor = dst_conn.cursor()

    all_passed = True

    # 1. 检验各个表的行数是否完全符合预期
    print("\n1. 验证关系型数据子集行数:", flush=True)
    print(f"   {'表名':<25} | {'预期行数':<12} | {'新库实际行数':<12} | {'状态':<6}", flush=True)
    print(f"   {'-'*65}", flush=True)
    
    for table, expected in EXPECTED_COUNTS.items():
        dst_cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
        actual = dst_cursor.fetchone()[0]
        
        status = "PASSED" if actual == expected else "FAILED"
        if status == "FAILED":
            all_passed = False
            
        print(f"   - {table:<22} | {expected:<12,} | {actual:<12,} | {status:<6}", flush=True)

    # 2. 验证字典小表是否全量导入成功
    print("\n2. 验证基础字典表行数:", flush=True)
    dict_tables = ["device_hierarchy_mapping", "fda_device_problem_mapping"]
    for table in dict_tables:
        src_cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
        src_cnt = src_cursor.fetchone()[0]
        dst_cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
        dst_cnt = dst_cursor.fetchone()[0]
        
        status = "PASSED" if src_cnt == dst_cnt else "FAILED"
        if status == "FAILED":
            all_passed = False
        print(f"   - {table:<27} | 源库: {src_cnt:<8,} | 新库: {dst_cnt:<8,} | {status:<6}", flush=True)

    # 3. 校验关键物理索引在新库中是否存在且正常
    print("\n3. 验证新表上的物理索引继承情况:", flush=True)
    for table in EXPECTED_COUNTS.keys():
        dst_cursor.execute(f"SHOW INDEX FROM `{table}`")
        indices = dst_cursor.fetchall()
        index_names = list(set([idx[2] for idx in indices]))
        print(f"   - 表 `{table:<20}` 物理索引列表: {index_names}", flush=True)
        if not index_names:
            all_passed = False
            print(f"     [警告] 表 `{table}` 没有任何索引！", flush=True)

    # 4. 随机抽样 MDR_REPORT_KEY 字段一致性比对
    print("\n4. 随机抽样字段一致性精密比对...", flush=True)
    # 先从新库中拿 5 个随机的 MDR_REPORT_KEY
    dst_cursor.execute("SELECT MDR_REPORT_KEY FROM mdr_report ORDER BY RAND() LIMIT 5")
    sample_keys = [r[0] for r in dst_cursor.fetchall()]
    print(f"   - 随机抽样报告键值: {sample_keys}", flush=True)

    for key in sample_keys:
        print(f"     * 正在比对报告键 MDR_REPORT_KEY = {key} ... ", end="", flush=True)
        key_all_fields_match = True
        
        # 比对 mdr_report 和 device 中的字段内容
        for table in ["mdr_report", "device"]:
            dst_cursor.execute(f"SELECT * FROM `{table}` WHERE MDR_REPORT_KEY = %s", (key,))
            dst_rows = dst_cursor.fetchall()
            src_cursor.execute(f"SELECT * FROM `{table}` WHERE MDR_REPORT_KEY = %s", (key,))
            src_rows = src_cursor.fetchall()
            
            # 因为数据完全克隆，结构一样，所以结果集大小和内容应该完全相同
            if len(dst_rows) != len(src_rows):
                key_all_fields_match = False
                break
                
            for r_idx in range(len(dst_rows)):
                if dst_rows[r_idx] != src_rows[r_idx]:
                    key_all_fields_match = False
                    break
        
        if key_all_fields_match:
            print("OK (源库与新库物理属性完全一致)", flush=True)
        else:
            all_passed = False
            print("FAILED (数据属性有差异！)", flush=True)

    print("\n==================================================", flush=True)
    if all_passed:
        print(">>> [SUCCESS] 新数据库 maude_stapler_db 数据校验全部通过！", flush=True)
    else:
        print(">>> [ERROR] 校验中发现不一致，请核查以上日志！", flush=True)
    print("==================================================", flush=True)

    src_conn.close()
    dst_conn.close()

if __name__ == '__main__':
    main()
