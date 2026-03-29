# AI 淘汰写代码的人，但解决不了这11个工程问题——Harness Engineering 深度解析

> AI 能写代码，但它搞不定自己的工作环境。这 11 个工程问题，就是程序员在 AI 时代的新战场。

---

## 一个 PPT 引发的问题

前段时间，领导问了我一个问题：做好一个 PPT，除了换更好的模型，还有什么办法？

我的回答是：先让大模型写 HTML，再把 HTML 转成 PPT。

这个方法效果不错。同一个模型，同样的内容需求，只因为换了一个"中间表示"，产出质量就有了明显提升。当时我只觉得这是个巧妙的 workaround。直到后来读到 Harness Engineering 这个概念，我才意识到——我做的事情，本质上就是在改变模型的工作环境。

不换模型，换环境。这就是 Harness Engineering 的核心思路。

---

## 换模型是条死胡同

大部分团队在用 AI Agent 的时候，遇到问题的第一反应是：换个更强的模型。

这个直觉是错的。

LangChain 团队做过一个实验：同样的任务，不换模型，只优化 Harness（也就是模型工作的环境），Terminal Bench 2.0 的成绩从 52.8% 涨到了 66.5%——从榜外直接冲进 Top 5。更夸张的例子是 Can Boluk 的发现：仅仅改变代码编辑的输出格式（从普通 diff 换成 Hashline），同一个模型的性能从 6.7% 飙到 68.3%。十倍差距，一行配置的事。

还有一组数据更有说服力。同一个 Claude Opus 4.6 模型，在 HumanLayer 的 Harness 里跑出了 #5 的排名，在另一个 Harness 里只排 #33。同一个大脑，不同的工作环境，排名差了 28 位。

问题从来不在模型的"智力"上。问题在于：你给它搭了一个什么样的工作环境。

---

## Agent = Model + Harness

这里需要先把一个概念说清楚。

Agent 不等于大模型。Agent = Model + Harness。

Model 是大脑——负责推理、生成、决策。Harness 是大脑之外的一切——提示词、工具描述、执行环境、编排逻辑、中间件和策略。

用一个更直观的类比：Model 是 CPU，上下文窗口是 RAM，Harness 是操作系统，Agent 是跑在操作系统上的应用程序。

CPU 再强，没有操作系统管理内存、调度进程、提供文件系统，应用也跑不起来。Harness 做的就是这件事。

那 Harness 到底包含哪些东西？AI 解决不了哪些问题？经过对 30 多篇文献的系统分析，我梳理出 5 个方向、11 个核心工程问题。下面这张图先给你一个全景：

<!-- 图1：11要素全景图 -->

> **图片提示词（信息图，非手稿风格）**：
>
> ```
> Clean modern infographic on white background, flat design style with thin line icons. Title at top: "AI解决不了的11个工程问题". A central circle labeled "Agent = Model + Harness" with the subtitle "有限上下文窗口约束下的可靠性环境工程". Five colored bands radiate outward, each as a problem direction: Band 1 (blue) "问题一: 工作空间" contains C1上下文+C2记忆; Band 2 (orange) "问题二: 护栏" contains C3约束+C4验证; Band 3 (green) "问题三: 分工" contains C5编排+C8人机协作; Band 4 (purple) "问题四: 进化" contains C6自演化+C7可拆卸; Band 5 (red) "问题五: 保障" contains C9可观测+C10安全+C11评估. Each element has a one-line problem statement and a minimal icon. Connecting lines between bands show key dependencies. Bottom annotation: "5个方向 × 11个工程问题 — AI做不了, 人来做". Style: Notion/Linear-style tech infographic, no 3D, no gradients, high information density, bilingual Chinese-English labels.
> ```

五个方向，十一个工程问题。逐个拆解。

---

## 问题一：AI 记不住事，也管不好自己的"工作台"

*对应要素：C1 上下文生命周期管理 + C2 分层记忆架构*

AI 最大的瓶颈不是推理能力，是上下文窗口。

你可能听说过"上下文窗口越大越好"这个说法。数据告诉你另一面：当上下文接近窗口极限时，模型的推理性能会下滑 50%-70%。上下文窗口不是"越大越好的仓库"，它更像工作台——摊满了东西反而什么都找不到。AI 自己不会整理这张工作台，也不会主动去"回忆"上次的经验。这是人要解决的问题。

