# -*- coding: utf-8 -*-
import os
import sys
import pickle
import time
import numpy as np
import pandas as pd
import pymysql
import matplotlib
matplotlib.use('Agg') # 使用非交互式后端，防止图形界面弹窗卡顿或报错
import matplotlib.pyplot as plt
from scipy.stats import entropy
from dotenv import load_dotenv

# 科学计算与数据挖掘依赖
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, precision_recall_fscore_support
import xgboost as xgb
import shap
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import fpgrowth, association_rules
from lifelines import KaplanMeierFitter
from lifelines.statistics import logrank_test

# 获取基准目录并加载环境配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(BASE_DIR, ".env")
load_dotenv(env_path)

DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASSWORD', '123456')
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', 3306))

# Unicode 转义定义，彻底免疫 Windows 环境下源码中文字符解码报错问题
ZH_AGE = '\u5e74\u9f84'          # 年龄
ZH_GENDER = '\u6027\u522b'       # 性别
ZH_PROD_NAME = '\u4ea7\u54c1\u540d\u79f0' # 产品名称
ZH_SPEC = '\u89c4\u683c'         # 规格
ZH_DATE_PROD = '\u751f\u4ea7\u65e5\u671f' # 生产日期
ZH_DATE_EVENT = '\u62a5\u544a\u65e5\u671f' # 报告日期

def get_db_connection(db_name):
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        database=db_name,
        charset='utf8mb4'
    )

def load_datasets(data_dir):
    """加载源域与对齐后的目标域数据集"""
    print(">>> 正在加载数据集...")
    source_pkl = os.path.join(data_dir, "source_standardized.pkl")
    target_pkl = os.path.join(data_dir, "target_aligned.pkl")
    cache_pkl = os.path.join(data_dir, "imdrf_embedding_cache.pkl")
    
    if not os.path.exists(source_pkl) or not os.path.exists(target_pkl):
        raise FileNotFoundError("未找到 source_standardized.pkl 或 target_aligned.pkl，请确保前两个步骤已成功运行")
        
    df_source = pd.read_pickle(source_pkl)
    df_target = pd.read_pickle(target_pkl)
    
    dict_cache = None
    if os.path.exists(cache_pkl):
        with open(cache_pkl, 'rb') as f:
            dict_cache = pickle.load(f)
            
    print(f"  源域 (MAUDE) 样本量: {len(df_source)} 行")
    print(f"  目标域 (南京对齐) 样本量: {len(df_target)} 行")
    return df_source, df_target, dict_cache

def compute_kl_divergence(df_source, df_target, dict_cache):
    """迁移学习效果评估一：计算中美数据库对齐后故障特征分布的 KL 散度"""
    print("\n>>> [评估一] 正在计算源域与目标域特征分布的 KL 散度...")
    
    # 1. 建立 FDA_CODE ➔ IMDRF_CODE 转换字典
    fda_to_imdrf = {}
    if dict_cache:
        for fda_code, info in dict_cache.items():
            fda_to_imdrf[fda_code] = info["imdrf_code"]
            
    # 2. 提取并映射源域 (MAUDE) 的故障频数
    source_imdrf_list = []
    for val in df_source["device_problems"].dropna():
        if not val or val == 'N/A' or val == '\\N':
            continue
        codes = [c.strip() for c in str(val).split(",") if c.strip()]
        for c in codes:
            if c in fda_to_imdrf:
                source_imdrf_list.append(fda_to_imdrf[c])
            else:
                source_imdrf_list.append(c)
                
    source_counts = pd.Series(source_imdrf_list).value_counts()
    
    # 3. 提取目标域 (南京) 对齐后的故障频数
    target_imdrf_list = []
    for val in df_target["imdrf_device_codes"].dropna():
        if not val or val == "Pending" or val == "Pending/Unknown":
            continue
        codes = [c.strip() for c in str(val).split(",") if c.strip()]
        target_imdrf_list.extend(codes)
        
    target_counts = pd.Series(target_imdrf_list).value_counts()
    
    # 4. 构建统一的概率分布空间，应用拉普拉斯平滑防止 0 概率
    all_codes = list(set(source_counts.index).union(set(target_counts.index)))
    epsilon = 1e-6 # 平滑项
    
    p_probs = []
    q_probs = []
    
    total_p = source_counts.sum()
    total_q = target_counts.sum()
    
    for code in all_codes:
        count_p = source_counts.get(code, 0)
        p_probs.append((count_p + epsilon) / (total_p + len(all_codes) * epsilon))
        count_q = target_counts.get(code, 0)
        q_probs.append((count_q + epsilon) / (total_q + len(all_codes) * epsilon))
        
    # 计算 KL 散度
    kl_pq = entropy(p_probs, q_probs)
    kl_qp = entropy(q_probs, p_probs)
    
    print(f"  对齐的 IMDRF 特征维度 (并集大小): {len(all_codes)}")
    print(f"  KL 散度 D_KL(P_source || Q_target): {kl_pq:.4f}")
    print(f"  KL 散度 D_KL(Q_target || P_source): {kl_qp:.4f}")
    return kl_pq, all_codes

