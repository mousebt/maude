# 吻合器不良事件跨多源数据库迁移学习与风险挖掘研究 (Stapler Research)

本专用目录承载了《基于大语言模型的吻合器不良事件跨多源数据库对齐与多维风险挖掘研究》的完整代码实现、中间数据集以及研究分析报告。

---

## 📁 目录结构

```text
stapler_research/
├── data/                                 # 存放本项目特有的数据集和缓存
│   ├── source_standardized.pkl           # 源域 (FDA MAUDE) 清洗标准化后的特征视图 (5.3万行)
│   ├── target_standardized.pkl           # 目标域 (中国南京) 清洗标准化后的特征视图 (1,094行)
│   ├── target_aligned.pkl                # 经过跨语言对齐及缺失型号抽取回填后的全量分析数据集
│   ├── imdrf_embedding_cache.pkl         # 官方 IMDRF 标准英文术语及中文释义的语义嵌入向量缓存
│   └── risk_association_rules.csv        # 经 FP-Growth 算法挖掘产出的临床严重结局强关联规则库
├── reports/                              # 存放学术报告与实验可视化图表
│   ├── academic_report.md                # 完整的学术论文级研究结题报告 (包含详细统计结论与讨论)
│   ├── detailed_experimental_steps.md    # 实验细化设计方案
│   ├── shap_importance.png               # 迁移模型严重度分类预测的 SHAP 特征重要性归因图
│   └── survival_comparison.png           # 中美真实世界吻合器失效生存寿命对照曲线 (Kaplan-Meier)
└── scripts/                              # 存放核心实验步骤 Python 运行脚本
    ├── standardize_data.py               # 步骤一：源域与目标域结局口径清洗与字段对齐
    ├── llm_alignment.py                  # 步骤二：利用 LLM 与 OpenAI Embedding 的跨语言故障编码对齐
    ├── fill_missing_models.py            # 步骤三：利用 LLM 显式抽取并回填临床描述中的缺失器械型号与规格
    ├── risk_mining.py                    # 步骤四：多维风险挖掘主程序 (KL散度、XGBoost、FP-Growth、生存分析)
    ├── export_stapler_db.py              # (辅助) 从大盘 MySQL 提取吻合器专有子库数据
    └── verify_stapler_db.py              # (辅助) 克隆数据库与索引级物理校验工具
```

---

## ⚙️ 环境依赖与准备

本项目运行于 Windows / Linux 平台（Python 3.13.9 环境测试通过）。运行前请确保安装了以下核心依赖库：

```bash
pip install pandas numpy scikit-learn xgboost shap mlxtend lifelines matplotlib openai sqlalchemy mysqlconnector
```

### API 秘钥配置
在项目根目录下创建 `.env` 文件，并填写您的 API Key：
```env
OPENROUTER_API_KEY="your_openrouter_api_key"
OPENAI_API_BASE="https://openrouter.ai/api/v1"
```
*提示：实体抽取调用 `deepseek/deepseek-chat` 模型，语义嵌入计算调用 `openai/text-embedding-3-small` 向量接口。*

---

## 🚀 核心实验步骤运行手册

请严格按照以下步骤顺序执行脚本以复现全部实验结果：

### 步骤一：数据规范化与统一特征视图构建
运行数据规范化脚本，统一中美两个数据库的不良事件结局（死亡、严重伤害、普通故障）口径，并抽取基础特征。
```bash
python scripts/standardize_data.py
```
* **输出**：生成 `data/source_standardized.pkl` 与 `data/target_standardized.pkl`。

### 步骤二：基于大语言模型的跨语言实体抽取与故障编码对齐
调用大模型提取南京中文自由文本中的故障短语，并与 491 条 IMDRF 官方英文词条进行语义嵌入余弦相似度匹配（对齐门槛阈值定为最优的 `0.60`）。
```bash
python scripts/llm_alignment.py
```
* **输出**：创建 `data/imdrf_embedding_cache.pkl` 向量缓存，并输出初步对齐文件（含映射得到的 IMDRF 标准 Annex A 故障编码）。

### 步骤三：从描述性自由文本中显式抽取并回填缺失型号与规格
为了在保证学术严谨性的前提下解决规格型号缺失问题，运行该脚本使用大模型定位并抽取隐藏在自述长文本中的器械真实型号（如 `ECS29`）与规格（如 `60mm`）。
```bash
python scripts/fill_missing_models.py
```
* **效果**：型号缺失率从 **23.03% 骤降至 8.04%**。
* **输出**：生成高完整度的全量对齐分析数据集 `data/target_aligned.pkl`。

### 步骤四：多维风险信息联合挖掘与统计学验证
一键运行本项目的联合风险挖掘脚本。主程序将依次运行以下算法并生成图表：
```bash
python scripts/risk_mining.py
```
* **包含的挖掘与检验任务**：
  1. **KL 散度评估**：测算中美两地在 233 维共享故障空间下的条件概率差异。
  2. **XGBoost 跨域零样本迁移学习**：在源域（MAUDE）上训练严重度分类器并在南京数据上做 Zero-shot 迁移预测（生成 [shap_importance.png](reports/shap_importance.png)）。
  3. **FP-Growth 强关联规则挖掘**：针对极不平衡结局，优化后件为严重结局的预警法则并输出至 [risk_association_rules.csv](data/risk_association_rules.csv)。
  4. **Kaplan-Meier 失效生存估计**：计算中美两地器械的工作寿命并进行非参数 Log-Rank 假设检验，判定寿命是否存在显著性差异（生成 [survival_comparison.png](reports/survival_comparison.png)）。

---

## 📈 核心研究结论汇总

1. **真实缺失型号回填**：从目标域文本中为 **162条记录回填了物理型号**，为 **27条记录回填了物理规格**。
2. **中美故障相似度 (KL 散度)**：高维共享故障空间下的 KL 散度为 $D_{KL}(P \parallel Q) = 5.8517$。
3. **零样本严重度预测**：XGBoost 预测 AUC 为 `0.4593`，其性能退化展现了明显的结局上报口径偏置（Covariate/Label Shift）。基于 SHAP 的归因指出，**钉成形失败 (A050704)** 和 **击发失败 (A050502)** 具有最高的严重度预测贡献。
4. **中美失效寿命生存曲线对比**：Log-Rank 检验得出 **`p-value = 0.000000`**，具有极显著的统计学寿命分化。
   * **美国 FDA MAUDE 数据库中位数工作寿命**：**`317.0 天`（约 10.6 个月）**
   * **中国 南京地区数据库中位数工作寿命**：**`224.0 天`（约 7.5 个月）**