### C1：上下文生命周期管理

C1 解决的问题是：窗口里该放什么、什么时候放、满了怎么办。

核心策略是三个词：Reduce（压缩）、Offload（卸载）、Isolate（隔离）。压缩就是把冗余信息浓缩；卸载就是把暂时不用的信息挪到外部存储；隔离就是拆成多个小任务，每个任务用干净的上下文。

实践中有一个关键阈值：40%。上下文利用率超过 40%，推理质量就开始下滑。这意味着一个 200K 窗口的模型，真正可用的高质量空间只有 80K。

还有一个值得警惕的反模式——**上下文死亡螺旋**。Agent 犯了一个错误，你把错误信息塞进上下文让它修正，这导致上下文变大、决策质量下降、产生更多错误、需要更多上下文……这个循环一旦启动就不可逆。

### C2：分层记忆架构

上下文窗口管的是"当前能看到什么"，记忆管的是"上一次的经验还在不在"。

没有记忆系统的 Agent 就像一个每天早上失忆的员工——你昨天教他的东西，今天要重新教一遍。

分层记忆把知识分成三类：程序记忆（行为规则，"怎么做事"）、情景记忆（历史经验，"上次发生了什么"）、语义记忆（领域知识，"关于业务的理解"）。一个关键的设计决策是 Everything is a File——所有记忆都用文件存储，可读、可写、可版本追踪。这不是偷懒，这是让 Agent 能够自我演化的前提条件。

有一句话总结了记忆系统的本质约束：**Agent 在运行时无法访问的东西就不存在**。不管你的知识库有多丰富，如果 Agent 在执行的那一刻看不到，它就等于零。

> **C1+C2 一句话**：上下文是 Agent 的工作台，记忆是 Agent 的档案柜——工作台要整洁，档案柜要有分类。

<!-- 图2：问题一 组级图 -->

> **图片提示词（手稿风格）**：
>
> ```
> Hand-drawn pencil sketch on faint grid paper, classical European scientific manuscript style, Leonardo da Vinci natural philosophy era. At the top, the main title "工作空间：上下文与记忆" in large elegant Renaissance hand-drawn calligraphy in Chinese, highlighted with soft amber crayon coloring. The image is split into two halves by a thin dashed line. LEFT HALF: An alchemist's distillation apparatus with four interconnected glass vessels labeled "Inject → Monitor → Compress → Archive". A graduated measuring cylinder beside it shows a fill line at 40% with a warning symbol glowing amber. Above 40%, glass cracks. Below the apparatus, a small spiral labeled "Death Spiral" shows a vortex consuming itself. RIGHT HALF: A geological cross-section cliff face with three sedimentary layers — top "Procedural Memory" (crystalline rule tablets), middle "Episodic Memory" (amber-tinted fossils), bottom "Semantic Memory" (branching knowledge veins). A great tree with roots labeled "File System" penetrates all layers. A stone monument at top reads "AGENTS.md". A banner across the bottom unifies both halves: "窗口是工作台, 记忆是档案柜 — 整理它们是人的工作". Predominantly black and white graphite with fine crosshatching. Selective warm crayon color: amber/gold on the 40% threshold and episodic fossils, terracotta on the root system.
> ```

---

## 问题二：AI 不会给自己装"护栏"

*对应要素：C3 架构约束硬执行 + C4 验证管道与自愈*

AI 能生成代码，但它不会给自己设边界。你不拦它，它就会改不该改的文件、调不该调的接口、用不该用的权限。怎么防止 Agent 干蠢事？答案是两道防线：约束告诉它"什么不能做"，验证检查它"做得对不对"。这两道防线都需要人来设计。

### C3：架构约束硬执行

重点在"硬"字上。

写 prompt 告诉模型"请不要修改 config 文件"——这是软约束，相当于在门上贴个"请勿入内"的牌子，对 LLM 来说约等于没有。真正有效的做法是把门锁上：用代码白名单限制可用工具，用 Pydantic/TypeScript 做参数类型检查，用权限分层控制访问范围。

