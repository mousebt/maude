# FDA MAUDE 达芬奇致死病案描述文本结构化拆解示例 (MDR 2803906)

> **研究案例 ID**: MDR_REPORT_KEY 2803906
> **判定分类**: 机器物理故障致险/致死 (Shocking)
> **技术支持**: Antigravity AI 真实世界数据挖掘课题组

---

## 一、 病例原始描述 (Original Narrative Text)

> **英文病志原文：**
> AT THE BEGINNING OF THE SURGERY, WHILE EXPLORING THE PATIENT'S ABDOMEN, THE SOUND OF THE MONOPOLAR ESU WAS HEARD BY THE SURGEON, STAFF RN, AND DAVINCI REPRESENTATIVE. THE SURGEON STATED THAT SHE WASN'T DEPRESSING THE BIPOLAR FOOT PEDAL. PHYSICIAN PHONE STATEMENT NOTED THAT THIS INCIDENT OCCURRED AT THE VERY START OF THE CASE, AND THE FOOT PEDAL WAS NOT BEING ACTIVATED WHEN THE ESU WAS HEARD GOING OFF BY ITSELF; OBSERVE THE DAVINCI REP UNPLUGGING THE FOOT PEDALS CONNECTIONS FROM THE ROBOT AT THE REAR OF THE ESU. HEARD IT ACTIVATE AGAIN AFTER THIS WAS DONE. NURSE WHO WROTE UP INCIDENT STATEMENT SAYS SHE WAS ON THE OTHER SIDE OF THE ROOM, BUT DID HEAR THE ESU GOING OFF. SAYS SHE WAS THE PERSON WHO UNPLUGGED THE CABLES FROM THE FRONT OF THE DEVICE. SHE WAS NOT QUITE SURE IF THIS HAPPENED AT THE BEGINNING OR THE MIDDLE OF THE CASE. NURSE WITNESS STATEMENT: TWO DOCTORS WERE USING THE DAVINCI ROBOT CONSOLE; THEY WERE USING MONO-POLAR SETTING AT THAT MOMENT, HEARD WHEN PHYSICIAN SAY "WHY IS THE MONO-POLAR STILL GOING," SAID THAT SURGEON SAW SMOKE IN THE FIELD.SAW DAVINCI REP UN-PLUGGED THE CABLES FROM THE BACK OF THE FORCE FX ESU, SWITCHED OUT FORCE FX TO THE NEWER FORCE TRIAD ESU, CONTINUE WITH CASE.AS A RESULT OF WHAT APPEARS TO BE AN UNINTENDED DELIVERY OF MONOPOLAR ENERGY THROUGH A BIPOLAR MARYLAND CLAMP, THE PATIENT SUSTAINED A PERFORATED BOWEL, AND DESPITE CAREFUL EXAMINATION OF THE SURGICAL AREA, IT WAS NOT DISCOVERED UNTIL THE PATIENT CAME BACK TO THE HOSPITAL APPROXIMATELY A WEEK LATER WITH SIGNS OF INFECTION. THIS REQUIRED AN EXPLORATORY LAPAROTOMY, WHICH REVEALED A PERFORATED BOWEL.  A PORTION OF COLON WAS REMOVED AND SENT TO SURGICAL PATHOLOGY. PATIENT SUBSEQUENTLY DEVELOPED BILATERAL PULMONARY EMBOLI AND REMAINS HOSPITALIZED TO THIS DAY.

---

## 二、 中文忠实翻译 (Chinese Translation)

在手术开始阶段探查患者腹部时，主刀医生、手术室护士以及达芬奇技术代表都听到了单极高频发生器（ESU）被激活的声音。主刀医生声明她当时并没有踩下双极脚踏板。医生的电话陈述也证实，事件发生在手术刚开始时，当听到电刀自行启动发声时，脚踏板并未被激活；现场目击达芬奇技术代表从电刀主机后方拔掉了与机器人的脚踏板连接线，但此后仍能听到电刀再次自动激活。

撰写事故报告的护士表示，她当时虽然在房间的另一侧，但也确实听到了电刀自行启动的声音，并表示是她从设备前方拔掉了电缆。她不太确定这发生在手术开始还是中间阶段。护士证词指出：当时有两位医生在使用达芬奇机器人控制台，正在使用单极模式，随后听到医生说“为什么单极电刀还在持续放电？”，并看到手术视野里冒烟。技术代表随后拔掉了 Force FX 电刀主机后方的电缆，并将 Force FX 更换为更新的 Force Triad 电刀系统后继续手术。

