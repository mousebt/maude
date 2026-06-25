# FDA MAUDE 医疗器械不良事件挖掘计划 (双轨增强版)

## 一、 项目总体架构 (Data Infrastructure)
我们在实战中发现 MAUDE 数据高度庞杂，包含极多由于填报错误遗留的“暗黑长文本”（如套娃 CSV 表格、串联并发医疗器械清单）。为兼顾极致性能与科研探索双重诉求，本项目自研并采用了首创的 **“BLOB 分离双轨重组架构（Vertical Partitioning）”**。

### 1.1 数据底座设计（已实装并落盘完成）
- **高速主库 (Normal Tables)**：强制剥离极度庞杂的数据。诸如 `EVENT_KEY`、`DATE_RECEIVED` 均限定合理的 `VARCHAR`。涉及长文本（FOI_TEXT, SEQUENCE_NUMBER_TREATMENT等）一旦超长则立即被斩断截留至最大阈值。主库查询畅通无阻，主要用于后续 PRR / ROR 快速统计算法。
- **暗总仓辅表 (Outlier Tables)**：设立 `patient_outliers` 与 `foi_text_outliers`。采用 `LONGTEXT` 记忆空间，借助 Python 导入时旁路拦截保存的几十万条具有超高“复合医疗网络解析”价值的全量异端文本。用于提供给底层大语言模型（LLM）展开“显微镜模式”逐案分析。

---

## 二、 后续挖掘行动路线 (Mining Action Roadmap)
数据底盘搭建完毕后，项目将正式分 **A / B 双轴** 推进真正的挖掘产出任务：

### A轴：传统药械警戒信号检测 (Signal Detection)
**目标**：在大盘全量库中，筛查与某类特定器械强关联的致命故障模式。
1. **构建基本 2x2 列联表**
   - 提取感兴趣的 Target Device (如某个品牌支架) 与 Target Event (如某类致命并发症)。
2. **频数比例计算** (Python/SQL 联合执行)
   - 计算 **PRR (比例报告比, Proportional Reporting Ratio)**：对比目标设备与其他设备发生该故障的比例。
   - 计算 **ROR (报告比值比, Reporting Odds Ratio)**。
3. **成果产出**：直接输出带有置信区间 (95% CI) 的火山图（Volcano Plot），形成标准的一区量化循证医学文献图表。

### B轴：LLM 暗数据高维网络重构 (Dark-Data LLM Restructuring) - ⭐ 核心创新点
**目标**：破解传统的 MAUDE 只能做单器械分析的困局。我们将利用辅表中拦截的那近乎 60 万条珍稀畸形记录，让大模型还原手术当时的配套生态。
1. **大模型结构化管道开发**：
   - 编写 Python 脚本直连数据库 `student_outliers`。
   - 逐批次调用 `Zhipu / Gemini API` 进行 Prompt 工程提取。
2. **提取清单拆解化元结构 (Tuple Extraction)**：
   - 从庞大的 `ORIGINAL_SEQ_TREATMENT` 源文本内提取：`[目标手术] -> [核心器械模型A] -> [伴随工具B] -> [麻醉或施加用药C]` 的共现矩阵。
3. **成果产出**：输出**多模态关联知识图谱 (Co-occurrence Network Map)**。论证核心器械在哪些特定耗材伴随的情况下具有极高连锁崩塌风险。

---
**当前阶段节点**：已完成环境配建、双轨数据底座建立。随时可向 A / B 轴进军。本项目旨在对 MAUDE 最新的原始数据集（截至2025年数据）进行数据解析、清洗、并存入 MySQL 数据库，为后续分析医疗器械的不良事件特征、产品缺陷以及进行潜在风险信号的挖掘提供基础数据支撑。

## 2. 原始数据分析

原始数据存放在 `e:\pythonProject\MAUDE\rawData` 目录下，各项数据文件均为以竖线 `|` 作为分隔符的文本文件（首行为表头）。各文件基础分析如下：

