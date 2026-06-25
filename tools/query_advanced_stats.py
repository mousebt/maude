import os
import time
import pymysql
from dotenv import load_dotenv

env_path = r"e:\pythonProject\MAUDE\.env"
load_dotenv(env_path)

DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASSWORD', '123456')
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_NAME = os.getenv('DB_NAME') or 'maude_db'

REPORT_PATH = r"e:\pythonProject\MAUDE\MAUDE各年份数据记录统计报告.md"

def get_event_type_distribution(cursor):
    print(">>> 正在统计事件后果分布 (利用 idx_event_type 覆盖索引)...")
    t0 = time.time()
    cursor.execute("SELECT EVENT_TYPE, COUNT(*) FROM mdr_report GROUP BY EVENT_TYPE ORDER BY COUNT(*) DESC")
    rows = cursor.fetchall()
    print(f"  完成，耗时: {time.time() - t0:.2f} 秒")
    return rows

def get_reporter_distribution(cursor):
    print(">>> 正在统计报告人职业类型分布...")
    t0 = time.time()
    cursor.execute("SELECT REPORTER_OCCUPATION_CODE, COUNT(*) FROM mdr_report GROUP BY REPORTER_OCCUPATION_CODE ORDER BY COUNT(*) DESC LIMIT 15")
    rows = cursor.fetchall()
    print(f"  完成，耗时: {time.time() - t0:.2f} 秒")
    return rows

def get_product_code_top20(cursor):
    print(">>> 正在统计产品代码 Top 20 (利用 idx_product_code 覆盖索引)...")
    t0 = time.time()
    cursor.execute("SELECT DEVICE_REPORT_PRODUCT_CODE, COUNT(*) FROM device GROUP BY DEVICE_REPORT_PRODUCT_CODE ORDER BY COUNT(*) DESC LIMIT 20")
    top20 = cursor.fetchall()
    print(f"  Top 20 代码获取完成，耗时: {time.time() - t0:.2f} 秒")
    
    result = []
    print(">>> 正在点查询获取产品代码对应的代表性品牌与通用名称...")
    for prod_code, count in top20:
        if not prod_code:
            result.append((prod_code, count, "未知设备类型", "未知通用名"))
            continue
        # 极速点查
        cursor.execute("""
            SELECT BRAND_NAME, GENERIC_NAME 
            FROM device 
            WHERE DEVICE_REPORT_PRODUCT_CODE = %s AND BRAND_NAME IS NOT NULL AND BRAND_NAME != '' 
            LIMIT 1
        """, (prod_code,))
        meta = cursor.fetchone()
        brand = meta[0].strip() if meta and meta[0] else "未命名品牌"
        generic = meta[1].strip() if meta and meta[1] else "未命名通用名"
        result.append((prod_code, count, brand, generic))
    return result

def get_overflow_stats(cursor):
    print(">>> 正在统计超长暗数据 (foi_text_overflow) 物理长度分布...")
    t0 = time.time()
    # 统计长度区间
    cursor.execute("""
        SELECT 
            COUNT(*),
            SUM(CASE WHEN CHAR_LENGTH(FOI_TEXT) < 6000 THEN 1 ELSE 0 END),
            SUM(CASE WHEN CHAR_LENGTH(FOI_TEXT) BETWEEN 6000 AND 10000 THEN 1 ELSE 0 END),
            SUM(CASE WHEN CHAR_LENGTH(FOI_TEXT) > 10000 THEN 1 ELSE 0 END)
        FROM foi_text_overflow
    """)
    stats = cursor.fetchone()
    print(f"  完成，耗时: {time.time() - t0:.2f} 秒")
    return stats

