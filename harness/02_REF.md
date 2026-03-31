# 参考资料索引

## 一、Harness Engineering 方法论核心文献

### 1. LangChain 系列（Harness 概念的主要定义方）

**The Anatomy of an Agent Harness** — LangChain Blog
提出 Agent = Model + Harness 的核心公式。定义 Harness 为"模型之外的一切代码、配置和执行逻辑"。详细阐述了 Harness 的组成层：System Prompts、Tools & Skills、Infrastructure、Orchestration Logic、Middleware/Hooks。提出 Working Backwards 方法论、渐进式披露、Ralph Loop、自验证闭环等关键设计模式。指出模型与 Harness 共演化趋势。
https://blog.langchain.com/the-anatomy-of-an-agent-harness/

**Improving Deep Agents with Harness Engineering** — LangChain Blog
实验数据：仅修改 Harness（不换模型），Terminal Bench 2.0 成绩从 52.8% 提升到 66.5%，从榜外进入 Top 5。关键中间件：LocalContextMiddleware（启动时映射环境）、PreCompletionChecklistMiddleware（拦截退出强制验证）、LoopDetectionMiddleware（检测死循环）。提出"推理三明治"（xhigh-high-xhigh）策略。五条核心发现：上下文工程、自验证、Trace 反馈、短期模式检测、模型特化调优。
https://blog.langchain.com/improving-deep-agents-with-harness-engineering/

**How Middleware Lets You Customize Your Agent Harness** — LangChain Blog
定义了 Agent 中间件的六个拦截点：before_agent、before_model、wrap_model_call、wrap_tool_call、after_model、after_agent。覆盖合规（PII 脱敏）、动态控制（运行时工具注入）、上下文管理（摘要压缩）、生产就绪（重试/降级）、工具初始化等场景。
https://blog.langchain.com/how-middleware-lets-you-customize-your-agent-harness/

**Harness Capabilities — LangChain Docs**
Deep Agents 的 Harness 能力文档：FilesystemMiddleware（文件上下文卸载与长期记忆）、SubagentMiddleware（上下文隔离的子代理）、SummarizationMiddleware（上下文溢出管理）、SkillsMiddleware（按需加载能力）。
https://docs.langchain.com/oss/python/deepagents/harness

### 2. OpenAI 系列（Codex Harness 工程实践）

**Harness Engineering: Leveraging Codex in an Agent-First World** — OpenAI (Ryan Lopopolo, 2026.2.11)
★ 极高价值。OpenAI 团队用 Codex 构建了百万行零人工代码产品的完整复盘。关键上下文管理洞察："Give Codex a map, not a 1,000-page instruction manual"——AGENTS.md 作为约 100 行的目录索引，docs/ 目录作为 system of record，实现渐进式披露。明确指出"Context is a scarce resource"，巨型指令文件会挤占任务和代码的上下文空间。"From the agent's point of view, anything it can't access in-context while running effectively doesn't exist"——所有知识必须在仓库内、版本化、可寻址。熵治理："golden principles" + 定期 GC agent 扫描并修复偏差，类比垃圾回收。工程实践：3人团队平均每人每天 3.5 个 PR，扩展到 7 人仍未触发 Brooks 定律。
https://openai.com/index/harness-engineering/

