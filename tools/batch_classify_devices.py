import os
import sys
import time
import json
import requests
import pymysql
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# 加载环境变量
env_path = r"e:\pythonProjects\MAUDE\.env"
load_dotenv(env_path)

DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASSWORD', '123456')
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_NAME = os.getenv('DB_NAME') or 'maude_db'

LOCAL_LLM_BASE_URL = os.getenv('LOCAL_LLM_BASE_URL', 'http://127.0.0.1:1234/v1')
LOCAL_LLM_MODEL = os.getenv('LOCAL_LLM_MODEL', 'google/gemma-4-12b')

def init_mapping_table():
    """
    初始化/修改层级映射表和唯一器械频次缓存表
    """
    conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, port=DB_PORT, database=DB_NAME)
    cursor = conn.cursor()
    
    # 1. 确认映射表结构，增加 IMPORT_PHASE 列
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS device_hierarchy_mapping (
            BRAND_NAME VARCHAR(100) NOT NULL,
            GENERIC_NAME VARCHAR(100) NOT NULL,
            CLEANED_NAME VARCHAR(255) NOT NULL,
            LEVEL_1_CATEGORY VARCHAR(100) NOT NULL,
            LEVEL_2_CATEGORY VARCHAR(100) NOT NULL,
            DEATH_COUNT INT DEFAULT 0,
            INJURY_COUNT INT DEFAULT 0,
            MALFUNCTION_COUNT INT DEFAULT 0,
            TOTAL_COUNT INT DEFAULT 0,
            IMPORT_PHASE VARCHAR(50) DEFAULT NULL,
            CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (BRAND_NAME, GENERIC_NAME),
            KEY idx_l1 (LEVEL_1_CATEGORY),
            KEY idx_l2 (LEVEL_2_CATEGORY)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    conn.commit()
    
    # 强制统一排序规则，消除 1267 校对集冲突错误
    cursor.execute("ALTER TABLE device_hierarchy_mapping CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci")
    conn.commit()
    
    # 动态检查并添加 IMPORT_PHASE 列和索引（如果不存在）
    cursor.execute("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s 
          AND TABLE_NAME = 'device_hierarchy_mapping' 
          AND COLUMN_NAME = 'IMPORT_PHASE'
    """, (DB_NAME,))
    if not cursor.fetchone():
        print(">>> 正在为 `device_hierarchy_mapping` 表添加 `IMPORT_PHASE` 列...")
        cursor.execute("ALTER TABLE device_hierarchy_mapping ADD COLUMN IMPORT_PHASE VARCHAR(50) DEFAULT NULL")
        cursor.execute("ALTER TABLE device_hierarchy_mapping ADD INDEX idx_phase (IMPORT_PHASE)")
        conn.commit()
        print(">>> `IMPORT_PHASE` 列与索引添加成功。")

    # 2. 确认并初始化唯一品牌及通用名称的频次缓存表 `device_unique_pairs`
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS device_unique_pairs (
            BRAND_NAME VARCHAR(100) NOT NULL,
            GENERIC_NAME VARCHAR(100) NOT NULL,
            CNT INT NOT NULL DEFAULT 0,
            PRIMARY KEY (BRAND_NAME, GENERIC_NAME),
            KEY idx_cnt (CNT DESC)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    conn.commit()
    
    # 检查缓存表是否有数据
    cursor.execute("SELECT COUNT(*) as cnt FROM device_unique_pairs")
    cache_count = cursor.fetchone()[0]
    if cache_count == 0:
        print(">>> 检测到唯一名称频次缓存表 `device_unique_pairs` 为空，正在执行一劳永逸的数据初始化...")
        print(">>> 这可能需要 1~2 分钟时间，请耐心等待...")
        t0 = time.time()
        cursor.execute("""
            INSERT INTO device_unique_pairs (BRAND_NAME, GENERIC_NAME, CNT)
            SELECT BRAND_NAME, GENERIC_NAME, COUNT(*)
            FROM device
            WHERE BRAND_NAME IS NOT NULL AND BRAND_NAME != ''
              AND GENERIC_NAME IS NOT NULL AND GENERIC_NAME != ''
              AND BRAND_NAME != '\\\\N' AND GENERIC_NAME != '\\\\N'
            GROUP BY BRAND_NAME, GENERIC_NAME;
        """)
        conn.commit()
        print(f">>> 唯一器械频次缓存初始化完成！共导入 {cursor.rowcount} 对唯一名称，耗时: {time.time() - t0:.2f} 秒。")
    else:
        print(f">>> 唯一名称频次缓存表已就绪，当前拥有 {cache_count} 条缓存记录。")
        
    conn.close()

def get_devices_for_coverage(target_coverage=0.80):
    """
    计算达到目标覆盖率 (例如 80%) 需要的最少唯一 (BRAND_NAME, GENERIC_NAME) 列表，并过滤已映射记录。
    """
    conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, port=DB_PORT, database=DB_NAME)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # 1. 计算总有效记录行数（直接在缓存表做 SUM，速度是毫秒级）
    cursor.execute("SELECT SUM(CNT) as total_valid_rows FROM device_unique_pairs")
    total_valid_rows = cursor.fetchone()['total_valid_rows'] or 1
    
    # 2. 查出高频 unique pairs (考虑到 95% 覆盖率仅需要 13 万对，我们这里限制最高查 150,000 条足以覆盖绝大多数覆盖率计算需求)
    print("正在从 `device_unique_pairs` 缓存表加载高频名称对并计算累积覆盖率...")
    t0 = time.time()
    cursor.execute("""
        SELECT BRAND_NAME, GENERIC_NAME, CNT
        FROM device_unique_pairs
        ORDER BY CNT DESC
        LIMIT 150000
    """)
    all_pairs = cursor.fetchall()
    print(f"加载了 {len(all_pairs)} 个高频对，耗时: {time.time() - t0:.2f} 秒。")
    
    # 3. 动态算累计覆盖率，找到 cutoff 位置
    accumulated = 0
    cutoff_idx = len(all_pairs)
    
    for idx, p in enumerate(all_pairs):
        accumulated += p['CNT']
        ratio = accumulated / total_valid_rows
        if ratio >= target_coverage:
            cutoff_idx = idx + 1
            print(f"  -> 达到目标覆盖率 {target_coverage*100:.2f}% 需要清洗前 {cutoff_idx} 个唯一对。")
            print(f"  -> 当前累计覆盖行数: {accumulated:,} / 总有效行数: {total_valid_rows:,} ({ratio*100:.2f}%)")
            break
    else:
        # 即使 LIMIT 150000 也没达到，那就取全部 150,000 对
        ratio = accumulated / total_valid_rows
        print(f"  -> 提取了全部 {len(all_pairs)} 个唯一对，可达到最大覆盖率: {ratio*100:.2f}%")
        
    target_pairs = all_pairs[:cutoff_idx]
    
    # 4. 获取已映射的 (BRAND_NAME, GENERIC_NAME) set 以排重
    cursor.execute("SELECT BRAND_NAME, GENERIC_NAME FROM device_hierarchy_mapping")
    mapped_set = {(r['BRAND_NAME'], r['GENERIC_NAME']) for r in cursor.fetchall()}
    
    # 5. 过滤掉已映射的对
    unmapped_target = []
    for p in target_pairs:
        pair = (p['BRAND_NAME'], p['GENERIC_NAME'])
        if pair not in mapped_set:
            unmapped_target.append(p)
            
    print(f"  -> 目标范围 {cutoff_idx} 对中，已完成映射: {cutoff_idx - len(unmapped_target)} 对。")
    print(f"  -> 剩余待清洗映射: {len(unmapped_target)} 对。")
    
    conn.close()
    return unmapped_target

def call_llm_batch(batch_devices):
    """
    将一批器械名称发送给大模型进行清洗和二级分类
    """
    deepseek_key = os.getenv('DEEPSEEK_API_KEY')
    deepseek_url = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
    
    # 构造输入文本
    input_lines = []
    for idx, d in enumerate(batch_devices, 1):
        input_lines.append(f"{idx}. Brand: {d['BRAND_NAME']} | Generic: {d['GENERIC_NAME']}")
    input_text = "\n".join(input_lines)
    
    prompt = f"""
你是一个专业的医疗器械警戒专家。下面是一个医疗器械名称列表，包含原始品牌名 (Brand) 和 通用名称 (Generic)。
请对这些名称进行清洗，并根据它们的功能及类别，向上进行两级（2个维度）的中文分类聚合：

1. **中文清洗名称 (cleaned_name)**: 将原始英文品牌/通用名进行规范的中文翻译或清洗表述。
2. **一级分类 (level_1_category)**: 中间类别。例如：将不同厂家的“胰岛素抽血泵”和“胰岛素输注泵”归为“胰岛素注射泵/输注系统”。
3. **二级分类 (level_2_category)**: 更高级别的宏观类别。例如：将“胰岛素注射泵”、“胰岛素笔”都归为大类“胰岛素给药装置”或“胰岛素泵”。

请直接以 JSON 格式输出，不要包含 any markdown 标记（如 ```json 等），返回一个 JSON 数组，格式如下：
[
  {{
    "original_brand": "原始品牌名",
    "original_generic": "原始通用名",
    "cleaned_name": "中文清洗名称",
    "level_1_category": "一级分类",
    "level_2_category": "二级分类"
  }},
  ...
]

【待处理列表】：
{input_text}
"""
    
    if deepseek_key:
        api_url = f"{deepseek_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {deepseek_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a medical data expert. You must output raw JSON array of objects with keys: original_brand, original_generic, cleaned_name, level_1_category, level_2_category."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1
        }
    else:
        api_url = f"{LOCAL_LLM_BASE_URL.rstrip('/')}/chat/completions"
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": LOCAL_LLM_MODEL,
            "messages": [
                {"role": "system", "content": "You are a medical data expert. You must output raw JSON array of objects with keys: original_brand, original_generic, cleaned_name, level_1_category, level_2_category."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1
        }
        
    for attempt in range(3):
        try:
            response = requests.post(api_url, headers=headers, json=payload, timeout=90)
            if response.status_code == 200:
                res_data = response.json()
                content = res_data['choices'][0]['message']['content'].strip()
                
                # 正则匹配 JSON 数组
                import re
                json_match = re.search(r'(\[.*\])', content, re.DOTALL)
                if json_match:
                    content = json_match.group(1)
                elif not content.startswith('['):
                    json_match_obj = re.search(r'(\{.*\})', content, re.DOTALL)
                    if json_match_obj:
                        content = "[" + json_match_obj.group(1) + "]"
                        
                return json.loads(content)
            elif response.status_code == 429:
                wait_time = 5 * (attempt + 1)
                print(f"  [Rate Limit] 收到 429 频控，等待 {wait_time} 秒后进行重试 (第 {attempt+1}/3 次重试)...")
                time.sleep(wait_time)
            else:
                print(f"  [LLM Error] API 返回状态码 {response.status_code}: {response.text}")
                if attempt < 2:
                    time.sleep(2)
        except Exception as e:
            print(f"  [LLM Connection Error] 调用大模型异常: {e}")
            if attempt < 2:
                time.sleep(2)
    return None

def save_mappings_with_stats(mappings, phase_tag):
    """
    计算并在数据库中批量保存分类映射、事件类型统计数据以及批次标记 (优化版: 轻量维度写入, 事实指标离线批量预计算)
    """
    if not mappings:
        return 0
        
    conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, port=DB_PORT, database=DB_NAME)
    cursor = conn.cursor()
    
    insert_sql = """
        INSERT INTO device_hierarchy_mapping (
            BRAND_NAME, GENERIC_NAME, CLEANED_NAME, LEVEL_1_CATEGORY, LEVEL_2_CATEGORY,
            DEATH_COUNT, INJURY_COUNT, MALFUNCTION_COUNT, TOTAL_COUNT, IMPORT_PHASE
        ) VALUES (%s, %s, %s, %s, %s, 0, 0, 0, 0, %s)
        ON DUPLICATE KEY UPDATE 
            CLEANED_NAME = VALUES(CLEANED_NAME),
            LEVEL_1_CATEGORY = VALUES(LEVEL_1_CATEGORY),
            LEVEL_2_CATEGORY = VALUES(LEVEL_2_CATEGORY),
            IMPORT_PHASE = VALUES(IMPORT_PHASE)
    """
    
    data_tuples = []
    for item in mappings:
        brand = item.get('original_brand', '')[:100]
        generic = item.get('original_generic', '')[:100]
        cleaned = item.get('cleaned_name', '')[:255]
        l1 = item.get('level_1_category', '')[:100]
        l2 = item.get('level_2_category', '')[:100]
        
        if brand and generic:
            data_tuples.append((brand, generic, cleaned, l1, l2, phase_tag))
            
    if data_tuples:
        cursor.executemany(insert_sql, data_tuples)
        conn.commit()
    conn.close()
    return len(data_tuples)

def _stats_worker(chunk, results):
    """
    点查事实指标的工作子线程
    """
    conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, port=DB_PORT, database=DB_NAME)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    sql = """
        SELECT 
            SUM(CASE WHEN r.EVENT_TYPE = 'D' THEN 1 ELSE 0 END) as death_count,
            SUM(CASE WHEN r.EVENT_TYPE = 'IN' THEN 1 ELSE 0 END) as injury_count,
            SUM(CASE WHEN r.EVENT_TYPE = 'M' THEN 1 ELSE 0 END) as malfunction_count,
            COUNT(*) as total_count
        FROM device d
        JOIN mdr_report r ON d.MDR_REPORT_KEY = r.MDR_REPORT_KEY
        WHERE d.BRAND_NAME = %s AND d.GENERIC_NAME = %s
    """
    for brand, generic in chunk:
        try:
            cursor.execute(sql, (brand, generic))
            res = cursor.fetchone()
            if res:
                results.append((
                    res['death_count'] or 0,
                    res['injury_count'] or 0,
                    res['malfunction_count'] or 0,
                    res['total_count'] or 0,
                    brand,
                    generic
                ))
        except Exception as e:
            print(f"  [!] 聚合点查出错 ({brand}, {generic}): {e}", flush=True)
    conn.close()

def refresh_mapping_stats(phase_tag, max_workers=10):
    """
    多线程并发点查事实指标，最后 executemany 批量刷回更新（彻底杜绝大 JOIN 在大表下的超时断连问题）
    """
    print(f"\n>>> 正在针对当前批次 ({phase_tag}) 执行多线程事实指标并行计算...", flush=True)
    t0 = time.time()
    
    conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, port=DB_PORT, database=DB_NAME)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT BRAND_NAME, GENERIC_NAME FROM device_hierarchy_mapping WHERE IMPORT_PHASE = %s", (phase_tag,))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        print(f">>> 当前批次 ({phase_tag}) 无需更新事实指标。", flush=True)
        return
        
    print(f"  -> 本次待计算指标的映射记录共: {len(rows)} 行。正在启动 {max_workers} 个并行线程计算...", flush=True)
    
    # 拆分 chunks
    chunks = [[] for _ in range(max_workers)]
    for i, r in enumerate(rows):
        chunks[i % max_workers].append((r['BRAND_NAME'], r['GENERIC_NAME']))
        
    results = []
    threads = []
    
    for chunk in chunks:
        if chunk:
            t = threading.Thread(target=_stats_worker, args=(chunk, results))
            t.start()
            threads.append(t)
            
    for t in threads:
        t.join()
        
    print(f"  -> 计算完成！开始刷入数据库...", flush=True)
    t_write = time.time()
    
    # 批量 update 写回
    conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, port=DB_PORT, database=DB_NAME)
    cursor = conn.cursor()
    update_sql = """
        UPDATE device_hierarchy_mapping 
        SET DEATH_COUNT = %s, INJURY_COUNT = %s, MALFUNCTION_COUNT = %s, TOTAL_COUNT = %s
        WHERE BRAND_NAME = %s AND GENERIC_NAME = %s
    """
    try:
        cursor.executemany(update_sql, results)
        conn.commit()
        print(f">>> [OK] 批量事实统计指标更新刷入成功！共更新了 {len(results)} 个映射对。", flush=True)
        print(f"    => 计算耗时: {t_write - t0:.2f}s | 写入耗时: {time.time() - t_write:.2f}s | 总耗时: {time.time() - t0:.2f}s", flush=True)
    except Exception as e:
        print(f"[x] 大表批量更新事实指标失败: {e}", flush=True)
    finally:
        conn.close()

def process_batch_worker(batch, batch_index, total_batches, phase_tag, stats_lock, stats_data):
    """
    单批次处理 worker 线程
    """
    t0 = time.time()
    result = call_llm_batch(batch)
    
    if result:
        try:
            saved_count = save_mappings_with_stats(result, phase_tag)
            with stats_lock:
                stats_data['total_saved'] += saved_count
                stats_data['total_processed'] += len(batch)
                stats_data['completed_batches'] += 1
                completed = stats_data['completed_batches']
                print(f" [{completed}/{total_batches}] 批次 {batch_index} 成功！保存了 {saved_count} 个映射关系 | 耗时: {time.time() - t0:.2f}s (累计保存: {stats_data['total_saved']})", flush=True)
        except Exception as e:
            with stats_lock:
                print(f" [!] 批次 {batch_index} 数据库写入异常: {e}", flush=True)
    else:
        with stats_lock:
            print(f" [x] 批次 {batch_index} 失败！大模型未返回结果。", flush=True)

def run_pipeline(target_coverage=0.80, batch_size=20, max_workers=5):
    """
    执行增量层级映射归纳流水线 (多线程并发优化版)
    """
    init_mapping_table()
    
    devices = get_devices_for_coverage(target_coverage=target_coverage)
    if not devices:
        print(f"目标覆盖率 {target_coverage*100:.2f}% 所包含的所有器械对已经映射完毕！", flush=True)
        return
        
    phase_tag = f"{int(target_coverage*100)}%_COVERAGE"
    print(f"\n>>> 开始运行层级映射归纳流水线 (多线程并发优化)...", flush=True)
    print(f"  -> 本阶段标记: {phase_tag}", flush=True)
    print(f"  -> 本次需处理: {len(devices)} 对唯一名称", flush=True)
    print(f"  -> 批次大小: {batch_size} | 并发线程数: {max_workers}", flush=True)
    
    batches = [devices[i : i + batch_size] for i in range(0, len(devices), batch_size)]
    total_batches = len(batches)
    
    stats_lock = threading.Lock()
    stats_data = {
        'total_processed': 0,
        'total_saved': 0,
        'completed_batches': 0
    }
    
    t_start = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for idx, batch in enumerate(batches, 1):
            futures.append(executor.submit(
                process_batch_worker, 
                batch, idx, total_batches, phase_tag, stats_lock, stats_data
            ))
            # 稍微错开线程启动时间，防止瞬间发出大量并发请求
            time.sleep(0.2)
            
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"线程执行中抛出异常: {e}", flush=True)
                
    total_processed = stats_data['total_processed']
    total_saved = stats_data['total_saved']
    
    print(f"\n====== 流水线执行完毕！共耗时: {time.time() - t_start:.2f}秒 ======", flush=True)
    print(f"成功处理: {total_processed}/{len(devices)}，成功保存/更新: {total_saved} 个映射。", flush=True)
    
    # 批量更新事实统计数据 (离线一次性刷新，避开大循环里的 JOIN)
    if total_saved > 0:
        refresh_mapping_stats(phase_tag, max_workers=max_workers)

if __name__ == '__main__':
    # 默认覆盖率 80% (0.80)
    target_cov = 0.80
    max_workers = 5
    if len(sys.argv) > 1:
        try:
            target_cov = float(sys.argv[1])
            # 支持传入如 "80" 转换成 0.80
            if target_cov > 1.0:
                target_cov = target_cov / 100.0
        except ValueError:
            pass
            
    if len(sys.argv) > 2:
        try:
            max_workers = int(sys.argv[2])
        except ValueError:
            pass
            
    run_pipeline(target_coverage=target_cov, batch_size=20, max_workers=max_workers)
