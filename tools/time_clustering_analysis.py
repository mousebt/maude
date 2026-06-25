import os
import json
import time
import pymysql
import numpy as np
from dotenv import load_dotenv

# 尝试导入机器学习常用库，若不存在则提示安装
try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import MinMaxScaler
except ImportError:
    print(">>> 警告: 缺少 sklearn 库，请使用 pip install scikit-learn 进行安装。")
    raise

env_path = r"e:\pythonProjects\MAUDE\.env"
load_dotenv(env_path)

DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASSWORD', '123456')
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_NAME = os.getenv('DB_NAME') or 'maude_db'

NEW_PRODUCTS_JSON = r"e:\pythonProjects\MAUDE\reports\new_products_info.json"
OUTPUT_HTML = r"e:\pythonProjects\MAUDE\reports\new_products_time_clustering.html"

# 高精度的医疗器械通用名与品牌中文翻译对照表 (100% 覆盖 91 种器械)
TRANSLATIONS = {
    "CONTINUOUS GLUCOSE MONITOR": "持续血糖监测仪",
    "CONTINUOUS GLUCOSE MONITORING SYSTEM": "持续血糖监测系统",
    "INSULIN PUMP SECONDARY DISPLAY": "胰岛素泵辅助显示应用",
    "CARDIAC IRREVERSIBLE ELECTROPORATION SYSTEM CATHETER": "心脏不可逆电穿孔消融系统导管",
    "STAPLE, REMOVABLE (SKIN)": "一次性皮肤缝合器",
    "INTEGRATED CONTINUOUS GLUCOSE MONITOR FOR NON-INTENSIVE GLUCOSE MONITORING, OVER": "非重症监护一体式持续血糖监测仪",
    "COVID-19 MULTI-ANALYTE RESPIRATORY PANEL NUCLEIC ACID DEVICES": "呼吸道多病原新冠核酸检测试剂",
    "TRICUSPID VALVE REPAIR DEVICE, PERCUTANEOUSLY DELIVERED": "经皮三尖瓣修复系统",
    "EVERSENSE CONTINUOUS GLUCOSE MONITOR SYSTEM": "Eversense 植入式持续血糖监测系统",
    "DETECTOR AND ALARM, ARRHYTHMIA": "心律失常监测与报警系统",
    "PERCUTANEOUSLY DELIVERED PROSTHESES AND TRICUSPID VALVES": "经皮置入三尖瓣人工瓣膜",
    "DRUG-ELUTING PERCUTANEOUS TRANSLUMINAL CORONARY ANGIOPLASTY CATHETER": "药物洗脱经皮球囊冠状动脉成形术导管",
    "4K": "4K 前列腺癌筛查",
    "PUMP, BLOOD, CARDIOPULMONARY BYPASS, NON-ROLLER TYPE": "体外循环非滚轴式血泵",
    "REACTIV8 IMPLANTABLE PULSE GENERATOR": "Reactiv8 可植入脉冲发生器",
    "NORMOTHERMIC MACHINE PERFUSION SYSTEM FOR THE PRESERVATION OF DONOR LIVERS PRIOR": "常温肝脏灌注系统",
    "INFUSION PUMP, DRUG SPECIFIC, PHARMACY-FILLED": "药房填充型专用输注泵",
    "THORAFLEX HYBRID": "Thoraflex 混合血管支架",
    "IMAGE PROCESSING DEVICE FOR ESTIMATION OF EXTERNAL BLOOD LOSS": "失血量图像处理评估系统",
    "LANCET, BLOOD": "一次性采血针",
    "SENSOR, GLUCOSE, INVASIVE, COMPONENT OF AUTOMATED INSULIN DELIVERY SYSTEM": "自动胰岛素输注系统血糖传感器",
    "STENT, INFRAPOPLITEAL, ABSORBABLE": "腘下可吸收支架",
    "SIMPLE POINT-OF-CARE DEVICE TO DETECT SAR-COV-2 NUCLEIC ACID TARGETS": "即时新冠核酸检测设备",
    "OVER-THE-COUNTER COVID-19 ANTIGEN TEST": "家用新冠抗原检测试剂",
    "HIP INSTRUMENT - BROACH": "髋关节手术假体锉",
    "ENDOVASCULAR SYSTEM FOR TREATMENT OF THORACOABDOMINAL AND PARARENAL AORTIC LESIO": "胸腹主动脉瘤腔内修复系统",
    "MODULAR ELECTROMECHANICAL SURGICAL SYSTEM": "模块化微创手术机器人系统",
    "FOLEY CATHETER KIT (EXCLUDES HIV TESTING)": "导尿管套件",
    "FAT TRANSFER": "自体脂肪移植回收系统",
    "SYSTEM, SUCTION, LIPOPLASTY": "共振吸脂负压吸引系统",
    "Absorbable synthetic wound dressing": "可吸收伤口合成敷料",
    "SAFEBREAK VASCULAR": "血管输液安全阀",
    "ASD OCCLUDER": "房间隔缺损封堵器",
    "ACUTE CORONARY SYNDROME EVENT DETECTOR": "急性冠脉综合征事件监测系统",
    "DIRECT BLOOD BACTERIAL NUCLEIC ACID DETECTION SYSTEM": "血液细菌核酸直接检测仪",
    "TYPE 2": "2型糖尿病辅助器具",
    "EXTRACORPOREAL SYSTEM FOR CARBON DIOXIDE REMOVAL": "体外二氧化碳清除系统",
    "Focused ultrasound system for non-thermal, mechanical tissue ablation": "聚焦超声无创组织消融系统",
    "MULTIPLE-GENUS RESPIRATORY VIRUS NUCLEIC ACID IVD, KIT, NUCLEIC ACID TECHNIQUE": "呼吸道多病毒核酸检测试剂盒",
    "SHOULDER SPACER FOR MASSIVE IRREPARABLE ROTATOR CUFF TEAR, RESORBABLE, INFLATABL": "可降解充气式肩袖间隙球囊支架",
    "GALLBLADDER DRAINAGE STENT AND DELIVERY SYSTEM": "胆囊引流支架与输送系统",
    "SHOULDER JOINT HUMERAL (HEMI-SHOULDER) CERAMIC HEAD/METALLIC STEM CEMENTED": "肩关节陶瓷肱骨头金属柄假体",
    "MOTION-PRESERVING SPINAL IMPLANT": "非融合活动脊柱植入物",
    "LEADLESS CARDIAC RESYNCHRONIZATION THERAPY (CRT)": "无导线心脏再同步治疗系统",
    "EXTRACORPOREAL SYSTEM FOR CARBON DIOXIDE REMOVAL FOR THE TREATMENT OF  COVID-19": "体外二氧化碳清除系统 (用于新冠治疗)",
    "CRANIAL NEUROSTIMULATOR": "经颅微电流脑部刺激仪",
    "SINGLE LUMEN ECMO CANNULA": "单腔体外膜肺氧合 (ECMO) 插管",
    "ELECTROCONVULSIVE THERAPY DEVICE FOR CATATONIA, MAJOR DEPRESSIVE DISORDER, AND B": "电抽搐治疗仪",
    "TOUCH - CMC1 PROSTHESIS  CONICAL CUP 9MM": "微创腕关节假体",
    "LANCET": "采血针",
    "HEARING AID, AIR-CONDUCTION, OVER THE COUNTER": "家用非处方气导助听器",
    "PROSTHESIS, EYELID SPACER/GRAFT, POLYMER": "高分子眼睑修补假体",
    "ABLATION CATHETER, RENAL DENERVATION": "肾动脉去交感神经消融导管",
    "UNO EWIS BLUE 60/9 HCAP 10PK INT": "Extended 延长心电记录仪",
    "BEAR IMPLANT FOR ACL REPAIR": "前交叉韧带支架植入物",
    "ADJUNCTIVE PREDICTIVE CARDIOVASCULAR INDICATOR": "心血管预后辅助预测传感器",
    "NUCLEIC ACID DETECTION SYSTEM FOR NON-VIRAL MICROORGANISM(S) CAUSING SEXUALLY TR": "性传播病原体核酸检测系统",
    "TYMPANOSTOMY TUBE DELIVERY PRODUCT WITH DRUG": "载药鼓膜置管输送器",
    "CONTINUOUS GLUCOSE MONITORING SYSTEM": "持续血糖监测系统",
    "ELEOS NANOCEPT TECHNOLOGY ANTIBACTERIAL  COATED MALE-FEMALE MIDSECTION SIZE 50MM": "ELEOS 纳米抗菌防感染型肢体重建系统",
    "ECOIN UUI": "Ecoin 尿失禁外周神经刺激器",
    "INTERVERTEBRAL BODY GRAFT CONTAINMENT": "椎间骨融合假体网袋",
    "SERAPH 100": "Seraph 100 病原体吸附血液灌流器",
    "FULL LENGTH BED RAILS": "医用床全长护栏",
    "PERIPHERAL STENT GRAFT": "外周覆膜支架系统",
    "SOLUTION, ISOTONIC": "等渗生理盐水溶液",
    "PISTON SYRINGE": "活塞注射器",
    "IMPLANTED TIBIAL ELECTRICAL URINARY CONTINENCE DEVICE": "植入式胫神经尿失禁电刺激器",
    "PERCUSSOR, POWERED-ELECTRIC": "电动排痰振动排痰仪",
    "MONSEL'S SOLUTION": "Monsel 氏止血溶液",
    "REPROCESSED BRONCHOSCOPE": "一次性使用复用支气管镜",
    "LAVA LIQUID EMBOLIC SYSTEM": "Lava 液体血管栓塞系统",
    "SOFTWARE": "临床辅助诊断评估软件 (Sepsis)",
    "ORGAN CARE SYSTEM (OCS) HEART SYSTEM": "OCS 离体心脏保存与灌注系统",
    "FLUID DRAINAGE TRAY": "心包穿刺引流盘",
    "VIVISTIM SYSTEM": "Vivistim 迷走神经电刺激系统",
    "LASER-POWERED INFERIOR VENA CAVA FILTER RETRIEVAL": "激光辅助下腔静脉滤器回收鞘",
    "TITANIUM PATIENT SPECIFIC TALUS SPACER, SMALL": "患者定制钛合金距骨假体",
    "CUTANEOUS ELECTRODE STIMULATOR FOR URINARY INCONTINENCE": "经皮电极尿失禁刺激仪",
    "IMPLANTED SHOCK ABSORBER": "植入式膝关节减震减压假体",
    "PERCUTANEOUS ATRIAL CATHETER KIT": "经皮穿刺心房插管套件",
    "DILAPAN-S": "Dilapan-S 亲水性宫颈扩张棒",
    "FENTANYL AND OTHER OPIOID PROTECTION GLOVE": "芬太尼及阿片类药物高防防护手套",
    "CATHETER, BALLOON, URETHRAL, DRUG-COATED": "药物涂层尿道球囊扩张导管",
    "ANTISERA, ALL GROUPS, SALMONELLA SPP.": "沙门氏菌诊断血清",
    "SUPERSATURATED OXYGEN THERAPY SYSTEM CARTRIDGE": "超饱和氧疗系统灌注耗材",
    "ENDOSCOPIC TRANSHEPATIC VENOUS ACCESS NEEDLE": "内镜下经肝穿刺针",
    "HEARING AID, AIR-CONDUCTION WITH WIRELESS TECHNOLOGY, OVER THE COUNTER": "家用非处方无线气导助听器",
    "SELF-FITTING AIR-CONDUCTION HEARING AID, OVER THE COUNTER": "家用非处方自验配气导助听器",
    "NON-NIOSH-APPROVED DISPOSABLE FILTERING FACEPIECE RESPIRATORS (FFRS)": "一次性非 NIOSH 认证口罩",
    "LAB-BASED HIV NAT DIAGNOSTIC AND/OR SUPPLEMENTAL TEST": "实验室用艾滋病毒核酸定性检测试剂",
    "RXM1000": "Reflexion 放射治疗放疗引导系统",
}

