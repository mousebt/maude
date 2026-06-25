import os
import time
import urllib.request
import zipfile
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

RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")

# FDA Downloads URLs
URL_DEVICE_PROBLEMS = "https://www.accessdata.fda.gov/MAUDE/ftparea/foidevproblem.zip"
URL_PATIENT_PROBLEMS = "https://www.accessdata.fda.gov/MAUDE/ftparea/patientproblemcode.zip"

def download_file(url, dest_path):
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 5 * 1024 * 1024:
        print(f"文件已存在且大小正常，跳过下载: {dest_path}", flush=True)
        return
        
    print(f"正在从 {url} 下载文件...", flush=True)
    t0 = time.time()
    
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    
    with urllib.request.urlopen(req) as response, open(dest_path, 'wb') as out_file:
        data = response.read()
        out_file.write(data)
        
    print(f"下载完成！保存至: {dest_path}，用时: {time.time() - t0:.2f} 秒，大小: {os.path.getsize(dest_path) / 1024 / 1024:.2f} MB", flush=True)

def unzip_and_get_name(zip_path, extract_to):
    print(f"正在解压 {zip_path}...", flush=True)
    t0 = time.time()
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        names = zip_ref.namelist()
        zip_ref.extractall(extract_to)
    print(f"解压完成，用时: {time.time() - t0:.2f} 秒。解压出的文件列表: {names}", flush=True)
    return names[0] if names else None

def inspect_and_import(conn, txt_path, table_name):
    cursor = conn.cursor()
    
    print(f"\n>>> 正在分析并导入无表头文本文件: {txt_path}...", flush=True)
    
    with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
        sample = [f.readline().strip() for _ in range(3)]
        
    print(f"  [样例行 1] {sample[0]}")
    print(f"  [样例行 2] {sample[1]}")
    
    delimiter = '|'
    
    # 1. 创建无索引的干净表结构，以防导入过程中维护索引拖慢速度
    print(f"  正在创建 MySQL 表（暂无索引）: {table_name}...", flush=True)
    cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
    
    if "patient" in table_name:
        fields = ['MDR_REPORT_KEY', 'PATIENT_SEQUENCE_NUMBER', 'PATIENT_PROBLEM_CODE']
        create_sql = f"""
            CREATE TABLE {table_name} (
                MDR_REPORT_KEY BIGINT NOT NULL,
                PATIENT_SEQUENCE_NUMBER INT,
                PATIENT_PROBLEM_CODE VARCHAR(50)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
    else:
        fields = ['MDR_REPORT_KEY', 'DEVICE_PROBLEM_CODE']
        create_sql = f"""
            CREATE TABLE {table_name} (
                MDR_REPORT_KEY BIGINT NOT NULL,
                DEVICE_PROBLEM_CODE VARCHAR(50)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
    cursor.execute(create_sql)
    
    # 2. 高速导入数据
    formatted_path = txt_path.replace('\\', '/')
    print(f"  正在通过 LOAD DATA 高速导入数据到 {table_name}...", flush=True)
    t0 = time.time()
    
    load_sql = f"""
        LOAD DATA LOCAL INFILE '{formatted_path}'
        INTO TABLE {table_name}
        FIELDS TERMINATED BY '{delimiter}'
        LINES TERMINATED BY '\\r\\n'
        ({', '.join(fields)})
    """
    try:
        cursor.execute(load_sql)
        conn.commit()
    except Exception as e:
        print(f"  [常规换行导入失败，尝试普通换行符 \\n...] 错误: {e}", flush=True)
        load_sql_alt = f"""
            LOAD DATA LOCAL INFILE '{formatted_path}'
            INTO TABLE {table_name}
            FIELDS TERMINATED BY '{delimiter}'
            LINES TERMINATED BY '\\n'
            ({', '.join(fields)})
        """
        cursor.execute(load_sql_alt)
        conn.commit()
        
    print(f"  [导入完成] 耗时: {time.time() - t0:.2f} 秒。", flush=True)
    
    # 3. 后期补建索引：利用 MySQL 的快速索引创建机制，在数据加载后一次性构建
    print(f"  正在为 {table_name} 追加建立物理索引...", flush=True)
    t_idx = time.time()
    if "patient" in table_name:
        cursor.execute(f"ALTER TABLE {table_name} ADD INDEX idx_mdr_key (MDR_REPORT_KEY), ADD INDEX idx_prob_code (PATIENT_PROBLEM_CODE)")
    else:
        cursor.execute(f"ALTER TABLE {table_name} ADD INDEX idx_mdr_key (MDR_REPORT_KEY), ADD INDEX idx_prob_code (DEVICE_PROBLEM_CODE)")
    print(f"  [索引构建完成] 耗时: {time.time() - t_idx:.2f} 秒。", flush=True)
    
    # 4. 统计行数
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    row_count = cursor.fetchone()[0]
    print(f"  [统计] 表 {table_name} 实际导入行数: {row_count:,} 行。\n", flush=True)

def main():
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    
    zip_device = os.path.join(RAW_DATA_DIR, "foidevproblem.zip")
    zip_patient = os.path.join(RAW_DATA_DIR, "patientproblemcode.zip")
    
    # 1. 下载文件
    try:
        download_file(URL_DEVICE_PROBLEMS, zip_device)
        download_file(URL_PATIENT_PROBLEMS, zip_patient)
    except Exception as e:
        print(f"下载文件失败: {e}", flush=True)
        return
        
    # 2. 解压缩并获取真实文件名
    try:
        filename_device = unzip_and_get_name(zip_device, RAW_DATA_DIR)
        filename_patient = unzip_and_get_name(zip_patient, RAW_DATA_DIR)
    except Exception as e:
        print(f"解压失败: {e}", flush=True)
        return
        
    if not filename_device or not filename_patient:
        print("未能在压缩包中找到有效的文件！", flush=True)
        return
        
    txt_device = os.path.join(RAW_DATA_DIR, filename_device)
    txt_patient = os.path.join(RAW_DATA_DIR, filename_patient)
        
    # 3. 建立数据库连接
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        database=DB_NAME,
        local_infile=True
    )
    
    try:
        # 4. 导入数据
        inspect_and_import(conn, txt_device, "device_problem_code")
        inspect_and_import(conn, txt_patient, "patient_problem_code")
    finally:
        conn.close()
        
    print(">>> 所有的 FDA 不良事件问题编码表数据已全部物理入库完成！")

if __name__ == '__main__':
    main()
