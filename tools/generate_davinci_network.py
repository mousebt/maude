import os
import pymysql
import networkx as nx
from pyvis.network import Network
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(BASE_DIR, ".env")
load_dotenv(env_path)

DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASSWORD', '123456')
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_NAME = 'davinci_death_db'

def clean_brand_name(brand):
    if not brand:
        return "未知机型"
    brand_upper = brand.upper()
    if "XI" in brand_upper:
        return "DaVinci Xi (第四代)"
    elif "SI" in brand_upper:
        return "DaVinci Si (第三代)"
    elif "SP" in brand_upper:
        return "DaVinci SP (单通道)"
    elif " S " in brand_upper or brand_upper.endswith(" S"):
        return "DaVinci S (第二代)"
    elif "STANDARD" in brand_upper or "CLASSIC" in brand_upper:
        return "DaVinci Standard (第一代)"
    else:
        return "其他/通用达芬奇"

def clean_component(comp):
    if not comp or comp == "未知" or comp == "None":
        return None
    comp_upper = comp.upper()
    if "MARYLAND" in comp_upper:
        return "Maryland Grasping (双极电凝钳)"
    elif "SHEARS" in comp_upper or "SCISSORS" in comp_upper:
        return "Hot Shears (单极弯剪)"
    elif "STAPLER" in comp_upper:
        return "SureForm Stapler (吻合器)"
    elif "SEALER" in comp_upper:
        return "Vessel Sealer (血管闭合器)"
    elif "FORCEPS" in comp_upper:
        return "Cadiere Forceps (持针抓钳)"
    elif "NEEDLE" in comp_upper:
        return "Veress Needle (气腹针)"
    elif "CANNULA" in comp_upper:
        return "8mm Cannula (穿刺套管)"
    elif "CLIP" in comp_upper:
        return "Hemo-clip (血管夹)"
    return comp

def fetch_data():
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        database=DB_NAME
    )
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    sql = """
        SELECT 
            k.MDR_REPORT_KEY,
            k.CLASSIFICATION,
            k.HAZARD_CATEGORY,
            k.FAULT_COMPONENT,
            k.CLINICAL_COMPLICATION,
            k.SURGEON_DECISION,
            k.FACTUAL_SUMMARY,
            k.CLINICAL_SUMMARY,
            (SELECT BRAND_NAME FROM device d WHERE d.MDR_REPORT_KEY = k.MDR_REPORT_KEY LIMIT 1) as BRAND_NAME
        FROM foi_text_knowledge k
    """
    cursor.execute(sql)
    rows = cursor.fetchall()
    conn.close()
    return rows

