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
DB_NAME = 'davinci_death_db'

def main():
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        database=DB_NAME
    )
    cursor = conn.cursor()
    
    print("======================================================================")
    print(">>> 正在从 MySQL foi_text_knowledge 表中提炼全量达芬奇致死归因大盘数据...")
    print("======================================================================\n")

    # 1. 惊悚病例 (Shocking) 的安全隐患大类统计
    print("一、 289条【安全隐患分类】多维统计：")
    cursor.execute("""
        SELECT HAZARD_CATEGORY, COUNT(*) as cnt
        FROM foi_text_knowledge
        WHERE CLASSIFICATION = 'Shocking'
        GROUP BY HAZARD_CATEGORY
        ORDER BY cnt DESC
    """)
    rows = cursor.fetchall()
    total_shocking = sum(r[1] for r in rows)
    for r in rows:
        pct = (r[1] / total_shocking) * 100 if total_shocking > 0 else 0
        cat_name = r[0] if r[0] else "其他/未分类"
        print(f"  - {cat_name:<25}: {r[1]:>3} 例 | 占比: {pct:.2f}%")
    print()

    # 2. 惊悚病例中排名前 8 的具体故障附件
    print("二、 【具体故障器械组件/耗材】Top 8 排行（在惊悚病案中提及）：")
    cursor.execute("""
        SELECT FAULT_COMPONENT, COUNT(*) as cnt
        FROM foi_text_knowledge
        WHERE CLASSIFICATION = 'Shocking' AND FAULT_COMPONENT IS NOT NULL AND FAULT_COMPONENT != '未知'
        GROUP BY FAULT_COMPONENT
        ORDER BY cnt DESC
        LIMIT 8
    """)
    rows = cursor.fetchall()
    for idx, r in enumerate(rows, 1):
        print(f"  {idx}. 器械名称: {r[0]:<40} | 提及频次: {r[1]:>3} 例")
    print()

    # 3. 常规病例 (Normal) 的临床并发症统计
    print("三、 424条【临床并发症与死因】分类统计：")
    cursor.execute("""
        SELECT CLINICAL_COMPLICATION, COUNT(*) as cnt
        FROM foi_text_knowledge
        WHERE CLASSIFICATION = 'Normal'
        GROUP BY CLINICAL_COMPLICATION
        ORDER BY cnt DESC
    """)
    rows = cursor.fetchall()
    total_normal = sum(r[1] for r in rows)
    for r in rows:
        pct = (r[1] / total_normal) * 100 if total_normal > 0 else 0
        comp_name = r[0] if r[0] else "未分类/其他"
        print(f"  - {comp_name:<25}: {r[1]:>3} 例 | 占比: {pct:.2f}%")
    print()

    # 4. 常规病例中医生的中转开腹救治决策 (Surgeon Decision)
    print("四、 常规病例中【中转开放手术 (Conversion)】决策统计：")
    cursor.execute("""
        SELECT SURGEON_DECISION, COUNT(*) as cnt
        FROM foi_text_knowledge
        WHERE CLASSIFICATION = 'Normal'
        GROUP BY SURGEON_DECISION
        ORDER BY cnt DESC
    """)
    rows = cursor.fetchall()
    for r in rows:
        dec = r[0] if r[0] else "未提及"
        print(f"  - 是否中转开放手术: {dec:<10} | {r[1]:>3} 例")
    print()

    # 5. 结构问题病例的线索复原成功率
    print("五、 7条【结构受损病例】的线索复原成功率统计：")
    cursor.execute("""
        SELECT CAN_BE_REPAIRED, COUNT(*) as cnt
        FROM foi_text_knowledge
        WHERE CLASSIFICATION = 'Structural_Issue'
        GROUP BY CAN_BE_REPAIRED
    """)
    rows = cursor.fetchall()
    for r in rows:
        rep = r[0] if r[0] else "未知"
        print(f"  - 是否能通过AI考古复原线索: {rep:<5} | {r[1]:>2} 例")
    print()

    conn.close()

if __name__ == '__main__':
    main()
