本人所在的团队负责维护阿里巴巴 Agent Framework 框架，业界领先的 AgentScope（Python/Java）、Spring AI Alibaba 都是我们团队开源出来的智能体框架，框架在阿里巴巴集团内部、业界都有着非常广泛的应用，尤其是在 Java 智能体开发方向，目前可以说是国内事实标准的、采用度最高的开发框架。
﻿
在我们支持众多用户、超 1000+ 企业级智能体应用落地的过程中，我们与用户合作输出了大量定制化的智能体编排、记忆管理等方案，帮助很多企业成功的实现了智能体落地，同时，我们也一直在思考如何将这些经验沉淀为系统化的解决方案，逐步总结出了包括 任务规划与分解、文件系统上下文管理、子 Agent 委派、长期记忆、闭环反馈校验等系统解决方案。
﻿
随着 Claude Code、OpenClaw 等产品的广泛应用，我们发现自己的实践经验与产品中广泛采用的 Harness 概念非常相似。因此，在这篇文章中我们尝试总结 Harness Engineering，同时引出我们将要发布的 AgentScope Harness Framework 框架。
Harness Engineering 
为什么需要 Harness
对于很多企业开发者而言，在使用 ReactAgent 解决企业需求的过程中，可能有如下的强烈感受：开发简单、Token消耗大、效果不稳定。尤其是对于一些复杂任务——比如 "帮我调研竞品、整理成报告、存到文件里"——Agent 就开始展现出以上问题了。
问题的本质在于：单纯的 ReactAgent 是"浅的"，它的核心架构是一个 ReAct 循环：推理 → 调个工具 → 再推理 → 再调工具……这套循环对短平快的任务没问题，但面对需要多步规划、跨越大量上下文、拆解子任务的复杂工作，它会迷失方向——要么忘了自己在做什么，要么上下文塞满了不知道怎么管理，要么一条路走到黑不懂得拆解。
﻿
Claude Code、Manus 这类产品为何在各自的垂直领域有如此好的表现呢？因为它们在 ReAct 循环之上，额外实现了几个关键能力：任务规划与分解、文件系统上下文管理、子 Agent 委派、长期记忆、闭环反馈校验，业界把这种附加于 Agent Loop 之上，来保障 Agent 运行效果的工程实践叫做 Harness。
怎么定义 Harness
Harness 回答的是除了模型能力与推理本身之外，我们还必须为模型装配什么，才能把它变成可完成真实工作的系统设计与实践。
相比于我们在 AgentScope、Spring Ai Alibaba 等框架中所定义的 ReactAgent 模式，Harness Engineering 不是再写几个 Tool，而是围绕模型智力做状态、执行、知识、约束与观测的系统设计：同一模型在不同 Harness 下表现可能差异巨大。
﻿
Langchain 社区在博客中给出的 Harness 定义如下：
﻿
Agent = Model + Harness 
﻿
在开发 Agent 的过程中，凡是不属于模型本体的东西，都可以视为 Harness 的一部分（提示词、工具与技能描述、执行环境、编排逻辑、中间件与可强制执行的策略等）。
﻿
﻿﻿
如何实施 Harness，有哪些关键事项
从 “我们希望 Agent 表现出什么行为” 反推到工程上，Harness 通常需要解决如下工程问题：
﻿
﻿﻿
结合业界 Coding Agent、OpenClaw 等产品思路，我把一些关键能力、实现方案总结如下：
维度
Harness 要解决什么问题
典型实现形态
分层记忆与经验沉淀（Memory）
Agent 应该遵循的规则，包含过往经验学习与沉淀等，可持续迭代进化。
●
AGENTS.md，规则沉淀与路径导航
●
基于文件系统的语义化记忆，Procedural / Semantic / Episodic 
●
SKILL 标准流程
●
GC Agent 汇总与清理机制
工作区上下文工程（Context）
上下文窗口有限，如何在有限的窗口内确保给到模型连续&有效的信息
●
System Prompt
●
压缩策略，包括大工具结果卸载（offload）
●
会话记忆召回策略
●
TODO List
工具与 Sandbox
在隔离环境中运行工具
●
Bash/Filesystem/Python/Fetch工具集
●
Sandbox 生命周期管理
●
分布式场景下的工作空间隔离与共享
编排与协作
单轮对话无法覆盖复杂任务分解与并行
●
子智能体定义与注册规范，CompiledAgent、SpecAgent、RemoteAgent
●
子智能体交互与隔离规范，workspace隔离共享、异步响应
验证与反馈闭环
避免 agent 过早停止、错误累积、无法自检；为智能体施加软性、硬性规则检查等校验机制。
●
Hook
●
Rules
●
Ralph Loop
●
Browser Agent