一个直觉：**约束应该编码成代码，而不是写在 prompt 里**。能用 if-else 拦截的事，别交给概率模型去"理解"。

权限设计上有一个渐进授权的思路：默认模式（最小权限）→ 自动编辑 → 计划模式 → 自动模式。用户根据信任度逐步放权，而不是一上来就给 Agent 全部权限。

### C4：验证管道与自愈

约束管的是"别碰不该碰的"，验证管的是"碰了的东西对不对"。

验证管道的核心是四层检查：Build（编译通过吗）→ Lint-Arch（符合架构规范吗）→ Test（功能正确吗）→ Verify（端到端通了吗）。每一层都是机械化检查，不依赖 LLM 的"直觉"。

背后有一个理论支撑——**验证-生成不对称性**。验证答案几乎总是比生成答案容易。这就是为什么正确的做法是让 LLM 生成，然后用确定性代码去验证，而不是反过来。

数据说话：有效的验证机制可以把输出质量提升 2-3 倍。

当验证失败时，系统的反应不是直接报错退出，而是一套升级策略：先自我校正，不行就换策略重试，再不行升级给人工，最后才彻底中止并输出诊断报告。这就是"自愈"的含义——Agent 有能力从错误中恢复，而不是一出错就死机。

> **C3+C4 一句话**：约束是"事前把门锁好"，验证是"事后逐个检查"——两道防线缺一不可。

<!-- 图3：问题二 组级图 -->

> **图片提示词（手稿风格）**：
>
> ```
> Hand-drawn pencil sketch on faint grid paper, classical European scientific manuscript style. At the top, the main title "护栏：约束与验证" in large elegant Renaissance hand-drawn calligraphy in Chinese, highlighted with soft amber crayon coloring. LEFT HALF: A medieval fortress blueprint viewed from above — five concentric defensive rings labeled L0 through L4. Some gates have locks labeled "Contract", guards with shields labeled "Pydantic". A rejected tangled prompt arrow bounces off the outer wall, annotated "Prompt劝说 → 无效, 代码拦截 → 有效". A callout: "6.7% → 68.3%". RIGHT HALF: A watchmaker's inspection bench with four sequential stations: "Build" (lens checking gear fit), "Lint-Arch" (protractor verifying angles), "Test" (spring tension tester), "Verify" (complete watch wound by tiny mechanical hand). A curved feedback arrow from station 4 back to station 1 labeled "Self-Healing". A three-tier escalation ladder at the end: "自修 → 换策略 → 人工 → 中止". A banner across bottom: "约束锁门, 验证查岗 — 都是人设计的机制". Predominantly black and white graphite with fine crosshatching. Selective warm crayon color: amber/gold on the contract locks and the verified watch, terracotta on the escalation ladder.
> ```

---

## 问题三：AI 不会自己组建团队，也不知道什么时候该问人

*对应要素：C5 多Agent编排与隔离 + C8 人机协作模型*

单个 Agent 的能力有上限，这个上限就是上下文窗口。AI 不会自己决定"这个任务太复杂了，我该拆成三个小任务分别做"，也不会自己判断"这个决策我拿不准，该问一下人"。编排和协作的边界，都是人划的。

### C5：多 Agent 编排与隔离

多 Agent 系统有一条最重要的原则：**协调者绝不写代码**。

协调者只做三件事：规划、委派、汇总。具体的执行交给专门的执行者。每个执行者从干净的上下文开始，只拿到完成任务所需的最小信息。

这不是什么高深的架构设计，这是分治思想在上下文维度的应用。一个 200K 窗口塞满一个大任务，不如拆成 5 个 40K 的小任务分别执行。每个小任务的上下文更干净，执行质量更高。

隔离有四重：任务边界隔离（全新上下文）、信息接口化（结构化消息传递，不共享原始上下文）、错误隔离（一个 Agent 失败不传播到下游）、Git Worktree 隔离（结构性变更在临时副本执行）。

模型调度也有讲究。75%+ 的生产环境已经在用多模型路由：简单任务用轻量模型（Haiku），复杂推理用重量模型（Opus），检索用专用模型（Flash）。成本能降 60-70%。

