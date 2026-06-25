import os
import subprocess
import markdown

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 定义源文件和目标文件路径
src_md = os.path.join(BASE_DIR, "reports", "davinci_death_dataset", "davinci_death_analysis_report.md")
dest_html = os.path.join(BASE_DIR, "reports", "davinci_death_dataset", "davinci_death_analysis_report.html")
dest_pdf = os.path.join(BASE_DIR, "reports", "davinci_death_dataset", "davinci_death_analysis_report.pdf")

# 高级设计感的 CSS 样式 (Premium Research Report Style)
CSS_STYLE = """
<style>
    :root {
        --primary-color: #2563eb;
        --text-color: #1f2937;
        --bg-color: #f9fafb;
        --card-bg: #ffffff;
        --border-color: #e5e7eb;
        --code-bg: #f3f4f6;
    }
    
    body {
        font-family: 'Outfit', 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        line-height: 1.7;
        color: var(--text-color);
        background-color: var(--bg-color);
        margin: 0;
        padding: 40px 20px;
    }
    
    .container {
        max-width: 850px;
        margin: 0 auto;
        background: var(--card-bg);
        padding: 50px;
        border-radius: 12px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.02);
        border: 1px solid var(--border-color);
    }
    
    h1 {
        font-size: 2.2rem;
        color: #111827;
        border-bottom: 2px solid var(--primary-color);
        padding-bottom: 15px;
        margin-top: 0;
        margin-bottom: 30px;
        font-weight: 800;
        letter-spacing: -0.025em;
    }
    
    h2 {
        font-size: 1.5rem;
        color: #1f2937;
        margin-top: 40px;
        margin-bottom: 20px;
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 8px;
        font-weight: 700;
    }
    
    h3 {
        font-size: 1.2rem;
        color: #374151;
        margin-top: 30px;
        font-weight: 600;
    }
    
    p {
        margin-bottom: 1.5rem;
    }
    
    blockquote {
        border-left: 4px solid var(--primary-color);
        background-color: #eff6ff;
        padding: 15px 20px;
        margin: 20px 0;
        border-radius: 0 8px 8px 0;
        color: #1e40af;
        font-style: italic;
    }
    
    blockquote p {
        margin: 0;
    }
    
    /* 强提示样式 */
    blockquote strong {
        color: #1d4ed8;
    }
    
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 30px 0;
        font-size: 0.95rem;
    }
    
    th, td {
        border: 1px solid var(--border-color);
        padding: 12px 15px;
        text-align: left;
    }
    
    th {
        background-color: #f8fafc;
        font-weight: 600;
        color: #334155;
    }
    
    tr:nth-child(even) {
        background-color: #f8fafc;
    }
    
    code {
        font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
        background-color: var(--code-bg);
        padding: 3px 6px;
        border-radius: 4px;
        font-size: 0.9em;
        color: #d97706;
    }
    
    pre {
        background-color: #1e293b;
        color: #f8fafc;
        padding: 20px;
        border-radius: 8px;
        overflow-x: auto;
        margin: 20px 0;
    }
    
    pre code {
        background-color: transparent;
        padding: 0;
        color: inherit;
        font-size: 0.9em;
    }
    
    ul, ol {
        margin-bottom: 1.5rem;
        padding-left: 25px;
    }
    
    li {
        margin-bottom: 0.5rem;
    }
    
    /* 打印分页优化 */
    @media print {
        body {
            background-color: #ffffff;
            padding: 0;
        }
        .container {
            box-shadow: none;
            border: none;
            padding: 0;
            max-width: 100%;
        }
        h2, h3, table {
            page-break-inside: avoid;
        }
    }
</style>
"""

def md_to_html():
    print(">>> 正在将 Markdown 报告转换为 HTML...")
    if not os.path.exists(src_md):
        print(f"[错误] 未找到源 Markdown 文件: {src_md}")
        return False
        
    with open(src_md, 'r', encoding='utf-8') as f:
        md_text = f.read()
        
    # 处理 Github Alerts 语法类似 > [!NOTE] 转为普通 blockquote 的美化
    # 简单替换为可识别的样式
    md_text = md_text.replace("> [!NOTE]", "> **[注]**")
    md_text = md_text.replace("> [!IMPORTANT]", "> **[重要提示]**")
    md_text = md_text.replace("> [!WARNING]", "> **[警示]**")
    
    html_content = markdown.markdown(md_text, extensions=['tables', 'fenced_code'])
    
    full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>达芬奇手术机器人致死案例挖掘报告</title>
    {CSS_STYLE}
</head>
<body>
    <div class="container">
        {html_content}
    </div>
</body>
</html>
"""
    
    with open(dest_html, 'w', encoding='utf-8') as f:
        f.write(full_html)
    print(f"[成功] HTML 报告已输出: {dest_html}")
    return True

def find_edge_path():
    # 常见 Microsoft Edge 安装路径列表
    paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe")
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return None

def html_to_pdf():
    print(">>> 正在调用 Headless Edge 浏览器将 HTML 打印成 PDF...")
    edge_path = find_edge_path()
    if not edge_path:
        print("[警告] 未发现 Microsoft Edge 安装路径！无法完成 PDF 转换。")
        return False
        
    print(f"    - 发现 Edge 路径: {edge_path}")
    print(f"    - 正在将 {dest_html} 导出为 PDF...")
    
    # 构造 Edge headless 打印 pdf 命令
    cmd = [
        edge_path,
        "--headless",
        "--disable-gpu",
        f"--print-to-pdf={dest_pdf}",
        dest_html
    ]
    
    try:
        # 运行 Edge 转换进程
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"[成功] PDF 报告已输出: {dest_pdf}")
        return True
    except Exception as e:
        print(f"[错误] PDF 转换进程执行异常: {e}")
        return False

def main():
    if md_to_html():
        html_to_pdf()

if __name__ == '__main__':
    main()
