# PubMed 文献分析：FDA MAUDE 数据库挖掘（过去 10 年）

> [!NOTE]
> 本报告总结了过去 10 年（2016-2026年）发表在 PubMed 上的相关文献，内容涉及应用数据挖掘、文本挖掘、自然语言处理（NLP）、机器学习（ML）和大语言模型（LLMs）对美国食品药品监督管理局（FDA）的“制造商和用户设施器械体验”（MAUDE）数据库进行的研究与应用。

## 研究发现概述

我们共检索出 **41** 篇发表于 2016 至 2026 年间的相关论文。这些研究大致可分为以下三大核心领域：

1. **大语言模型与生成式 AI（8 篇）：** 代表了最新研究趋势（2024-2026年），利用 GPT-4 等模型阅读 MAUDE 报告中非结构化的描述性叙述，进行信息抽取（ETL）、构建交互式安全问答机器人，以及自动化生成研究问题。
2. **传统 NLP 与机器学习分类（29 篇）：** 应用传统分类器（随机森林、支持向量机、深度学习、BERT 等）对安全事件进行分类、预测器械召回、识别归类错误的死亡事件，并分析健康信息技术（Health IT）中的不良事件。
3. **临床器械安全与高级统计挖掘（4 篇）：** 大规模的横断面研究，旨在开发特定的不良事件严重程度分类体系，或通过统计性文本挖掘对比特定医疗器械（如植入物）的并发症发生率。

---

## 分类一：大语言模型（LLM）与生成式 AI（2024-2026年）
该研究类别代表了 MAUDE 数据库挖掘的最新前沿，使研究从简单的关键词检索走向理解复杂的临床叙述文本。