| 数据文件名称 | 文件大小 | 字段数量 | 核心作用与说明 |
| :--- | :--- | :--- | :--- |
| **mdrfoiThru2025.txt** | 约 6.4 GB | 86 | **主表数据（MDR 主表）**。记录不良事件的基础报告信息，如报告编号、事件发生日期、上报人职业、事件类型等。主键为 `MDR_REPORT_KEY`。 |
| **foitext2025.txt** | 约 3.5 GB | 6 | **文本表（FOI 文本表）**。包含详尽的事件经过与厂商调查描述记录（自由文本）。主键为 `MDR_REPORT_KEY` 与 `MDR_TEXT_KEY`，对应主表的外键。 |
| **patientThru2025.txt** | 约 0.95 GB | 10 | **患者信息表**。记录事件中涉及患者的年龄、性别、体重等信息。主键为 `MDR_REPORT_KEY`。 |
| **DEVICE2025.txt** | 约 0.7 GB | 34 | **设备信息表**。包含不良事件中涉及的具体医疗器械名称、品牌、制造商、批号以及产品代码等。主键为 `MDR_REPORT_KEY`。 |

> **数据特点注意**：数据量非常庞大（特别是主表和文本表），文本中存在大量的异常字符和没有经过严格校验的自由文本，因此在导入和清洗时需特别处理。

---

## 3. 数据库设计与建表方案 (MySQL)

将这四部分数据以关系型数据库的形式存储。因为部分数据文件包含很长的字符串，建议对长文本字段采用 `TEXT` 或 `LONGTEXT` 类型。

### 3.1 建表脚本概览

**MDR主表 (mdr_report)**
```sql
CREATE TABLE mdr_report (
    MDR_REPORT_KEY BIGINT PRIMARY KEY,
    EVENT_KEY BIGINT,
    REPORT_NUMBER VARCHAR(255),
    REPORT_SOURCE_CODE VARCHAR(50),
    DATE_RECEIVED DATE,
    ADVERSE_EVENT_FLAG VARCHAR(5),
    PRODUCT_PROBLEM_FLAG VARCHAR(5),
    DATE_REPORT DATE,
    DATE_OF_EVENT DATE,
    EVENT_TYPE VARCHAR(100),
    -- 省略部分其他字段...需根据86个字段完整建立
    INDEX idx_date_received (DATE_RECEIVED)
);
```

**设备表 (device)**
```sql
CREATE TABLE device (
    MDR_REPORT_KEY BIGINT,
    DEVICE_EVENT_KEY BIGINT,
    BRAND_NAME VARCHAR(500),
    GENERIC_NAME VARCHAR(500),
    MANUFACTURER_D_NAME VARCHAR(500),
    DEVICE_REPORT_PRODUCT_CODE VARCHAR(50),
    -- 其他设备属性字段...
    INDEX idx_mdr_key (MDR_REPORT_KEY),
    INDEX idx_product_code (DEVICE_REPORT_PRODUCT_CODE)
);
```

**患者表 (patient)**
```sql
CREATE TABLE patient (
    MDR_REPORT_KEY BIGINT,
    PATIENT_SEQUENCE_NUMBER INT,
    PATIENT_AGE VARCHAR(50),
    PATIENT_SEX VARCHAR(50),
    PATIENT_WEIGHT VARCHAR(50),
    -- 其他患者相关字段...
    INDEX idx_mdr_key (MDR_REPORT_KEY)
);
```

**文本描述表 (foi_text)**
```sql
CREATE TABLE foi_text (
    MDR_REPORT_KEY BIGINT,
    MDR_TEXT_KEY BIGINT,
    TEXT_TYPE_CODE VARCHAR(10),
    PATIENT_SEQUENCE_NUMBER INT,
    DATE_REPORT DATE,
    FOI_TEXT LONGTEXT,
    PRIMARY KEY (MDR_REPORT_KEY, MDR_TEXT_KEY)
);
```