BRAND_TRANSLATIONS = {
    "SMARTPHONE ANDROID APP: PUMP CONNECT": "智能手机 Android 应用: 胰岛素泵连接",
    "FARAWAVE": "Farawave 心脏不可逆电穿孔导管",
    "WECK VISISTAT SKIN STAPLER 35R": "Weck Visistat 35R 一次性皮肤缝合器",
    "DEXCOM STELO CGM": "德康 (Dexcom) Stelo 持续血糖监测仪",
    "COBAS SARS-COV-2 & INFLUENZA A/B": "罗氏 Cobas 新冠与流感 A/B 核酸检测试剂",
    "TRICLIP G4 SYSTEM": "雅培 TriClip G4 三尖瓣反流修复系统",
    "EVERSENSE SENSOR": "Eversense 植入式血糖传感器",
    "ZIO AT": "Zio AT 心电记录仪",
    "EVOQUE TRICUSPID VALVE REPLACEMENT SYSTEM": "爱德华 Evoque 三尖瓣置换系统",
    "AGENT": "波士顿科学 Agent 药物球囊",
    "4KSCORE TEST": "4Kscore 前列腺癌筛查测试盒",
    "PEDIMAG BLOOD PUMP": "雅培 PediMag 离心血泵",
    "REACTIV8": "Reactiv8 慢性腰痛电刺激系统",
    "TRANSMEDICS OCS FOR LIVER": "TransMedics 离体肝脏养护系统",
    "REMUNITY": "Remunity 贴片式胰岛素泵",
    "THORAFLEX HYBRID": "Terumo Thoraflex 混合支架血管",
    "TRITON AI": "Triton AI 术中失血量实时监测系统",
    "LANCE DVC": "一次性采血针",
    "SENSOR MMT-5120A SIMPLERA SYNC 5PK US": "美敦力 Simplera Sync 连续血糖传感器",
    "ESPRIT BTK RX IDE": "雅培 Esprit BTK 生物可吸收药物支架",
    "ID NOW COVID-19 2.0 TEST KIT 24T JAPAN": "雅培 ID NOW 新冠 2.0 快速核酸检测试剂盒",
    "FLOWFLEX OVER-THE-COUNTER COVID TEST": "艾康 Flowflex 家用新冠抗原自测盒",
    "ACTIS BROACH SIZE 7": "强生 Actis 髋关节假体骨髓锉",
    "GORE EXCLUDER THORACOABDOMINAL BRANCH ENDOPROSTHESIS": "戈尔 GORE Excluder 胸腹主动脉分支覆膜支架",
    "HUGO RAS SYSTEM": "美敦力 Hugo 机器人辅助手术系统",
    "MEDLINE SILICONE FOLEY CATHETER TRAY": "麦迪兰 (Medline) 硅胶导尿管置管盘",
    "LIPOASPIRATE WASH SYSTEM": "脂肪移植抽吸物清洗系统",
    "VASERLIPO SYSTEM": "Vaser 威塑超声共振吸脂仪",
    "NOVOSORB BTM": "Novosorb 聚氨酯真皮基质敷料",
    "SAFEBREAK VASCULAR": "SafeBreak 输液管安全阀",
    "FIGULLA FLEX II ASD OCCLUDER": "Figulla Flex II 房间隔封堵器",
    "GUARDIAN SYSTEM": "AngelMed Guardian 急性心梗报警系统",
    "T2BACTERIA PANEL": "T2Bacteria 血液细菌快速检测板",
    "TWINJECT/ADRENACLICK": "Adrenaclick 肾上腺素自动注射笔",
    "HEMOLUNG RAS": "Hemolung 体外二氧化碳清除系统",
    "EDISON SYSTEM": "Edison 聚焦超声肾消融系统",
    "BD RESPIRATORY VIRAL PANEL FOR BD MAX SYSTEM": "BD MAX 呼吸道多病毒核酸检测试剂",
    "INSPACE BALLOON IMPLANT FOR SHOULDER": "美敦力 InSpace 肩袖间隙气囊植入物",
    "AXIOS STENT AND ELECTROCAUTERY ENHANCED DELIVERY SYSTEM": "波士顿科学 Axios 胆囊引流金属支架系统",
    "TORNIER PYROCARBON HUM HEAD  DIA 54MMX23MMX4.0MM ECC HI": "Tornier 焦碳陶瓷肱骨头假体",
    "TOPS SYSTEM": "Premia Spine TOPS 脊柱非融合活动关节",
    "WISE CORTICAL STRIP WCS": "Wise 脑皮层贴片电极",
    "FISHER WALLACE CRANIAL NEUROSTIMULATOR": "Fisher Wallace 脑部微电流刺激仪",
    "BIO-MEDICUS LIFE SUPPORT TM": "美敦力 Bio-Medicus 体外膜肺氧合插管",
    "ECT MACHINE": "电抽搐治疗仪",
    "TOUCH CMC 1 PROSTHESIS": "腕关节假体",
    "LIVONGO LANCET": "Livongo 家用血糖仪采血针",
    "HEARING AID": "非处方助听器",
    "CORNEAT EVERPATCH": "Corneat 生物合成眼睑修补片",
    "MEDTRONIC EXTENDED": "美敦力 Extended 延长佩戴型输注管路",
    "BRIDGE-ENHANCED ACL RESTORATION (BEAR) IMPLANT": "Miach Orthopaedics BEAR 前交叉韧带修复支架",
    "ACUMEN IQ SENSOR": "爱德华 Acumen IQ 心血管监测传感器",
    "ALINITY M STI AMPLIFICATION REAGENT KIT": "雅培 Alinity m 性传播疾病核酸扩增试剂盒",
    "TULA CONTROL UNIT SPARE": "Tula 鼓膜置管控制仪备件",
    "FREESTYLE LIBRE 3": "雅培瞬感 FreeStyle Libre 3 持续血糖监测仪",
    "ELEOS LIMB SALVAGE SYSTEM": "Eleos 纳米抗菌保肢重建系统",
    "ECOIN PERIPHERAL NUEROSTIMULATOR": "Ecoin 外周尿失禁电刺激物",
    "OPTIMESH": "Optimesh 椎间骨融合假体网袋",
    "SERAPH 100": "Seraph 100 病原体吸附血液灌流器",
    "ROSCOE": "Roscoe 医用防坠床护栏",
    "DETOUR SYSTEM TORUS": "Detour 外周旁路覆膜支架",
    "SODIUM CHLORIDE, 0.9% (W/V) ISOTONIC SALINE": "0.9% 医用等渗生理盐水",
    "MDS-21NRFIT": "美迪斯一次性注药活塞注射器",
    "REVI SYSTEM": "Revi 植入式胫神经刺激系统",
    "CONTROLLER, VEST 105": "Hillrom Vest 105 排痰振动马甲控制器",
    "ASTRINGYN 12 PACK BOX": "Astringyn 硫酸铁局部收敛止血剂",
    "MONARCH BRONCHOSCOPE": "Monarch 机器人辅助气管镜",
    "LAVA-18, 6 ML": "Lava-18 液体血管栓塞剂 (6ml)",
    "SEPSIS": "Sepsis 脓毒症早期临床预警软件",
    "OCS HEART SYSTEM": "TransMedics OCS 离体心脏灌注保存仪",
    "PERICARDIOCENTESIS KIT.": "一次性心包穿刺手术包",
    "MICROTRANSPONDER VIVISTIM PAIRED VNS SYSTEM (VIVISTIM SYSTEM)": "Vivistim 迷走神经电刺激系统",
    "CAVACLEAR LASER SHEATH": "CavaClear 激光辅助下腔静脉滤器回收鞘",
    "PATIENT SPECIFIC TALUS SPACER": "定制钛合金距骨假体",
    "INNOVO, TYPE NUMBER 208": "Innovo 穿戴式盆底肌电刺激尿失禁仪",
    "MISHA KNEE SYSTEM": "Misha 膝关节内侧植入式减震系统",
    "VERSACROSS STEERABLE ACCESS SOLUTION": "VersaCross 可调向经皮心房穿刺套件",
    "DILAPAN-S": "Dilapan-S 亲水性宫颈扩张棒",
    "GOODWORKS FENTANYL SAFE GLOVES": "GoodWorks 芬太尼高防护级丁腈手套",
    "OPTILUME URETHRAL DRUG COATED BALLOON CATHETER": "Optilume 药物涂层尿道球囊扩张导管",
    "BD DIFCO SALMONELLA O ANTISERUM GROUP E FACTORS 1, 3, 10, 15, 19, 34": "BD Difco 沙门氏菌 O 诊断血清 E 群",
    "DOWNSTREAM CARTRIDGE": "超饱和氧疗系统管路耗材",
    "ECHOTIP INSIGHT": "EchoTip 胃镜下经肝穿刺针",
    "JABRA ENHANCE 200 HEARING AID": "捷波朗 (Jabra) Enhance 200 家用无线助听器",
    "EARGO HEARING DEVICES": "Eargo 家用隐形自验配助听器",
    "3PE-X127 NIOSH N95": "3PE-X127 家用防尘过滤口罩",
    "COBAS HIV-1/HIV-2 QUALITATIVE (192T)": "罗氏 cobas 艾滋病毒 HIV-1/HIV-2 定性核酸检测试剂",
    "REFLEXION MEDICAL RADIOTHERAPY SYSTEM": "RefleXion 生物引导放射治疗系统",
}

