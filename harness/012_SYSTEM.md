# 012_SYSTEM: Harness Engineering 系统要素模型

> 本文档为 011_STRUCTURE 扎根理论编码与结构检验的精炼产出。
> 材料基础：3篇内部文章 + 30+篇互联网文献，167个概念标签 → 11个核心类别。
> 分析方法：扎根理论三级编码 + Zachman 6×6完备性检验 + Beer VSM S1-S5结构验证。
> 版本说明：由初版12类别精简而来——去除原C11(形式化规约语言，属描述视角而非实现维度)。
>
> 内部文章地址：
> - 020_PERSPECTIVE_1.md — AgentScope 团队视角
> - 021_PERSPECTIVE_2.md — Harness 工程落地视角
> - 022.md — Harness Engineering 六大支柱体系

---

## 一、核心命题

**Agent = Model + Harness** <sup>*[1,46]*</sup>

Harness 是模型之外的一切：提示词、工具与技能描述、执行环境、编排逻辑、中间件与策略。<sup>*[1]*</sup>

**核心类别**：有限上下文窗口约束下的可靠性环境工程

LLM 推理能力强大，但运行在根本性受限的上下文窗口中。Harness Engineering 不是让模型更聪明，而是设计一个让模型在有限视野内依然可靠工作的环境。<sup>*[32,33]*</sup> 这一核心命题统摄以下全部 11 个要素类别。

**类比框架**：Model = CPU，Context Window = RAM，Harness = OS，Agent = Application <sup>*[46,32]*</sup>

---

## 二、十一要素体系

### C1 上下文生命周期管理（Context Lifecycle Management）

**本质**：管控窗口内信息的质量与数量，使模型始终在最佳利用率区间工作。

**核心机制**：
- **生命周期四阶段**：注入 → 监控 → 压缩 → 归档 <sup>*[27]*</sup>
- **40% 利用率阈值**：超过此值推理质量显著下降 <sup>*[27]*</sup>；上下文接近极限时性能下滑 50-70% <sup>*[32]*</sup>
- **Reduce / Offload / Isolate 三原则**：压缩上下文、卸载到外部存储、多Agent隔离 <sup>*[16]*</sup>
- **渐进式披露**：AGENTS.md 作为导航地图（~100行），详细内容按需加载 <sup>*[46,1]*</sup>
- **结构化上下文**：XML标签/分隔符组织上下文块，信息优先级分层 <sup>*[27]*</sup>
- **焦点锚定**：TODO List 即使空操作也保持任务焦点 <sup>*[46]*</sup>
- **Prompt缓存优化**：静态内容前置 + 变量内容后置，最大化前缀命中 <sup>*[6]*</sup>
- **推理三明治**：xhigh(规划) → high(实现) → xhigh(验证)，按阶段分配算力 <sup>*[2]*</sup>
- **硬性截断**：CLAUDE.md 首200行/25KB <sup>*[10]*</sup>，系统指令 32KiB 上限 <sup>*[8]*</sup>

**反模式**：上下文死亡螺旋——错误→更多上下文→决策下降→更多错误→循环不可逆 <sup>*[47]*</sup>

---

### C2 分层记忆架构（Layered Memory Architecture）

**本质**：跨会话持久化知识，使 Agent 具备积累和演化能力。