**Unrolling the Codex Agent Loop** — OpenAI (Michael Bolin, 2026.1.23)
★ 极高价值，Codex Agent Loop 的权威技术深度解析。上下文管理核心内容：（1）Prompt 结构——system（模型指令）→ tools → developer（sandbox 权限）→ developer（config）→ user（AGENTS.md 聚合指令，32KiB 上限）→ user（环境上下文 cwd/shell）→ user message，顺序由服务端决定。（2）Prompt 缓存——"old prompt is exact prefix of new prompt"是刻意设计，使采样从二次方降为线性；缓存失效原因：mid-conversation 工具变更、模型切换、sandbox/cwd 变更；MCP 工具枚举顺序不稳定曾导致缓存失效 bug。（3）Compaction 演化——从手动 `/compact` 命令 → 自动 `auto_compact_limit` 阈值触发 → `/responses/compact` 端点返回 opaque `encrypted_content` 保留模型对原始对话的潜在理解。（4）ZDR（Zero Data Retention）合规——不使用 `previous_response_id`，每次请求无状态，加密推理内容可由 OpenAI 持有的解密密钥恢复。（5）环境变更处理——sandbox/cwd 变更时追加新 developer/user 消息而非修改历史消息，保护缓存前缀。
https://openai.com/index/unrolling-the-codex-agent-loop/

**Unlocking the Codex Harness: How We Built the App Server** — OpenAI (Celia Chen, 2026.2.4)
Codex App Server 架构详解。JSON-RPC over stdio 双向协议，支撑 CLI、Web、IDE（VS Code/JetBrains/Xcode）、macOS App 共享同一 Harness。三层会话原语：Item（原子 I/O 单元，有 started/delta/completed 生命周期）→ Turn（一次用户输入到 agent 完成）→ Thread（持久化对话容器，支持 create/resume/fork/archive）。App Server 内部四组件：stdio reader → Codex message processor → thread manager → core threads。Web 端使用容器化部署，状态保存在服务端（标签页关闭不影响任务继续）。上下文相关：提到 "auto-compaction in Codex core" 作为服务端可独立升级的能力。
https://openai.com/index/unlocking-the-codex-harness/

**Building Production-Ready AI Agents: Codex CLI Architecture** — ZenML
对 Codex CLI 架构的技术分析：Agent Loop 设计、Prompt 构建（instructions + tools + input）、SSE 流式响应、配置层级（$CODEX_HOME → 项目根目录 → 当前目录）、32KiB 指令限制。
https://www.zenml.io/llmops-database/building-production-ready-ai-agents-openai-codex-cli-architecture-and-agent-loop-design

**OpenAI Compaction API Guide** — OpenAI Developer Docs
Codex 上下文压缩的官方 API 文档。两种实现方式：服务端压缩（设置 `compact_threshold` 后自动触发，返回加密的 opaque compaction item）和独立 Compact 端点（`/responses/compact`，无状态、ZDR 友好，接受完整上下文窗口返回压缩版本）。关键原则：standalone compact 的输出即权威的下一轮上下文窗口，不应再裁剪。
https://developers.openai.com/docs/guides/compaction