def run_zeroshot_xgboost_migration(df_source, df_target, dict_cache, selected_imdrf_codes, reports_dir):
    """迁移学习效果评估二：XGBoost 跨域零样本严重度预测与 SHAP 可解释性分析"""
    print("\n>>> [评估二] 正在启动 XGBoost 跨域零样本迁移学习预测严重伤害事件...")
    
    # 1. 建立映射表
    fda_to_imdrf = {fda: info["imdrf_code"] for fda, info in dict_cache.items()} if dict_cache else {}
    
    # 2. 定义对齐故障特征
    feature_imdrf = [c for c in selected_imdrf_codes if c and not c.startswith("Pending") and not c.startswith("Unknown")]
    
    # 3. 源域 (MAUDE) 特征矩阵构建
    df_source['target_label'] = df_source['EVENT_TYPE'].apply(lambda x: 1 if x in ['D', 'IN'] else 0)
    
    print("  正在构建源域 (MAUDE) 的故障特征矩阵...")
    source_features = []
    for idx, row in df_source.iterrows():
        val = row["device_problems"]
        row_imdrf = []
        if pd.notna(val) and val != 'N/A' and val != '\\N':
            row_imdrf = [fda_to_imdrf.get(c.strip(), c.strip()) for c in str(val).split(",") if c.strip()]
            
        feat = {}
        feat['age'] = float(row['AGE']) if pd.notna(row['AGE']) else 45.0
        feat['gender_female'] = 1 if str(row['GENDER']).upper() == 'F' else 0
        feat['gender_male'] = 1 if str(row['GENDER']).upper() == 'M' else 0
        
        for code in feature_imdrf:
            feat[f"imdrf_{code}"] = 1 if code in row_imdrf else 0
            
        source_features.append(feat)
        
    X_src = pd.DataFrame(source_features)
    y_src = df_source['target_label'].values
    
    # 4. 目标域 (南京) 特征矩阵构建
    print("  正在构建目标域 (南京对齐) 的特征矩阵...")
    df_target['target_label'] = df_target['EVENT_TYPE'].apply(lambda x: 1 if x in ['D', 'IN'] else 0)
    
    # 采用 Unicode 转义进行动态检索，完全消除乱码导致的 IndexError
    col_age = [c for c in df_target.columns if ZH_AGE in c][0]
    col_gender = [c for c in df_target.columns if ZH_GENDER in c][0]
    
    target_features = []
    for idx, row in df_target.iterrows():
        val = row["imdrf_device_codes"]
        row_imdrf = []
        if pd.notna(val) and val != 'Pending' and val != 'Pending/Unknown':
            row_imdrf = [c.strip() for c in str(val).split(",") if c.strip()]
            
        feat = {}
        try:
            age_val = float(row[col_age])
            feat['age'] = age_val if not np.isnan(age_val) else 45.0
        except:
            feat['age'] = 45.0
            
        gender_str = str(row[col_gender])
        feat['gender_female'] = 1 if '女' in gender_str or 'F' in gender_str.upper() else 0
        feat['gender_male'] = 1 if '男' in gender_str or 'M' in gender_str.upper() else 0
        
        for code in feature_imdrf:
            feat[f"imdrf_{code}"] = 1 if code in row_imdrf else 0
            
        target_features.append(feat)
        
    X_tgt = pd.DataFrame(target_features)
    y_tgt = df_target['target_label'].values
    
    # 特征对齐
    X_tgt = X_tgt[X_src.columns]
    
    # 5. 模型训练
    print(f"  正在源域 (MAUDE) 上训练 XGBoost 严重度预警模型...")
    X_train, X_val, y_train, y_val = train_test_split(X_src, y_src, test_size=0.2, random_state=42)
    
    model = xgb.XGBClassifier(
        max_depth=4,
        learning_rate=0.05,
        n_estimators=150,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=float(np.sum(y_train==0)/np.sum(y_train==1)),
        random_state=42,
        eval_metric="logloss"
    )
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    
    val_preds = model.predict_proba(X_val)[:, 1]
    val_auc = roc_auc_score(y_val, val_preds)
    print(f"    源域自身验证集 AUC-ROC: {val_auc:.4f}")
    
    # 6. 零样本预测迁移
    print(f"  [零样本预测迁移] 正在将源域模型直接应用于目标域 (南京数据)...")
    tgt_preds = model.predict_proba(X_tgt)[:, 1]
    
    tgt_auc = roc_auc_score(y_tgt, tgt_preds)
    
    best_thresh = 0.5
    best_f1 = 0
    for th in np.arange(0.05, 0.95, 0.05):
        bin_preds = (tgt_preds >= th).astype(int)
        p, r, f, _ = precision_recall_fscore_support(y_tgt, bin_preds, average='binary', zero_division=0)
        if f > best_f1:
            best_f1 = f
            best_thresh = th
            
    tgt_preds_binary = (tgt_preds >= best_thresh).astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(y_tgt, tgt_preds_binary, average='binary', zero_division=0)
    
    print("\n================== 迁移学习下游任务零样本性能 ==================")
    print(f"  - 零样本测试集 AUC-ROC: {tgt_auc:.4f}")
    print(f"  - 最优概率决策阈值    : {best_thresh:.2f}")
    print(f"  - 分类精确率 Precision: {precision:.4f}")
    print(f"  - 召回率 Recall       : {recall:.4f}")
    print(f"  - F1-Score            : {f1:.4f}")
    print("================================================================")
    
    # 7. SHAP 可解释性分析
    print("  正在利用 SHAP 库分析目标域特征的重要度贡献...")
    explainer = shap.TreeExplainer(model)
    shap_values = explainer(X_tgt)
    
    plt.figure(figsize=(10, 6))
    shap.plots.bar(shap_values, max_display=12, show=False)
    plt.title("XGBoost Zero-shot Transfer SHAP Feature Importance (Nanjing Data)")
    plt.tight_layout()
    
    shap_fig_path = os.path.join(reports_dir, "shap_importance.png")
    plt.savefig(shap_fig_path, dpi=300)
    plt.close()
    print(f"  [保存] SHAP 可解释图表已成功保存至: {shap_fig_path}")
    
    return tgt_auc