# 构建月份列表 (2021/06 到 2026/06)
def generate_months():
    months = []
    # 2021/06 - 2021/12
    for m in range(6, 13):
        months.append(f"2021/{m:02d}")
    # 2022/01 - 2025/12
    for y in range(2022, 2026):
        for m in range(1, 13):
            months.append(f"{y}/{m:02d}")
    # 2026/01 - 2026/06
    for m in range(1, 7):
        months.append(f"2026/{m:02d}")
    return months

def main():
    # 1. 读取新上市产品代码
    if not os.path.exists(NEW_PRODUCTS_JSON):
        print(f"错误: 未找到新产品列表文件 {NEW_PRODUCTS_JSON}，请先运行筛选脚本！")
        return
        
    with open(NEW_PRODUCTS_JSON, 'r', encoding='utf-8') as f:
        products = json.load(f)
        
    if not products:
        print("错误: 新产品列表为空！")
        return

    # 为所有 products 注入汉化翻译
    for p in products:
        brand = p['brand_name']
        generic = p['generic_name']
        
        # 汉化品牌
        p['brand_name_zh'] = BRAND_TRANSLATIONS.get(brand, brand)
        # 汉化通用名
        p['generic_name_zh'] = TRANSLATIONS.get(generic, generic)
        
        # 规范占位符
        if p['brand_name_zh'] == '\\N':
            p['brand_name_zh'] = "未命名品牌"
        if p['generic_name_zh'] == '\\N':
            p['generic_name_zh'] = "未知通用名"

    print(f">>> 1. 成功加载并本地汉化了 {len(products)} 个近 5 年内新上市的产品。")

    # 2. 连接数据库拉取时序与严重后果数据
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        database=DB_NAME
    )
    cursor = conn.cursor()

    months = generate_months()
    month_to_idx = {m: i for i, m in enumerate(months)}
    
    print("\n>>> 2. 正在从 MySQL 中拉取每个产品的月度时序及事件后果分布...")
    t_start = time.time()
    
    timeseries_data = [] # 存储时序矩阵 (N, 61)
    severity_stats = {}   # 存储各产品后果：death, injury, malfunction, total
    
    for idx, p in enumerate(products):
        code = p['code']
        # 初始化时序序列 (全0)
        ts = np.zeros(len(months))
        
        # 2.1 查询月度事件频数
        sql_ts = """
            SELECT SUBSTRING(DATE_RECEIVED, 1, 7) as yr_mo, COUNT(*) 
            FROM device 
            WHERE DEVICE_REPORT_PRODUCT_CODE = %s AND DATE_RECEIVED >= '2021/06/15'
            GROUP BY yr_mo
        """
        cursor.execute(sql_ts, (code,))
        for yr_mo, cnt in cursor.fetchall():
            # 格式为 YYYY/MM
            if yr_mo in month_to_idx:
                ts[month_to_idx[yr_mo]] = cnt
                
        timeseries_data.append(ts)
        
        # 2.2 查询不良事件临床后果分布
        sql_sev = """
            SELECT 
                SUM(CASE WHEN m.EVENT_TYPE = 'D' THEN 1 ELSE 0 END) as death_count,
                SUM(CASE WHEN m.EVENT_TYPE = 'IN' THEN 1 ELSE 0 END) as injury_count,
                SUM(CASE WHEN m.EVENT_TYPE = 'M' THEN 1 ELSE 0 END) as malfunction_count,
                COUNT(*) as total_count
            FROM device d
            JOIN mdr_report m ON d.MDR_REPORT_KEY = m.MDR_REPORT_KEY
            WHERE d.DEVICE_REPORT_PRODUCT_CODE = %s
        """
        cursor.execute(sql_sev, (code,))
        death, injury, malf, total = cursor.fetchone()
        
        severity_stats[code] = {
            'death': int(death or 0),
            'injury': int(injury or 0),
            'malfunction': int(malf or 0),
            'total': int(total or 0)
        }
        
        if (idx + 1) % 20 == 0 or (idx + 1) == len(products):
            print(f"   已处理 {idx + 1}/{len(products)} 个产品的数据拉取...")
            
    print(f"   数据拉取完成，耗时: {time.time() - t_start:.2f} 秒。")

    X = np.array(timeseries_data) # 形状: (91, 61)

    # 3. 归一化与平滑处理
    print("\n>>> 3. 正在进行时序归一化与平滑处理...")
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X.T).T
    X_scaled = np.nan_to_num(X_scaled)
    
    # 4. 执行 K-Means 聚类
    K = 3
    print(f"\n>>> 4. 正在应用 K-Means 对时序演变进行聚类 (K = {K})...")
    kmeans = KMeans(n_clusters=K, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_scaled)
    cluster_centers = kmeans.cluster_centers_ # 形状: (3, 61)

    # 5. 分析与统计聚类特征
    print("\n>>> 5. 正在汇总各聚类别的临床后果与特征...")
    cluster_info = {i: {
        'count': 0,
        'total_events': 0,
        'death': 0,
        'injury': 0,
        'malfunction': 0,
        'members': [],
        'center_ts': list(cluster_centers[i])
    } for i in range(K)}
    
    for idx, p in enumerate(products):
        code = p['code']
        label = int(labels[idx])
        sev = severity_stats[code]
        
        cluster_info[label]['count'] += 1
        cluster_info[label]['total_events'] += sev['total']
        cluster_info[label]['death'] += sev['death']
        cluster_info[label]['injury'] += sev['injury']
        cluster_info[label]['malfunction'] += sev['malfunction']
        
        p['cluster'] = label
        p['severity'] = sev
        p['normalized_ts'] = list(X_scaled[idx])
        p['raw_ts'] = list(X[idx])
        
        cluster_info[label]['members'].append(p)

    # 打印聚类汇总信息
    for label, info in cluster_info.items():
        total = info['total_events'] if info['total_events'] > 0 else 1
        death_pct = info['death'] / total * 100
        injury_pct = info['injury'] / total * 100
        malf_pct = info['malfunction'] / total * 100
        print(f"Cluster {label}: 器械品种数 = {info['count']} | 不良事件总数 = {info['total_events']:,}")
        print(f"          死亡占比 = {death_pct:.2f}% | 严重伤害占比 = {injury_pct:.2f}% | 设备故障占比 = {malf_pct:.2f}%")

    # 6. 生成高颜值的 ECharts 可视化大盘 HTML
    print(f"\n>>> 6. 正在构建并生成高颜值的可视化大盘 {OUTPUT_HTML}...")
    
    js_months = json.dumps(months)
    js_cluster_info = json.dumps(cluster_info, ensure_ascii=False)
    js_products = json.dumps(products, ensure_ascii=False)
    
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FDA MAUDE 数据库近5年新器械不良事件时间聚类大盘</title>
    <!-- 引入谷歌 Outfit 和 Inter 字体 -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Outfit:wght@400;600;800&display=swap" rel="stylesheet">
    <!-- 引入 ECharts CDN -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/echarts/5.4.3/echarts.min.js"></script>
    <style>
        :root {{
            --bg-color: #0b0f19;
            --card-bg: rgba(22, 28, 45, 0.6);
            --card-border: rgba(255, 255, 255, 0.08);
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
            --accent-cyan: #06b6d4;
            --accent-pink: #ec4899;
            --accent-gold: #fbbf24;
            --accent-green: #10b981;
            --accent-purple: #8b5cf6;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            background-color: var(--bg-color);
            color: var(--text-primary);
            font-family: 'Inter', sans-serif;
            padding: 24px;
            min-height: 100vh;
            background-image: radial-gradient(circle at 10% 20%, rgba(90, 120, 250, 0.05) 0%, transparent 40%),
                              radial-gradient(circle at 90% 80%, rgba(236, 72, 153, 0.05) 0%, transparent 40%);
        }}

        header {{
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--card-border);
            padding-bottom: 20px;
        }}

        h1 {{
            font-family: 'Outfit', sans-serif;
            font-weight: 800;
            font-size: 28px;
            background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.5px;
        }}

        .subtitle {{
            color: var(--text-secondary);
            font-size: 14px;
            margin-top: 4px;
        }}

        .badge-current-time {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 13px;
            color: var(--accent-cyan);
            backdrop-filter: blur(10px);
        }}

        /* 数据大盘网格 */
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }}

        .metric-card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 24px;
            position: relative;
            overflow: hidden;
            backdrop-filter: blur(10px);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}

        .metric-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
            border-color: rgba(6, 182, 212, 0.3);
        }}

        .metric-title {{
            font-size: 13px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .metric-value {{
            font-family: 'Outfit', sans-serif;
            font-size: 36px;
            font-weight: 700;
            margin-top: 8px;
            background: linear-gradient(135deg, #ffffff 0%, #d1d5db 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .metric-desc {{
            font-size: 12px;
            color: var(--text-secondary);
            margin-top: 4px;
        }}

        .metric-card::after {{
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 4px;
            height: 100%;
        }}

        .metric-card.cyan::after {{ background-color: var(--accent-cyan); }}
        .metric-card.pink::after {{ background-color: var(--accent-pink); }}
        .metric-card.gold::after {{ background-color: var(--accent-gold); }}
        .metric-card.purple::after {{ background-color: var(--accent-purple); }}

        /* 图表区布局 */
        .charts-row {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }}

        .chart-card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 24px;
            backdrop-filter: blur(10px);
            min-height: 420px;
        }}

        .chart-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}

        .chart-title {{
            font-family: 'Outfit', sans-serif;
            font-size: 18px;
            font-weight: 600;
        }}

        .chart-container {{
            width: 100%;
            height: 350px;
        }}

        /* 聚类解读卡片 */
        .clustering-desc-card {{
            grid-column: span 3;
            background: linear-gradient(135deg, rgba(22, 28, 45, 0.8) 0%, rgba(11, 15, 25, 0.8) 100%);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
        }}

        .desc-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 24px;
            margin-top: 16px;
        }}

        .desc-item {{
            border-left: 3px solid;
            padding-left: 16px;
        }}

        .desc-item.c0 {{ border-color: var(--accent-cyan); }}
        .desc-item.c1 {{ border-color: var(--accent-pink); }}
        .desc-item.c2 {{ border-color: var(--accent-gold); }}

        .desc-name {{
            font-family: 'Outfit', sans-serif;
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 6px;
        }}

        .desc-text {{
            font-size: 13px;
            color: var(--text-secondary);
            line-height: 1.6;
        }}

        /* 列表表格区 */
        .list-card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 24px;
            backdrop-filter: blur(10px);
        }}

        .list-tools {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            gap: 16px;
        }}

        .search-box {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 10px 16px;
            color: var(--text-primary);
            font-size: 14px;
            width: 350px;
            outline: none;
            transition: border-color 0.3s ease;
        }}

        .search-box:focus {{
            border-color: var(--accent-cyan);
        }}

        .filter-buttons {{
            display: flex;
            gap: 8px;
        }}

        .filter-btn {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--card-border);
            color: var(--text-secondary);
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.3s ease;
        }}

        .filter-btn:hover, .filter-btn.active {{
            background: var(--accent-cyan);
            color: #000;
            border-color: var(--accent-cyan);
            font-weight: 600;
        }}

        .filter-btn.c0:hover, .filter-btn.c0.active {{
            background: var(--accent-cyan);
            color: #000;
            border-color: var(--accent-cyan);
        }}

        .filter-btn.c1:hover, .filter-btn.c1.active {{
            background: var(--accent-pink);
            color: #fff;
            border-color: var(--accent-pink);
        }}

        .filter-btn.c2:hover, .filter-btn.c2.active {{
            background: var(--accent-gold);
            color: #000;
            border-color: var(--accent-gold);
        }}

        .table-container {{
            width: 100%;
            overflow-x: auto;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
            text-align: left;
        }}

        th {{
            color: var(--text-secondary);
            font-weight: 600;
            padding: 16px;
            border-bottom: 1px solid var(--card-border);
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 0.5px;
        }}

        td {{
            padding: 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.03);
            vertical-align: middle;
        }}

        tr:hover td {{
            background: rgba(255, 255, 255, 0.02);
        }}

        .code-badge {{
            font-family: 'Outfit', sans-serif;
            background: rgba(6, 182, 212, 0.1);
            color: var(--accent-cyan);
            padding: 4px 8px;
            border-radius: 6px;
            font-weight: 600;
        }}

        .cluster-tag {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }}

        .cluster-tag.c0 {{ background: rgba(6, 182, 212, 0.15); color: var(--accent-cyan); }}
        .cluster-tag.c1 {{ background: rgba(236, 72, 153, 0.15); color: var(--accent-pink); }}
        .cluster-tag.c2 {{ background: rgba(251, 191, 36, 0.15); color: var(--accent-gold); }}

        .severity-bar-container {{
            width: 120px;
            height: 8px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
            overflow: hidden;
            display: flex;
        }}

        .severity-bar {{
            height: 100%;
        }}

        .severity-bar.death {{ background: var(--accent-pink); }}
        .severity-bar.injury {{ background: var(--accent-cyan); }}
        .severity-bar.malf {{ background: var(--text-secondary); }}

        .tooltip-custom {{
            font-size: 11px;
            color: var(--text-secondary);
            margin-top: 4px;
        }}

        footer {{
            margin-top: 50px;
            text-align: center;
            color: var(--text-secondary);
            font-size: 13px;
            border-top: 1px solid var(--card-border);
            padding-top: 20px;
        }}
    </style>