### C8：人机协作模型

如果 Agent 做所有事，人做什么？

答案是：人从"写代码的"变成"设计环境的"。Harness Engineering 里有两个角色——harness-creator（搭建基础设施的人）和 harness-executor（在基础设施中执行任务的 Agent）。人负责设计规则、定义约束、审批关键决策；Agent 负责在这套环境里高效执行。

这不是一个新模式。1788 年瓦特发明离心调速器——蒸汽机不再需要人手动调节阀门，工程师的工作从"转阀门"变成"设计调速器"。Kubernetes 的声明式控制也是同一个模式：你声明想要的状态，系统自己去实现。现在 Harness Engineering 把这个模式搬到了 AI Agent 领域。

238 年，同一个控制论范式。当传感器和执行器足够强大时，工程师的角色必然从直接操作转向系统设计。

> **C5+C8 一句话**：Agent 做执行，人做设计——协调者不写代码，设计者不转阀门。

<!-- 图4：问题三 组级图 -->

> **图片提示词（手稿风格）**：
>
> ```
> Hand-drawn pencil sketch on faint grid paper, classical European scientific manuscript style. At the top, the main title "分工：编排与人机协作" in large elegant Renaissance hand-drawn calligraphy in Chinese, highlighted with soft amber crayon coloring. The image is divided into two scenes. TOP SCENE: A Renaissance architecture workshop — a master architect on an elevated platform holding only a scroll and compass (annotated "Coordinator: 规划/委派/汇总 — 绝不亲自动手"), below him four glass-walled chambers each containing a craftsman: "Haiku-简单", "Opus-复杂", "Flash-检索", "Cross-Review". Clean walls between chambers, annotation: "四重隔离". BOTTOM SCENE: Three horizontal panels showing the same feedback loop across 238 years — Panel 1 (1788): Watt governor, "设计调速器"; Panel 2 (2015): Kubernetes control loop, "声明期望状态"; Panel 3 (2026): Human placing AGENTS.md around AI agent loop, "设计环境". A vertical dashed line labeled "同一模式: 人从操作者→设计者". Banner across bottom: "AI做执行, 人做设计 — 这是238年未变的工程范式". Predominantly black and white graphite with fine crosshatching. Selective warm crayon color: amber/gold on the coordinator's scroll and the governance mechanisms in each era panel.
> ```

---

## 问题四：AI 不会自我进化，也不会主动适配新模型

*对应要素：C6 自演化与熵治理 + C7 可拆卸性与模块化*

系统搭好了，能一直用下去吗？不能。Manus 团队 6 个月重构了 5 次 Harness。这不是他们能力有问题，这是 Bitter Lesson 在应用层的体现——模型能力半年一迭代，你的架构假设 6 个月就会过时。AI 不会主动清理过时的规则，也不会自己把 Harness 从旧模型迁移到新模型。进化和适配，是人要持续解决的工程问题。

### C6：自演化与熵治理

一个不维护的 Harness 会越用越差。规则互相矛盾、过时的配置没清理、知识库里充满陈旧信息。这就是"熵"在侵蚀系统。

自演化的核心是一个闭环：Agent 执行 → 验证发现问题 → Critic 分析错误模式 → Refiner 更新规则 → 下一个 Agent 受益。这个闭环让系统能从自身的错误中学习。

其中最有杠杆效应的机制叫**轨迹编译**：当同类任务成功完成 3 次以上，系统就把成功模式编译为确定性脚本。比如"添加一个 API 端点"这个操作，前几次由 Agent 推理完成，之后变成一条 `make add-endpoint` 命令。编译的模式成为永久基础设施，Agent 被释放去处理新问题——这就是棘轮效应，系统只进不退。

更大的图景是**数据飞轮**：Agent 的执行轨迹本身就是训练数据。部署即训练。DeepMind 的 Philipp Schmid 说，未来的竞争优势不在于谁的模型参数多，而在于谁能捕获更高质量的执行轨迹。

### C7：可拆卸性与模块化

前面提到同一个 Opus 模型在不同 Harness 下排名差 28 位。这说明 Harness 对性能的影响可能超过模型选择本身。但反过来也意味着——如果你的 Harness 绑死了某个模型，模型一升级你就要重写。

