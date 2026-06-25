import os
import json
import csv

def build_collapsible_html():
    csv_path = r"e:\pythonProjects\MAUDE\reports\maude_global_hierarchy_analysis.csv"
    print(f">>> 正在从 CSV 报表获取层级分类数据: {csv_path}")
    
    if not os.path.exists(csv_path):
        print(f"[ERROR] 找不到 CSV 报表文件: {csv_path}")
        return
        
    tree = {}
    
    # 使用 utf-8-sig 以便自动剥离 Excel 导出的 BOM 头
    with open(csv_path, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for r in reader:
            l1 = r.get('一级分类(清洗后中文器械名)') or "未分类微观器械"
            l2 = r.get('二级分类(中观大类)') or "未分类中观"
            l3 = r.get('三级分类(宏观大类)') or "未分类宏观"
            
            # 过滤异常行
            if l1 == '一级分类(清洗后中文器械名)':
                continue
                
            try:
                pairs = int(r.get('关联器械对数') or 0)
                death = int(r.get('死亡事件数') or 0)
                injury = int(r.get('伤害事件数') or 0)
                malfunc = int(r.get('故障事件数') or 0)
                total = int(r.get('事件总数') or 0)
            except ValueError:
                continue
            
            # 1. 注入 L3
            if l3 not in tree:
                tree[l3] = {"total": 0, "death": 0, "injury": 0, "malfunc": 0, "pairs": 0, "children": {}}
            tree[l3]["total"] += total
            tree[l3]["death"] += death
            tree[l3]["injury"] += injury
            tree[l3]["malfunc"] += malfunc
            tree[l3]["pairs"] += pairs
            
            # 2. 注入 L2
            if l2 not in tree[l3]["children"]:
                tree[l3]["children"][l2] = {"total": 0, "death": 0, "injury": 0, "malfunc": 0, "pairs": 0, "children": {}}
            tree[l3]["children"][l2]["total"] += total
            tree[l3]["children"][l2]["death"] += death
            tree[l3]["children"][l2]["injury"] += injury
            tree[l3]["children"][l2]["malfunc"] += malfunc
            tree[l3]["children"][l2]["pairs"] += pairs
            
            # 3. 注入 L1
            if l1 not in tree[l3]["children"][l2]["children"]:
                tree[l3]["children"][l2]["children"][l1] = {
                    "total": 0,
                    "death": 0,
                    "injury": 0,
                    "malfunc": 0,
                    "pairs": 0
                }
            tree[l3]["children"][l2]["children"][l1]["total"] += total
            tree[l3]["children"][l2]["children"][l1]["death"] += death
            tree[l3]["children"][l2]["children"][l1]["injury"] += injury
            tree[l3]["children"][l2]["children"][l1]["malfunc"] += malfunc
            tree[l3]["children"][l2]["children"][l1]["pairs"] += pairs
            
    print(f">>> 成功提取并构建层级树。宏观分类数: {len(tree)}")
    
    # 转换为 JSON
    tree_json = json.dumps(tree, ensure_ascii=False)
    
    # 使用原始多行字符串，保护所有反斜杠不被 Python 转义
    html_template = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MAUDE 医疗器械全球层级聚合折叠树状大盘</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Noto+Sans+SC:wght@300;400;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: hsl(222, 47%, 9%);
            --panel-bg: rgba(15, 23, 42, 0.65);
            --border-color: rgba(255, 255, 255, 0.08);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --card-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            background-color: var(--bg-color);
            background-image: 
                radial-gradient(at 0% 0%, rgba(59, 130, 246, 0.1) 0, transparent 50%),
                radial-gradient(at 100% 100%, rgba(139, 92, 246, 0.1) 0, transparent 50%);
            background-attachment: fixed;
            color: var(--text-primary);
            font-family: 'Outfit', 'Noto Sans SC', sans-serif;
            min-height: 100vh;
            padding: 2.5rem;
        }

        .container {
            max-width: 1540px;
            margin: 0 auto;
        }

        header {
            margin-bottom: 2rem;
            text-align: center;
        }

        h1 {
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(to right, #60a5fa, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
            letter-spacing: -0.5px;
        }

        .subtitle {
            color: var(--text-secondary);
            font-size: 1.05rem;
            font-weight: 300;
        }

        /* 统计卡片网格 */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 1rem;
            margin-bottom: 1.5rem;
        }

        .stat-card {
            background: var(--panel-bg);
            border: 1px solid var(--border-color);
            backdrop-filter: blur(12px);
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
            box-shadow: var(--card-shadow);
            transition: transform 0.2s ease;
        }

        .stat-card:hover {
            transform: translateY(-2px);
        }

        .stat-label {
            color: var(--text-secondary);
            font-size: 0.8rem;
            margin-bottom: 0.25rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .stat-value {
            font-size: 1.35rem;
            font-weight: 800;
            color: #fff;
            font-family: 'Outfit', sans-serif;
        }

        /* 控制栏 */
        .control-bar {
            background: var(--panel-bg);
            border: 1px solid var(--border-color);
            backdrop-filter: blur(12px);
            border-radius: 16px;
            padding: 1rem 1.5rem;
            box-shadow: var(--card-shadow);
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }

        .search-box-wrapper {
            position: relative;
            flex: 1;
            max-width: 450px;
        }

        .search-box {
            width: 100%;
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 0.6rem 1.15rem;
            color: #fff;
            font-family: inherit;
            font-size: 0.95rem;
            transition: all 0.3s ease;
        }

        .search-box:focus {
            outline: none;
            border-color: #3b82f6;
            box-shadow: 0 0 12px rgba(59, 130, 246, 0.25);
        }

        .btn-group {
            display: flex;
            gap: 0.75rem;
        }

        .btn {
            font-family: inherit;
            font-size: 0.9rem;
            font-weight: 600;
            padding: 0.55rem 1.1rem;
            border-radius: 10px;
            border: 1px solid var(--border-color);
            cursor: pointer;
            transition: all 0.2s ease;
            user-select: none;
        }

        .btn-primary {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: #fff;
            border: none;
        }

        .btn-primary:hover {
            background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%);
            box-shadow: 0 0 12px rgba(59, 130, 246, 0.35);
            transform: translateY(-1px);
        }

        .btn-secondary {
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-primary);
        }

        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.15);
            transform: translateY(-1px);
        }

        /* 表格容器 */
        .table-container {
            background: var(--panel-bg);
            border: 1px solid var(--border-color);
            backdrop-filter: blur(12px);
            border-radius: 16px;
            box-shadow: var(--card-shadow);
            overflow: hidden;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }

        th {
            background: rgba(15, 23, 42, 0.6);
            border-bottom: 2px solid var(--border-color);
            padding: 1rem 1.5rem;
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            cursor: pointer;
            transition: all 0.2s ease;
            user-select: none;
        }

        th:hover {
            background: rgba(30, 41, 59, 0.8);
            color: #fff;
        }

        th.sorted-active {
            color: #3b82f6;
            font-weight: 700;
        }

        td {
            padding: 0.8rem 1.5rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
            font-size: 0.95rem;
            color: #e2e8f0;
            transition: background-color 0.2s ease;
        }

        .num-col {
            text-align: right;
            font-family: 'Outfit', sans-serif;
        }

        .high-risk {
            color: #f87171;
            font-weight: 600;
            text-shadow: 0 0 8px rgba(248, 113, 113, 0.4);
        }

        /* 树形行层级色彩 */
        .row-l3 {
            background: rgba(30, 41, 59, 0.55);
            font-weight: 600;
            border-left: 4px solid #3b82f6;
            cursor: pointer;
        }

        .row-l3:hover {
            background: rgba(30, 41, 59, 0.8);
        }

        .row-l2 {
            background: rgba(30, 41, 59, 0.25);
            font-weight: 500;
            border-left: 3px solid #a78bfa;
            cursor: pointer;
        }

        .row-l2:hover {
            background: rgba(30, 41, 59, 0.45);
        }

        .row-l1 {
            background: transparent;
            font-weight: 300;
            border-left: 2px dashed rgba(255, 255, 255, 0.1);
        }

        .row-l1:hover {
            background: rgba(255, 255, 255, 0.02);
        }

        /* 折叠箭头 */
        .toggle-icon {
            display: inline-block;
            width: 14px;
            margin-right: 6px;
            color: var(--text-secondary);
            font-size: 0.8rem;
            transition: transform 0.2s ease;
            text-align: center;
        }

        .sort-icon {
            display: inline-block;
            margin-left: 4px;
            font-family: monospace;
            font-size: 0.85rem;
            color: var(--text-secondary);
        }

        th.sorted-active .sort-icon {
            color: #3b82f6;
        }

        .indent-l2 {
            padding-left: 2.25rem !important;
        }

        .indent-l1 {
            padding-left: 3.75rem !important;
        }

        @media (max-width: 1200px) {
            .stats-grid {
                grid-template-columns: repeat(3, 1fr);
            }
        }

        @media (max-width: 768px) {
            body {
                padding: 1rem;
            }
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            .control-bar {
                flex-direction: column;
                align-items: stretch;
            }
            .search-box-wrapper {
                max-width: none;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>MAUDE 医疗器械全球层级聚合折叠树状大盘</h1>
            <p class="subtitle">分级聚合分析 • 3级: 宏观大类 ▸ 2级: 中观分类 ▸ 1级: 微观器械明细 (全量数据，支持多级自适应排序)</p>
        </header>

        <!-- 统计面板 -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">宏观大类 (L3)</div>
                <div class="stat-value" id="stat-l3">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">中观分类 (L2)</div>
                <div class="stat-value" id="stat-l2">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">微观器械 (L1)</div>
                <div class="stat-value" id="stat-l1">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">死亡事件</div>
                <div class="stat-value high-risk" id="stat-death">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">伤害事件</div>
                <div class="stat-value" id="stat-injury">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">事件总数</div>
                <div class="stat-value" id="stat-total" style="background: linear-gradient(to right, #60a5fa, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">0</div>
            </div>
        </div>

        <div class="control-bar">
            <div class="search-box-wrapper">
                <input type="text" id="searchInput" class="search-box" placeholder="输入名称关键字快速检索大、中、微类..." oninput="handleSearch()">
            </div>
            <div class="btn-group">
                <button class="btn btn-primary" onclick="expandAll()">展开全部</button>
                <button class="btn btn-secondary" onclick="collapseAll()">折叠全部</button>
            </div>
        </div>

        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th id="th-name" onclick="changeSort('name')" style="width: 45%;">
                            层级架构 (3级: 宏观 ▸ 2级: 中观 ▸ 1级: 清洗名) <span class="sort-icon">↕</span>
                        </th>
                        <th id="th-pairs" onclick="changeSort('pairs')" class="num-col" style="width: 10%;">
                            器械对数 <span class="sort-icon">↕</span>
                        </th>
                        <th id="th-death" onclick="changeSort('death')" class="num-col" style="width: 10%;">
                            死亡事件 <span class="sort-icon">↕</span>
                        </th>
                        <th id="th-injury" onclick="changeSort('injury')" class="num-col" style="width: 10%;">
                            伤害事件 <span class="sort-icon">↕</span>
                        </th>
                        <th id="th-malfunc" onclick="changeSort('malfunc')" class="num-col" style="width: 10%;">
                            故障事件 <span class="sort-icon">↕</span>
                        </th>
                        <th id="th-total" onclick="changeSort('total')" class="num-col" style="width: 15%;">
                            事件总数 <span class="sort-icon">↕</span>
                        </th>
                    </tr>
                </thead>
                <tbody id="tableBody">
                    <!-- JS 声明式动态渲染 -->
                </tbody>
            </table>
        </div>
    </div>

    <script>
        // 压入全量分级聚合树型数据
        const treeData = __TREE_DATA_JSON__;

        // 全局展开状态
        const expandedL3 = new Set();
        const expandedL2 = new Set(); // 存储格式为 "l3Key||l2Key"

        // 默认排序：按事件总数降序
        let sortField = 'total';
        let sortOrder = 'desc';

        // 搜索词
        let searchQuery = '';

        // 格式化千分位
        function fmt(n) {
            if (n === undefined || n === null) return '0';
            return Number(n).toLocaleString('en-US');
        }

        // HTML 及 字符串转义，避免单引号导致 onclick 挂掉
        function escapeHtml(str) {
            if (!str) return '';
            return str.toString()
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#039;');
        }

        function escapeQuote(str) {
            if (!str) return '';
            return str.toString()
                .replace(/\\/g, '\\\\')
                .replace(/'/g, "\\'")
                .replace(/"/g, '&quot;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');
        }

        // 排序规则生成器
        function getCompareFn(field, order, getValFn) {
            return (a, b) => {
                const valA = getValFn(a);
                const valB = getValFn(b);
                if (field === 'name') {
                    const strA = String(valA || '');
                    const strB = String(valB || '');
                    return order === 'asc' ? strA.localeCompare(strB, 'zh') : strB.localeCompare(strA, 'zh');
                } else {
                    const numA = Number(valA || 0);
                    const numB = Number(valB || 0);
                    return order === 'asc' ? numA - numB : numB - numA;
                }
            };
        }

        // 计算搜索匹配情况
        function computeSearchMatch(query) {
            if (!query) return null;
            const q = query.toLowerCase();

            const matchInfo = {
                visibleL3: new Set(),
                visibleL2: new Set(),         // 存储格式: "l3Key||l2Key"
                visibleL1: new Set(),         // 存储格式: "l3Key||l2Key||l1Key"
                forceExpandL3: new Set(),
                forceExpandL2: new Set()
            };

            Object.keys(treeData).forEach(l3Key => {
                const l3Data = treeData[l3Key];
                const l3Match = l3Key.toLowerCase().includes(q);
                let hasMatchedSubNode = false;

                Object.keys(l3Data.children).forEach(l2Key => {
                    const l2Data = l3Data.children[l2Key];
                    const l2Match = l2Key.toLowerCase().includes(q);
                    const l2CompoundKey = l3Key + '||' + l2Key;
                    let hasMatchedL1 = false;

                    Object.keys(l2Data.children).forEach(l1Key => {
                        const l1Match = l1Key.toLowerCase().includes(q);
                        const l1CompoundKey = l3Key + '||' + l2Key + '||' + l1Key;

                        if (l1Match || l2Match || l3Match) {
                            matchInfo.visibleL1.add(l1CompoundKey);
                            if (l1Match) {
                                hasMatchedL1 = true;
                            }
                        }
                    });

                    if (l2Match || hasMatchedL1 || l3Match) {
                        matchInfo.visibleL2.add(l2CompoundKey);
                        hasMatchedSubNode = true;
                        if (hasMatchedL1) {
                            matchInfo.forceExpandL2.add(l2CompoundKey);
                        }
                    }
                });

                if (l3Match || hasMatchedSubNode) {
                    matchInfo.visibleL3.add(l3Key);
                    if (hasMatchedSubNode) {
                        matchInfo.forceExpandL3.add(l3Key);
                    }
                }
            });

            return matchInfo;
        }

        // 声明式渲染整个表格与更新卡片统计
        function renderTable() {
            const tbody = document.getElementById('tableBody');
            const matchInfo = computeSearchMatch(searchQuery);

            // 1. 筛选 L3 键
            let l3Keys = Object.keys(treeData);
            if (matchInfo) {
                l3Keys = l3Keys.filter(k => matchInfo.visibleL3.has(k));
            }
            // 排序 L3 键
            const cmpL3 = getCompareFn(sortField, sortOrder, key => sortField === 'name' ? key : treeData[key][sortField]);
            l3Keys.sort(cmpL3);

            let htmlLines = [];

            // 2. 统计量初始化
            let totalL3Count = 0;
            let totalL2Count = 0;
            let totalL1Count = 0;
            let sumDeath = 0;
            let sumInjury = 0;
            let sumTotal = 0;

            if (matchInfo) {
                totalL3Count = matchInfo.visibleL3.size;
                totalL2Count = matchInfo.visibleL2.size;
                totalL1Count = matchInfo.visibleL1.size;

                // 从可见 L1 中累加事件总数
                matchInfo.visibleL1.forEach(compKey => {
                    const parts = compKey.split('||');
                    const l3 = parts[0];
                    const l2 = parts[1];
                    const l1 = parts[2];
                    const l1Data = treeData[l3].children[l2].children[l1];
                    sumDeath += l1Data.death || 0;
                    sumInjury += l1Data.injury || 0;
                    sumTotal += l1Data.total || 0;
                });
            } else {
                // 全量统计
                totalL3Count = l3Keys.length;
                l3Keys.forEach(l3Key => {
                    const l3Data = treeData[l3Key];
                    sumDeath += l3Data.death || 0;
                    sumInjury += l3Data.injury || 0;
                    sumTotal += l3Data.total || 0;

                    const l2Keys = Object.keys(l3Data.children);
                    totalL2Count += l2Keys.length;
                    l2Keys.forEach(l2Key => {
                        totalL1Count += Object.keys(l3Data.children[l2Key].children).length;
                    });
                });
            }

            // 更新卡片数据
            document.getElementById('stat-l3').innerText = fmt(totalL3Count);
            document.getElementById('stat-l2').innerText = fmt(totalL2Count);
            document.getElementById('stat-l1').innerText = fmt(totalL1Count);
            document.getElementById('stat-death').innerText = fmt(sumDeath);
            document.getElementById('stat-injury').innerText = fmt(sumInjury);
            document.getElementById('stat-total').innerText = fmt(sumTotal);

            // 3. 构建表格 DOM 行
            l3Keys.forEach(l3Key => {
                const l3Data = treeData[l3Key];
                const isL3Expanded = matchInfo ? (matchInfo.forceExpandL3.has(l3Key) || expandedL3.has(l3Key)) : expandedL3.has(l3Key);

                htmlLines.push(`
                    <tr class="row-l3" onclick="handleL3Click('${escapeQuote(l3Key)}')">
                        <td><span class="toggle-icon">${isL3Expanded ? '▾' : '▸'}</span>${escapeHtml(l3Key)}</td>
                        <td class="num-col">${fmt(l3Data.pairs)}</td>
                        <td class="num-col ${l3Data.death > 0 ? 'high-risk' : ''}">${fmt(l3Data.death)}</td>
                        <td class="num-col">${fmt(l3Data.injury)}</td>
                        <td class="num-col">${fmt(l3Data.malfunc)}</td>
                        <td class="num-col">${fmt(l3Data.total)}</td>
                    </tr>
                `);

                if (isL3Expanded) {
                    let l2Keys = Object.keys(l3Data.children);
                    if (matchInfo) {
                        l2Keys = l2Keys.filter(k => matchInfo.visibleL2.has(l3Key + '||' + k));
                    }
                    // 排序 L2 键
                    const cmpL2 = getCompareFn(sortField, sortOrder, key => sortField === 'name' ? key : l3Data.children[key][sortField]);
                    l2Keys.sort(cmpL2);

                    l2Keys.forEach(l2Key => {
                        const l2Data = l3Data.children[l2Key];
                        const l2CompoundKey = l3Key + '||' + l2Key;
                        const isL2Expanded = matchInfo ? (matchInfo.forceExpandL2.has(l2CompoundKey) || expandedL2.has(l2CompoundKey)) : expandedL2.has(l2CompoundKey);

                        htmlLines.push(`
                            <tr class="row-l2" onclick="handleL2Click(event, '${escapeQuote(l3Key)}', '${escapeQuote(l2Key)}')">
                                <td class="indent-l2"><span class="toggle-icon">${isL2Expanded ? '▾' : '▸'}</span>${escapeHtml(l2Key)}</td>
                                <td class="num-col">${fmt(l2Data.pairs)}</td>
                                <td class="num-col ${l2Data.death > 0 ? 'high-risk' : ''}">${fmt(l2Data.death)}</td>
                                <td class="num-col">${fmt(l2Data.injury)}</td>
                                <td class="num-col">${fmt(l2Data.malfunc)}</td>
                                <td class="num-col">${fmt(l2Data.total)}</td>
                            </tr>
                        `);

                        if (isL2Expanded) {
                            let l1Keys = Object.keys(l2Data.children);
                            if (matchInfo) {
                                l1Keys = l1Keys.filter(k => matchInfo.visibleL1.has(l3Key + '||' + l2Key + '||' + k));
                            }
                            // 排序 L1 键
                            const cmpL1 = getCompareFn(sortField, sortOrder, key => sortField === 'name' ? key : l2Data.children[key][sortField]);
                            l1Keys.sort(cmpL1);

                            l1Keys.forEach(l1Key => {
                                const l1Data = l2Data.children[l1Key];
                                htmlLines.push(`
                                    <tr class="row-l1">
                                        <td class="indent-l1">• ${escapeHtml(l1Key)}</td>
                                        <td class="num-col">${fmt(l1Data.pairs)}</td>
                                        <td class="num-col ${l1Data.death > 0 ? 'high-risk' : ''}">${fmt(l1Data.death)}</td>
                                        <td class="num-col">${fmt(l1Data.injury)}</td>
                                        <td class="num-col">${fmt(l1Data.malfunc)}</td>
                                        <td class="num-col">${fmt(l1Data.total)}</td>
                                    </tr>
                                `);
                            });
                        }
                    });
                }
            });

            tbody.innerHTML = htmlLines.join('');
            updateHeaderSortIcons();
        }

        // 行点击交互
        function handleL3Click(l3Key) {
            if (expandedL3.has(l3Key)) {
                expandedL3.delete(l3Key);
            } else {
                expandedL3.add(l3Key);
            }
            renderTable();
        }

        function handleL2Click(event, l3Key, l2Key) {
            event.stopPropagation();
            const compoundKey = l3Key + '||' + l2Key;
            if (expandedL2.has(compoundKey)) {
                expandedL2.delete(compoundKey);
            } else {
                expandedL2.add(compoundKey);
            }
            renderTable();
        }

        // 排序交互
        function changeSort(field) {
            if (sortField === field) {
                sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
            } else {
                sortField = field;
                sortOrder = 'desc'; // 切换新字段时默认降序
            }
            renderTable();
        }

        function updateHeaderSortIcons() {
            const fields = ['name', 'pairs', 'death', 'injury', 'malfunc', 'total'];
            fields.forEach(f => {
                const th = document.getElementById('th-' + f);
                if (!th) return;
                const icon = th.querySelector('.sort-icon');
                if (sortField === f) {
                    th.classList.add('sorted-active');
                    icon.innerHTML = sortOrder === 'asc' ? ' ▲' : ' ▼';
                } else {
                    th.classList.remove('sorted-active');
                    icon.innerHTML = ' ↕';
                }
            });
        }

        // 快捷折叠/展开
        function expandAll() {
            expandedL3.clear();
            expandedL2.clear();
            Object.keys(treeData).forEach(l3Key => {
                expandedL3.add(l3Key);
                Object.keys(treeData[l3Key].children).forEach(l2Key => {
                    expandedL2.add(l3Key + '||' + l2Key);
                });
            });
            renderTable();
        }

        function collapseAll() {
            expandedL3.clear();
            expandedL2.clear();
            renderTable();
        }

        // 搜索处理
        function handleSearch() {
            searchQuery = document.getElementById('searchInput').value.trim();
            renderTable();
        }

        // 页面入口初始化
        renderTable();
    </script>
</body>
</html>
"""

    report_html_path = r"e:\pythonProjects\MAUDE\reports\maude_global_hierarchy_analysis.html"
    
    # 替换占位符并覆写 HTML 文件
    final_html = html_template.replace("__TREE_DATA_JSON__", tree_json)
    
    with open(report_html_path, mode='w', encoding='utf-8') as f:
        f.write(final_html)
        
    print(f">>> [SUCCESS] 折叠树形层级分析 HTML 页面成功覆写生成至: {report_html_path}")

if __name__ == '__main__':
    build_collapsible_html()