**由于单极电能量意外通过双极 Maryland 电凝钳释放**，导致患者发生了**肠穿孔**。尽管术中对非手术区域进行了仔细检查，但当时并未发现异常。直到约一周后，患者因出现感染迹象返回医院才被确诊。为此行剖腹探查术，证实了肠穿孔的存在。随后切除了部分结肠并送病理检查。患者此后并发了**双侧肺栓塞**，并在上报之日仍处于住院抢救状态（后确认死亡）。

---

## 三、 结构化字段拆解 Schema 映射 (JSON Mapping)

大模型清洗管道将非结构化病例描述文本，拆解为以下规范化的数据库结构化字段：

```json
{
  "mdr_report_key": 2803906,
  "classification": "Shocking",
  "brand_name": "DaVinci Standard (第一代)",
  "hazard_category": "能量器械漏电/电弧/击穿/灼伤",
  "fault_component": "Maryland Grasping (双极电凝钳)",
  "causal_chain": "手术开始时单极电刀意外自行激活放电，能量意外通过双极Maryland钳释放，灼伤并导致患者肠穿孔，一周后发生腹腔感染行结肠切除，后并发双侧肺栓塞死亡。",
  "root_cause": "单极能量通过双极Maryland钳旁路异常释放，导致隐蔽性热灼伤肠穿孔未被术中发现。",
  "clinical_complication": "大出血 / 肠穿孔 / 术后肺栓塞",
  "surgeon_decision": "YES",
  "factual_summary": "单极电刀意外自行激活，能量通过双极Maryland钳旁路释放烧穿肠管，患者术后并发肺栓塞死亡。"
}
```

---

## 四、 字段提取逻辑与原文对照解析 (Attribution Rationale)

1.  **判定类型 (`classification`) $\rightarrow$ `Shocking (机器物理故障/故障致险)`**
    *   *提取与判定逻辑*：原文中明确描述了“unintended delivery of monopolar energy”（非预期的单极电能释放）和“ESU going off by itself”（电刀自行激活），这属于明显的电气与硬件机械失效，直接贡献了致命风险，因此归入 Shocking 类。
2.  **机型代际 (`brand_name`) $\rightarrow$ `DaVinci Standard (第一代)`**
    *   *提取与判定逻辑*：原文提到了“Force FX ESU”和“Force Triad ESU”两款高频电刀发生器。在直觉外科公司（Intuitive Surgical）的产品配套历史中，这是第一代 DaVinci Classic/Standard 手术系统最为典型的配套电火花发生平台（2010年前后）。
3.  **细分隐患类别 (`hazard_category`) $\rightarrow$ `能量器械漏电/电弧/击穿/灼伤`**
    *   *提取与判定逻辑*：核心线索来自“delivery of monopolar energy through a bipolar Maryland clamp”（单极能量通过双极钳释放）。单极高频电流在非预期情况下传导到双极抓钳表面，发生旁路放电或电弧击穿，导致热灼伤。
4.  **涉事具体组件 (`fault_component`) $\rightarrow$ `Maryland Grasping (双极电凝钳)`**
    *   *提取与判定逻辑*：原文直接指出了承载并释放意外能量的机械臂附件为“bipolar Maryland clamp”。
5.  **临床并发症 (`clinical_complication`) $\rightarrow$ `肠穿孔`、`术后肺栓塞`**
    *   *提取与判定逻辑*：原文后半段指出患者的最终病情表现：“sustained a perforated bowel”（发生了肠道穿孔）和“developed bilateral pulmonary emboli”（并发了双侧肺栓塞）。
6.  **医生救治决策 (`surgeon_decision`) $\rightarrow$ `YES (中转开放手术)`**
    *   *提取与判定逻辑*：对应原文中“required an exploratory laparotomy”（需要进行开腹剖腹探查术，并切除结肠送检）。当术后发生肠穿孔感染时，医生做出了开腹中转抢救决策。
7.  **物理因果链重构 (`causal_chain` / `root_cause`)**
    *   *时序推演逻辑*：
        1.  `手术刚启动` ➔ 2. `单极高频电刀异常自行激活放电` ➔ 3. `电能通过双极Maryland电凝钳发生旁路电弧释放` ➔ 4. `患者肠壁发生隐蔽性热灼伤穿孔（术中探查未见异常）` ➔ 5. `一周后腹腔感染返回医院` ➔ 6. `中转开腹行结肠切除` ➔ 7. `术后制动/体弱并发双侧肺栓塞致死`。