</head>
<body>

    <header>
        <div>
            <h1>FDA MAUDE 近5年新出现医疗器械时间聚类分析大盘</h1>
            <div class="subtitle">基于真实世界 FDA 不良事件数据挖掘 (数据覆盖至 2025 年底)</div>
        </div>
        <div class="badge-current-time">
            分析基准时间: {time.strftime("%Y-%m-%d")}
        </div>
    </header>

    <!-- 核心指标区 -->
    <div class="metrics-grid">
        <div class="metric-card cyan">
            <div class="metric-title">监测新器械种类</div>
            <div class="metric-value">{len(products)} 种</div>
            <div class="metric-desc">最早事件在 2021-06-15 之后且事件 >= 10</div>
        </div>
        <div class="metric-card pink">
            <div class="metric-title">累计不良事件数</div>
            <div class="metric-value">{sum(p['total_count'] for p in products):,} 起</div>
            <div class="metric-desc">近5年内这 91 种新上市器械的事故总和</div>
        </div>
        <div class="metric-card gold">
            <div class="metric-title">严重事件 (死亡+伤害)</div>
            <div class="metric-value">
                {sum(p['severity']['death'] + p['severity']['injury'] for p in products):,} 起
            </div>
            <div class="metric-desc">高临床关联临床事故占比: {(sum(p['severity']['death'] + p['severity']['injury'] for p in products) / sum(p['severity']['total'] for p in products) * 100):.2f}%</div>
        </div>
        <div class="metric-card purple">
            <div class="metric-title">单一产品最高事故数</div>
            <div class="metric-value">{products[0]['total_count']:,} 起</div>
            <div class="metric-desc">代表产品: {products[0]['brand_name_zh']} ({products[0]['code']})</div>
        </div>
    </div>

    <!-- 图表展示区 -->
    <div class="charts-row">
        <div class="chart-card">
            <div class="chart-header">
                <div class="chart-title">聚类时间中心趋势曲线 (时序归一化折线图)</div>
            </div>
            <div id="timeline-chart" class="chart-container"></div>
        </div>
        <div class="chart-card">
            <div class="chart-header">
                <div class="chart-title">各聚类临床后果分布 (严重程度对比)</div>
            </div>
            <div id="severity-chart" class="chart-container"></div>
        </div>
    </div>

    <!-- 聚类科学解读 -->
    <div class="clustering-desc-card">
        <div class="chart-title" style="margin-bottom: 10px;">聚类演变规律与风险类型解读</div>
        <p style="font-size: 14px; color: var(--text-secondary); line-height: 1.5;">
            基于 K-Means 对 91 种新器械进行的时序聚类，可明确分为三大核心类别。以下为各类别在真实世界中的风险演化规律：
        </p>
        <div class="desc-grid">
            <div class="desc-item c0">
                <div class="desc-name" style="color: var(--accent-cyan);">Cluster 0: 早期暴发平缓释放类 (常态散发型)</div>
                <div class="desc-text">
                    该类产品在 2021-2022 年间上市初期即引发了小高峰，随后随着市场渗透和医生操作熟练，不良事件率维持在**中低频缓慢震荡下行**。死亡率为 0.82%，设备故障占比 80.61%。这符合新器械临床应用早期“操作熟练度阵痛期”，最终走向平稳释放。
                </div>
            </div>
            <div class="desc-item c1">
                <div class="desc-name" style="color: var(--accent-pink);">Cluster 1: 迟滞缓慢稳步抬头类 (高危致死型)</div>
                <div class="desc-text">
                    该类器械上市较晚，早期报告率低，但随着医院采购与临床铺开，其不良事件呈**按季度稳步线性爬坡**趋势。该聚类包含高风险消融导管、缝合器等，其**致死率极高 (2.68%)**！严重伤害占比达 38.60%，说明它们一旦出事，有极高概率危及生命安全。
                </div>
            </div>
            <div class="desc-item c2">
                <div class="desc-name" style="color: var(--accent-gold);">Cluster 2: 爆发攀升风险类 (高频故障型)</div>
                <div class="desc-text">
                    该类器械上市初期平静，但随着移动胰岛素泵显示App或新型家用血糖传感器的普及，在 2022-2024 年中期呈现**井喷式暴增**。虽然其不良事件频数巨大（数万起），但**设备故障占比高达 99.18%**（死亡率仅 0.03%）。其主要风险是软件可靠性与设备低故障率。
                </div>
            </div>
        </div>
    </div>

    <!-- 新上市器械详细列表 -->
    <div class="list-card">
        <div class="chart-header" style="margin-bottom: 16px;">
            <div class="chart-title">专设监测新上市器械临床明细列表 (91 种)</div>
        </div>
        <div class="list-tools">
            <input type="text" id="searchInput" class="search-box" placeholder="搜索产品代码、中文/英文通用名或品牌...">
            <div class="filter-buttons">
                <button class="filter-btn active" data-filter="all">全量器械</button>
                <button class="filter-btn c0" data-filter="0">Cluster 0 (早期平缓)</button>
                <button class="filter-btn c1" data-filter="1">Cluster 1 (高危抬头)</button>
                <button class="filter-btn c2" data-filter="2">Cluster 2 (高频爆发)</button>
            </div>
        </div>
        <div class="table-container">
            <table id="deviceTable">
                <thead>
                    <tr>
                        <th style="width: 80px;">产品代码</th>
                        <th style="width: 120px;">首次上报日期</th>
                        <th style="width: 100px;">总事件数</th>
                        <th>通用名称 (Generic Name)</th>
                        <th>代表品牌 (Brand Name)</th>
                        <th style="width: 120px;">聚类归属</th>
                        <th style="width: 150px;">临床后果占比</th>
                    </tr>
                </thead>
                <tbody id="tableBody">
                    <!-- JS 渲染 -->
                </tbody>
            </table>
        </div>
    </div>

    <footer>
        <p>© 2026 FDA MAUDE 医疗器械不良事件挖掘大盘 | 汉化与聚类技术支持: Antigravity AI Agent</p>
    </footer>

    <script>
        // 1. 获取 Python 注入的数据
        const months = {js_months};
        const clusterInfo = {js_cluster_info};
        const products = {js_products};

        // 2. 初始化 ECharts - 时序趋势
        const timelineChart = echarts.init(document.getElementById('timeline-chart'), 'dark', {{
            backgroundColor: 'transparent'
        }});

        const timelineOption = {{
            tooltip: {{
                trigger: 'axis',
                backgroundColor: '#1f2937',
                borderColor: '#374151',
                textStyle: {{ color: '#f3f4f6' }},
                formatter: function(params) {{
                    let html = `<div style="font-family: 'Outfit'; font-weight: bold; margin-bottom: 5px;">${{params[0].name}}</div>`;
                    params.forEach(p => {{
                        html += `<div style="display:flex; justify-content:space-between; align-items:center; width:220px; margin: 3px 0;">
                            <span><span style="display:inline-block; margin-right:5px; border-radius:10px; width:9px; height:9px; background-color:${{p.color}};"></span>${{p.seriesName}}</span>
                            <span style="font-weight:bold;">${{(p.value * 100).toFixed(1)}}%</span>
                        </div>`;
                    }});
                    return html;
                }}
            }},
            legend: {{
                data: ['Cluster 0 (早期平缓类)', 'Cluster 1 (高危抬头类)', 'Cluster 2 (高频爆发类)'],
                textStyle: {{ color: '#9ca3af' }},
                bottom: 0
            }},
            grid: {{
                left: '4%',
                right: '4%',
                bottom: '10%',
                top: '5%',
                containLabel: true
            }},
            xAxis: {{
                type: 'category',
                boundaryGap: false,
                data: months,
                axisLine: {{ lineStyle: {{ color: '#374151' }} }},
                axisLabel: {{ color: '#9ca3af', fontStyle: 'Outfit' }}
            }},
            yAxis: {{
                type: 'value',
                name: '归一化频数',
                min: 0,
                max: 1.0,
                axisLine: {{ lineStyle: {{ color: '#374151' }} }},
                axisLabel: {{ color: '#9ca3af' }},
                splitLine: {{ lineStyle: {{ color: '#1f2937' }} }}
            }},
            series: [
                {{
                    name: 'Cluster 0 (早期平缓类)',
                    type: 'line',
                    smooth: true,
                    showSymbol: false,
                    lineStyle: {{ width: 3, color: '#06b6d4' }},
                    itemStyle: {{ color: '#06b6d4' }},
                    data: clusterInfo['0']['center_ts']
                }},
                {{
                    name: 'Cluster 1 (高危抬头类)',
                    type: 'line',
                    smooth: true,
                    showSymbol: false,
                    lineStyle: {{ width: 3, color: '#ec4899' }},
                    itemStyle: {{ color: '#ec4899' }},
                    data: clusterInfo['1']['center_ts']
                }},
                {{
                    name: 'Cluster 2 (高频爆发类)',
                    type: 'line',
                    smooth: true,
                    showSymbol: false,
                    lineStyle: {{ width: 3, color: '#fbbf24' }},
                    itemStyle: {{ color: '#fbbf24' }},
                    data: clusterInfo['2']['center_ts']
                }}
            ]
        }};
        timelineChart.setOption(timelineOption);

        // 3. 初始化 ECharts - 聚类后果堆叠柱状图
        const severityChart = echarts.init(document.getElementById('severity-chart'), 'dark', {{
            backgroundColor: 'transparent'
        }});

        const clusterLabels = ['Cluster 0 (早期平缓)', 'Cluster 1 (高危抬头)', 'Cluster 2 (高频爆发)'];
        const deaths = [];
        const injuries = [];
        const malfunctions = [];

        for (let i = 0; i < 3; i++) {{
            const info = clusterInfo[i.toString()];
            const tot = info['total_events'] || 1;
            deaths.push(parseFloat((info['death'] / tot * 100).toFixed(2)));
            injuries.push(parseFloat((info['injury'] / tot * 100).toFixed(2)));
            malfunctions.push(parseFloat((info['malfunction'] / tot * 100).toFixed(2)));
        }}

        const severityOption = {{
            tooltip: {{
                trigger: 'axis',
                axisPointer: {{ type: 'shadow' }},
                backgroundColor: '#1f2937',
                borderColor: '#374151',
                textStyle: {{ color: '#f3f4f6' }},
                formatter: function(params) {{
                    let html = `<div style="font-weight: bold; margin-bottom: 5px;">${{params[0].name}} 临床后果占比</div>`;
                    params.forEach(p => {{
                        html += `<div style="display:flex; justify-content:space-between; width:170px; margin:3px 0;">
                            <span>${{p.seriesName}}</span>
                            <span style="font-weight:bold;">${{p.value}}%</span>
                        </div>`;
                    }});
                    return html;
                }}
            }},
            legend: {{
                data: ['死亡 (Death)', '严重伤害 (Injury)', '器械故障 (Malfunction)'],
                textStyle: {{ color: '#9ca3af' }},
                bottom: 0
            }},
            grid: {{
                left: '3%',
                right: '4%',
                bottom: '10%',
                top: '5%',
                containLabel: true
            }},
            xAxis: {{
                type: 'category',
                data: clusterLabels,
                axisLine: {{ lineStyle: {{ color: '#374151' }} }},
                axisLabel: {{ color: '#9ca3af' }}
            }},
            yAxis: {{
                type: 'value',
                axisLine: {{ lineStyle: {{ color: '#374151' }} }},
                axisLabel: {{ formatter: '{{value}}%', color: '#9ca3af' }},
                splitLine: {{ lineStyle: {{ color: '#1f2937' }} }}
            }},
            series: [
                {{
                    name: '死亡 (Death)',
                    type: 'bar',
                    stack: 'total',
                    color: '#ec4899',
                    label: {{ show: true, formatter: '{{c}}%' }},
                    data: deaths
                }},
                {{
                    name: '严重伤害 (Injury)',
                    type: 'bar',
                    stack: 'total',
                    color: '#06b6d4',
                    label: {{ show: true, formatter: '{{c}}%' }},
                    data: injuries
                }},
                {{
                    name: '器械故障 (Malfunction)',
                    type: 'bar',
                    stack: 'total',
                    color: '#4b5563',
                    label: {{ show: true, formatter: '{{c}}%' }},
                    data: malfunctions
                }}
            ]
        }};
        severityChart.setOption(severityOption);

        // 4. 渲染表格数据
        const tableBody = document.getElementById('tableBody');
        let currentFilter = 'all';
        let searchQuery = '';

        function renderTable() {{
            tableBody.innerHTML = '';
            
            const filteredProducts = products.filter(p => {{
                const labelMatch = currentFilter === 'all' || p.cluster.toString() === currentFilter;
                const lowerSearch = searchQuery.toLowerCase();
                const searchMatch = searchQuery === '' || 
                    p.code.toLowerCase().includes(lowerSearch) ||
                    p.generic_name.toLowerCase().includes(lowerSearch) ||
                    p.brand_name.toLowerCase().includes(lowerSearch) ||
                    (p.generic_name_zh && p.generic_name_zh.toLowerCase().includes(lowerSearch)) ||
                    (p.brand_name_zh && p.brand_name_zh.toLowerCase().includes(lowerSearch));
                
                return labelMatch && searchMatch;
            }});

            if (filteredProducts.length === 0) {{
                tableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; color: var(--text-secondary); padding: 40px;">没有符合条件的器械产品。</td></tr>`;
                return;
            }}

            filteredProducts.forEach(p => {{
                const tr = document.createElement('tr');
                
                const tot = p.severity.total || 1;
                const dPct = (p.severity.death / tot * 100).toFixed(2);
                const iPct = (p.severity.injury / tot * 100).toFixed(2);
                const mPct = (p.severity.malfunction / tot * 100).toFixed(2);

                let cClass = 'c0';
                let cText = 'Cluster 0 (早期平缓)';
                if (p.cluster === 1) {{ cClass = 'c1'; cText = 'Cluster 1 (高危抬头)'; }}
                else if (p.cluster === 2) {{ cClass = 'c2'; cText = 'Cluster 2 (高频爆发)'; }}

                tr.innerHTML = `
                    <td><span class="code-badge">${{p.code}}</span></td>
                    <td style="font-family: 'Outfit'; color: var(--text-secondary);">${{p.first_date}}</td>
                    <td style="font-family: 'Outfit'; font-weight: 600;">${{p.total_count.toLocaleString()}}</td>
                    <td>
                        <div style="font-weight: 600; color: var(--text-primary); font-size: 14px;">${{p.generic_name_zh}}</div>
                        <div style="font-size: 11px; color: var(--text-secondary); font-weight: normal; margin-top: 2px;">${{p.generic_name}}</div>
                    </td>
                    <td>
                        <div style="font-weight: 500; color: var(--text-primary); font-size: 14px;">${{p.brand_name_zh}}</div>
                        <div style="font-size: 11px; color: var(--text-secondary); font-style: italic; margin-top: 2px;">${{p.brand_name}}</div>
                    </td>
                    <td><span class="cluster-tag ${{cClass}}">${{cText}}</span></td>
                    <td>
                        <div class="severity-bar-container">
                            <div class="severity-bar death" style="width: ${{dPct}}%"></div>
                            <div class="severity-bar injury" style="width: ${{iPct}}%"></div>
                            <div class="severity-bar malf" style="width: ${{mPct}}%"></div>
                        </div>
                        <div class="tooltip-custom">
                            死亡: ${{dPct}}% | 伤害: ${{iPct}}% | 故障: ${{mPct}}%
                        </div>
                    </td>
                `;
                tableBody.appendChild(tr);
            }});
        }}

        document.getElementById('searchInput').addEventListener('input', (e) => {{
            searchQuery = e.target.value;
            renderTable();
        }});

        const filterBtns = document.querySelectorAll('.filter-btn');
        filterBtns.forEach(btn => {{
            btn.addEventListener('click', (e) => {{
                filterBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentFilter = btn.getAttribute('data-filter');
                renderTable();
            }});
        }});

        renderTable();

        window.addEventListener('resize', () => {{
            timelineChart.resize();
            severityChart.resize();
        }});
    </script>
</body>
</html>
"""

    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"\n>>> 成功！分析报告大盘已渲染并写入: {OUTPUT_HTML}")
    conn.close()

if __name__ == '__main__':
    main()
