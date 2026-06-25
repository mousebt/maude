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

    # 1. 查找 NAY (达芬奇手术机器人常见代码) 的设备记录及致死情况
    print(">>> 正在查询 DEVICE_REPORT_PRODUCT_CODE = 'NAY' 且 EVENT_TYPE = 'D' 的数据...")
    sql_count = """
        SELECT 
            m.EVENT_TYPE,
            COUNT(*) as cnt
        FROM device d
        JOIN mdr_report m ON d.MDR_REPORT_KEY = m.MDR_REPORT_KEY
        WHERE d.DEVICE_REPORT_PRODUCT_CODE = 'NAY'
        GROUP BY m.EVENT_TYPE
    """
    cursor.execute(sql_count)
    rows = cursor.fetchall()
    print("查询结果（产品代码 NAY 的不良事件类型分布）：")
    for row in rows:
        print(f"  Event Type: {row[0]}, Count: {row[1]}")

    # 2. 查询是否有达芬奇的导出文件，在代码或报告中
    print("\n>>> 正在查询 NAY 且 EVENT_TYPE = 'D' 的具体病例样本前 5 条：")
    sql_detail = """
        SELECT 
            m.MDR_REPORT_KEY,
            m.REPORT_NUMBER,
            m.DATE_OF_EVENT,
            d.BRAND_NAME,
            d.GENERIC_NAME,
            d.MANUFACTURER_D_NAME
        FROM device d
        JOIN mdr_report m ON d.MDR_REPORT_KEY = m.MDR_REPORT_KEY
        WHERE d.DEVICE_REPORT_PRODUCT_CODE = 'NAY'
          AND m.EVENT_TYPE = 'D'
        LIMIT 5
    """
    cursor.execute(sql_detail)
    details = cursor.fetchall()
    for detail in details:
        print(f"  MDR_KEY: {detail[0]}, ReportNo: {detail[1]}, Date: {detail[2]}, Brand: {detail[3]}, Generic: {detail[4]}")


    conn.close()

if __name__ == '__main__':
    main()