可拆卸性就是为了解决这个问题。核心设计是三层分离：应用层（业务逻辑）/ Harness 核心层（上下文管理、验证、工具注册，模型无关）/ 模型适配层（抽象接口，对接不同模型）。换模型的时候，只动最底下一层。

这也是这个领域演进的缩影。2022-2024 年是 Prompt Engineering（写好提示词），2025 年是 Context Engineering（管好上下文），2026 年到了 Harness Engineering（设计整个运行环境）。每一步都在把更多的"人的经验"从脑子里搬到工程系统里。

> **C6+C7 一句话**：自演化让系统越用越好，可拆卸让系统不怕换大脑。

<!-- 图5：问题四 组级图 -->

> **图片提示词（手稿风格）**：
>
> ```
> Hand-drawn pencil sketch on faint grid paper, classical European scientific manuscript style. At the top, the main title "进化：自演化与可拆卸" in large elegant Renaissance hand-drawn calligraphy in Chinese, highlighted with soft amber crayon coloring. LEFT HALF: A botanical illustration of a grand tree in a walled garden. Three growth types annotated: "Passive" (natural shoots), "Active" (grafted branches tagged "[user-confirmed]"), "GC" (gardener pruning dead wood: "Contradictions/Outdated/Gaps/Drift"). Cut branches fall into compost bin labeled "Trace→Critic→Refiner". Rich soil feeds back to roots, annotation: "Data Flywheel: 部署即训练". A ratchet on the trunk prevents shrinking — "棘轮效应". A calendar shows "6 months × 5 rewrites (Manus)". RIGHT HALF: A Leonardo da Vinci mechanical exploded-view — three separated horizontal layers with dashed assembly lines. Top: "Application Layer" (clock face). Middle: "Harness Core" (gear train, model-agnostic). Bottom: "Model Adapter" with three interchangeable engines side by side ("Claude", "GPT", "Gemini") fitting the same interface. Annotation: "换模型只动底层". A timeline arrow: "Prompt Eng→Context Eng→Harness Eng". Banner across bottom: "系统越用越好, 换脑不用重建 — 进化机制是人设计的". Predominantly black and white graphite. Selective warm crayon: amber on healthy growth and universal mounting interface, terracotta on compost cycle and interchangeable engines.
> ```

---

## 问题五：AI 看不见自己的问题，也管不住自己的行为

*对应要素：C9 可观测性 + C10 企业安全与合规 + C11 评估与基准测试*

前四个问题解决了"怎么让 Agent 干活"。但 AI 不会自己审视"我干得好不好"，更不会自己判断"我是不是越界了"。监控、安全、评估——这三件事全靠外部系统，而外部系统全靠人设计。

### C9：可观测性与质量度量

你无法改进你无法衡量的东西。

可观测性覆盖六个维度：上下文健康度、执行效率、验证质量、上下文治理、工具可靠性、端到端性能。技术实现依赖六钩子中间件架构——在 Agent 执行的六个关键节点埋点，采集运行时数据。

一个容易被忽略的要求：**审计要捕获 Agent 推理的"为什么"，而不仅仅是"做了什么"**。SOC 2 合规需要业务上下文和取证重建能力。Agent 不是黑盒——或者说，不应该是黑盒。

还有一条经验值得记住：**5 个清晰的工具优于 20 个模糊的工具**。工具多了，模型选错工具的概率就上去了。好的错误信息等于一次教学——告诉 Agent 什么违反了、为什么违反、怎么修。

### C10：企业安全与合规

这一块是写给做 B 端产品的同学看的。

有一组数据很刺眼：Agent 可以做到 100% 任务完成率，同时只有 33% 的策略遵从率。任务完成和安全合规是两个完全独立的维度。你的 Agent 把活干完了，但它在过程中泄露了客户数据——这种"高效但违规"的场景在企业环境下是不可接受的。

另一个缺口更危险——**治理-遏制缺口**。58% 的组织有 Agent 行为监控，但只有 37% 有终止开关。能看到 Agent 在做什么，但没办法在它做错的时候叫停。这就像装了摄像头但没有刹车的车。

