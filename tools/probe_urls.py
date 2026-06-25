import urllib.request

urls = [
    "https://www.accessdata.fda.gov/MAUDE/ftparea/deviceproblemcode.zip",
    "https://www.accessdata.fda.gov/MAUDE/ftparea/deviceproblems.zip",
    "https://www.accessdata.fda.gov/MAUDE/ftparea/deviceproblem.zip",
    "https://www.accessdata.fda.gov/MAUDE/ftparea/foidevproblems.zip",
    "https://www.accessdata.fda.gov/MAUDE/ftparea/foidevproblem.zip",
    "https://www.accessdata.fda.gov/MAUDE/ftparea/mdrfoiproblems.zip",
    "https://www.accessdata.fda.gov/MAUDE/ftparea/mdrfoiproblem.zip",
    "https://www.accessdata.fda.gov/MAUDE/ftparea/mdrproblemcodes.zip",
    "https://www.accessdata.fda.gov/MAUDE/ftparea/mdrproblemcode.zip",
]

def main():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    for url in urls:
        print(f"正在探测: {url} ... ", end="", flush=True)
        req = urllib.request.Request(url, method='HEAD', headers=headers)
        try:
            with urllib.request.urlopen(req) as resp:
                print(f"成功! Status: {resp.status}")
        except urllib.error.HTTPError as e:
            print(f"失败 (HTTP {e.code})")
        except Exception as e:
            print(f"出错 ({e})")

if __name__ == '__main__':
    main()