**核心机制**：
- **三类记忆** <sup>*[46]*</sup>：
  - 程序记忆（Procedural）= 行为规则（AGENTS.md / rules.md）
  - 情景记忆（Episodic）= 历史经验（Session / Checkpoint）
  - 语义记忆（Semantic）= 知识库（domain/*.md）
- **Everything is a File**：四类记忆全部文件化，可读/可写/可版本追踪——自演化的基础条件 <sup>*[46]*</sup>
- **State Semantics 三性质**：外部化、路径可寻址、压缩稳定 <sup>*[17]*</sup>
- **可插拔文件系统后端**：统一存储抽象（目录/文件读写/glob/grep/shell），支持多种实现 <sup>*[4]*</sup>
- **配置层级优先级**：$HOME → 项目根 → 当前目录，层级覆盖 <sup>*[8]*</sup>
- **置信度标注**：区分 [hot-path, unverified] 与 [user-confirmed] <sup>*[46]*</sup>

**目录结构范式** <sup>*[46]*</sup>：
```
agent-root/
├── AGENTS.md           ← 唯一总入口，~100行目录
├── memory/
│   ├── working/        ← 当前任务状态
│   ├── procedural/     ← 行为规则 + 用户偏好
│   ├── semantic/       ← 知识地图 + 领域知识
│   └── episodic/       ← 会话记录 + 检查点
└── evolution/          ← 待审核 + GC日志 + 冲突
```

**核心约束**：Agent 在运行时无法访问的东西就不存在。<sup>*[47]*</sup>

---

### C3 架构约束硬执行（Architectural Constraint Enforcement）

**本质**：用工程手段替代 prompt 劝说，将规则从"希望被遵守"变为"不遵守就报错"。<sup>*[27]*</sup>

**核心机制**：
- **仓库是Agent的OS**：一切编码到仓库，不在仓库里Agent就看不见 <sup>*[47]*</sup>
- **层级编号系统**：L0(类型) → L1(工具) → L2(配置) → L3(业务) → L4(接口)，高层可引低层反之不行 <sup>*[47]*</sup>
- **中心化约束 + 本地自治**：只管架构边界，内部实现自由 <sup>*[47]*</sup>
- **Contracts（合约）**：输入输出规约 + 格式约束 + 验证门 + 权限边界 + 重试/停止规则 <sup>*[17,1]*</sup>
- **工具白名单 + 动态注册**：只暴露安全工具集合，按任务类型注册 <sup>*[27]*</sup>
- **参数强类型约束**：Pydantic/TypeScript 类型系统拒绝非法输入 <sup>*[27]*</sup>
- **权限四级分层**：默认 → 自动编辑 → 计划模式 → 自动模式（渐进授权）<sup>*[27,10]*</sup>
- **幂等性设计**：重复执行不产生副作用，Agent 可安全重试 <sup>*[27]*</sup>
- **沙箱隔离 + 最小权限暴露**：当前任务最小所需工具集 <sup>*[27]*</sup>
- **配置驱动行为**：持久化机器可读配置（AGENTS.md / CLAUDE.md）引导行为 <sup>*[47,1]*</sup>

**关键数据**：格式即性能乘数——Hashline 单一格式修改使性能从 6.7% 升至 68.3%。<sup>*[28]*</sup>

---

### C4 验证管道与自愈（Validation Pipeline & Self-Healing）

**本质**：机械化检查替代 LLM"直觉"，将错误拦截前移。<sup>*[47]*</sup>

**核心机制**：
- **事前预验证**：写代码前先检查合法性（2次交互替代10次tool call）<sup>*[47]*</sup>
- **四层验证管道**：build(编译) → lint-arch(架构合规) → test(功能正确) → verify(端到端) <sup>*[47]*</sup>
- **四类验证点**：前置条件 / 步骤后 / 进展检测(状态指纹比对) / 终止边界(预算式) <sup>*[27]*</sup>
- **三级错误升级**：自我校正 → 换策略重试 → 升级人工 → 彻底中止+诊断报告 <sup>*[27]*</sup>
- **PreCompletionChecklist**：拦截退出强制对照任务规约验证 <sup>*[2]*</sup>
- **LoopDetection**：追踪每文件编辑次数，N次后强制换方法 <sup>*[2]*</sup>
- **Failure Taxonomy**：命名故障模式（缺失制品/路径错误/验证失败/工具错误/超时）驱动恢复策略 <sup>*[17]*</sup>
- **Ralph Loop**：拦截退出 → 重注入目标 → 利用文件系统跨窗口持续执行 <sup>*[29,1]*</sup>
- **回压验证**：静默成功 + 大声失败 = 上下文高效的反馈循环 <sup>*[2]*</sup>
- **四阶段会话分离**：Research → Plan → Execute → Verify <sup>*[32]*</sup>

**理论基础**：验证-生成不对称性（P vs NP 直觉）——验证答案通常比生成答案容易。<sup>*[33]*</sup>

**关键数据**：有效验证机制可将输出质量提升 2-3 倍。<sup>*[32]*</sup>

---

### C5 多Agent编排与隔离（Multi-Agent Orchestration & Isolation）

**本质**：通过分治策略将大任务拆解为多个小上下文任务，每个执行者从干净状态开始。<sup>*[47]*</sup>

**核心机制**：
- **协调者绝不写代码**（中等以上任务最重要的原则）<sup>*[47]*</sup>
- **两层架构**：协调者(规划/委派/汇总) + 执行者(干净上下文/精确prompt) <sup>*[47]*</sup>
- **复杂度分级委派**：一句话→直接做；需清单→委派；需设计决策→委派+隔离 <sup>*[47]*</sup>
- **模型分级调度**：Haiku(简单) / Opus(复杂) / Flash(检索)——成本降 60-70% <sup>*[47]*</sup>
- **Roles 显式定义**：solver / verifier / researcher / orchestrator，职责不重叠 <sup>*[17]*</sup>
- **Stage Structure**：显式工作负载拓扑 plan → execute → verify → repair <sup>*[17]*</sup>
- **四重隔离** <sup>*[27,47]*</sup>：
  - 任务边界隔离（全新上下文，只传必要定义）
  - 信息接口化（结构化消息替代原始上下文共享）
  - 错误隔离（一个Agent错误不传播到下游）
  - Git Worktree隔离（结构性变更在临时副本执行）
- **交叉模型Review**：不同模型review避免思维盲区重叠 <sup>*[47]*</sup>
- **跨产品共享Agent Loop**：CLI/Web/IDE/App 复用同一套执行逻辑 <sup>*[7]*</sup>

**关键数据**：75%+ 组织在生产中使用多模型路由。<sup>*[37]*</sup>

---

### C6 自演化与熵治理（Self-Evolution & Entropy Governance）

**本质**：对抗长期退化，实现系统越运行越高效。<sup>*[46,47]*</sup>

**核心机制**：
- **三种演化机制** <sup>*[46]*</sup>：
  - 被动（hot-path）：用户纠正/任务完成时写入，标注[unverified]
  - 主动（显式）：用户说"记住"时直接写目标文件，标注[user-confirmed]
  - 后台（GC）：定时扫描，矛盾升级人工裁决
- **自演化闭环**：Agent执行 → 验证抓到问题 → Critic分析模式 → Refiner更新规则 → 下一个Agent受益 <sup>*[47]*</sup>
- **GC 四目标**：矛盾内容 / 过时决策 / 知识空白 / 漂移模式 <sup>*[46]*</sup>
- **轨迹编译**：同类任务成功3次以上 → 编译为确定性脚本（如 `make add-endpoint`）<sup>*[47]*</sup>
- **棘轮效应**：编译的模式成为永久基础设施，Agent 被释放去处理新问题 <sup>*[47]*</sup>
- **Review → Lint规则**：反复出现的review问题编码为新lint规则——软知识变硬规则 <sup>*[47]*</sup>
- **上下文蒸馏**：保留决策结论，丢弃推理过程 <sup>*[27]*</sup>
- **数据飞轮**：执行轨迹即训练数据，部署即训练，竞争优势从模型参数迁移到轨迹捕获 <sup>*[32]*</sup>
- **模型-Harness共进化**：社区摸索 → Post-training → 模型内化 → 新Harness支持更高阶能力 <sup>*[32]*</sup>
- **Harness Debt**：Harness本身也需维护，类比技术债务 <sup>*[14]*</sup>

**规律**：Bitter Lesson 在应用层的体现——架构假设 6 个月内过时，需拥抱持续重构。<sup>*[16]*</sup> Manus 6个月重构 5 次 Harness。<sup>*[40]*</sup>

---

### C7 可拆卸性与模块化（Detachability & Modularity）

**本质**：使 Harness 不绑定特定模型，适配 AI 模型快速迭代的现实。<sup>*[27]*</sup>

**核心机制**：
- **三层架构分离**：应用层 / Harness核心层 / 模型适配层 <sup>*[27]*</sup>
- **抽象模型接口**：统一模型调用，屏蔽 API 差异 <sup>*[27]*</sup>
- **工具定义模型无关**：工具描述与 function calling 格式解耦 <sup>*[27]*</sup>
- **Prompt模板分离**：模板外置为可配置资源 <sup>*[27]*</sup>
- **能力特性标记**：标记模型是否支持视觉/长上下文/函数调用等 <sup>*[27]*</sup>

**关键数据**：
- Post-Training 耦合——同一模型 Opus 4.6 在不同 Harness 中排名 #33 vs #5，Harness 影响可能超过模型选择 <sup>*[13]*</sup>
- 三阶段工程演进：Prompt Engineering(2022-24) → Context Engineering(2025) → Harness Engineering(2026) <sup>*[14,28]*</sup>

**场景偏向警示**：当前 Harness 实践偏向 Web 开发（LLM训练数据饱和领域），嵌入式系统/小众语言/非编码场景回报可能递减。<sup>*[34]*</sup>

---

### C8 人机协作模型（Human-Agent Collaboration Model）

**本质**：定义人在 Agent 环境中的角色——从编码者转为环境设计者。<sup>*[47]*</sup>

**核心机制**：
- **harness-creator / harness-executor** 分工：creator 搭基础设施，executor 在其中执行任务 <sup>*[47]*</sup>
- **项目健康度评分**：0-20裸奔，21-70有缺口，71+健康 <sup>*[47]*</sup>
- **执行计划审批**：非简单任务生成执行计划文件，人扫一眼批准 <sup>*[47]*</sup>
- **门控人工干预**：interrupt_on 参数将特定操作映射到审批门 <sup>*[2,15]*</sup>
- **三级错误升级**含人工裁决环节 <sup>*[27]*</sup>
- **问题驱动，非过度预防**：聚焦已发生的问题，由实际失败驱动迭代 <sup>*[13]*</sup>
- **配置起点原则**：从简单开始，仅在观察到失败后增加配置 <sup>*[13]*</sup>
- **渐进复杂度路径**：六阶段渐进建设，从 Context 到 Detachability <sup>*[27]*</sup>

**理论基础**：控制论同构——瓦特离心调速器(1788) → Kubernetes声明式控制 → AI Agent Harness，238年同一模式：当传感器和执行器足够强大时，工程师从直接操作转向系统设计。<sup>*[33]*</sup>

**关键发现**：Brooks 定律未触发——团队 3→7 人未出现沟通爆炸，因为 Agent 间依赖是环境级而非代码级。<sup>*[34]*</sup>

---

### C9 可观测性与质量度量（Observability & Quality Metrics）

**本质**：提供 Harness 运行时监控的数据基础。<sup>*[27]*</sup>

**核心机制**：
- **六维可观测性**：上下文健康 / 执行效率 / 验证质量 / 上下文治理 / 工具可靠性 / 端到端性能 <sup>*[27]*</sup>
- **六钩子中间件架构**：before_agent / before_model / wrap_model / wrap_tool / after_model / after_agent <sup>*[3]*</sup>
- **Trace-Based 主动反馈**：Agent 获取自身执行轨迹并派生分析 <sup>*[2]*</sup>
- **工具质量 > 工具数量**：5个清晰工具优于20个模糊工具 <sup>*[27]*</sup>
- **错误信息教学质量**：好的报错=一次教学（什么违反了/为什么/怎么修）<sup>*[47]*</sup>
- **自主决策审计**：审计须捕获 Agent 推理"为什么"而非仅"做了什么" <sup>*[22]*</sup>
- **证据质量审计轨迹**：SOC 2 合规需业务上下文 + 取证重建能力 <sup>*[22]*</sup>

**关键缺口**：可观测性 ≠ 评估——89% 有可观测性但仅 37% 有在线评估（见 C11）。<sup>*[37]*</sup>

---

### C10 企业安全与合规治理（Enterprise Security & Compliance）

**本质**：Agent 行为可靠性在企业场景下的安全延伸。<sup>*[20]*</sup>

**核心机制**：
- **机器主体身份**：Agent 作为自主"主体"需要与人类同等的身份认证/授权 <sup>*[20]*</sup>
- **治理-遏制缺口**：58-59% 有监控但仅 37-40% 有终止开关——可见性 ≠ 可干预性 <sup>*[22]*</sup>
- **间接数据访问绕过**：Agent 通过数据库查询/配置文件读取绕过传统 DLP <sup>*[21]*</sup>
- **Prompt级DLP**：在查询时、网络出口前检测和脱敏敏感信息 <sup>*[21]*</sup>
- **工具级访问控制**：限制特定 MCP 工具调用而非文件系统级权限 <sup>*[22]*</sup>
- **用途绑定**：约束 Agent 到预期功能，超越权限范围 <sup>*[21]*</sup>
- **影子AI发现**：未授权 Agent(浏览器扩展/个人账户/本地安装) = 不可控攻击面 <sup>*[23]*</sup>
- **伦理墙**：防止 Agent 跨敏感业务功能滥用（类比金融信息隔离墙）<sup>*[23]*</sup>
- **通道级安全管理**：按通信通道(邮件/API/数据库)设定独立策略 <sup>*[22]*</sup>
- **默认行为即治理**：策略编码为默认行为而非反应式过滤 <sup>*[22]*</sup>

**关键数据**：100% 任务完成但仅 33% 策略遵从——安全合规与功能正确是独立维度。<sup>*[42]*</sup>

---

### C11 评估与基准测试（Evaluation & Benchmarking）

**本质**：离线量化验证 Harness 工程效果（区别于 C9 的运行时监控）。<sup>*[38]*</sup>

**核心机制**：
- **pass@k vs pass^k** <sup>*[38]*</sup>：
  - pass@k = k次中至少1次成功（衡量能力上限）
  - pass^k = k次全部成功（衡量一致性可靠性，如单次75% → 三次全成功仅42%）
- **Task/Trial/Grader 框架**：模块化评估组件（任务定义 + 试验执行 + 评分逻辑）<sup>*[38]*</sup>
- **三类评分器**：代码型(快/脆) / 模型型(灵活/非确定) / 人工(金标准/不可扩展) <sup>*[38]*</sup>
- **轨迹 vs 结果区分**：交互历史与最终环境状态是独立评估关注点 <sup>*[38]*</sup>
- **策略遵从独立度量**：任务完成率与策略遵从率须分开测量 <sup>*[42]*</sup>
- **四支柱评估模型**：LLM组件 / 记忆系统 / 工具行为 / 环境 <sup>*[42]*</sup>
- **消融实验方法**：逐模块递增添加，测量差分贡献 <sup>*[17]*</sup>
- **长程可靠性测试**：覆盖 50-100+ 工具调用，1%榜单差异无法检测第50步后的漂移 <sup>*[40]*</sup>
- **Agent 崩溃模式**：螺旋进入"怪异行为"而非渐进退化 <sup>*[40]*</sup>
- **HAL 统一评估 CLI**：框架无关的跨基准测试（SWE-bench/USACO/AppWorld/OSWorld等9+）<sup>*[39]*</sup>
- **轨迹加密防污染**：加密存储 Agent 轨迹防止评估数据泄露到训练集 <sup>*[39]*</sup>

**关键数据**：
- LLM-as-Judge $0.06 vs Agent-as-Judge $0.96（16倍成本差异）<sup>*[42]*</sup>
- Harness 优化 52.8%→66.5%（+13.7pp，不换模型）<sup>*[2]*</sup>

---

## 三、要素间结构关系

```
C1(上下文管理) ←─ 约束 ─→ C3(架构约束) ←─ 扩展 ─→ C10(企业安全)
      ↑                          ↑                          │
      │ 管理                规则来源                    合规要求
      ↓                          │                          ↓
C2(分层记忆) ←─ 存储 ─→ C6(自演化/熵治理) ── 轨迹 ──→ C11(评估基准)
      ↑                          │                          │
      │ 支撑                进化产物                    度量反馈
      ↓                          ↓                          ↓
C5(多Agent编排) ←─ 验证 ─→ C4(验证管道) ←─ 数据 ─→ C9(可观测性)
      ↑
      │ 协作                         解耦
      ↓                              ↓
C8(人机协作) ──────────────→ C7(可拆卸性)
```

**关系逻辑**：
1. C1↔C3：上下文管理依赖架构约束限制信息流入；约束本身也是上下文的一部分 <sup>*[27,47]*</sup>
2. C2↔C6：记忆是熵治理的对象；熵治理产物（清洁后的知识）回写到记忆 <sup>*[46]*</sup>
3. C5→C1：多Agent编排的核心动机就是管理上下文（协调者不写代码以保护上下文）<sup>*[47]*</sup>
4. C6→C4：自演化将Review中的软知识编译为验证管道的硬规则 <sup>*[47]*</sup>
5. C10→C3：企业安全是架构约束在合规维度的延伸 <sup>*[22,27]*</sup>
6. C11↔C6：评估数据驱动演化；演化产生的轨迹成为评估输入 <sup>*[32,38]*</sup>
7. C8→C7：人机协作通过可拆卸性实现模型无关的环境设计 <sup>*[27]*</sup>

---

## 四、VSM 可行系统映射

| VSM子系统 | 功能 | Harness要素 |
|-----------|------|-------------|
| **S1 操作** | 执行基本工作 | C3(工具/沙箱) + C4(验证) + C7(适配层) |
| **S2 协调** | 操作间冲突处理 | C5(隔离) + C1(上下文管理) |
| **S3 控制** | 优化效能/分配资源 | C5(协调者) + C8(人机协作) |
| **S3* 审计** | 深入检查操作实际 | C4(验证管道) + C9(可观测) + C11(评估) |
| **S4 智能** | 扫描环境/学习改进 | C6(自演化) + C2(记忆) + C11(评估) |
| **S5 政策** | 定义身份与价值观 | C8(人机协作) + C3(约束) + C10(安全) |

**Ashby 必要多样性定律验证**：Harness 通过多层互补策略匹配 Agent 行为多样性——硬约束(C3)压缩行为空间，验证管道(C4)检测逸出，隔离(C5)防止扩散，熵治理(C6)防止长期积累，人工升级(C8)兜底。"预防→检测→纠正→升级"的层叠式多样性匹配。<sup>*[33]*</sup>

---

## 五、关键量化证据

| 数据点 | 含义 | 来源 |
|--------|------|------|
| Harness优化 52.8%→66.5%（不换模型） | Harness工程直接效果 | <sup>*[2]*</sup> |
| Hashline格式改变 6.7%→68.3% | 微小环境变化产生巨大性能差异 | <sup>*[28]*</sup> |
| 同模型Opus排名 #33 vs #5（不同Harness） | Harness影响可能超过模型选择 | <sup>*[13]*</sup> |
| 上下文接近极限时性能下滑 50-70% | 上下文管理是核心瓶颈 | <sup>*[32]*</sup> |
| 有效验证提升质量 2-3倍 | 验证管道的杠杆效应 | <sup>*[32]*</sup> |
| 100%任务完成但33%策略遵从 | 安全合规是独立维度 | <sup>*[42]*</sup> |
| 58%监控 vs 37%终止开关 | 治理-遏制缺口 | <sup>*[22]*</sup> |
| 89%可观测 vs 37%在线评估 | 可观测性≠评估 | <sup>*[37]*</sup> |
| LLM-Judge $0.06 vs Agent-Judge $0.96 | 评估成本16倍差异 | <sup>*[42]*</sup> |
| 75%+生产环境使用多模型路由 | 多模型是常态 | <sup>*[37]*</sup> |
| Manus 6个月重构5次Harness | Bitter Lesson应用层体现 | <sup>*[40]*</sup> |

---

## 六、场景迁移关注点（Coding → Office）

当前 Harness 方法论主要从 Coding Agent 实践中涌现。迁移到企业办公场景时，以下维度需重点关注：

| 关注点 | 说明 | 来源 |
|--------|------|------|
| 用户意图消歧 | 办公指令比编码指令模糊度更高，需要更强的意图理解和澄清机制 | 归纳推导 |
| 格式多样性适配 | PDF/DOCX/PPTX/XLSX 等格式处理远超代码文件 | 归纳推导 |
| 框架场景偏向 | 当前偏 Web 开发（LLM训练数据饱和领域），Office 场景训练数据可能不饱和 | <sup>*[34]*</sup> |
| 多租户Harness隔离 | 不同部门/用户的 Agent 策略和数据须隔离 | <sup>*[22,23]*</sup> |

---

## 参考文献

[1] LangChain Blog — [The Anatomy of an Agent Harness](https://blog.langchain.com/the-anatomy-of-an-agent-harness/)
[2] LangChain Blog — [Improving Deep Agents with Harness Engineering](https://blog.langchain.com/improving-deep-agents-with-harness-engineering/)
[3] LangChain Blog — [How Middleware Lets You Customize Your Agent Harness](https://blog.langchain.com/how-middleware-lets-you-customize-your-agent-harness/)
[4] LangChain Docs — [Harness Capabilities — Deep Agents](https://docs.langchain.com/oss/python/deepagents/harness)
[6] OpenAI — [Unrolling the Codex Agent Loop](https://openai.com/index/unrolling-the-codex-agent-loop/)
[7] OpenAI — [Unlocking the Codex Harness](https://openai.com/index/unlocking-the-codex-harness/)
[8] ZenML — [Building Production-Ready AI Agents: Codex CLI Architecture](https://www.zenml.io/llmops-database/building-production-ready-ai-agents-openai-codex-cli-architecture-and-agent-loop-design)
[10] GitHub/Piebald-AI — [Claude Code System Prompts](https://github.com/Piebald-AI/claude-code-system-prompts)
[13] HumanLayer Blog — [Skill Issue: Harness Engineering for Coding Agents](https://www.humanlayer.dev/blog/skill-issue-harness-engineering-for-coding-agents)
[14] Louis Bouchard — [Harness Engineering: The Missing Layer Behind AI Agents](https://www.louisbouchard.ai/harness-engineering/)
[15] NxCode — [What Is Harness Engineering? Complete Guide 2026](https://www.nxcode.io/resources/news/what-is-harness-engineering-complete-guide-2026)
[16] Hugo Bowne-Anderson — [AI Agent Harness, 3 Principles for Context Engineering](https://hugobowne.substack.com/p/ai-agent-harness-3-principles-for)
[17] arXiv — [Natural-Language Agent Harnesses (NLAHs)](https://arxiv.org/html/2603.25723)
[20] McKinsey — [Securing the Agentic Enterprise](https://www.mckinsey.com/capabilities/risk-and-resilience/our-insights/securing-the-agentic-enterprise-opportunities-for-cybersecurity-providers)
[21] Microsoft Security — [Secure Agentic AI End-to-End](https://www.microsoft.com/en-us/security/blog/2026/03/20/secure-agentic-ai-end-to-end/)
[22] MintMCP — [AI Agent Security: The Complete Enterprise Guide 2026](https://www.mintmcp.com/blog/ai-agent-security)
[23] AGAT Software — [AI Agent Security in 2026: What Enterprises Are Getting Wrong](https://agatsoftware.com/blog/ai-agent-security-enterprise-2026/)
[27] 微信公众号 (022.md) — [Harness Engineering：构建高可靠AI Agent的工程方法论](https://mp.weixin.qq.com/s/p1JPMhyM3yygJVCBhnBcaA)
[28] CSDN/shadowcz007 — [Harness Engineering 是什么？从上下文工程到驾驭工程](https://blog.csdn.net/shadowcz007/article/details/159111359)
[29] CSDN — [AI Agent 系统架构进阶指南：Agent Harness 深度解析](https://blog.csdn.net/m0_59235245/article/details/159247402)
[32] 腾讯新闻 — [Harness is the New Dataset：模型智能提升的下一个关键方向](https://news.qq.com/rain/a/20260326A080NG00)
[33] 腾讯新闻 — [Harness Engineering 为什么是 Agent 时代的"控制论"？](https://news.qq.com/rain/a/20260318A03ZHX00)
[34] 博客园/warm3snow — [Harness Engineering：当人类不再写代码，软件工程反而更"工程"了](https://www.cnblogs.com/informatics/p/19740439)
[37] LangChain — [State of Agent Engineering](https://www.langchain.com/state-of-agent-engineering)
[38] Anthropic Engineering — [Demystifying Evals for AI Agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
[39] Princeton PLI — [HAL-Harness (Holistic Agent Leaderboard)](https://github.com/princeton-pli/hal-harness)
[40] Philipp Schmid (DeepMind) — [The Importance of Agent Harness in 2026](https://www.philschmid.de/agent-harness-2026)
[42] arXiv — [Beyond Task Completion: An Assessment Framework for Evaluating Agentic AI](https://arxiv.org/html/2512.12791v1)
[46] 内部文章 — 020_PERSPECTIVE_1.md（AgentScope 团队视角）
[47] 内部文章 — 021_PERSPECTIVE_2.md（Harness 工程落地视角）