def main():
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        database=DB_NAME
    )
    cursor = conn.cursor()

    # 执行统计
    event_dist = get_event_type_distribution(cursor)
    reporter_dist = get_reporter_distribution(cursor)
    prod_top20 = get_product_code_top20(cursor)
    overflow_stats = get_overflow_stats(cursor)

    conn.close()

    # 格式化数据为 Markdown 文本
    md_content = []
    
    md_content.append("\n## 四、 不良事件临床后果与事件类型分布统计 (Event Type Distribution)")
    md_content.append("\n本节基于主表 `EVENT_TYPE` 字段进行聚合统计，揭示了 FDA 接收到的不良事件严重程度大盘分布。")
    md_content.append("\n| 不良事件类型 | 报告频数 | 占比 |")
    md_content.append("| :--- | :--- | :--- |")
    total_reports = sum(r[1] for r in event_dist)
    for etype, cnt in event_dist:
        etype_str = etype if etype else "未分类/缺失"
        pct = (cnt / total_reports) * 100 if total_reports > 0 else 0
        md_content.append(f"| {etype_str} | {cnt:,} | {pct:.3f}% |")

    md_content.append("\n## 五、 不良事件报告人职业类型分布统计 (Reporter Occupation)")
    md_content.append("\n本节汇总了报告人的职业分布（前 15 类），展示了 MAUDE 数据库中各专业群体及患者个人的上报参与度。")
    md_content.append("\n| 报告人职业代码/名称 | 报告频数 | 占比 |")
    md_content.append("| :--- | :--- | :--- |")
    total_reporters = sum(r[1] for r in reporter_dist)
    for occup, cnt in reporter_dist:
        occup_str = occup if occup else "未知/未填报"
        pct = (cnt / total_reporters) * 100 if total_reporters > 0 else 0
        md_content.append(f"| {occup_str} | {cnt:,} | {pct:.3f}% |")

    md_content.append("\n## 六、 医疗器械产品代码 (Product Code) 不良事件风险排行 Top 20")
    md_content.append("\n本节利用索引覆盖技术筛选出不良事件关联频数最高的前 20 类器械产品代码，并点查关联其典型品牌与通用名称。")
    md_content.append("\n| 排名 | 产品代码 | 不良事件频数 | 典型代表品牌 (BRAND_NAME) | 代表通用名称 (GENERIC_NAME) |")
    md_content.append("| :--- | :--- | :--- | :--- | :--- |")
    for idx, (code, count, brand, generic) in enumerate(prod_top20, 1):
        code_str = code if code else "N/A"
        md_content.append(f"| {idx} | `{code_str}` | {count:,} | {brand} | {generic} |")

    md_content.append("\n## 七、 自由描述超长“暗数据”物理特征统计 (Foi Text Overflow Profile)")
    md_content.append("\n`foi_text_overflow` 表专门拦截存储了描述文本长度大于 4,000 字符的极度复杂医疗事件记录（最大保留 16,000 字符）。本节统计了这批高价值暗数据的具体长度区间分布。")
    md_content.append("\n* **溢出表记录总数**: {:,} 条".format(overflow_stats[0] if overflow_stats[0] else 0))
    md_content.append("\n| 文本字数区间 (字符数) | 记录条数 | 占比 |")
    md_content.append("| :--- | :--- | :--- |")
    total_overflow = overflow_stats[0] if overflow_stats[0] else 1
    
    # 4000 - 6000
    cnt_small = overflow_stats[1] if overflow_stats[1] else 0
    pct_small = (cnt_small / total_overflow) * 100
    md_content.append(f"| 4,000 ~ 6,000 字符 | {cnt_small:,} | {pct_small:.2f}% |")
    
    # 6000 - 10000
    cnt_med = overflow_stats[2] if overflow_stats[2] else 0
    pct_med = (cnt_med / total_overflow) * 100
    md_content.append(f"| 6,000 ~ 10,000 字符 | {cnt_med:,} | {pct_med:.2f}% |")
    
    # > 10000
    cnt_large = overflow_stats[3] if overflow_stats[3] else 0
    pct_large = (cnt_large / total_overflow) * 100
    md_content.append(f"| > 10,000 字符 | {cnt_large:,} | {pct_large:.2f}% |")

    new_section_text = "\n".join(md_content)

    # 读取原有报告，去除末尾的分割线和生成时间，重新追加
    if os.path.exists(REPORT_PATH):
        with open(REPORT_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 寻找末尾的 --- 符号，将其及后面的内容截断
        cut_idx = len(lines)
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == '---':
                cut_idx = i
                break
        
        trimmed_content = "".join(lines[:cut_idx])
        
        # 追加新内容和新的结尾
        final_content = trimmed_content + new_section_text + "\n\n---\n*报告生成时间: {} | 数据底座优化与多维指标统计技术支持: Antigravity*\n".format(time.strftime("%Y-%m-%d %H:%M:%S"))
        
        with open(REPORT_PATH, 'w', encoding='utf-8') as f:
            f.write(final_content)
        print(f"\n>>> 报告已成功更新并追加高级统计数据: {REPORT_PATH}")
    else:
        print(f"未找到原始报告 {REPORT_PATH}，无法进行追加更新！")

if __name__ == '__main__':
    main()