**Codex CLI GitHub Repository** — OpenAI
Codex CLI 开源代码仓库（Rust）。核心上下文管理模块位于 [`codex-rs/core/src/context_manager/`](https://github.com/openai/codex/tree/main/codex-rs/core/src/context_manager)（history.rs、normalize.rs、updates.rs）、[`codex-rs/core/src/compact.rs`](https://github.com/openai/codex/blob/main/codex-rs/core/src/compact.rs)（本地压缩）、[`codex-rs/core/src/compact_remote.rs`](https://github.com/openai/codex/blob/main/codex-rs/core/src/compact_remote.rs)（远端压缩）。BM25 tool_search 工具搜索、中间截断输出策略、上下文增量 diff 更新机制。两阶段 Memory Pipeline（rollout extraction + global consolidation）。
https://github.com/openai/codex

**Context Compaction Strategies: Comparative Analysis** — badlogic (GitHub Gist)
Claude Code、Codex CLI、OpenCode、Amp 四款 Agent 的上下文压缩策略横向对比。关键发现：Claude Code 触发阈值约 95% 容量；Codex CLI 按 token 数触发（180k-244k），保留最近 20k tokens 的用户消息；OpenCode 用 prune 保护最近 40k tokens；Amp 完全不做自动压缩，靠 handoff/fork 手动控制。所有产品都承认多次压缩导致质量累积衰减。
https://gist.github.com/badlogic/cd2ef65b0697c4dbe2d13fbecb0a0a5f

### 3. Anthropic 系列（Claude Code / Cowork 实践）

**How Claude Code Works** — Anthropic Docs
Claude Code 的工作原理文档。
https://code.claude.com/docs/en/how-claude-code-works

**Claude Code System Prompts** — GitHub (Piebald-AI)
Claude Code 全部系统提示词的逆向整理：18 个内置工具、Plan/Explore/Task 子代理提示词、CLAUDE.md、Compact、WebFetch、安全审查等模块。随版本更新。
https://github.com/Piebald-AI/claude-code-system-prompts

**Claude Cowork: Architecture, Capabilities, and Usage Overview** — TensorLake
Cowork 架构分析：基于 Claude Code 的 Agentic 基础，面向知识工作者。结构化计划、子代理协调、Plugin 机制（Skills + Connectors + Sub-agents 打包）。
https://tensorlake.ai/blog/claude-cowork-architecture-overview

**Claude Cowork System Prompt Analysis** — ClaudeCN
Cowork 系统提示词分析：三层设计（安全合规 → 交互语气 → 可靠性默认值）、三引擎执行（信息检索 → 行动执行 → 结构化输出）、Computer Use 能力、政策执行机制。
https://claudecn.com/en/blog/claude-cowork-system-prompt/

### 4. 综合分析与指南

**Skill Issue: Harness Engineering for Coding Agents** — HumanLayer Blog
最详尽的 Harness 配置点指南。五大配置点：CLAUDE.md/AGENTS.md（程序记忆）、MCP 服务器（工具扩展）、Skills（渐进式披露）、Sub-Agents（上下文防火墙）、Hooks（确定性控制流）。引用 ETH Zurich 研究：LLM 自动生成的 agentfile 反而降低性能且增加 20%+ 成本。关键洞察：Post-training coupling（Opus 4.6 在 Claude Code 中排 #33，但换 Harness 后排 #5）。
https://www.humanlayer.dev/blog/skill-issue-harness-engineering-for-coding-agents

**Harness Engineering: The Missing Layer Behind AI Agents** — Louis Bouchard
区分三个层次：Prompt Engineering = "问什么"；Context Engineering = "给模型什么信息"；Harness Engineering = "整个系统如何运转"。引用 Stripe 每周 1000+ 合并 PR、OpenAI 百万行零人工代码。提出 Harness Debt 概念：Harness 本身也需要维护。
https://www.louisbouchard.ai/harness-engineering/

**What Is Harness Engineering? Complete Guide 2026** — NxCode
五大支柱总结：Tool Orchestration、Guardrails & Safety Constraints、Error Recovery & Feedback Loops、Observability、Human-in-the-Loop Checkpoints。包含 Claude Code、Codex、Cursor 的对比分析。
https://www.nxcode.io/resources/news/what-is-harness-engineering-complete-guide-2026

**AI Agent Harness, 3 Principles for Context Engineering, and the Bitter Lesson Revisited** — Hugo Bowne-Anderson
Lance Martin 的三原则：Reduce（压缩上下文）、Offload（卸载到外部）、Isolate（多代理隔离）。Bitter Lesson 的应用层启示：随着模型快速进步，架构假设会在数月内过时，需要拥抱持续重构。
https://hugobowne.substack.com/p/ai-agent-harness-3-principles-for

### 5. 学术论文

**Natural-Language Agent Harnesses (NLAHs)** — arXiv (2603.25723)
首篇将 Agent Harness 形式化的学术论文。定义 NLAH 的组成：Contracts（输入输出规约）、Roles（角色分工）、Stage Structure（阶段拓扑）、Adapters/Scripts（确定性钩子）、State Semantics（持久化状态）、Failure Taxonomy（故障分类）。提出 Intelligent Harness Runtime (IHR) 架构。文件支撑的状态模块三性质：外部化、路径可寻址、压缩稳定。实验：OSWorld 上 NLAH 47.2% vs 原生代码 30.4%。
https://arxiv.org/html/2603.25723

## 二、Context Engineering 相关

**Context Engineering: The New Sensation** — 36Kr
Karpathy 和 Shopify CEO Tobi Lütke 推动"上下文工程"概念。Karpathy 在 2026 年 2 月进一步提出"agentic engineering"。
https://eu.36kr.com/en/p/3366869315372801

**Context Engineering for Developers: Complete Guide** — Faros AI
Context Engineering 的系统化定义与实施指南。
https://www.faros.ai/blog/context-engineering-for-developers

## 三、企业级 AI Agent 安全与治理

**Securing the Agentic Enterprise** — McKinsey
Agentic AI 如何重塑企业网络安全。
https://www.mckinsey.com/capabilities/risk-and-resilience/our-insights/securing-the-agentic-enterprise-opportunities-for-cybersecurity-providers

**Secure Agentic AI End-to-End** — Microsoft Security Blog
微软端到端 Agentic AI 安全框架。
https://www.microsoft.com/en-us/security/blog/2026/03/20/secure-agentic-ai-end-to-end/

**AI Agent Security: The Complete Enterprise Guide 2026** — MintMCP
企业 AI Agent 安全完整指南。数据：80.9% 团队已进入测试/部署阶段，平均管理 37 个 Agent。超过半数 Agent 无安全监控。75% 企业将安全合规列为最关键需求。
https://www.mintmcp.com/blog/ai-agent-security

**AI Agent Security in 2026: What Enterprises Are Getting Wrong** — AGAT Software
企业 AI Agent 安全常见错误。多租户架构下的安全风险放大。
https://agatsoftware.com/blog/ai-agent-security-enterprise-2026/

## 四、OpenCode 相关

**OpenCode Official Site & Docs**
OpenCode 官方文档：Agent 配置（Build/Plan 双主 Agent + General/Explore 子 Agent）、Skills（渐进式披露）、Tools、MCP Registry、Permission 系统（ask/allow/deny 三态 + bash 命令 glob 匹配）、Markdown Agent 定义格式。
https://opencode.ai/

**OpenCode GitHub Repository** — anomalyco/opencode
当前活跃的 OpenCode 代码仓库。TypeScript 为主（56.8%），Client/Server 架构，TUI 基于 Bun + Turbo 构建。132k stars，828 contributors，743 releases（截至 2026.3 最新 v1.3.5）。支持桌面应用（macOS/Windows/Linux）。LSP 开箱支持、模型无关（Claude/OpenAI/Google/本地模型）。MIT 协议。
https://github.com/anomalyco/opencode

注：早期版本曾托管于 github.com/opencode-ai/opencode（Go + BubbleTea），2025年9月归档。当前版本已用 TypeScript 完全重写。

**OpenCode Plugins Documentation** — OpenCode
OpenCode Plugin 机制完整文档。Plugin 是 JS/TS 模块，通过导出函数返回 Hooks 实现。支持的 Hook 包括：tool.execute.before/after（工具调用拦截）、experimental.chat.system.transform（system prompt 改写）、experimental.chat.messages.transform（消息历史改写）、experimental.session.compacting（压缩时注入上下文）、shell.env（环境变量注入）、event（全局事件监听）、自定义 tool 定义等。Plugin 可从 npm 或本地 .opencode/plugins/ 加载。
https://opencode.ai/docs/zh-cn/plugins/

## 五、评估与观测相关

**Evaluating Context Compression Strategies for Long-Running AI Agent Sessions** — Factory AI (2025.12)
★ 高价值。Probe-based 评估框架：四类探针（recall/artifact/continuation/decision）×六维评分（准确性/上下文意识/工件追踪/完整性/连贯性/指令遵循）。36,000+ 条生产消息，GPT-5.2 盲测评分。Factory 结构化摘要（3.70）> Anthropic 内置压缩（3.44）> OpenAI compact 端点（3.35）。关键发现：65% 企业 AI 失败归因于 context drift 而非 context exhaustion。
https://docs.factory.ai/guides/power-user/evaluating-context-compression

**Two Experiments We Need to Run on AI Agent Compaction** — Jason Liu (2025.8)
提出两个关键实验：（1）Compaction as Momentum——测试压缩时机对 Agent 工作"势头"的影响，在不同阈值（50%/75%/自然边界/Agent 自决）触发压缩，测量 backtracking 次数；（2）Trajectory Observability via Specialized Compaction——用领域特定的压缩 prompt 提取不同类型的故障模式（linter 循环、语言切换、用户反馈），再用 embedding 聚类发现群体模式。指出公开 benchmark 缺乏足够长的 Agent 轨迹。
https://jxnl.co/writing/2025/08/30/context-engineering-compaction/

**Beyond Black-Box Benchmarking: Observability, Analytics, and Optimization of Agentic Systems** — arXiv:2503.06745 (2025)
首个针对 Agentic System 可观测性的系统方法论。扩展 OpenTelemetry 引入 GenAI Events（创建/更新/启动/结束/失败等）。三层分析：被动（自动指标汇总）→探索性（根因分析、跨轨迹对比）→干预性（配置调优、组件替换）。提出执行流图编辑距离等新指标。ABBench 数据集（30 条日志），TAMAS 系统 60% benchmark 与 ground truth 一致。
https://arxiv.org/abs/2503.06745

**AI Agent Observability - Evolving Standards and Best Practices** — OpenTelemetry (2025)
OpenTelemetry GenAI SIG 的 AI Agent 语义约定标准化进展。两层约定：Agent Application Conventions（已定稿）和 Agent Framework Conventions（开发中）。两种插桩方式：内置（框架原生 emit）vs 外部 OTel 库。覆盖：Agent 执行模式、工具调用链、LLM 交互质量、VectorDB 操作。
https://opentelemetry.io/blog/2025/ai-agent-observability/

**Context-Bench: Benchmarking LLMs on Agentic Context Engineering** — Letta (2025.10)
专注于长运行上下文能力的 benchmark，基于 Letta Evals 框架构建。测试 Agent 能否跨多步骤工作流维护、复用和推理上下文——链式文件操作、项目结构关系追踪、长对话一致性决策。追踪 memory 管理效率、上下文重访频率和任务完成成本。结果：Claude Sonnet 4.5 以 74.0%/$24.58 领先，GPT-5 72.67%/$43.56。排行榜：https://leaderboard.letta.com/
https://www.letta.com/blog/context-bench

**OpenCode vs Claude Code** — Builder.io
OpenCode 与 Claude Code 的详细对比。
https://www.builder.io/blog/opencode-vs-claude-code

## 五、中文深度解析

**Harness Engineering：构建高可靠AI Agent的工程方法论** — 微信公众号（已收录为 022.md）
项目核心参考文章。提出 Harness Engineering 的"六大支柱"框架，是目前最结构化的中文 Harness 工程指南。六大支柱：① 上下文架构（Context Architecture）——上下文生命周期四阶段：注入→监控→压缩→归档，40% 利用率阈值警戒线；② 架构约束（Architectural Constraints）——用代码强制执行规则而非依赖 prompt 软约束，工具白名单、参数类型约束、权限分层、幂等性设计、沙箱隔离；③ 自验证循环（Self-Validation Loops）——前置条件验证、步骤后验证、进展检测（状态指纹比对）、终止条件检查，三级升级：自我校正→换策略→人工确认→中止；④ 上下文隔离（Context Isolation）——任务边界隔离、信息接口化、错误隔离、角色上下文分离；⑤ 熵治理（Entropy Governance）——上下文蒸馏（保留决策结论丢弃推理过程）、状态清理检查点、规则冲突检测、死亡引用清理、知识蒸馏沉淀；⑥ 可拆卸性（Detachability）——三层架构（应用层/Harness核心层/模型适配层），模型无关设计。每个支柱均以 Claude Code 为实践参考。最佳实践：以问题为导向、工具质量胜于数量、监控可观测性六维指标、先简单再复杂的渐进路径。
https://mp.weixin.qq.com/s/p1JPMhyM3yygJVCBhnBcaA

**Harness Engineering 是什么？从上下文工程到驾驭工程** — CSDN / shadowcz007
三层递进：Prompt Engineering（说什么）→ Context Engineering（给什么）→ Harness Engineering（什么条件下运行）。三层核心架构：Context Engineering（动态知识库）、Architectural Constraints（架构约束强制执行）、Garbage Collection（过时文档清理）。HashiCorp 联合创始人 2026.2 首次正式命名。关键数据：Can Boluk 仅改变代码编辑格式（Hashline），性能从 6.7% 升至 68.3%。
https://blog.csdn.net/shadowcz007/article/details/159111359

**AI Agent 系统架构进阶指南：Agent Harness 深度解析** — CSDN
五层完整架构：系统提示词 → 工具与技能系统 → 执行环境 → 任务编排逻辑 → 执行控制逻辑。文件系统三功能：持久存储、上下文卸载、任务协作。Ralph Loop 模式详解：拦截退出 → 重新注入目标 → 文件持久化跨窗口状态。核心洞察：优化 Harness 可能比换模型更重要。
https://blog.csdn.net/m0_59235245/article/details/159247402

**Harness Engineering 深度解析：AI Agent 时代的工程范式革命** — 知乎
https://zhuanlan.zhihu.com/p/2014014859164026634

**Harness Engineering 实践：Fitness Function 如何成为 AI 交付的防腐层** — 知乎
将软件工程中的 Fitness Function（适应度函数）概念引入 Harness 验证体系。
https://zhuanlan.zhihu.com/p/2017015528984717268

**Harness is the New Dataset：模型智能提升的下一个关键方向** — 腾讯新闻
★ 极高价值。提出"Harness 即新数据集"的核心观点。DeepMind Philipp Schmid 指出竞争优势在于 Harness 能捕获怎样的执行轨迹。Harness 6 组件按信息流分三层：信息层（记忆与上下文管理、工具与技能）→ 执行层（编排与协调、基础设施与保障）→ 反馈层（评估与验证、追踪与观测）。Mitchell Hashimoto 的四阶段 Session 分离：Research → Plan → Execute → Verify。模型-Harness 共进化循环：社区摸索 → Post-training → 模型内化 → 新 Harness 支持更高阶能力。关键数据：上下文接近极限时模型表现下滑 50-70%；有效验证机制可将输出质量提升 2-3 倍。
https://news.qq.com/rain/a/20260326A080NG00

**Harness Engineering 为什么是 Agent 时代的"控制论"？** — 腾讯新闻
★ 独特视角。将 Harness Engineering 置于控制论（Cybernetics）框架下分析。三次历史类比：瓦特离心调速器（1788）→ Kubernetes 声明式控制 → LLM Agent Harness。核心论证：当传感器（可观测性）和执行器（代码生成）足够强大时，工程师的工作就从直接操作转向系统设计。Agent 失败不是能力不足，而是缺乏对"什么是好"的认知——架构模式、设计约束、团队审美通常只存在于工程师脑中。验证优于生成的不对称性：基于 P vs NP 直觉，验证答案通常比生成答案容易。
https://news.qq.com/rain/a/20260318A03ZHX00

**Harness Engineering：当人类不再写代码，软件工程反而更"工程"了** — 博客园 / warm3snow
★ 对企业场景有直接启示。核心论点：工程师从"写代码的人"变成"设计笼子的人"。五大操作实践：应用可读性（Agent 通过浏览器和遥测"看到"自己的输出）、仓库即记录、架构编码化、合并哲学修订（降低门槛加快周期、纠错成本低于等待成本）、熵管理（持续清理 Agent 维护一致性）。团队规模从 3→7 人未触发 Brooks 定律——因为 Agent 间依赖是环境级别而非代码级别。局限性警示：框架偏向 Web 开发（LLM 训练数据饱和领域），嵌入式系统、小众语言可能回报递减。
https://www.cnblogs.com/informatics/p/19740439

**搜狗微信搜索：Harness Engineering Agent** — 微信公众号聚合搜索
约 604 条微信公众号文章结果（截至 2026.3.29），按相关度排列前 10 篇涵盖：核心定义、多 Agent 协作、核心问题解答、与 prompt/context engineering 的区别、Agent 时代新范式、长程运行秘诀等角度。主要公众号：ASA空间站、Noumena物自体科技、AI技术风向、数字零虎冲、Hyman的杂货铺等。
https://weixin.sogou.com/weixin?type=2&query=harness+engineering+agent

## 六、行业趋势

**2025 Was Agents. 2026 Is Agent Harnesses** — Aakash Gupta / Medium
2025 证明 Agent 可以工作；2026 是让 Agent 可靠工作的一年。新护城河是 Harness 质量。
https://aakashgupta.medium.com/2025-was-agents-2026-is-agent-harnesses-heres-why-that-changes-everything-073e9877655e

**State of Agent Engineering** — LangChain
Agent 工程现状报告。
https://www.langchain.com/state-of-agent-engineering

## 七、Harness 评估方法与实验框架

**Demystifying Evals for AI Agents** — Anthropic Engineering Blog
★ 极高价值，Anthropic 官方 Agent 评估指南。核心框架：三类评分器（代码型/模型型/人工）。关键指标对：pass@k（k 次中至少一次成功，衡量能力上限）vs pass^k（k 次全部成功，衡量一致性可靠性，如单次 75% → 三次全成功仅 42%）。Agent 类型细分评估：编码 Agent（单元测试+LLM规则）、对话 Agent（状态检查+模拟用户）、研究 Agent（根据性+覆盖+来源质量）、计算机使用 Agent（DOM/截图交互）。最佳实践路线图：20-50 个任务起步 → 任务质量保证 → 环境隔离 → 评分器校准 → 饱和监测。关键发现：检查 Agent 是否遵循特定步骤序列的做法过于僵硬，应评估输出结果而非执行路径。
https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents

**Natural-Language Agent Harnesses (NLAH) — 消融实验方法** — arXiv 2603.25723
首篇对 Harness 模块进行严格消融实验的学术论文。三个研究问题：RQ1（行为效果：完整 Harness vs 消融版）、RQ2（可组合性：逐模块递增添加测量独立贡献）、RQ3（迁移：代码 Harness vs 自然语言 Harness 配对比较）。量化指标体系：任务解决率、提示词 token 数、完成 token 数、工具调用次数、LLM 调用次数、总运行时间、API 成本。关键方法：差分贡献度量（添加模块后解决率 - 基础解决率）。数据：自进化模块 +4.8%，多候选搜索反而 -2.4%；NLAH 在 OSWorld 上 47.2% vs 原生代码 30.4%。
https://arxiv.org/html/2603.25723

**HAL-Harness (Holistic Agent Leaderboard)** — Princeton PLI
标准化的可复现 Agent 评估框架。支持 9+ 基准测试（SWE-bench、USACO、AppWorld、τ-bench、OSWorld 等）。核心特性：框架无关（不限制 Agent 实现）、全面并行化、加密轨迹存储防止污染、统一 CLI 接口。跨领域综合评估：编码+工具调用+科学推理+人机协作。
https://github.com/princeton-pli/hal-harness

**The Importance of Agent Harness in 2026** — Philipp Schmid (DeepMind)
Harness 将模糊的多步流程转化为可记录、可评分的结构化数据。关键洞察：1% 的排行榜差异无法检测模型在第 50 步后的漂移。评估需覆盖 50-100 次工具调用的长期可靠性，而非单轮准确率。Harness 的三重作用：验证真实进度、赋能用户体验、创建反馈循环。
https://www.philschmid.de/agent-harness-2026

**Harness Engineering with LangChain DeepAgents and LangSmith** — Analytics Vidhya
LangSmith 作为 Harness 可观测性平台的实践。评估方法：创建多个 Agent 变体（不同系统提示词），在相同问题集上系统对比。核心指标：Pass@1（生产系统金标准）、Pass@k、延迟、token 消耗。ModelCallLimitMiddleware 约束模型调用次数作为 Harness 控制手段。
https://www.analyticsvidhya.com/blog/2026/03/harness-engineering/

**Beyond Task Completion: An Assessment Framework for Evaluating Agentic AI Systems** — arXiv
超越任务完成率的 Agent 评估框架。支柱消融研究：Tools 支柱故障率最高（平均 7.67 次失败）、Memory 故障随复杂度递增（0.67→3.67）、Environment 护栏违规仅在复杂场景出现。LLM-as-Judge 成本 $0.06/14.7秒 vs Agent-as-Judge 成本 $0.96/913秒。
https://arxiv.org/html/2512.12791v1

**Evaluations for the Agentic World** — McKinsey / QuantumBlack
McKinsey 对多 Agent 系统评估方法的分析。多 Agent 系统的非确定性使传统 LLM 评估方法失效，需要全新的评估范式。
https://medium.com/quantumblack/evaluations-for-the-agentic-world-c3c150f0dd5a

**The Reliability Gap: Agent Benchmarks for Enterprise** — Paul Simmering
企业级 Agent 基准测试的可靠性差距分析。
https://simmering.dev/blog/agent-benchmarks/

**ECC (Everything Claude Code) v1.8.0** — GitHub
跨平台 Agent Harness 性能优化系统。997 项内部测试、116+ Skills、28 Agents、102 安全规则。在 Claude Code / Cursor / OpenCode / Codex 间实现行为一致性。用 SWE-bench Pro 和 Terminal-Bench 2.0 作为跨 Agent 的苹果对苹果比较基准。
https://github.com/affaan-m/everything-claude-code

## 八、项目内部文章

**020_PERSPECTIVE_1.md** — AgentScope 团队视角
阿里巴巴 Agent Framework 团队（AgentScope）的 Harness 实践总结。Harness 五维度：分层记忆、上下文工程、工具与沙箱、编排与协作、验证与反馈闭环。三类记忆：程序记忆(AGENTS.md)、情景记忆(Session/Checkpoint)、语义记忆(知识库)。Everything is a File 理念。三种演化机制：被动(hot-path)、主动(显式)、后台(GC)。

**021_PERSPECTIVE_2.md** — Harness 工程落地视角
从实际开发痛点出发的 Harness 深度解析。核心原则：仓库是 Agent 的操作系统、渐进式披露、机械验证优先于直觉、协调者不写代码。四层验证管道：build → lint-arch → test → verify。子代理隔离与模型分级策略。自演化闭环：Trace → Critic → Refiner → 规则更新。轨迹编译（成功模式脚本化）。

**022.md** — Harness Engineering 六大支柱体系（微信公众号文章）
最结构化的 Harness 工程指南。提出六大支柱：上下文架构、架构约束、自验证循环、上下文隔离、熵治理、可拆卸性。每个支柱均含设计原则、工程落地方法、Claude Code 实践参考。提出渐进实施路径（六阶段）和四大最佳实践。与其他方法论（SDD、LLMOps、RAG、传统软件工程）的关系定位。