从 Coding Agent、OpenClaw 看 Harness 实践
分层记忆与经验沉淀（Memory）
参考 Cognitive Architectures for Language Agents论文，我们可以将 Agent 的记忆分三类，Harness 对每类都提供对应的工程实现。包括 Langchain 也在其博客中做了类似的分类。
﻿﻿
1.1 程序记忆（Procedural Memory）= 行为规则
通过 
AGENTS.md 声明智能体应遵循的规则与流程，简单来说，编写 AGENTS.md 就像是给 AI 助手写一份“入职说明书”：你要清晰地定义它是谁（角色设定）、能干什么（技能工具），以及最关键的——它的脑子好不好使（记忆系统设计）。重点要说明它如何处理“记性”问题，比如是像翻笔记一样查找旧信息，还是把长篇大论总结成精华。
﻿
举个具体的例子。
﻿
如果你在为一个“私人旅游管家”写 AGENTS.md，文档里应该包含：
●
角色设定：它不仅是一个订票员，而是一个懂地理、会省钱、且记得用户偏好的资深导游。
●
记忆逻辑：这部分是核心。你要说明它怎么记住用户的习惯。例如：“短期内它要记住你刚填的出发地；长期来看，它要从过去的对话中检索出你‘不喜欢红眼航班’和‘对花生过敏’这些陈年旧事。”
●
工具调用：它怎么去查天气、怎么调取地图、怎么支付订单。
●
思考过程：当用户说“我想去个暖和的地方”时，它第一步是查历史喜好，第二步是搜实时天气，第三步才是出方案。
﻿
编写 AGENTS.md 的核心是为 AI 编写一份 “行为与记忆手册”：首先要明确它的身份（如代码专家或理财顾问）和行动逻辑 —— 即它如何像人一样通过“翻阅旧档案”（语义检索）或“看摘要笔记”（历史总结）来保证在多轮对话中不忘事、不带偏；最后要列出它能调用的外部工具清单，确保它在处理复杂任务时知道何时该思考、何时该动手。
﻿
一个巨大的 AGENTS.md 是失败的尝试 —— 情境是稀缺资源，当一切都'重要'时，一切都不重要了。正确做法是渐进式披露：Agent 从小而稳定的入口开始，被引导去下一步查看什么，而不是一开始就被淹没，它应该是起到导航地图的作用。
1.2 情景记忆（Episodic Memory）= 历史经验
存储早期决策周期的经验、历史事件流。
﻿
Harness 实现方式：
●
Session 机制：自动在每次运行前取回对话历史，运行后存入新消息（磁盘文件+索引快速检索+定期总结）
●
Checkpoint：Agent 崩溃后从最近检查点恢复，而不是从头开始
●
子 Agent 隔离：主 Agent 调用子 Agent 时，Harness 创建干净的内存作用域，防止试错过程污染主上下文
﻿
OpenAI SDK 的四种跨会话状态策略：
策略
存储位置
适用场景
﻿
result.to_input_list()﻿
应用内存
手动精确控制
﻿
session（SQLite/Redis 等）
自己的存储
持久化、可恢复的对话
﻿
conversation_id﻿
OpenAI 服务端
命名共享对话
﻿
previous_response_id﻿
OpenAI 服务端
轻量级续接



1.3 语义记忆（Semantic Memory）= 知识库
Agent 对世界和自身的知识，从外部知识库初始化。知识库可以包含标准 SKILLS 以及任意目录下的文档，具体取决于你要构建的 Agent 所属领域。
﻿
核心约束：
"Agent 在运行时无法访问的东西就不存在。用户的历史对话、业务规则、领域知识——如果不以结构化形式存入知识库，对 Agent 不可见。"
﻿
因此，所有知识必须以版本化的形式存在于 Agent 的知识库中，这里我们以文件系统方式存储：





1
2
3
4
5
6
7

AGENTS.md ← 地图（~100行），指向下层
memory/
├── procedural/ ← 行为规则和用户偏好
├── semantic/
│ ├── index.md ← 知识地图
│ └── domain/ ← 各业务领域知识
└── episodic/ ← 历史会话和 checkpoint


质量保障：结构校验 + 定期运行 GC Agent 扫描过时内容，自动提交修复建议。
工作区上下文工程（Context）
上下文是指 Agent 当前决策周期里活跃的信息，一般存储在内存 context window 里，是我们接下来一轮模型调用看到的内容，通常包括 “System Prompt + AGENTS.md + 压缩后的历史消息”。这其实就是过去大半年业界一直在实践的 Context Engineering。
﻿
同样是做 Context Engineering，Harness 相当于是提供了实施 Context Engineering 的环境：通过结构化的记忆召回、SKILLS、计划、压缩策略等核心机制，有效的避免 Agent 冷启动、经验遗忘、连续性差等问题。
问题
Harness 的解法
Context 膨胀
上下文压缩：把过去 50 轮压缩成摘要；读大文件时只给相关片段
Agent 跑偏
规划工具（todo list）作为"锚点"，即使是空操作也能让 Agent 保持任务焦点
指令太多
AGENTS.md 只做目录（~100 行），指向深层文件；过多指导让 Agent 退化成本地模式匹配