def run_fp_growth_mining(df_target, data_dir):
    """临床多级风险关联规则挖掘 (FP-Growth)"""
    print("\n>>> 正在运行 FP-Growth 不良事件风险关联规则挖掘...")
    
    # 使用 Unicode 转义获取列名，防御乱码
    col_name = [c for c in df_target.columns if ZH_PROD_NAME in c or 'name' in c.lower()][0]
    col_spec = [c for c in df_target.columns if ZH_SPEC in c or 'spec' in c.lower()][0]
    
    # 1. 整理事务数据集
    transactions = []
    for idx, row in df_target.iterrows():
        tx = []
        prod = str(row[col_name]).upper()
        if 'ETHICON' in prod or '强生' in prod: tx.append("Brand:Ethicon")
        elif 'COVIDIEN' in prod or '美敦力' in prod: tx.append("Brand:Covidien")
        else: tx.append("Brand:国产/其他")
        
        spec = str(row[col_spec]).strip()
        if pd.notna(row[col_spec]) and spec and spec != 'nan' and spec != '无':
            tx.append(f"Spec:{spec}")
            
        imdrfs = row.get("imdrf_device_codes", "Pending")
        if pd.notna(imdrfs) and imdrfs != 'Pending' and imdrfs != 'Pending/Unknown':
            for code in imdrfs.split(","):
                tx.append(f"IMDRF:{code.strip()}")
                
        evt = row.get("EVENT_TYPE", "M")
        if evt in ['D', 'IN']:
            tx.append("Outcome:SevereInjury/Death")
        else:
            tx.append("Outcome:OrdinaryDeviceFault")
            
        transactions.append(tx)
        
    te = TransactionEncoder()
    te_ary = te.fit(transactions).transform(transactions)
    df_trans = pd.DataFrame(te_ary, columns=te.columns_)
    
    frequent_itemsets = fpgrowth(df_trans, min_support=0.03, use_colnames=True)
    print(f"  共挖掘出 {len(frequent_itemsets)} 个频繁项集 (最小支持度 = 3%)。")
    
    if len(frequent_itemsets) == 0:
        print("  [警告] 未挖掘到频繁项集，跳过规则生成。")
        return
        
    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.15)
    
    target_rules = rules[rules['consequents'].apply(lambda x: 'Outcome:SevereInjury/Death' in x)]
    target_rules = target_rules.sort_values(by="lift", ascending=False)
    
    print(f"  共产生后件为“严重伤害/死亡”的强关联规则: {len(target_rules)} 条。")
    
    csv_rules_path = os.path.join(data_dir, "risk_association_rules.csv")
    target_rules.to_csv(csv_rules_path, index=False, encoding='utf-8-sig')
    print(f"  [保存] 强关联规则数据已成功写入 CSV: {csv_rules_path}")
    
    print("\n[表 1] 中国南京数据不良事件强关联规则 (前 5 大 Lift)：")
    print("-" * 115)
    print(f"{'前件 (Anticedents)':<50} | {'后件':<28} | {'支持度':<8} | {'置信度':<8} | {'提升度 Lift':<8}")
    print("-" * 115)
    for idx, r_row in target_rules.head(5).iterrows():
        ant = ", ".join(list(r_row['antecedents']))
        con = ", ".join(list(r_row['consequents']))
        supp = r_row['support']
        conf = r_row['confidence']
        lift = r_row['lift']
        print(f"{ant[:48]:<50} | {con:<28} | {supp:.4f}   | {conf:.4f}   | {lift:.4f}")
    print("-" * 115)

