import os
import pymysql
import csv
import time
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

    t0 = time.time()
    print(">>> 正在优化检索方案以避免全表大表 JOIN...")
    
    # 步骤 1: 极速利用索引捞取产品代码 NAY 的所有设备信息
    print(" 1/4 正在利用索引查询 NAY 产品代码设备...")
    sql_nay = """
        SELECT MDR_REPORT_KEY, BRAND_NAME, GENERIC_NAME, MANUFACTURER_D_NAME, DEVICE_REPORT_PRODUCT_CODE
        FROM device
        WHERE DEVICE_REPORT_PRODUCT_CODE = 'NAY'
    """
    cursor.execute(sql_nay)
    nay_devices = cursor.fetchall()
    print(f"      通过 NAY 索引找到 {len(nay_devices)} 个设备记录。")

    # 步骤 2: 单表扫描品牌名包含 'da vinci'/'davinci' 但不是 NAY 代码的设备记录
    print(" 2/4 正在扫描非 NAY 代码但品牌名包含 'da vinci' 的设备...")
    sql_non_nay_vinci = """
        SELECT MDR_REPORT_KEY, BRAND_NAME, GENERIC_NAME, MANUFACTURER_D_NAME, DEVICE_REPORT_PRODUCT_CODE
        FROM device
        WHERE (BRAND_NAME LIKE '%da vinci%' OR BRAND_NAME LIKE '%davinci%')
          AND (DEVICE_REPORT_PRODUCT_CODE != 'NAY' OR DEVICE_REPORT_PRODUCT_CODE IS NULL)
    """
    cursor.execute(sql_non_nay_vinci)
    non_nay_vinci_devices = cursor.fetchall()
    print(f"      通过品牌名扫描找到 {len(non_nay_vinci_devices)} 个非 NAY 的达芬奇设备记录。")

    # 合并所有的设备记录
    all_devices = {}
    for r in nay_devices + non_nay_vinci_devices:
        mdr_key = r[0]
        # 如果有重复的 mdr_key，保留一条
        if mdr_key not in all_devices:
            all_devices[mdr_key] = r

    mdr_keys = list(all_devices.keys())
    print(f"      合并后共有 {len(mdr_keys)} 个唯一的设备 MDR 报告键。")

    if not mdr_keys:
        print("未找到任何设备记录。")
        conn.close()
        return

    # 步骤 3: 分批使用 MDR_REPORT_KEY 主键索引，从 mdr_report 捞取 EVENT_TYPE = 'D' 的致死病例
    print(" 3/4 正在分批点查主键索引筛选致死病例 (EVENT_TYPE = 'D')...")
    death_report_keys = {}
    batch_size = 50000
    for idx in range(0, len(mdr_keys), batch_size):
        sub_keys = mdr_keys[idx : idx + batch_size]
        format_strings = ','.join(['%s'] * len(sub_keys))
        sql_deaths = f"""
            SELECT MDR_REPORT_KEY, REPORT_NUMBER, DATE_OF_EVENT, DATE_RECEIVED
            FROM mdr_report
            WHERE MDR_REPORT_KEY IN ({format_strings})
              AND EVENT_TYPE = 'D'
        """
        cursor.execute(sql_deaths, tuple(sub_keys))
        rows = cursor.fetchall()
        for r in rows:
            death_report_keys[r[0]] = r

    print(f"      筛选出致死病例共 {len(death_report_keys)} 条。")

    if not death_report_keys:
        print("无致死病例数据。")
        conn.close()
        return

    # 步骤 4: 捞取这些致死病例的 foi_text 描述并导出为 CSV
    export_file = os.path.join(BASE_DIR, "reports", "davinci_death_events.csv")
    print(f" 4/4 正在获取事件详细文本并导出至 {export_file}...")

    header = [
        "MDR_REPORT_KEY", 
        "REPORT_NUMBER", 
        "DATE_OF_EVENT", 
        "DATE_RECEIVED", 
        "BRAND_NAME", 
        "GENERIC_NAME", 
        "MANUFACTURER_D_NAME", 
        "PRODUCT_CODE", 
        "FOI_TEXT"
    ]

    death_keys_list = list(death_report_keys.keys())
    
    with open(export_file, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)

        # 每次处理 100 条记录来查 foi_text
        text_batch_size = 100
        for i in range(0, len(death_keys_list), text_batch_size):
            sub_keys = death_keys_list[i : i + text_batch_size]
            format_strings = ','.join(['%s'] * len(sub_keys))
            sql_text = f"""
                SELECT MDR_REPORT_KEY, FOI_TEXT 
                FROM foi_text 
                WHERE MDR_REPORT_KEY IN ({format_strings})
                ORDER BY MDR_REPORT_KEY, MDR_TEXT_KEY
            """
            cursor.execute(sql_text, tuple(sub_keys))
            text_rows = cursor.fetchall()

            text_dict = {}
            for k, txt in text_rows:
                if k not in text_dict:
                    text_dict[k] = []
                if txt:
                    text_dict[k].append(txt.strip())

            for k in sub_keys:
                d_info = death_report_keys[k]
                dev_info = all_devices[k]
                full_text = "\n".join(text_dict.get(k, ["无详细事件描述"]))
                
                writer.writerow([
                    d_info[0], # MDR_REPORT_KEY
                    d_info[1], # REPORT_NUMBER
                    d_info[2], # DATE_OF_EVENT
                    d_info[3], # DATE_RECEIVED
                    dev_info[1], # BRAND_NAME
                    dev_info[2], # GENERIC_NAME
                    dev_info[3], # MANUFACTURER_D_NAME
                    dev_info[4], # PRODUCT_CODE
                    full_text # FOI_TEXT
                ])

    print(f">>> 导出完成！成功写入 {len(death_keys_list)} 条数据，总耗时: {time.time() - t0:.2f} 秒。")
    conn.close()

if __name__ == '__main__':
    main()