熵控制：让系统长期稳定
长期运行的 Agent 系统面临一个必然问题：Agent 会复现它接触过的模式，包括坏的模式，漂移不可避免。
对 Agent Builder 服务而言，熵增的来源更多样：
●
用户反馈写入了互相矛盾的偏好
●
知识库内容随时间过时但没有更新
●
Agent 的实际行为和程序记忆里的规则逐渐偏离
﻿
解法：把垃圾回收自动化
﻿﻿
类比垃圾回收：持续以小额方式清理知识库，比让矛盾和过时内容积累后集中处理要好得多。
﻿
后台 GC 扫描的四个目标：
●
不同文件之间的矛盾（A.md 说"偏好 X"，B.md 说"避免 X"）
●
过时内容（记录的决策已经被后来的行为推翻）
●
知识空白（某个领域有引用但没有实质内容）
●
漂移的模式（实际行为和规则文件描述不一致）
﻿
吞吐量改变了审核哲学：在高并发的服务端场景里，GC 建议中无语义冲突的修复可以自动应用；只有涉及用户偏好冲突或规则变更的，才升级到人工裁决。
AgentScope Harness 规划
AgentScope Java 是一个面向智能体的编程框架，用于构建 LLM 驱动的应用程序。它提供了创建智能体所需的一切：ReAct 推理、工具调用、内存管理、多智能体协作等。
﻿
在此基础上，我们正在基于实践经验积累基础上定义 Harness Framework，用来帮助开发者快速将 Harness Engineering 最佳实践应用于企业级智能体开发中。
﻿
﻿﻿
﻿
Harness Framework 层的关注重点
●
文件系统抽象与存储
●
语义化的分层记忆：Procedural / Semantic / Episodic 
●
分布式 Sandbox 生命周期管理与工作空间隔离
●
标准化的 Agent Spec 定义
核心思想：Everything is a File
四类记忆全部以文件形式存在。Agent 的所有状态都是可读、可写、可版本化的文件——这是让 Agent 能够自演化的基础条件。
﻿﻿
Agent 在运行时无法访问的东西就不存在。 所有知识必须落地为文件，才能被 Agent 利用和演化。
文件结构
目录组织的核心原则是渐进式披露——Agent 从入口开始，按需深入，不是一次性全部载入。





1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23

agent-root/
├── AGENTS.md ← 唯一总入口，~100行，只做目录和地图
│
├── memory/
│ ├── working/
│ │ └── current-task.md ← 当前任务状态，每次覆盖
│ ├── procedural/
│ │ ├── rules.md ← 强制约束，linter 验证
│ │ └── preferences.md ← 偏好，可演化
│ ├── semantic/
│ │ ├── index.md ← 知识地图，指向子文件
│ │ └── domain/
│ │ └── *.md ← 各领域知识
│ └── episodic/
│ ├── sessions/
│ │ └── YYYY-MM-DD.md ← 每次会话记录
│ └── checkpoints/
│ └── latest.json ← 最近状态快照
│
└── evolution/
├── pending-review.md ← 待人工审核的写入
├── gc-log.md ← 后台 GC 扫描日志
└── conflicts.md ← 发现的矛盾，待解决


每类文件的格式约定：
文件
格式
特殊要求
﻿
AGENTS.md﻿
Markdown，纯目录
不超过 100 行，每条指向具体文件
﻿
rules.md﻿
编号列表，每条可机械验证
有对应 linter 规则
﻿
preferences.md﻿
KV 风格，带置信度和来源
标注是 hot-path 写入还是用户确认
﻿
domain/*.md﻿
自由结构，带最后更新时间
必须有交叉链接
﻿
sessions/*.md﻿
时间线流水账
不整理，原始记录
﻿
checkpoints/latest.json﻿
结构化 JSON
包含任务状态、上下文摘要



三种演化机制的分工
三种演化可以并存，各有职责：
﻿

﻿
﻿
机制
触发条件
写入目标
置信度标注
冲突处理
被动（hot-path）
用户纠正、任务完成、发现新信息

﻿
pending-review.md﻿

﻿
[hot-path, unverified]﻿

写入 
conflicts.md，不覆盖
主动（显式）
用户说"记住"/"以后不要这样"
目标文件，需确认

﻿
[user-confirmed]﻿
覆盖旧值，旧值存档到 episodic
后台（GC）
定时或手动触发
﻿
gc-log.md，diff 形式
—
矛盾升级给用户裁决，不自动解决



前两种是"分配内存"，后台演化是"垃圾回收"。没有 GC，文件系统最终会变成一堆互相矛盾的碎片。
同一套模板，三种用途
三种用途的本质差别只是文件内容不同，Harness 架构完全一样。
用途
核心文件
演化信号来源
个人助理



﻿
user-profile.md、rhythm.md、preferences.md﻿
用户的纠正和反馈
工程场景



﻿
domain/architecture.md、domain/patterns.md、preferences.md﻿
CI 失败、code review、linter
知识管理



﻿
domain/*.md、connections.md、unknowns.md﻿
阅读、探索、主动推断



创建不同的文件集合，同一个 Agent 模板就自然变成三种完全不同形态的专用 Agent。
总结
AgentScope Framework 解决了如何构建企业级智能体的问题，Harness Framewok 解决如何构建具备更好效果的企业级 Agent 的问题。
﻿