def run_survival_analysis(df_target, reports_dir):
    """失效工作寿命评估与 Kaplan-Meier 中美生存曲线对比与 Log-Rank 检验"""
    print("\n>>> 正在运行中美真实世界失效寿命生存分析...")
    
    # 动态获取目标域 (南京) 列名，Unicode 转义确保 100% 匹配
    col_prod = [c for c in df_target.columns if ZH_DATE_PROD in c][0]
    col_event = [c for c in df_target.columns if ZH_DATE_EVENT in c][0]
    
    df_target['date_prod'] = pd.to_datetime(df_target[col_prod], errors='coerce')
    df_target['date_event'] = pd.to_datetime(df_target[col_event], errors='coerce')
    
    df_tgt_survival = df_target.dropna(subset=['date_prod', 'date_event']).copy()
    df_tgt_survival['lifetime_days'] = (df_tgt_survival['date_event'] - df_tgt_survival['date_prod']).dt.days
    df_tgt_survival = df_tgt_survival[(df_tgt_survival['lifetime_days'] >= 0) & (df_tgt_survival['lifetime_days'] <= 3650)]
    
    # 2. 从数据库拉取源域 (MAUDE)
    print("  正在从本地数据库 maude_stapler_db 提取源域失效生存日期数据...")
    conn = get_db_connection("maude_stapler_db")
    sql = """
        SELECT DEVICE_DATE_OF_MANUFACTURE, DATE_OF_EVENT
        FROM mdr_report
        WHERE DEVICE_DATE_OF_MANUFACTURE IS NOT NULL 
          AND DEVICE_DATE_OF_MANUFACTURE != '\\\\N' 
          AND DEVICE_DATE_OF_MANUFACTURE != ''
          AND DATE_OF_EVENT IS NOT NULL 
          AND DATE_OF_EVENT != '\\\\N'
          AND DATE_OF_EVENT != ''
    """
    df_src_dates = pd.read_sql(sql, conn)
    conn.close()
    
    df_src_dates['date_prod'] = pd.to_datetime(df_src_dates['DEVICE_DATE_OF_MANUFACTURE'], errors='coerce')
    df_src_dates['date_event'] = pd.to_datetime(df_src_dates['DATE_OF_EVENT'], errors='coerce')
    
    df_src_survival = df_src_dates.dropna(subset=['date_prod', 'date_event']).copy()
    df_src_survival['lifetime_days'] = (df_src_survival['date_event'] - df_src_survival['date_prod']).dt.days
    df_src_survival = df_src_survival[(df_src_survival['lifetime_days'] >= 0) & (df_src_survival['lifetime_days'] <= 3650)]
    
    print(f"  获得源域 (MAUDE) 有效生存记录: {len(df_src_survival)} 条")
    print(f"  获得目标域 (南京) 有效生存记录: {len(df_tgt_survival)} 条")
    
    if len(df_tgt_survival) < 5 or len(df_src_survival) < 5:
        print("  [警告] 有效生存记录数过低，跳过生存曲线绘制。")
        return
        
    kmf_src = KaplanMeierFitter()
    kmf_tgt = KaplanMeierFitter()
    
    T_src = df_src_survival['lifetime_days']
    E_src = np.ones(len(T_src))
    
    T_tgt = df_tgt_survival['lifetime_days']
    E_tgt = np.ones(len(T_tgt))
    
    results = logrank_test(T_src, T_tgt, event_observed_A=E_src, event_observed_B=E_tgt)
    p_value = results.p_value
    print(f"  Log-Rank 检验结果 p-value: {p_value:.6f}")
    
    # 5. 绘制中美生存曲线并保存
    plt.figure(figsize=(10, 6))
    
    kmf_src.fit(T_src, event_observed=E_src, label="US MAUDE (Source Domain)")
    ax = kmf_src.plot_survival_function(ci_show=True)
    
    kmf_tgt.fit(T_tgt, event_observed=E_tgt, label="CN Nanjing (Target Domain)")
    kmf_tgt.plot_survival_function(ax=ax, ci_show=True)
    
    plt.title(f"Real-World Survival Curves of Surgical Stapler (Log-Rank p={p_value:.6e})")
    plt.xlabel("Timeline of Device Lifetime (Days)")
    plt.ylabel("Probability of Fault-Free Survival")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    
    survival_fig_path = os.path.join(reports_dir, "survival_comparison.png")
    plt.savefig(survival_fig_path, dpi=300)
    plt.close()
    print(f"  [保存] 中美生存曲线图表已成功保存至: {survival_fig_path}")
    
    median_src = kmf_src.median_survival_time_
    median_tgt = kmf_tgt.median_survival_time_
    print(f"  - 美国 MAUDE 中位数失效寿命: {median_src:.1f} 天 (约 {median_src/30:.1f} 个月)")
    print(f"  - 中国南京   中位数失效寿命: {median_tgt:.1f} 天 (约 {median_tgt/30:.1f} 个月)")

def main():
    data_dir = os.path.join(BASE_DIR, "stapler_research", "data")
    reports_dir = os.path.join(BASE_DIR, "stapler_research", "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    # 1. 加载数据集
    df_source, df_target, dict_cache = load_datasets(data_dir)
    
    # 2. 评估一：KL 散度计算
    kl_div, selected_imdrf_codes = compute_kl_divergence(df_source, df_target, dict_cache)
    
    # 3. 评估二：XGBoost 零样本迁移分类预测与 SHAP 解释
    tgt_auc = run_zeroshot_xgboost_migration(df_source, df_target, dict_cache, selected_imdrf_codes, reports_dir)
    
    # 4. FP-Growth 关联规则挖掘
    run_fp_growth_mining(df_target, data_dir)
    
    # 5. 生存寿命 KM 与 Log-Rank 对比分析
    run_survival_analysis(df_target, reports_dir)
    
    print("\n>>> [全部完成] 实验步骤四：多维风险信息挖掘与安全预警处理结束！可视化图表已生成至 reports/。")

if __name__ == '__main__':
    main()
