import os
import pandas as pd
import pymysql
from dotenv import load_dotenv

# 获取基准目录并加载环境配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(BASE_DIR, ".env")
load_dotenv(env_path)

DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASSWORD', '123456')
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', 3306))

def get_mysql_connection(db_name):
    """建立本地 MySQL 连接"""
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        database=db_name,
        charset='utf8mb4'
    )

def standardize_source_domain():
    """
    源域数据规范化：
    将 maude_stapler_db 中的多张表进行级联 JOIN 提取，
    融合成包含：基本信息、患者信息、合并英文叙述文本、标准 IMDRF 标签的 DataFrame。
    """
    print(">>> 正在从本地数据库 maude_stapler_db 级联提取源域特征...")
    conn = get_mysql_connection("maude_stapler_db")
    
    # 级联查询主表、设备表、患者表以及叙述文本
    sql = """
        SELECT 
            m.MDR_REPORT_KEY,
            m.DATE_RECEIVED,
            m.EVENT_TYPE,
            d.BRAND_NAME,
            d.GENERIC_NAME,
            d.DEVICE_REPORT_PRODUCT_CODE,
            p.PATIENT_AGE AS AGE,
            p.PATIENT_SEX AS GENDER,
            (
                SELECT GROUP_CONCAT(CONCAT('[', t.TEXT_TYPE_CODE, '] ', t.FOI_TEXT) SEPARATOR '\n\n')
                FROM foi_text t
                WHERE t.MDR_REPORT_KEY = m.MDR_REPORT_KEY
            ) AS foi_text_combined,
            (
                SELECT GROUP_CONCAT(DISTINCT dpc.DEVICE_PROBLEM_CODE)
                FROM device_problem_code dpc
                WHERE dpc.MDR_REPORT_KEY = m.MDR_REPORT_KEY
            ) AS device_problems,
            (
                SELECT GROUP_CONCAT(DISTINCT ppc.PATIENT_PROBLEM_CODE)
                FROM patient_problem_code ppc
                WHERE ppc.MDR_REPORT_KEY = m.MDR_REPORT_KEY
            ) AS patient_problems
        FROM mdr_report m
        LEFT JOIN device d ON m.MDR_REPORT_KEY = d.MDR_REPORT_KEY
        LEFT JOIN patient p ON m.MDR_REPORT_KEY = p.MDR_REPORT_KEY
    """
    
    df_src = pd.read_sql(sql, conn)
    conn.close()
    
    # 填充文本空值，并将年龄规范为数值
    df_src['foi_text_combined'] = df_src['foi_text_combined'].fillna('')
    df_src['AGE'] = pd.to_numeric(df_src['AGE'], errors='coerce')
    
    print(f"   [完成] 源域规范化完成，共提取 {df_src.shape[0]} 行, {df_src.shape[1]} 列。")
    return df_src

def standardize_target_domain(csv_path):
    """
    目标域数据规范化：
    1. 清理南京 CSV 表格中的冗余带有 '.1' 后缀的列和无关行政审批字段。
    2. 整合非结构化中文文本字段为统一特征列。
    3. 将结局标签映射映射到源域 EVENT_TYPE 对齐体系。
    """
    print(f"\n>>> 正在加载并规范化目标域（南京）数据: {os.path.basename(csv_path)}")
    
    # 兼容编码读取
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding='gbk')
        
    # 1. 滤除所有冗余的 .1 克隆列
    cleaned_cols = [col for col in df.columns if not col.endswith('.1')]
    df_clean = df[cleaned_cols].copy()
    
    # 2. 移除行政审批及联系方式噪音列
    admin_noise_cols = [
        '联系地址', '联系人', '联系电话', '上报单位所属地区', '审核人', '审核日期', 
        '审核意见', '审核结果', '市级监测机构', '省级监测机构', '国家级监测机构',
        '报告人', '单位名称', '使用单位、经营企业所属监测机构', '上市许可持有人名称'
    ]
    df_clean = df_clean.drop(columns=[c for c in admin_noise_cols if c in df_clean.columns], errors='ignore')
    
    # 3. 结局映射对齐 (严重伤害 ➔ IN, 死亡 ➔ D, 其他/无 ➔ M)
    outcome_mapping = {
        '严重伤害': 'IN',
        '死亡': 'D',
        '其他': 'M',
        '无': 'M'
    }
    df_clean['EVENT_TYPE'] = df_clean['伤害'].map(outcome_mapping).fillna('M')
    
    # 4. 融合非结构化中文描述为统一的中文文本列
    df_clean['使用过程'] = df_clean['使用过程'].fillna('')
    df_clean['调查情况'] = df_clean['调查情况'].fillna('')
    df_clean['初步处置情况'] = df_clean['初步处置情况'].fillna('')
    
    df_clean['nanjing_text_combined'] = (
        "[使用过程]: " + df_clean['使用过程'] + "\n" +
        "[调查情况]: " + df_clean['调查情况'] + "\n" +
        "[初步处置]: " + df_clean['初步处置情况']
    )
    
    # 5. 保留核心字段构建结构化视图
    core_cols = [
        '报告编码', '报告日期', '产品名称', '注册证编号/曾用注册证编号', 
        '型号', '规格', '产品批号', '生产日期', '有效期至',
        '年龄', '性别', '器械故障表现', '伤害表现', 'EVENT_TYPE', 
        'nanjing_text_combined'
    ]
    
    df_target_view = df_clean[[c for c in core_cols if c in df_clean.columns]]
    print(f"   [完成] 目标域规范化完成，共提取 {df_target_view.shape[0]} 行, {df_target_view.shape[1]} 列。")
    return df_target_view

def main():
    # 建立输出文件夹
    processed_data_dir = os.path.join(BASE_DIR, "stapler_research", "data")
    os.makedirs(processed_data_dir, exist_ok=True)
    
    # 执行源域规范化
    df_source = standardize_source_domain()
    df_source.to_pickle(os.path.join(processed_data_dir, "source_standardized.pkl"))
    
    # 执行目标域规范化
    nanjing_csv_path = os.path.join(BASE_DIR, "data", "吻合器南京.csv")
    if os.path.exists(nanjing_csv_path):
        df_target = standardize_target_domain(nanjing_csv_path)
        df_target.to_pickle(os.path.join(processed_data_dir, "target_standardized.pkl"))
        
    print("\n>>> 规范化特征视图构建完成，数据已以 pickle 格式序列化保存至 stapler_research/data/。")

if __name__ == '__main__':
    main()
