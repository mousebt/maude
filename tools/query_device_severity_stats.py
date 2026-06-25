import os
import time
import pymysql
from dotenv import load_dotenv

# 动态获取根目录
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

    print(">>> 正在对不良反应发生的品类（产品代码/通用名称）进行严重度分类统计...")
    print("    正在执行 2300万 行数据跨表关联与多维聚合（这需要约 1-2 分钟，请稍候）...")
    
    t0 = time.time()
    
    # 执行多维分析查询
    sql = """
        SELECT 
            d.DEVICE_REPORT_PRODUCT_CODE,
            d.GENERIC_NAME,
            SUM(CASE WHEN m.EVENT_TYPE = 'D' THEN 1 ELSE 0 END) as death_count,
            SUM(CASE WHEN m.EVENT_TYPE = 'IN' THEN 1 ELSE 0 END) as injury_count,
            SUM(CASE WHEN m.EVENT_TYPE = 'M' THEN 1 ELSE 0 END) as malfunction_count,
            COUNT(*) as total_count
        FROM device d
        JOIN mdr_report m ON d.MDR_REPORT_KEY = m.MDR_REPORT_KEY
        GROUP BY d.DEVICE_REPORT_PRODUCT_CODE, d.GENERIC_NAME
        ORDER BY total_count DESC
        LIMIT 20
    """
    
    cursor.execute(sql)
    rows = cursor.fetchall()
    
    print(f"\n>>> 统计完成！耗时: {time.time() - t0:.2f} 秒。\n")
    
    # 格式化输出 Markdown 表格
    print("| 排名 | 产品代码 | 设备通用名称 (Generic Name) | 死亡数 (Death) | 严重伤害数 (Injury) | 设备故障数 (Malfunction) | 总不良事件数 |")
    print("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for idx, row in enumerate(rows, 1):
        code = row[0] if row[0] else 'N/A'
        name = row[1].strip() if row[1] else '未知器械'
        deaths = f"{row[2]:,}"
        injuries = f"{row[3]:,}"
        malfunctions = f"{row[4]:,}"
        total = f"{row[5]:,}"
        print(f"| {idx} | `{code}` | {name} | {deaths} | {injuries} | {malfunctions} | {total} |")
        
    conn.close()

if __name__ == '__main__':
    main()
