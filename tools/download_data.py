import os
import urllib.request
import time
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

RAW_DATA_DIR = r"e:\pythonProject\MAUDE\rawData"
DOWNLOAD_LIST_PATH = r"e:\pythonProject\MAUDE\download_list.txt"
MAX_WORKERS = 2  # 降低并发数至 2，减少对 FDA 频繁请求导致的拦截
MAX_RETRIES = 15 # 既然有断点续传接力，可以调多重试次数，保障全部下全
TIMEOUT = 40     # 超时阈值

HEADERS_TEMPLATE = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

print_lock = threading.Lock()

def safe_print(message):
    with print_lock:
        print(message, flush=True)

def download_file(url):
    filename = url.split('/')[-1].strip()
    dest_path = os.path.join(RAW_DATA_DIR, filename)
    
    # 获取远程 Content-Length
    req_probe = urllib.request.Request(url, headers=HEADERS_TEMPLATE)
    remote_size = 0
    try:
        with urllib.request.urlopen(req_probe, timeout=TIMEOUT) as response:
            remote_size = int(response.info().get('Content-Length', 0))
    except Exception as e:
        safe_print(f"  [探测失败] {filename} 无法获取远程大小: {e}")
        # 如果获取失败，尝试无 Range 模式普通下载 (不跳过)
        pass

    # 开始断点接力下载
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # 检查本地已经下载的字节数
            local_size = os.path.getsize(dest_path) if os.path.exists(dest_path) else 0
            
            # 校验是否已经下完
            if remote_size > 0 and local_size == remote_size:
                safe_print(f"  [跳过] {filename} 已完整存在于本地。")
                return filename, True
            elif remote_size > 0 and local_size > remote_size:
                # 本地比远程还大，说明可能下载了错误的文件头，予以清理
                safe_print(f"  [清理] 本地 {filename} 异常偏大，正在清除重下...")
                os.remove(dest_path)
                local_size = 0

            # 构造请求头，支持断点续传 Range
            headers = HEADERS_TEMPLATE.copy()
            if local_size > 0:
                headers['Range'] = f"bytes={local_size}-"
                mode = 'ab'  # 追加模式
                action_str = f"接力下载 (当前已完成: {local_size/(1024**2):.2f} MB)"
            else:
                mode = 'wb'  # 新建写入模式
                action_str = "全新下载"
                
            req = urllib.request.Request(url, headers=headers)
            
            # 加一点随机避让，防多并发剧烈摩擦
            time.sleep(1.0)
            
            with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
                resp_info = response.info()
                
                # 如果我们发了 Range，但服务器返回了 200 而不是 206，说明不支持 Range，需要重头写
                status = response.status
                if status == 200 and local_size > 0:
                    # 服务器无视了 Range 重新发了全量数据，需要把 mode 纠正为 wb
                    mode = 'wb'
                    local_size = 0
                
                block_size = 1024 * 256  # 256KB
                downloaded_chunk = 0
                
                t0 = time.time()
                with open(dest_path, mode) as f:
                    while True:
                        buffer = response.read(block_size)
                        if not buffer:
                            break
                        f.write(buffer)
                        downloaded_chunk += len(buffer)
                
                # 校验最终大小
                final_local_size = os.path.getsize(dest_path)
                if remote_size > 0 and final_local_size != remote_size:
                    raise Exception(f"传输遭遇提前切断！当前本地大小: {final_local_size}，远程应为: {remote_size}。")
                
                duration = time.time() - t0
                speed = (downloaded_chunk / (1024**2)) / duration if duration > 0 else 0
                safe_print(f"  [成功] {filename} {action_str} 完成！本次拉取: {downloaded_chunk/(1024**2):.2f} MB, 平均速度: {speed:.2f} MB/s。")
                return filename, True
                
        except Exception as e:
            # 获取当前本地大小，以便下次重试打印
            curr_size = os.path.getsize(dest_path) if os.path.exists(dest_path) else 0
            safe_print(f"  [重试警告] {filename} (尝试 {attempt}/{MAX_RETRIES}) 遭遇中断: {e}")
            
            # 如果错误类似于 HTTP 416 (Requested Range Not Satisfiable)，说明范围冲突，清理重跑
            if "416" in str(e):
                if os.path.exists(dest_path):
                    try:
                        os.remove(dest_path)
                    except:
                        pass
            
            # 避让休眠
            time.sleep(3 * attempt)
            
    safe_print(f"  [失败] {filename} 在 {MAX_RETRIES} 次断点接力重试后依然未完整下载。")
    return filename, False

def main():
    print("==================================================")
    print("MAUDE 历史数据包自动下载工具 (终极 HTTP Range 断点续传版)")
    print("==================================================")
    
    if not os.path.exists(RAW_DATA_DIR):
        os.makedirs(RAW_DATA_DIR)
        
    if not os.path.exists(DOWNLOAD_LIST_PATH):
        print(f"错误: 找不到下载列表文件 {DOWNLOAD_LIST_PATH}。")
        return
        
    with open(DOWNLOAD_LIST_PATH, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip() and line.strip().startswith('http')]
        
    print(f"读取到 {len(urls)} 个下载任务，启用并发数: {MAX_WORKERS}")
    
    success_count = 0
    fail_count = 0
    
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(download_file, url): url for url in urls}
        
        for future in as_completed(futures):
            url = futures[future]
            try:
                fname, success = future.result()
                if success:
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                print(f"  处理任务 {url} 发生未知错误: {e}")
                fail_count += 1
                
    total_time = time.time() - t0
    print("\n==================================================")
    print("全部下载与断点接力校验任务处理完毕！")
    print(f"成功: {success_count} 个, 失败: {fail_count} 个。")
    print(f"总耗时: {total_time/60:.2f} 分钟。")
    print("==================================================")
    if fail_count == 0:
        print("下一步：您可以运行 python extract_and_rename.py 智能解压缩。")
    else:
        print("提示：有部分文件未完整下载。请重新运行本脚本，它会从上次中断的位置自动继续下载！")

if __name__ == '__main__':
    main()
