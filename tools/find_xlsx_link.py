import urllib.request
import re
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST_PATH = os.path.join(BASE_DIR, "data", "raw", "mdr_adverse_event_codes.xlsx")

# 探测最新定位的 FDA 编码页 URL 路径
urls_to_try = [
    "https://www.fda.gov/medical-devices/mdr-adverse-event-codes/coding-resources",
    "https://www.fda.gov/medical-devices/mdr-adverse-event-codes",
    "https://www.fda.gov/medical-devices/medical-device-safety/medical-device-reporting-mdr-how-report-medical-device-problems/mdr-adverse-event-codes",
]

def main():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    html_content = ""
    active_url = ""
    
    for url in urls_to_try:
        print(f"正在尝试抓取页面: {url} ... ", end="", flush=True)
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req) as resp:
                html_content = resp.read().decode('utf-8', errors='ignore')
                active_url = url
                print("成功! (200 OK)", flush=True)
                break
        except Exception as e:
            print(f"失败 ({e})", flush=True)
            
    if not html_content:
        print("未能在 FDA 网站上找到有效的问题编码映射页面！", flush=True)
        return
        
    # 在 HTML 中寻找 .xlsx 或 .xls 链接，或者 /media/ 链接
    links = re.findall(r'href="([^"]+\.xlsx[^"]*)"', html_content, re.IGNORECASE)
    links_media = re.findall(r'href="(/media/[^"]+)"', html_content, re.IGNORECASE)
    
    xlsx_url = ""
    for link in links + links_media:
        full_link = link if link.startswith('http') else "https://www.fda.gov" + link
        # 寻找与 mdr codes 相关的 Excel 下载链接
        if 'code' in link.lower() or 'mdr' in link.lower() or 'event' in link.lower():
            xlsx_url = full_link
            break
            
    if not xlsx_url and links_media:
        xlsx_url = "https://www.fda.gov" + links_media[0]
        
    if not xlsx_url:
        print("未在页面中找到符合条件的 Excel 下载链接！", flush=True)
        return
        
    print(f"找到 Excel 下载链接: {xlsx_url}", flush=True)
    
    # 确保 data/raw 目录存在
    os.makedirs(os.path.dirname(DEST_PATH), exist_ok=True)
    
    # 执行下载
    print(f"正在下载全量编码表到: {DEST_PATH} ...", flush=True)
    req_down = urllib.request.Request(xlsx_url, headers=headers)
    with urllib.request.urlopen(req_down) as response, open(DEST_PATH, 'wb') as out_file:
        out_file.write(response.read())
        
    print(f"全量映射表 Excel 下载成功！大小: {os.path.getsize(DEST_PATH) / 1024:.2f} KB", flush=True)

if __name__ == '__main__':
    main()
