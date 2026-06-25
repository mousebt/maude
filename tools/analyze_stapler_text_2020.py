import os
import time
import pymysql
import re
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

def get_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        database=DB_NAME
    )

def main():
    conn = get_connection()
    cursor = conn.cursor()

    print(">>> 正在分步创建临时表以匹配 2020 年以后吻合器相关的报告键 (MDR_REPORT_KEY)...", flush=True)
    t_start = time.time()
    
    # 1. 第一步：单表找出全量吻合器报告主键
    cursor.execute("DROP TEMPORARY TABLE IF EXISTS temp_all_staplers")
    t0 = time.time()
    cursor.execute("""
        CREATE TEMPORARY TABLE temp_all_staplers AS
        SELECT DISTINCT MDR_REPORT_KEY
        FROM device
        WHERE GENERIC_NAME LIKE '%stapler%' OR BRAND_NAME LIKE '%stapler%'
    """)
    print(f"  [1/3] 步骤 1：所有吻合器报告主键筛选完成，用时: {time.time() - t0:.2f} 秒。", flush=True)
    
    # 2. 第二步：为中间表添加主键索引
    t0 = time.time()
    cursor.execute("ALTER TABLE temp_all_staplers ADD PRIMARY KEY (MDR_REPORT_KEY)")
    print(f"  [2/3] 步骤 2：中间主键索引建立完成，用时: {time.time() - t0:.2f} 秒。", flush=True)
    
    # 3. 第三步：级联 JOIN 主表过滤 2020 年以后的唯一报告
    cursor.execute("DROP TEMPORARY TABLE IF EXISTS temp_stapler_2020_keys")
    t0 = time.time()
    cursor.execute("""
        CREATE TEMPORARY TABLE temp_stapler_2020_keys AS
        SELECT t.MDR_REPORT_KEY
        FROM temp_all_staplers t
        JOIN mdr_report m ON t.MDR_REPORT_KEY = m.MDR_REPORT_KEY
        WHERE m.DATE_RECEIVED LIKE '%/%/%'
          AND RIGHT(m.DATE_RECEIVED, 4) >= '2020'
    """)
    cursor.execute("ALTER TABLE temp_stapler_2020_keys ADD PRIMARY KEY (MDR_REPORT_KEY)")
    print(f"  [3/3] 步骤 3：2020年以后报告主键筛选及索引完成，用时: {time.time() - t0:.2f} 秒。", flush=True)
    print(f"临时表分步创建全部就绪，总共耗时: {time.time() - t_start:.2f} 秒。\n", flush=True)
    
    # 统计 2020 年以后的唯一报告总数
    cursor.execute("SELECT COUNT(*) FROM temp_stapler_2020_keys")
    total_count = cursor.fetchone()[0]
    print(f"  [发现] 2020 年以后共有 {total_count:,} 起吻合器不良事件报告。开始拉取描述文本进行 NLP 匹配...", flush=True)
    
    # 4. 批量拉取 foi_text 描述文本
    chunk_size = 2000
    offset = 0
    
    # 定义文本特征的正则表达式（不区分大小写），对应 IMDRF 体系
    patterns = {
        'A050502': {
            'desc': 'Misfire / Fail to Fire (未击发/哑火/未成功部署)',
            'regex': re.compile(r'\b(misfire|fail(ed)?\s+to\s+fire|not\s+fire|incomplete\s+firing?|did\s+not\s+deploy)\b', re.IGNORECASE),
            'count': 0
        },
        'A0512': {
            'desc': 'Staple Line Malformation (成钉不良/缝合钉变形)',
            'regex': re.compile(r'\b(malform(ed|ation)?|misshapen|bad\s+shape|staple\s+shape|unformed\s+staple|incomplete\s+staple|poorly\s+formed)\b', re.IGNORECASE),
            'count': 0
        },
        'A0506': {
            'desc': 'Mechanical Jam / Stuck (机械卡死/卡刀/无法打开)',
            'regex': re.compile(r'\b(jam(med|ming)?|stuck|locked|unable\s+to\s+open|cannot\s+open|restricted\s+motion|difficult\s+to\s+open)\b', re.IGNORECASE),
            'count': 0
        },
        'A0401': {
            'desc': 'Breakage / Separation / Crack (部件断裂/破碎/脱落)',
            'regex': re.compile(r'\b(break|broke|broken|crack(ed)?|fragment(ed)?|detach(ed)?|separat(ed|ion)|fall\s+off|apart)\b', re.IGNORECASE),
            'count': 0
        },
        'E1005 (Patient)': {
            'desc': 'Hemorrhage / Bleeding (患者术中或术后大出血)',
            'regex': re.compile(r'\b(bleeding?|bleed|hemorrhage|hemorrhagic|blood\s+loss)\b', re.IGNORECASE),
            'count': 0
        },
        'E0507 (Patient)': {
            'desc': 'Fistula / Anastomotic Leak (吻合口瘘/渗漏)',
            'regex': re.compile(r'\b(leak(age)?|anastomotic\s+leak|fistula)\b', re.IGNORECASE),
            'count': 0
        }
    }
    
    analyzed_count = 0
    
    while offset < total_count:
        # 分批查询
        query = """
            SELECT f.FOI_TEXT
            FROM temp_stapler_2020_keys t
            JOIN foi_text f ON t.MDR_REPORT_KEY = f.MDR_REPORT_KEY
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, (chunk_size, offset))
        rows = cursor.fetchall()
        if not rows:
            break
            
        for row in rows:
            text = row[0]
            if not text:
                continue
            
            # 对每条文本匹配各个模式
            for code, info in patterns.items():
                if info['regex'].search(text):
                    info['count'] += 1
            analyzed_count += 1
            
        offset += chunk_size
        print(f"  [进度] 已读取并匹配 {analyzed_count:,} / {total_count:,} 条文本...", flush=True)

    print(f"\n>>> 分析完成！总耗时: {time.time() - t_start:.2f} 秒。")
    print(f"2020 年以后分析的吻合器描述文本共: {analyzed_count:,} 份。")
    print("\n[表 5] 2020年以后吻合器不良事件常见 IMDRF 编码与失效模式映射统计：")
    print("-" * 110)
    print(f"{'IMDRF 代码':<18} | {'映射失效模式/临床后果':<45} | {'事件发生数':<12} | {'文本检出率':<8}")
    print("-" * 110)
    
    # 按照检出数量降序排列输出
    sorted_patterns = sorted(patterns.items(), key=lambda x: x[1]['count'], reverse=True)
    for code, info in sorted_patterns:
        cnt = info['count']
        pct = (cnt / analyzed_count) * 100 if analyzed_count > 0 else 0
        print(f"{code:<18} | {info['desc'][:45]:<45} | {cnt:<12,} | {pct:.2f}%")
    print("-" * 110)

    conn.close()

if __name__ == '__main__':
    main()