### 1. 软件类医疗器械安全监测自动化：基于 FDA MAUDE 数据的洞察
- **期刊与日期：** Stud Health Technol Inform (2026年5月21日)
- **PMID：** [42174919](https://pubmed.ncbi.nlm.nih.gov/42174919)
- **作者：** Kesharwani R, Cvijic L, Denecke K
- **匹配关键词：** `natural language processing, classification, large language model, clustering`
- **摘要核心细节：** 数字健康干预（DHI）利用数字技术提供并支持医疗服务。当这些干预措施注册为医疗器械时，其相关不良事件必须予以报告。本研究对 FDA MAUDE 数据库中记录的软件类医疗器械错误及事故进行了探讨。利用自然语言处理方法（具体为 BERTopic 聚类和大语言模型分类），我们分析了叙事性报告，以识别事件类型、诱发因素及时间分布规律。结果表明，BERTopic 能有效揭示主题趋势及演变，但许多聚类结果更多地反映了监管文件的语言惯例，而非软件特有的问题。网络安全、人机交互以及疫情监测等主题的出现，表明上市后监管正在延伸至更广泛的人机互动及公共卫生领域。虽然 MAUDE 叙述性文本提供了有价值的洞察，但其上下文细节的缺失限制了根本原因分析。为支持 DHI 的更安全设计及监管，仍需更完善的报告结构。

### 2. 利用大语言模型自动分类前列腺癌水凝胶直肠周围间隔物置入术后的不良事件
- **期刊与日期：** Urology (2026年3月)
- **PMID：** [41565161](https://pubmed.ncbi.nlm.nih.gov/41565161)
- **作者：** Sohoni N, Sohoni NS, Sutherland RA, Sundaresan VM, Smani S, Ananth P, Onofrey JA, Aneja S, Miszczyk M, Lee HJ, Olivieri JE, Leapman MS
- **匹配关键词：** `classification, llm, llms, gpt, large language models, automated`
- **摘要核心细节：** **目的：** 评估大语言模型（LLMs）在前列腺放射治疗前使用直肠周围水凝胶间隔物（SpaceOAR）相关不良事件（AEs）分析中的表现。**方法：** 检索 FDA MAUDE 数据库中与“SpaceOAR”相关的报告。最初通过人工提取了 97 份报告，对其不良事件问题、对放疗时间的影响以及基于不良事件常用术语标准（CTCAE）的严重程度进行分类。我们对比了 3 个大语言模型家族与人工提取的准确率差异，并使用表现最好的 LLM 对 2015 年 1 月至 2024 年 12 月间所有可用的 SpaceOAR MAUDE 报告（n = 1455）进行分类。**结果：** GPT-4o 表现最优，综合得分为 4.96（σ = 0.00526），极其接近人工评审员的 4.99（σ = 0.216）。在全部 1455 份报告中，GPT-4o 揭示出最常见的主要问题是水凝胶位置不当（58.7%）、感染/炎症/脓肿（10.4%）、瘘管（7.1%）以及直肠溃疡（4.7%）。入住 ICU 和死亡的报告率分别为 0.1% 和 0.3%。**结论：** 研究结果表明 LLMs 在自动整理器械相关不良事件这一耗时工作上具有巨大潜力。SpaceOAR 相关的严重 AE 凸显了潜在的安全性隐患，需进行持续的动态监测。

### 3. AutoQUEST：MAUDE 研究中用于自动问题生成与验证的思维链流水线
- **期刊与日期：** Stud Health Technol Inform (2025年8月7日)
- **PMID：** [40775892](https://pubmed.ncbi.nlm.nih.gov/40775892)
- **作者：** Hua L, Gong Y
- **匹配关键词：** `llms, large language models, automated`
- **摘要核心细节：** 使用 MAUDE 数据库构建研究问题时，通常会受到数据预处理和分析的困扰。为此，本研究提出了 AutoQUEST——一个基于 Python 的提示词流水线，利用大语言模型（LLMs）和思维链（CoT）来实现研究问题的自动化生成。在 5 个独立的测试用例中，AutoQUEST 生成有效研究问题的准确率达到了 100%，且数据库查询执行成功率处于 75% 至 100% 之间。该技术简化了研究问题的提出过程，降低了数据提取和转换的技术壁垒，提高了医疗器械患者安全研究的效率。

### 4. 揭示 MAUDE 数据库中的内窥镜手术事件：一种 ETL-LLM 混合方法
- **期刊与日期：** Stud Health Technol Inform (2025年6月26日)
- **PMID：** [40588888](https://pubmed.ncbi.nlm.nih.gov/40588888)
- **作者：** Shi Y, Yang E, Gong Y
- **匹配关键词：** `llm, llms, large language model, etl`
- **摘要核心细节：** 依赖 MAUDE 数据库开展患者安全研究的增加，强调了建立和标准化事件报告提取与分析方法的关键性。缺乏可复现的方法会导致对不良事件的理解不一致，降低临床警示作用。因此，本研究提出了结合大语言模型的 ETL（提取-转换-加载）流水线来标准化报告的识别与解析。以胃肠内窥镜夹报告为例，ETL-LLM 方法展示了在提取和分析分类与叙述性报告方面的有效性，揭示了患者并发症、手术过程及器械使用等方面的深度洞察。这种创新的透明方法展示了其及时向临床医生提供警示并推动基于开源数据库安全研究的潜力。

### 5. 利用数据流水线与大语言模型推进患者安全事件研究
- **期刊与日期：** Stud Health Technol Inform (2025年5月15日)
- **PMID：** [40380434](https://pubmed.ncbi.nlm.nih.gov/40380434)
- **作者：** Shah F, Yu Y, Shi Y, Gong Y
- **匹配关键词：** `llm, large language model, etl`
- **摘要核心细节：** 使用开源 MAUDE 数据库的研究常常因为数据提取与清洗方法不够清晰而导致复现性较差。本项目利用 openFDA API 和标准化的 MAUDE-ETL 提取清洗流水线，探讨了如何使用大语言模型（LLM）来分析医疗器械报告（MDR）中的自由文本叙述，从而提升事件归类的准确性与效率。以胃肠内窥镜黏膜切除术相关的 MDR 数据为载体展示了该方法，并指出了该框架在其他器械分类中的应用潜力。

### 6. 利用大语言模型理解 MAUDE 报告中的叙事文本
- **期刊与日期：** Stud Health Technol Inform (2025年4月8日)
- **PMID：** [40200473](https://pubmed.ncbi.nlm.nih.gov/40200473)
- **作者：** Shi Y, Gong Y
- **匹配关键词：** `llms, gpt, large language models`
- **摘要核心细节：** 利用 MAUDE 数据库调查医疗器械不良事件的兴趣日益浓厚。然而，这些报告中的叙述性文本在很大程度上仍未被开发，许多有价值的临床洞察未被利用。为了弥补这一差距，本研究使用 OpenAI 的 GPT-4-turbo 模型来分析和解读这些文本。我们聚焦于涉及内窥镜夹的 MAUDE 报告，成功识别出未被编码的手术步骤并挖掘出了其他临床洞察。这种方法展示了 LLM 处理自由文本叙述的潜力，是比以往人工标注更高效、成本更低的选择。

### 7. 开发基于生成式 AI 的 MAUDE 数据库分析问答机器人
- **期刊与日期：** Stud Health Technol Inform (2024年8月22日)
- **PMID：** [39176609](https://pubmed.ncbi.nlm.nih.gov/39176609)
- **作者：** Yu Y, Shi Y, Feng Y, Gong Y
- **匹配关键词：** `ai, gpt, generative ai`
- **摘要核心细节：** 本文展示了一个旨在简化 MAUDE 数据库医疗器械不良事件检索和理解的问答机器人。该机器人由生成式 AI 技术驱动，支持计数和搜索查询。它利用 openFDA API 并采用 GPT-4 模型来解析用户的自然语言查询、自动生成相应的 API 调用链接，并总结不良事件报告，同时提供原始报告的下载。通过使用 query-URL 键值对的 Few-shot 样本训练，API 调用生成的准确率显著提升。此外，生成的摘要质量也得到了领域专家的高分肯定。

### 8. 通过 GPT-4 和因果可视化增强 MAUDE 数据库的实用性
- **期刊与日期：** Stud Health Technol Inform (2024年7月24日)
- **PMID：** [39049270](https://pubmed.ncbi.nlm.nih.gov/39049270)
- **作者：** Yu Y, Shi Y, Feng Y, Gong Y
- **匹配关键词：** `gpt, large language model, automated`
- **摘要核心细节：** MAUDE 数据库是了解医疗器械及健康信息技术（Health IT）故障和不良事件的宝贵资源。然而，其庞大的体量和复杂结构带来了挑战。为此，我们开发了基于 GPT-4 的自动分析流水线，以极少的人工标注实现了安全事件的提取、归类和可视化。在对 2011-2021 年间 4459 份结肠镜检查报告的分析中，我们将事件归为操作、人为因素及器械相关三类。利用鱼骨图（Ishikawa diagrams）将数据在向量数据库中进行可视化及相似度检索对比。该方案显著降低了人工标注的负担。

---

## 分类二：用于分类的传统 NLP 与机器学习（2016-2026年）
这些研究侧重于构建分类模型（如随机森林、支持向量机、LSTM、BERT），以自动识别和分类各类不良事件。

### 1. 体外循环过程中氧合器失效及其相关的损伤模式研究
- **期刊与日期：** Perfusion (2026年5月21日)
- **PMID：** [42166660](https://pubmed.ncbi.nlm.nih.gov/42166660)
- **作者：** Bradshaw JC, Bradshaw A, Agarwal R, Dontu V, Shirodkar S, Tran C, Lawton JS, Pasrija C, Wierschke C, Lester L
- **匹配关键词：** `natural language processing, nlp, supervised`
- **摘要核心细节：** **背景：** 体外循环（CPB）氧合器在术中提供气体交换。虽然罕见，但其失效会导致灾难性的发病率和死亡率。本研究旨在通过 MAUDE 报告总结 CPB 氧合器失效的规律。**方法：** 回顾性分析了 2015 年 4 月至 2025 年 4 月间导致伤害或死亡的 CPB 氧合器失效报告。对叙述性文本进行监督式自然语言处理（NLP）以提取临床主题。**结果：** 共有 388 起事件符合标准（279 起受伤，109 起死亡）。通过监督式 NLP 发现，某些特定厂家的设备在死亡案例中占了不成比例的极高比重。

### 2. 输尿管软镜相关患者损伤：基于 FDA MAUDE 报告的横断面分析与可靠性验证的损伤分类体系
- **期刊与日期：** J Endourol (2026年5月20日)
- **PMID：** [42159167](https://pubmed.ncbi.nlm.nih.gov/42159167)
- **作者：** Akhmetov D, Oraz SS, Kambarov DT, Bolatov A
- **匹配关键词：** `classification, classifying`
- **摘要核心细节：** **背景：** 软性输尿管镜不良事件不断增加，但缺乏标准化的损伤分类法限制了研究的复现。**方法：** 对 2020-2025 年间 532 份输尿管镜受伤/死亡 MAUDE 报告进行横断面分析。构建并评估了一个可复现的损伤分类体系。**结果：** 分类体系具有较高的评分者间信度（κ = 0.82）。创伤性（31.1%）和感染性（30.4%）损伤占主导地位。大多数事件（69.4%）被评定为中度或重度。虽然断裂/脱落是最常见的机械因素，但 48% 的报告缺少关键细节导致难以分类。 reprocessing/污染相关的报告中重度事件比例极高。**结论：** 验证过的损伤分类体系使被动监管库中的伤害表型分析变得可复现，但仍有近半数报告因为细节有限无法进行病因归因。

### 3. 预装式与手动装载式人工晶体推注失败模式：基于 FDA 器械报告的分析
- **期刊与日期：** J Cataract Refract Surg (2026年5月18日)
- **PMID：** [42153648](https://pubmed.ncbi.nlm.nih.gov/42153648)
- **作者：** Hecht I, Tuuminen R, Kanclerz P, Sella R
- **匹配关键词：** `natural language processing, classification, automated`
- **摘要核心细节：** **方法：** 检索了 2016-2025 年间描述术中人工晶体（IOL）装载、推注或定位问题的报告。使用自动化自然语言处理辅助对自由文本叙述进行清洗和特征分类。**结果：** 在符合标准的 14,460 份术中报告中，10,567 份涉及预装式系统，3,893 份涉及手动装载式。手动装载式系统显示出更高的人工晶体损伤及装载问题，而预装式系统则表现出更高的推注失败率及材料异常。**结论：** NLP 成功提取并对比了两种主流人工晶体装载系统的临床失效特征。

### 4. FDA 批准的 AI 医疗器械的利益与风险报告现状
- **期刊与日期：** JAMA Health Forum (2025年9月5日)
- **PMID：** [41004181](https://pubmed.ncbi.nlm.nih.gov/41004181)
- **作者：** Lin JC, Jain B, Iyer JM, Rola I, Srinivasan AR, Kang C, Patel H, Parikh RB
- **匹配关键词：** `machine learning, artificial intelligence, ai, classification`
- **摘要核心细节：** **目的：** 探讨 FDA 批准的 AI/ML 医疗器械的临床试验与上市后不良事件。**方法：** 关联分析了 FDA 审批数据库、MAUDE 数据库以及医疗器械召回数据库中 1995-2023 年间 cleared 的所有 691 款 AI/ML 器械。**结果：** 发现器械审批决策摘要往往缺乏训练样本量（53.3%）和人口统计信息（95.5%）。只有 6 款器械有随机临床试验数据。在 MAUDE 中共确定了 489 起涉及 AI 器械的不良事件，主要因软件问题导致。**结论：** 这表明目前尚缺乏针对 AI/ML 医疗器械安全与风险的标准化监管体系，亟需专用的 post-market 监测通道。

### 5. 可膨胀但代价是什么？373 例真实椎体肿瘤切除网笼（Corpectomy Cages）不良事件失效模式分析
- **期刊与日期：** Spine (2025年9月4日)
- **PMID：** [40905304](https://pubmed.ncbi.nlm.nih.gov/40905304)
- **作者：** Schneider D, Brown EDL, Toscano D, Obeng-Gyasi B, Elsamadicy AA, Sciubba DM, Lo SL
- **匹配关键词：** `artificial intelligence, ai, classification`
- **摘要核心细节：** 利用 AI 辅助分类技术，对 MAUDE 数据库中 373 例涉及可膨胀椎体网笼的不良事件报告进行处理。结果发现，置入器械问题是最常见的安全事件（34.3%），而严重的机械失效如终板塌陷（80%）和器械移位（77.8%）具有极高的手术翻修率。

### 6. 规范上市后 AI/ML 医疗器械的通用治理框架
- **期刊与日期：** NPJ Digit Med (2025年5月31日)
- **PMID：** [40450160](https://pubmed.ncbi.nlm.nih.gov/40450160)
- **作者：** Babic B, Glenn Cohen I, Stern AD, Li Y, Ouellet M
- **匹配关键词：** `machine learning, artificial intelligence, ai`
- **摘要核心细节：** 本研究对 FDA 利用 MAUDE 数据库对合法上市的 AI/ML 医疗器械进行上市后监管的情况进行了系统性评估。分析了 2010-2023 年间批准的约 950 款 AI/ML 设备的 adverse events，指出当前的报告体系在评估 AI/ML 特殊安全性（如算法漂移等）方面存在缺陷，并提出了改革建议。

### 7. 利用人工智能提升医疗器械上市后监管：以输液泵为例
- **期刊与日期：** Technol Health Care (2025年3月)
- **PMID：** [40105162](https://pubmed.ncbi.nlm.nih.gov/40105162)
- **作者：** Merdović N, Spahić L, Hundur M, Pokvić LG, Badnjević A
- **匹配关键词：** `machine learning, artificial intelligence, predictive`
- **摘要核心细节：** 本文展示了如何通过分析 MAUDE 数据来改进输液泵的维护和监测策略。其终极目标是利用机器学习建立预测模型，将现有的“发生后响应式”器械治理转变为“主动预测式”治理。

### 8. 用于预测 FDA 医疗器械召回的机器学习算法
- **期刊与日期：** West J Emerg Med (2025年1月)
- **PMID：** [39918157](https://pubmed.ncbi.nlm.nih.gov/39918157)
- **作者：** Barbosa Slivinskis V, Agi Maluli I, Seth Broder J
- **匹配关键词：** `machine learning, algorithm, algorithms`
- **摘要核心细节：** 旨在评估使用公共数据训练的机器学习算法预测 FDA 器械召回的灵敏度和特异性。我们构建了随机森林回归模型，自动检索 Google 趋势和 PubMed 的数据特征。测试显示，算法能以高达 90% 的灵敏度和 100% 的特异性，提前 3 到 12 个月成功预测医疗器械的召回状态。

### 9. 良性前列腺增生手术期间的不良事件是否与器械相关？MAUDE 数据库系统回顾
- **期刊与日期：** Urologia (2024年5月)
- **PMID：** [38520298](https://pubmed.ncbi.nlm.nih.gov/38520298)
- **作者：** Heidenberg DJ, Nethery E, Wymer KM, Judge N, Cheney SM, Stern KL, Humphreys MR
- **匹配关键词：** `classification`
- **摘要核心细节：** 检索 2018-2021 年间良性前列腺增生（BPH）微创及传统手术的相关不良事件。根据 Clavien-Dindo 分级体系，建立了一个 Level I-IV 的分类模式，以将事件划分为“器械缺陷驱动”与“非器械因素驱动（操作原因）”。分析共识别出 873 起事件。

### 10. 自动识别涉及机器学习医疗器械的安全事件
- **期刊与日期：** Stud Health Technol Inform (2024年1月25日)
- **PMID：** [38269880](https://pubmed.ncbi.nlm.nih.gov/38269880)
- **作者：** Wang Y, Lyell D, Coiera E, Magrabi F
- **匹配关键词：** `machine learning, classifier, classifiers, classification, automated`
- **摘要核心细节：** 针对 MAUDE 中稀疏的 ML 医疗器械故障报告，本研究开发了自动文本分类器。我们基于四种特征集构建了分层分类器。结果发现，结合了设备通用名称的分类器在测试集（F1 = 85%）和外部独立验证集（精确度 = 100%）上均表现优异，可直接部署以实时监测 MAUDE 库中的新兴 ML 设备故障。

### 11. 血管闭合器（Angio-Seal）的真实世界安全体验：基于 MAUDE 的分析
- **期刊与日期：** J Endovasc Ther (2025年10月)
- **PMID：** [38110358](https://pubmed.ncbi.nlm.nih.gov/38110358)
- **作者：** Ahrari A, Healy GM, Min A, Alkhalifah F, Oreopoulos G, Teng Tan K, Jaberi A, Rajan DK, Mafeld S
- **匹配关键词：** `classification`
- **摘要核心细节：** 对 2019-2020 年间 715 起涉及 Angio-Seal 的安全事件进行特征提取与分类。使用 CIRSE 评分标准，将失效模式归为损坏器械的盲用（43.4%）、部署失败（20.1%）等。大多数事件为轻微出血，可用徒手压迫止血，但也指出了漏报和不归还受损设备对溯源带来的负面影响。

### 12. 证据临床工程：应用自然语言处理识别与分类健康信息技术（Health IT）不良事件
- **期刊与日期：** Heliyon (2023年11月)
- **PMID：** [37954315](https://pubmed.ncbi.nlm.nih.gov/37954315)
- **作者：** Luschi A, Nesi P, Iadanza E
- **匹配关键词：** `natural language processing, nlp, artificial intelligence, classification`
- **摘要核心细节：** 本研究构建了一个用于识别 Health IT 软件相关故障的分类模型。微调并测试了 pre-trained 的 ClinicalBERT 模型，在由临床专家手动标注的 3075 例 MAUDE 自由文本报告上进行评估，实现了对日益增长的 Health IT 不良事件的精准提取。

### 13. 基于 FDA MAUDE 数据库的 Jetstream 斑块旋切系统治疗外周动脉疾病安全性评估
- **期刊与日期：** J Endovasc Ther (2025年8月)
- **PMID：** [37750495](https://pubmed.ncbi.nlm.nih.gov/37750495)
- **作者：** Min A, Alkhalifa F, Ahrari A, Healy G, Jaberi A, Tan KT, Mafeld S
- **匹配关键词：** `classification`
- **摘要核心细节：** 分析了 2019-2021 年间 500 起涉及 Jetstream 旋切系统的报告。将不良事件分类为患者并发症（栓塞、血管穿孔等）和设备本身机械故障（刀片无法旋转、抽吸丢失等），并应用 CIRSE 标准评估预后。

### 14. 主动脉内气囊泵（IABP）特征性不良事件分析：基于 2016-2021 年 FDA MAUDE 数据库
- **期刊与日期：** Cardiovasc Revasc Med (2023年11月)
- **PMID：** [37302952](https://pubmed.ncbi.nlm.nih.gov/37302952)
- **作者：** Schwarzman LS, Ishaaya EC, Patel D, Megowan N, Thomas JL
- **匹配关键词：** `classification`
- **摘要核心细节：** 对 2795 起 IABP 相关不良事件分类发现，设备本身故障占 91.4%，而患者并发症及死亡极低。主要失效模式为球囊破损和光纤校准错误。

### 15. 良性前列腺增生微创手术相关并发症的 MAUDE 数据库回顾
- **期刊与日期：** World J Urol (2023年7月)
- **PMID：** [37222779](https://pubmed.ncbi.nlm.nih.gov/37222779)
- **作者：** Porto JG, Arbelaez MCS, Blachman-Braun R, Bhatia A, Bhatia S, Satyanarayana R, Marcovich R, Shah HN
- **匹配关键词：** `classification`
- **摘要核心细节：** 分析了 692 份涉及 Rezum 等五类微创手术的报告。应用 Gupta 分类系统对严重度分级，发现多数为轻度，但 Urolift 和 TUMT 重度并发症（如血肿、败血症）比率显著偏高。

### 16. 不仅仅是算法：FDA 报告的涉及机器学习医疗器械的安全事件分析
- **期刊与日期：** J Am Med Inform Assoc (2023年6月20日)
- **PMID：** [37071804](https://pubmed.ncbi.nlm.nih.gov/37071804)
- **作者：** Lyell D, Wang Y, Coiera E, Magrabi F
- **匹配关键词：** `machine learning, artificial intelligence, algorithms`
- **摘要核心细节：** 系统性分析了 2015-2021 年间 266 起 ML 医疗器械不良事件。结果发现，绝大多数问题（93%）源于输入数据质量缺陷（82%，如数据采集故障导致算法失效）；然而，由于操作者误用导致的使用问题虽然较少（7%），但其致伤风险却高出 4.2 倍。这表明 ML 监管需要考虑包含“人机交互”的系统性框架。

### 17. 软性膀胱镜重复使用及污染的不良事件分析
- **期刊与日期：** Can J Urol (2022年12月)
- **PMID：** [36495577](https://pubmed.ncbi.nlm.nih.gov/36495577)
- **作者：** Lee J, Kaplan-Marans E, Jivanji D, Tennenbaum D, Schulman A
- **匹配关键词：** `classification`
- **摘要核心细节：** 检索了 reusable 膀胱镜的不良事件。通过人工与算法提取，对器械消毒不彻底导致的微生物交叉污染和尿路感染进行了特征归类。

### 18. 用于食管功能测试的器械评估报告
- **期刊与日期：** VideoGIE (2022年1月)
- **PMID：** [35059533](https://pubmed.ncbi.nlm.nih.gov/35059533)
- **作者：** Pannala R 等
- **匹配关键词：** `classification`
- **摘要核心细节：** 总结了高分辨率食管测压（HRM）等器械在 MAUDE 中的安全故障。提及了业界通用的芝加哥分类（Chicago classification）诊断架构。

### 19. 应用自然语言处理评估 hysteroscopic 避孕装置取出不良事件报告
- **期刊与日期：** Pharmacoepidemiol Drug Saf (2022年4月)
- **PMID：** [34919294](https://pubmed.ncbi.nlm.nih.gov/34919294)
- **作者：** Mao J, Sedrakyan A, Sun T, Guiahi M, Chudnoff S, Kinard M, Johnson SB
- **匹配关键词：** `natural language processing, nlp, algorithm, predictive`
- **摘要核心细节：** 开发了 NLP 标注提取模型，从 2005-2018 年间 Essure 避孕环取出相关的 MAUDE 报告中自动抽取 6 类不良事件特征，评估显示模型达到了极高的 F1-score，为被动报告库的不良事件挖掘提供了一套规范的标注与分析技术路线。

### 20. 美国 FDA 医疗器械不良事件报告中非死亡类别中的死亡事件漏报分析
- **期刊与日期：** JAMA Intern Med (2021年9月1日)
- **PMID：** [34309624](https://pubmed.ncbi.nlm.nih.gov/34309624)
- **作者：** Lalani C, Kunwar EM, Kinard M, Dhruva SS, Redberg RF
- **匹配关键词：** `natural language processing, algorithm`
- **摘要核心细节：** **重要性：** 尽管 FDA 要求若器械可能导致患者死亡必须在类别中标记为“死亡”，但大量事件存在分类错误。**方法：** 我们在 1991-2020 年间的 MAUDE 数据库中，应用 NLP 算法自动提取描述文本中包含“患者死亡”或“expired”等但在报告大类中却被归为“受伤”或“器械故障”的记录，随后进行人工核实。**结果：** 算法锁定了 290,141 份描述中提及死亡的报告。其中 47.9% 实际上被漏分或误分类到了故障、受伤或其他类别中。人工随机抽样核实表明，真正的死亡事件漏标率高达 17% 至 23%。**结论：** 许多涉及死亡的不良事件被严重归类错误，由于 FDA 通常只例行审查标记为“死亡”的报告，这一漏洞极大削弱了医疗器械的安全预警作用。

### 21. 利用混合深度学习模型构建健康信息技术（Health IT）不良事件数据库
- **期刊与日期：** J Biomed Inform (2020年10月)
- **PMID：** [32916305](https://pubmed.ncbi.nlm.nih.gov/32916305)
- **作者：** Kang H, Gong Y
- **匹配关键词：** `deep learning`
- **摘要核心细节：** 设计不良的 Health IT 系统会引发患者安全隐患。为了从海量 MAUDE 数据中自动剥离并提取出属于 Health IT 的故障记录，本研究对比了多种单一和混合深度学习分类器（结合了 LR、CNN 和 Hierarchical RNN）。模型实现了 0.903 的准确率，并据此建立了拥有 48,997 份记录的首个公开 Health IT 安全事件数据库。

### 22. SAGES TAVAC 共聚焦激光显微内镜（CLE）的安全与有效性分析
- **期刊与日期：** Surg Endosc (2021年5月)
- **PMID：** [32405892](https://pubmed.ncbi.nlm.nih.gov/32405892)
- **作者：** Al-Mansour MR 等
- **匹配关键词：** `classification`
- **摘要核心细节：** 对 PubMed 和 FDA MAUDE 数据库中涉及共聚焦显微内镜的医疗器械故障及患者损伤报告进行了梳理，以评定该新技术的安全特征和诊断准确度分级。

### 23. 美国 FDA 2009-2019 年围产期死亡案例中未识别的主体心率干扰：一个关键的患者安全问题
- **期刊与日期：** BMC Pregnancy Childbirth (2019年12月16日)
- **PMID：** [31842798](https://pubmed.ncbi.nlm.nih.gov/31842798)
- **作者：** Kiely DJ, Oppenheimer LW, Dornan JC
- **匹配关键词：** `algorithms`
- **摘要核心细节：** 胎儿监护仪中的自相关算法可能会将母亲的脉搏错当成胎儿心率输出，从而掩盖已发生死胎或胎儿窘迫的事实。我们通过在 MAUDE 数据库中检索 10 年间的相关“死亡”事件并进行临床文本分析，发现并证实了 47 例由该心率信号干扰导致的围产期死亡，并建议修改产科临床指南以强制验证胎儿生命迹象。

### 24. 经子宫动脉栓塞术治疗肌瘤的相关不良事件分析
- **期刊与日期：** J Minim Invasive Gynecol (2019年5-6月)
- **PMID：** [30016750](https://pubmed.ncbi.nlm.nih.gov/30016750)
- **作者：** Armstrong AA, Kroener L, Brower M, Al-Safi ZA
- **匹配关键词：** `classification`
- **摘要核心细节：** 回顾性检索 20 年间与子宫动脉栓塞相关的 193 份 MAUDE 报告。分析并将事件分类为疼痛（35.2%）、操作失误（19.2%）、翻修与切除率等，为临床医生提供了关于器械意外风险的重要数据。

### 25. 从 FDA MAUDE 数据库中探索健康信息技术事件的检索策略
- **期刊与日期：** Stud Health Technol Inform (2018年)
- **PMID：** [29857426](https://pubmed.ncbi.nlm.nih.gov/29857426)
- **作者：** Yao B, Kang H, Wang J, Zhou S, Gong Y
- **匹配关键词：** `classification`
- **摘要核心细节：** 以往的 Health IT 检索过度依赖品牌和厂家关键字，本研究引入并探索了 Classification Product Code 这一分类代码字段。通过与文本特征的结合，绘制了产品代码的分布图谱，极大优化了 MAUDE 中 HIT 事件的二级检索召回率。

### 26. 经导管瓣膜介入术的注册研究数据与 FDA MAUDE 安全监测数据的匹配度对比
- **期刊与日期：** Am Heart J (2018年4月)
- **PMID：** [29653650](https://pubmed.ncbi.nlm.nih.gov/29653650)
- **作者：** Galper BZ 等
- **匹配关键词：** `natural language processing`
- **摘要核心细节：** 探讨了主动登记库（TVT）与被动报告库（MAUDE）之间的统计偏差。应用自然语言处理技术提取并归纳了数千份心脏瓣膜植入报告，通过回归分析证实，利用 NLP 从 MAUDE 被动报告库中提取的各类不良反应发生率，与官方高成本的 TVT 主动登记库数据高度相关（R² > 0.96），表明自动 NLP 上市后监测在经济性和实效性上的巨大优势。

### 27. 调查与枕神经刺激相关的并发症：一项 MAUDE 研究
- **期刊与日期：** Neuromodulation (2018年4月)
- **PMID：** [29345415](https://pubmed.ncbi.nlm.nih.gov/29345415)
- **作者：** Doran J, Ward M, Ward B, Paskhover B, Umanoff M, Mammis A
- **匹配关键词：** `classification`
- **摘要核心细节：** 分析 10 年间涉及枕神经刺激的 1233 起事件。通过对患者主诉和硬件失效模式（电极移位、破损等）进行分类，为缺乏该领域长期临床试验的临床医生提供了真实世界的并发症预期参考。

### 28. 经皮肾镜取石术（PCNL）期间的器械相关不良事件分析
- **期刊与日期：** J Endourol (2017年10月)
- **PMID：** [28830243](https://pubmed.ncbi.nlm.nih.gov/28830243)
- **作者：** Patel NH, Schulman AA, Bloom JB, Uppaluri N, Phillips JL, Konno S, Choudhury M, Eshghi M
- **匹配关键词：** `classification`
- **摘要核心细节：** 收集了 10 年间 PCNL 手术涉及的 218 起器械故障。采用标准化分类系统评定，81% 为轻微。回归分析表明球囊扩张导管的严重并发症发生率最高。此外，高达 54.8% 的器械故障归因于操作者误用，显示出医生培训的重要性。

### 29. 开发用于检验医疗器械不良事件的分类方案：以达芬奇手术系统为例
- **期刊与日期：** J Endourol (2017年1月)
- **PMID：** [27806637](https://pubmed.ncbi.nlm.nih.gov/27806637)
- **作者：** Gupta P, Schomburg J, Krishna S, Adejoro O, Wang Q, Marsh B, Nguyen A, Genere JR, Self P, Lund E, Konety BR
- **匹配关键词：** `classification, classifying`
- **摘要核心细节：** 收集了 2009-2012 年间达芬奇手术机器人的 2837 起安全事件。邀请 14 名外科专家合作构建了一套严重度及器械因果相关性分类体系（信度中等，Kappa = 0.52），并据此指出了不同科室手术以及不同机械臂组件的不良事件严重度分布规律。

---

## 分类三：临床器械安全与高级统计挖掘（过去 10 年）
这些研究结合了传统的数据挖掘技术、图表统计和横断面比对研究，旨在量化评估临床常用重点医疗器械在真实世界使用中的失效模式与安全性。

### 1. 眼科植入物上市后监管：真实世界证据（RWE）的作用与技术演进
- **期刊与日期：** Expert Rev Med Devices (2025年12月)
- **PMID：** [41123186](https://pubmed.ncbi.nlm.nih.gov/41123186)
- **作者：** Gurnani B, Kaur K
- **摘要核心细节：** 本文献综述探讨了眼科植入物（人工晶体、青光眼引流阀等）上市后监管从传统的“被动上报”模式向基于“真实世界证据（RWE）”的主动注册登记系统的演变。作者重点强调了引入人工智能数据挖掘分析技术，以及全球监管协调在早期快速发现安全性“微弱信号”中的核心贡献。

### 2. 机器人脊柱手术的隐伤：1346 起真实事件分析显示平均延时达 58 分钟并削弱了医院的财务可行性
- **期刊与日期：** Spine J (2026年1月)
- **PMID：** [40628307](https://pubmed.ncbi.nlm.nih.gov/40628307)
- **作者：** Schneider D, Brown EDL, Elsamadicy AA, Sciubba DM, Lo SL
- **摘要核心细节：** **目的：** 评估器械安全事故对医疗机构财务和手术效率的负面冲击。**方法：** 收集 2016-2025 年间报告至 MAUDE 数据库的 1,346 起机器人脊柱手术（MazorX 及 Globus）不良事件，通过建立手术延时、工作流中断参数，引入了 189 种医院财务模型的模拟。**结果：** 不良事件导致单次手术平均延误高达 58.1 分钟，其中 34.4% 的情况下不得不完全弃用机器人回归传统手术。尽管厂商以精度为主要价值主张，但 66.4% 的并发症恰恰与精度偏差相关。财务模拟显示，在目前器械高故障率和高昂运营成本下，所有 189 种财务模型在机器人使用寿命内都无法实现成本回收。

### 3. 全踝关节置换术后聚乙烯衬垫相关翻修事件的统计对比分析
- **期刊与日期：** Foot Ankle Int (2023年1月)
- **PMID：** [36461676](https://pubmed.ncbi.nlm.nih.gov/36461676)
- **作者：** Jiang H, Wu L, Randsborg PH, Houck J, Sun L, Marine M, Chow M, Peluso J, Peat R
- **摘要核心细节：** 利用文本挖掘和人工二次审查，对 1991-2020 年间 MAUDE 中全踝关节置换涉及聚乙烯衬垫失效的不良事件（共 3114 起）进行分类对比。结果发现，移动平台（MB）设计的聚乙烯破损率（11.3%）和早期翻修翻转率显著高于固定平台（FB）设计的器械。

### 4. 胰岛素给药非辅助连续血糖监测的安全性：基于海量 complaints 的隐患分析
- **期刊与日期：** J Diabetes Sci Technol (2017年7月)
- **PMID：** [28540756](https://pubmed.ncbi.nlm.nih.gov/28540756)
- **作者：** Shapiro AR
- **摘要核心细节：** 近期 FDA 批准了连续血糖监测仪（CGM）可作为非辅助胰岛素给药的依据（不再需要常规指尖血校准）。然而，本研究对 2015 年以来的 MAUDE 数据库执行了文本数据挖掘，发现其中隐藏了超过 25,000 例由于传感器失准导致的投诉，其中不乏错误注射引发的重度休克。强调了单纯依靠电子连续监测仪而抛弃传统指血确认对患者安全带来的高风险。