企业安全的核心挑战还包括：Agent 通过数据库查询绕过传统 DLP（数据防泄露）、影子 AI（员工私自使用的未授权 Agent）形成不可控攻击面、跨业务的"伦理墙"隔离。这些都不是传统信息安全的思路能解决的，需要在 Harness 层面从设计上内置安全。

### C11：评估与基准测试

可观测性是"运行时看数据"，评估是"离线量化效果"。89% 的团队有可观测性，但只有 37% 有在线评估。这两件事差别很大。

评估最重要的一对指标是 **pass@k 和 pass^k**。pass@k 是 k 次中至少成功 1 次（衡量能力上限），pass^k 是 k 次全部成功（衡量一致性）。一个模型单次成功率 75%，看起来不错。但如果你需要它连续 3 次都成功？75% × 75% × 75% = 42%。在生产环境，一致性远比能力上限重要。

评估的成本也值得注意。用 LLM 做评判，每次 $0.06；用 Agent 做评判，每次 $0.96——16 倍差距。评估体系本身的经济性也是工程决策。

> **C9+C10+C11 一句话**：看得见（可观测）、管得住（安全）、测得准（评估）——三条腿缺一条桌子就塌。

<!-- 图6：问题五 组级图 -->

> **图片提示词（信息图，非手稿风格）**：
>
> ```
> Clean modern infographic on white background, flat design with thin line icons. Title: "保障：可观测 × 安全 × 评估". Three vertical columns side by side, connected at the bottom by a shared foundation bar. LEFT column "C9 可观测性": a radar chart icon with 6 axes (上下文健康/执行效率/验证质量/上下文治理/工具可靠性/端到端性能), below it 6 small hook icons labeled "六钩子中间件". CENTER column "C10 企业安全": a shield icon split into sections — "机器身份认证", "治理-遏制缺口: 58%监控 vs 37%终止", "Prompt级DLP", "伦理墙". A warning badge: "100%完成 but 33%合规". RIGHT column "C11 评估": two bar charts comparing pass@k (能力上限) vs pass^k (一致性), annotation "75%单次 → 42%连续三次". A cost comparison: "LLM-Judge $0.06 vs Agent-Judge $0.96". Foundation bar text: "看得见 × 管得住 × 测得准 — 全靠人设计的外部系统". Style: Notion/Linear-style, no 3D, thin lines, icons and data points, bilingual labels. Three color accents: blue (observable), red (security), green (evaluation).
> ```

---

## 五个问题不是孤岛

这 11 个要素之间有明确的协作关系，不是各自独立的清单。

<!-- 图7：要素关系全景 -->

> **图片提示词（信息图风格）**：
>
> ```
> Clean modern diagram on white background, thin dark lines, minimal style. Title: "5个工程问题 × 11个要素 — 结构关系". Layout: Five color-coded problem zones arranged in a network. Zone 1 "工作空间" (blue): C1↔C2. Zone 2 "护栏" (orange): C3↔C4. Zone 3 "分工" (green): C5↔C8. Zone 4 "进化" (purple): C6↔C7. Zone 5 "保障" (red): C9+C10+C11. Cross-zone arrows with labels: C3→C1 "约束信息流入", C6→C4 "软知识编译为硬规则", C10→C3 "合规延伸约束", C11↔C6 "评估驱动演化", C8→C7 "人机协作通过可拆卸实现". Style: Notion/Linear-style, no 3D, thin connecting lines with small text labels, bilingual Chinese-English.
> ```

几条关键关系：

C1 和 C3 双向依赖——上下文管理需要架构约束限制信息流入，约束本身也是上下文的一部分。C6 和 C4 之间有一条"软变硬"的通道——Review 中反复出现的问题被编码为新的 lint 规则，人的经验变成机器的检查点。C10 是 C3 在合规维度的延伸——安全约束本质上还是约束，只是多了法规和审计的要求。C11 和 C6 形成双向飞轮——评估数据驱动演化改进，演化产生的执行轨迹又成为评估的输入。

这些关系说明一件事：这 5 个问题是一个有机系统，不是可以挑三四个做的功能清单。

---

## 关键数据汇总

把文中提到的核心数据集中放一下，方便对照：

