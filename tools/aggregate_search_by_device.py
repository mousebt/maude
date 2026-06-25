import os
import sys
import time
import pymysql
from dotenv import load_dotenv

# 加载配置
env_path = r"e:\pythonProject\MAUDE\.env"
load_dotenv(env_path)

DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASSWORD', '123456')
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', 13306))
DB_NAME = os.getenv('DB_NAME') or 'maude_db'

def search_and_aggregate(keyword):
    """
    根据关键字搜索器械品类并聚合统计不良事件的严重度
    """
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        database=DB_NAME
    )
    cursor = conn.cursor()

    keyword = keyword.strip()
    print(f"\n================ 搜索关键字: '{keyword}' ================")
    
    t0 = time.time()
    
    # 1. 识别搜索模式：如果是 3 位字母，优先按产品代码精确匹配
    is_prod_code = len(keyword) == 3 and keyword.isalpha()
    
    if is_prod_code:
        print("  [模式] 检测到 3 位英文字母，执行产品代码 (Product Code) 精确搜索...")
        cursor.execute("""
            SELECT DEVICE_REPORT_PRODUCT_CODE, GENERIC_NAME, COUNT(*) as dev_count
            FROM device
            WHERE DEVICE_REPORT_PRODUCT_CODE = %s
            GROUP BY DEVICE_REPORT_PRODUCT_CODE, GENERIC_NAME
            ORDER BY dev_count DESC
            LIMIT 10
        """, (keyword.upper(),))
    else:
        print("  [模式] 执行通用名称 (Generic Name) / 品牌名称 (Brand Name) 模糊搜索...")
        # 模糊匹配，使用前缀匹配或双向模糊
        search_pattern = f"%{keyword}%"
        cursor.execute("""
            SELECT DEVICE_REPORT_PRODUCT_CODE, GENERIC_NAME, COUNT(*) as dev_count
            FROM device
            WHERE GENERIC_NAME LIKE %s OR BRAND_NAME LIKE %s
            GROUP BY DEVICE_REPORT_PRODUCT_CODE, GENERIC_NAME
            ORDER BY dev_count DESC
            LIMIT 10
        """, (search_pattern, search_pattern))
        
    matched_categories = cursor.fetchall()
    
    if not matched_categories:
        print(f"没有找到与 '{keyword}' 匹配的任何器械种类。")
        conn.close()
        return

    print(f"  [发现] 找到 {len(matched_categories)} 个匹配的器械类别。开始计算严重度聚合统计数据...")
    
    results = []
    for idx, (code, generic_name, count) in enumerate(matched_categories, 1):
        code = code or 'N/A'
        generic_name = (generic_name or '未知通用名称').strip()
        print(f"   ({idx}/{len(matched_categories)}) 正在聚合产品代码 `{code}` (预估事件数: {count:,})...", end="", flush=True)
        
        t_sub = time.time()
        # 针对每个品类（产品代码+通用名称），级联查询 mdr_report 的 EVENT_TYPE 分类统计
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN m.EVENT_TYPE = 'D' THEN 1 ELSE 0 END) as death_count,
                SUM(CASE WHEN m.EVENT_TYPE = 'IN' THEN 1 ELSE 0 END) as injury_count,
                SUM(CASE WHEN m.EVENT_TYPE = 'M' THEN 1 ELSE 0 END) as malfunction_count,
                COUNT(*) as total_count
            FROM device d
            JOIN mdr_report m ON d.MDR_REPORT_KEY = m.MDR_REPORT_KEY
            WHERE d.DEVICE_REPORT_PRODUCT_CODE = %s AND d.GENERIC_NAME = %s
        """, (code, generic_name))
        
        stats_row = cursor.fetchone()
        
        deaths = stats_row[0] if stats_row[0] is not None else 0
        injuries = stats_row[1] if stats_row[1] is not None else 0
        malfunctions = stats_row[2] if stats_row[2] is not None else 0
        total = stats_row[3] if stats_row[3] is not None else 0
        
        results.append((code, generic_name, deaths, injuries, malfunctions, total))
        print(f" 完成！用时 {time.time() - t_sub:.2f} 秒")
        
    print(f"\n>>> 聚合搜索完成！总耗时: {time.time() - t0:.2f} 秒。")
    print(f"结果按总不良事件数降序排列：\n")
    
    # 格式化输出 Markdown 表格
    print("| 序号 | 产品代码 | 设备通用名称 (Generic Name) | 死亡数 (Death) | 严重伤害数 (Injury) | 设备故障数 (Malfunction) | 匹配总数 |")
    print("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for idx, row in enumerate(results, 1):
        code, name, deaths, injuries, malfunctions, total = row
        print(f"| {idx} | `{code}` | {name} | {deaths:,} | {injuries:,} | {malfunctions:,} | {total:,} |")
        
    conn.close()

if __name__ == '__main__':
    # 允许从命令行传入关键字，若无则使用默认词 "insulin"（胰岛素泵相关）
    search_term = "insulin"
    if len(sys.argv) > 1:
        search_term = " ".join(sys.argv[1:])
        
    search_and_aggregate(search_term)