---

## 4. 数据清洗与导入路径

因为原始数据文件非常大（主表超 6GB），传统的单行 `INSERT` 或者是 `pandas.read_csv` 把整个文件读入内存的方式都会导致内存溢出。

**导入步骤规划：**
1. **预处理清洗 (Python)**：
   使用 Python 脚本，采用 `chunksize` 对数据进行分块读取。
   - 过滤不可见的控制字符（如 `\x00` 等），这些容易导致 MySQL 导入失败。
   - 统一日期格式转换为 `YYYY-MM-DD` 以适配 MySQL 的 Date 格式。
   - 处理定界符内容冲突：有些文本中间本身包含 `|`，或者未闭合的换行符，需制定对应的正则处理。
2. **高效存库**：
   - 方案一：采用 `pandas.to_sql` 结合 `chunksize` 逐批次写入数据库。
   - 方案二：**推荐方案**。预处理为干净的 CSV 无格式文件后，利用 MySQL 原生的高效导入命令 `LOAD DATA LOCAL INFILE` 导入数据库。耗时可从十几个小时缩短至几十分钟。
3. **数据校验**：校验各表的行数是否与预估值一致，`MDR_REPORT_KEY` 之间的外键关联是否存在大面积孤儿数据。

---

## 5. 数据挖掘路径与分析方案

完成仓储建设后，展开如下三个维度的深度发掘分析：

### 5.1 基础描述性分析 (Descriptive Analysis)
- **趋势分析**：基于上报时间（`DATE_RECEIVED`）统计每年的不良事件呈报总体趋势。
- **占比分析**：从设备类型（`DEVICE_REPORT_PRODUCT_CODE`）、事件后果（致命、住院等）和报告人类型多角度描绘整体全景图谱。

### 5.2 信号检测 (Signal Detection / Disproportionality Analysis)
借鉴药物警戒 (Pharmacovigilance) 中心常用的算法，挖掘“特定医疗器械 - 特定不良事件”之间的强关联信号。
- **算法模型应用**：
  - 比例失调法：PRR (Proportional Reporting Ratio), ROR (Reporting Odds Ratio)。
  - 贝叶斯方法：BCPNN (Bayesian Confidence Propagation Neural Network), MGPS (Multi-item Gamma Poisson Shrinker)。
- **分析实现**：筛选特定类别产品的产品代码，通过构建二阶列联表计算上述相关性指标，设定阈值提取医疗器械早期的风险预警信号。

### 5.3 自然语言处理与文本挖掘 (NLP Mining)
鉴于 MAUDE 中最具价值的信息往往隐藏在 `FOI_TEXT` 字段内的事件描述文本里。可以应用深度学习与 NLP 算法提取深层信息：
- **故障模式与后果分析 (FMEA)**：提取文本中导致器械失效的关键词（如“断裂”、“漏液”、“电量耗尽”等），建立核心术语词典。
- **实体抽取 (NER)**：利用预训练语言模型（如基于医疗文本的 BERT 模型模型）自动提取：患者症状、具体的并发症名词。
- **情感分析/严重度分类**：对文本描述训练分类器，自动判断该事件记录的掩藏严重性程度。

---

## 6. 项目落地与里程碑

- **Phase 1: 数据准备 (当前阶段)**：完成数据结构摸底，Python 建立分块清洗与入库脚本。
- **Phase 2: 数据库投产**：完成 11GB+ 文本数据向 MySQL 的导入与索引建立。
- **Phase 3: 分析模型开发**：构建 ROR / PRR 的 SQL 或 Python 运算逻辑代码封装。
- **Phase 4: 可视化与报告**：沉淀挖掘结果，连接 BI 工具或输出图表，形成针对特定科室/特定产品的医疗器械监察报告。