| 数据 | 说明 | 来源 |
|------|------|------|
| 52.8% → 66.5% | 不换模型只改 Harness 的提升 | LangChain |
| 6.7% → 68.3% | 仅改输出格式的十倍性能差 | Can Boluk / Hashline |
| #33 vs #5 | 同模型不同 Harness 的排名差 | HumanLayer |
| 50-70% 下滑 | 上下文接近极限时的性能衰减 | 腾讯新闻 |
| 2-3 倍 | 有效验证对输出质量的提升 | 腾讯新闻 |
| 100% vs 33% | 任务完成率 vs 策略遵从率 | Beyond Task Completion |
| 58% vs 37% | 有监控 vs 有终止开关 | MintMCP |
| 89% vs 37% | 有可观测 vs 有在线评估 | State of Agent Eng |
| 75%+ | 生产环境使用多模型路由的比例 | State of Agent Eng |

每一个数据点都在说同一件事：**环境工程的杠杆效应远超大多数人的直觉**。

---

## 从织布工到织布机工程师

写这篇文章的时候，我一直在想一个问题：在 AI 写代码的时代，程序员该学什么？

这个焦虑很真实。不止程序员，每一个被 AI 冲击的行业里的人都在问同样的问题。

但如果你回看历史，答案其实很清楚。

工业革命，织布工人消失了，织布机工程师诞生了。电力革命，烛台匠消失了，电气工程师诞生了。计算革命，打字员消失了，软件工程师诞生了。

每一次技术革命消灭的是"直接操作者"，催生的是"系统设计者"。

AI 革命也不例外。"写代码的人"会越来越少，但"为大模型设计工作环境的人"——也就是 Harness Engineer——会越来越多。

回到开头那个 PPT 的问题。我给领导的方案不是"换更贵的模型"，而是"让模型在更合适的环境里工作"。这个思路推广到极致，就是 Harness Engineering。不是让 AI 更聪明，而是让 AI 工作的环境更聪明。

这 11 个工程问题，AI 一个也解决不了。但能解决它们的人，就是 AI 时代最不可能被淘汰的人。

<!-- 图5：结尾呼应图 -->

> **图片提示词（手稿风格）**：
>
> ```
> Hand-drawn pencil sketch on faint grid paper, classical European scientific manuscript style. At the top, the title "从操作者到设计者" in elegant Renaissance hand-drawn calligraphy in Chinese, highlighted with soft amber crayon coloring. Four horizontal vignettes arranged as a timeline from left to right. Scene 1 (1760s): A weaver working at a hand loom, crossed out with a gentle X, transitioning to a figure designing a power loom blueprint. Scene 2 (1880s): A candlemaker at work, transitioning to an electrical engineer with circuit diagrams. Scene 3 (1970s): A typist at a typewriter, transitioning to a programmer at a terminal. Scene 4 (2026): A programmer writing code on a screen, transitioning to a person arranging constraint files, memory structures, and validation pipelines around an AI agent icon — labeled "Harness Engineer". Below the timeline, a single unifying annotation: "每次革命消灭操作者, 催生设计者". The fourth scene is larger and highlighted with warm amber/terracotta crayon. Predominantly black and white graphite with fine crosshatching. Dashed timeline arrow connecting all four scenes.
> ```

---

*本文基于 30+ 篇文献的系统分析（扎根理论编码 + Zachman 完备性检验 + Beer VSM 结构验证），完整技术细节见内部文档 012_SYSTEM。*

*核心参考：*

1. [The Anatomy of an Agent Harness](https://blog.langchain.com/the-anatomy-of-an-agent-harness/) — LangChain
2. [Improving Deep Agents with Harness Engineering](https://blog.langchain.com/improving-deep-agents-with-harness-engineering/) — LangChain
3. [Harness is the New Dataset](https://news.qq.com/rain/a/20260326A080NG00) — 腾讯新闻
4. [Harness Engineering 为什么是 Agent 时代的"控制论"](https://news.qq.com/rain/a/20260318A03ZHX00) — 腾讯新闻
5. [Natural-Language Agent Harnesses](https://arxiv.org/html/2603.25723) — arXiv
6. [Demystifying Evals for AI Agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) — Anthropic
