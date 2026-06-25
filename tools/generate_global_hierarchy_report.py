import pymysql
import os
import csv
import sys
from dotenv import load_dotenv

env_path = r"e:\pythonProjects\MAUDE\.env"
load_dotenv(env_path)

DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASSWORD', '123456')
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_NAME = os.getenv('DB_NAME', 'maude_db')

def generate_report():
    print(">>> 正在连接数据库，进行 1-2-3 级全局层级聚合...")
    conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, port=DB_PORT, database=DB_NAME)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # 按照 1级(CLEANED_NAME), 2级(LEVEL_1_CATEGORY), 3级(LEVEL_2_CATEGORY) 进行聚合
    sql = """
        SELECT 
            CLEANED_NAME as level_1,
            LEVEL_1_CATEGORY as level_2,
            LEVEL_2_CATEGORY as level_3,
            COUNT(*) as pairs_count,
            SUM(DEATH_COUNT) as death_sum,
            SUM(INJURY_COUNT) as injury_sum,
            SUM(MALFUNCTION_COUNT) as malfunction_sum,
            SUM(TOTAL_COUNT) as total_sum
        FROM device_hierarchy_mapping
        GROUP BY CLEANED_NAME, LEVEL_1_CATEGORY, LEVEL_2_CATEGORY
        ORDER BY total_sum DESC, pairs_count DESC
    """
    
    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        print(f">>> 成功聚合了 {len(rows)} 行层级分类数据。")
        
        # 导出为 CSV 报表，设置 utf-8-sig 以便 Excel 打开中文不乱码
        report_path = r"e:\pythonProjects\MAUDE\reports\maude_global_hierarchy_analysis.csv"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, mode='w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            # 写入纯中文表头，完全不带英文
            writer.writerow([
                "一级分类(清洗后中文器械名)",
                "二级分类(中观大类)",
                "三级分类(宏观大类)",
                "关联器械对数",
                "死亡事件数",
                "伤害事件数",
                "故障事件数",
                "事件总数"
            ])
            
            for r in rows:
                writer.writerow([
                    r['level_1'],
                    r['level_2'],
                    r['level_3'],
                    r['pairs_count'],
                    int(r['death_sum'] or 0),
                    int(r['injury_sum'] or 0),
                    int(r['malfunction_sum'] or 0),
                    int(r['total_sum'] or 0)
                ])
                
        print(f">>> [OK] 报表成功导出至: {report_path}")
    except Exception as e:
        print(f"[x] 导出报表失败: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    generate_report()
