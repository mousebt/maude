# FDA MAUDE 数据库数据底座与分析指南 (README_FOR_AI)

> **致 AI 编码助手**：本工作空间承载了 FDA MAUDE 医疗器械不良事件全量真实世界数据（RWD）数据挖掘项目。本地 MySQL `maude_db` 数据库中已完整载入了全量 1.26 亿行级的数据底座并建立了相应的物理索引，无需再进行重建。

---

## 一、 数据源与物理布局现状

原始数据放置在项目数据目录下（仅作归档保存，已全部物理入库）：
* **数据目录**：`e:\pythonProjects\MAUDE\data\raw\`
* **核心物理文本文件**（共 62 个文件，主要包含截至 2025 年全量数据）：
  1. **主表数据**：`mdrfoiThru2025.txt`（约 6.4 GB，86 字段）
  2. **自由文本表**：`foitext2025.txt` 与历年文本（约 3.5 GB，6 字段）
  3. **患者信息表**：`patientThru2025.txt`（约 0.95 GB，10 字段）
  4. **器械信息表**：`DEVICE2025.txt` 与历年设备（约 0.7 GB，34 字段）

---

## 二、 数据库与工程状态说明

* **数据底座已就绪**：目前本地 MySQL 中的数据库 `maude_db` 处于完好状态，包含 `mdr_report`、`device`、`patient`、`foi_text_overflow`、`foi_text_knowledge` 等主辅表。
* **脚本清理规范化**：由于本地数据已固化且无需再次运行导入，为实现项目空间瘦身并防止冗余脚本造成干扰，所有的 MySQL 原始载入脚本（`import_maude_v2.py` / `run_import.py` / `import_extra_sqls.py`）及调试、测试脚本已安全删除。
* **环境配置**：本地配置保存在根目录的 [`.env`](file:///e:/pythonProjects/MAUDE/.env) 中。在开展开发前，请务必核对其中的数据库和第三方 API 密钥。

---

## 三、 数据验证与辅助分析工具

为便于日常探索和数据校验，我们在 `tools/` 目录下提供了一组高效的分析与运维工具：

1. **年度数据合并验证**：运行 [merge_yearly_tables.py](file:///e:/pythonProjects/MAUDE/tools/merge_yearly_tables.py) 重新汇总合并年度大宽表，更新统计报告。
2. **多维指标统计**：运行 [query_device_severity_stats.py](file:///e:/pythonProjects/MAUDE/tools/query_device_severity_stats.py) 快速拉取不良事件后果（D/IN/M）、Top 20 产品代码以及严重度分布。
3. **器械聚合检索**：运行 [aggregate_search_by_device.py](file:///e:/pythonProjects/MAUDE/tools/aggregate_search_by_device.py) 快速检索和统计特定医疗器械不良事件的关键词与聚合数据。
4. **分类覆盖率分析**：运行 [analyze_coverage.py](file:///e:/pythonProjects/MAUDE/tools/analyze_coverage.py) 实时查询并评估映射字典对当前数据库中器械名称的分类覆盖率。
5. **增量器械分类工具**：运行 [batch_classify_devices.py](file:///e:/pythonProjects/MAUDE/tools/batch_classify_devices.py) 对数据库中的器械名进行大模型翻译和多级映射分类（目前全量 4,036 条未分类器械已成功全部入库）。

---

## 四、 学术报告与可视化成果

项目的最终文献翻译、聚类分析和可视化大盘成果均已归集到了 `/reports` 目录下：
* **学术大盘**：[MAUDE_research_dashboard.html](file:///e:/pythonProjects/MAUDE/reports/MAUDE_research_dashboard.html)
* **独立文献翻译库**：[analysis_results_zh.html](file:///e:/pythonProjects/MAUDE/reports/analysis_results_zh.html)
* **独立聚类分析报告**：[research_clustering_analysis.html](file:///e:/pythonProjects/MAUDE/reports/research_clustering_analysis.html)