def build_network():
    print(">>> 正在从数据库拉取清洗后数据...")
    rows = fetch_data()
    print(f"    成功拉取 {len(rows)} 条致死病例。")
    
    # 建立 NetworkX 有向图
    G = nx.DiGraph()
    
    # 存储各个节点和边的权重与 hover 提示
    # 边数据结构: (node1, node2) -> { "weight": count, "cases": [summaries] }
    edge_data = {}
    
    # 辅助函数: 安全地添加/增加边权重与摘要信息
    def add_edge_data(u, v, summary):
        if not u or not v:
            return
        edge_key = (u, v)
        if edge_key not in edge_data:
            edge_data[edge_key] = {"weight": 0, "cases": []}
        edge_data[edge_key]["weight"] += 1
        if summary and len(edge_data[edge_key]["cases"]) < 3: # 每个连接最多保留 3 个典型病例
            edge_data[edge_key]["cases"].append(summary)

    node_types = {} # 记录节点类型，用于着色

    for r in rows:
        brand = clean_brand_name(r["BRAND_NAME"])
        cls = r["CLASSIFICATION"]
        
        # 节点类型映射：
        # brand -> "brand" (机型)
        # cls_label -> "class" (死亡判定大类)
        # haz / comp -> "category" (物理故障/临床并发症)
        # comp -> "complication" (并发症)
        # component -> "component" (故障附件)
        # conversion -> "conversion" (中转开放)
        
        node_types[brand] = "brand"
        
        if cls == "Shocking":
            cls_label = "机器故障致险/致死"
            node_types[cls_label] = "class"
            add_edge_data(brand, cls_label, r["FACTUAL_SUMMARY"])
            
            haz = r["HAZARD_CATEGORY"]
            if haz:
                node_types[haz] = "hazard"
                add_edge_data(cls_label, haz, r["FACTUAL_SUMMARY"])
                
                comp = clean_component(r["FAULT_COMPONENT"])
                if comp:
                    node_types[comp] = "component"
                    add_edge_data(haz, comp, r["FACTUAL_SUMMARY"])
                    
        elif cls == "Normal":
            cls_label = "手术常规并发症致死"
            node_types[cls_label] = "class"
            add_edge_data(brand, cls_label, r["CLINICAL_SUMMARY"])
            
            complication = r["CLINICAL_COMPLICATION"]
            if complication:
                node_types[complication] = "complication"
                add_edge_data(cls_label, complication, r["CLINICAL_SUMMARY"])
                
                # 如果有中转决策
                decision = r["SURGEON_DECISION"]
                if decision == "YES":
                    conv_node = "紧急中转开腹/开胸"
                    node_types[conv_node] = "conversion"
                    add_edge_data(complication, conv_node, r["CLINICAL_SUMMARY"])
                    
        elif cls == "Structural_Issue":
            cls_label = "数据严重受损(脱敏)"
            node_types[cls_label] = "class"
            add_edge_data(brand, cls_label, "FDA 商业脱敏/隐私屏蔽导致细节缺失")

    # 构建 Pyvis 交互式网络
    net = Network(height="800px", width="100%", bgcolor="#0f172a", font_color="#e2e8f0", heading="达芬奇手术机器人致死故障因果关联网络图谱", directed=True)
    
    # 颜色面板定义 (Sleek Dark Mode Theme)
    colors = {
        "brand": "#3b82f6",       # 炫酷蓝 (机型)
        "class": "#a855f7",       # 霓虹紫 (分类)
        "hazard": "#f43f5e",      # 玫瑰红 (机器故障隐患)
        "component": "#eab308",   # 琥珀黄 (故障耗材)
        "complication": "#10b981",# 翡翠绿 (临床并发症)
        "conversion": "#f97316"   # 珊瑚橙 (紧急中转决策)
    }
    
    # 尺寸面板定义
    sizes = {
        "brand": 35,
        "class": 30,
        "hazard": 25,
        "complication": 25,
        "component": 20,
        "conversion": 22
    }

    # 1. 批量向图中添加节点
    # 统计各个节点的连接数作为大小的微调参考
    node_degrees = {}
    for (u, v) in edge_data.keys():
        node_degrees[u] = node_degrees.get(u, 0) + 1
        node_degrees[v] = node_degrees.get(v, 0) + 1

    for node, ntype in node_types.items():
        color = colors.get(ntype, "#94a3b8")
        base_size = sizes.get(ntype, 15)
        # 根据度数微调大小
        deg = node_degrees.get(node, 1)
        node_size = base_size + min(deg * 1.5, 15)
        
        # 节点悬停提示
        node_title = f"<b>节点名称:</b> {node}<br><b>节点类型:</b> {ntype.upper()}<br><b>关联连接数:</b> {deg}"
        
        net.add_node(
            node, 
            label=node, 
            title=node_title, 
            color=color, 
            size=node_size, 
            borderWidth=2,
            borderWidthSelected=4,
            font={"size": 13, "face": "Helvetica", "color": "#f1f5f9"}
        )

    # 2. 批量向图中添加边
    for (u, v), data in edge_data.items():
        w = data["weight"]
        # 组装边 hover 显示的典型病例详情 HTML
        cases_html = "<br>".join([f"• {c}" for c in data["cases"]])
        edge_title = f"<b>联结:</b> {u} ➔ {v}<br><b>共现发生频次:</b> {w} 例<br><b>典型案例背景:</b><br>{cases_html}"
        
        net.add_edge(
            u, 
            v, 
            value=w, 
            title=edge_title, 
            arrowStrikethrough=False, 
            color="#475569",
            hoverWidth=2,
            selectionWidth=3
        )

    # 3. 配置弹簧物理力学引擎，使布局流畅并具备流畅的交互弹性
    net.set_options("""
    var options = {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -60,
          "centralGravity": 0.015,
          "springLength": 120,
          "springConstant": 0.08
        },
        "maxVelocity": 50,
        "solver": "forceAtlas2Based",
        "timestep": 0.35,
        "stabilization": { "iterations": 150 }
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 200,
        "navigationButtons": true
      }
    }
    """)
    
    # 4. 生成 HTML
    output_html = os.path.join(BASE_DIR, "reports", "davinci_death_dataset", "davinci_death_network.html")
    net.write_html(output_html)
    print(f"\n==========================================================")
    print(f">>> [成功] 达芬奇死亡因果网络图谱 HTML 已生成落盘！")
    print(f"    - 保存路径: {output_html}")
    print(f"==========================================================\n")

if __name__ == '__main__':
    build_network()
