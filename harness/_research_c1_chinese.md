# Context Engineering 中文研究综合报告
## 上下文工程最新资料汇总（2025-2026）

**更新时间**：2026-03-30
**研究方向**：中文社区深度分析 + 开源实现 + 技术KOL + Anthropic官方指导

---

## 搜索方向1：中文社区对Context Engineering的深度分析（2025-2026）

### 1.1 核心概念界定

**定义与核心价值**
- 来源：知乎、CSDN、OSCHINA等中文技术社区的综合总结
- 定义：上下文工程是一门系统性地优化为LLM提供的信息有效载荷的学科
- 关键发现：**大模型的性能高度由推理时提供的上下文信息决定，而非仅由模型参数决定**
- 与提示词工程的关系：上下文工程是更准确、更专业的替代词，反映整个LLM应用范式的转变

**来源**：
- [知乎 - 上下文工程万字综述](https://zhuanlan.zhihu.com/p/1929823615228018882)
- [腾讯新闻 - 上下文工程综述](https://news.qq.com/rain/a/20250720A0029900)
- [CSDN - 提示词工程已Out！爆火的上下文工程](https://blog.csdn.net/csdnnews/article/details/149081734)

### 1.2 分类与框架体系

**三大基础组件** (基于论文对1400余篇论文的综述)
1. **上下文检索与生成** - 从海量数据中提取相关信息
2. **上下文处理** - 清洗、转换、压缩上下文
3. **上下文管理** - 动态调度和优化上下文分配

**四大系统级实现**
1. **RAG (检索增强生成)** - 动态引入外部知识
2. **记忆系统** - 短期、长期、混合记忆架构
3. **工具集成推理** - Agent工具调用的上下文优化
4. **多智能体系统** - 跨Agent的上下文共享与隔离

**来源**：[知乎 - 大语言模型上下文工程综述](https://zhuanlan.zhihu.com/p/1934605504165950750)

### 1.3 LLM存在的根本矛盾 (2025年新发现)

**核心发现**：
- LLM在复杂上下文理解上表现卓越
- **但在长文本生成、逻辑一致性维持上显著受限**
- 这构成了上下文工程需要解决的核心难题

**来源**：上述论文综述

### 1.4 Agent中的上下文管理策略

**记忆架构分类** (从AWS官方博客与InfoQ的分析)
- **短期记忆**：关于当前情境的上下文信息
- **长期记忆**：储存智能体历史行为，通过外部向量存储实现
- **混合记忆**：整合短期和长期记忆的混合方案

**LangChain提出的四种构建方式**
1. **写入上下文** - 预先注入必要信息
2. **筛选上下文** - 动态过滤相关信息
3. **压缩上下文** - 信息密度优化
4. **隔离上下文** - 不同任务间的上下文隔离

**来源**：
- [AWS官方 - Agentic AI基础设施实践](https://aws.amazon.com/cn/blogs/china/agentic-ai-infrastructure-practice-series-nine-context-engineering/)
- [InfoQ - AI Agent 上下文管理](https://www.infoq.cn/article/ufsvugyl6fvvmqx67ycc)
- [LangChain博客 - The Rise of Context Engineering](https://blog.langchain.com/the-rise-of-context-engineering/)

### 1.5 长时间任务中的挑战与优化策略

**核心挑战**：Agent平均多达50步的执行过程，系统需不断动态优化上下文

**优化策略体系** (来自Manus团队的Harness Engineering实践)
- **上下文压缩** - 摘要化处理历史信息
- **上下文替换** - 用关键信息替代冗余内容
- **上下文保留** - 保护关键任务上下文不被压缩
- **上下文锚定** - 固定重要的系统提示
- **上下文合并** - 多轮对话的智能合并
- **上下文共享** - 跨Agent的上下文复用
- **工具动态扩展** - 按需加载工具定义

**优化器演进方向**
- 当前：工程化实现为主
- 未来：模型驱动的优化器（可能由Claude/GPT自主决策上下文分配）

**来源**：
- [OSCHINA - Manus创始人复盘构建AI Agent的上下文工程实践](https://www.oschina.net/news/361386)
- [知乎 - 从Claude Code到Gemini CLI的上下文管理策略](https://zhuanlan.zhihu.com/p/1945440814282047866)

### 1.6 中文社区资源库与实践指南

**GitHub开源资源**
- [Context-Engineering-CN](https://github.com/xjthy001/Context-Engineering-CN) - 750K+字的完整中文教程，包括RAG系统、记忆架构、多智能体、认知工具、神经场论等即用模板
- [Awesome-Context-Engineering](https://github.com/Meirtz/Awesome-Context-Engineering) - 百余篇论文、框架和生产级实现指南汇总
- [context-engineering-intro](https://github.com/coleam00/context-engineering-intro) - 专注Claude Code的Context Engineering最佳实践

**来源**：以上GitHub链接

---

## 搜索方向2：开源Agent框架中Context管理的代码实现

### 2.1 Aider的Repository Map策略

**核心机制**：使用图论算法优化上下文分配
- 构建整个代码库的Repository Map（函数签名和文件结构）
- 使用AST (Abstract Syntax Tree) 进行代码结构化分析
- 通过图排序算法（Graph Ranking Algorithm）计算最优的文件选择

**优化逻辑**：
- 以源文件为节点，依赖关系为边的有向图
- 根据当前Token预算动态选择最重要的部分
- LLM可见整个仓库的类、方法、函数签名，即使未加载完整文件内容

**用户建议**：
- 只显式添加需要编辑的文件
- Aider会自动从相关文件中拉取上下文
- 这样能保持Token使用的高效

**来源**：
- [Aider官方文档 - Repository Map](https://aider.chat/docs/repomap.html)
- [Simran Chawla - Understanding AI Coding Agents Through Aider's Architecture](https://simranchawla.com/understanding-ai-coding-agents-through-aiders-architecture/)

### 2.2 LangChain的Middleware上下文管理

**核心实现**：ContextEditingMiddleware
- 维持最近N个工具结果在上下文中
- 当对话超过指定Token数时，自动清理旧的工具输出
- 保护最近K个工具结果永不清理（参数化配置）

**关键组件**：
- `ClearToolUsesEdit` - 工具输出的剪枝策略
- 支持灵活的Token阈值设置
- 在LangChain 1.0版本引入的Middleware架构

**代码位置**：`libs/langchain_v1/langchain/agents/middleware/`

**来源**：
- [LangChain官方文档 - Middleware](https://docs.langchain.com/oss/python/langchain/middleware/built-in)
- [LangChain博客 - Agent Middleware](https://blog.langchain.com/agent-middleware/)
- [Colin McNamara - LangChain Middleware Study Guide](https://colinmcnamara.com/blog/langchain-middleware-study-guide)

### 2.3 MemGPT的操作系统级上下文管理

**架构灵感**：操作系统内存管理
- Main Context = RAM（固定长度的标准上下文窗口）
- External Context = 二级存储（可选择移入Main Context的出线信息）

**核心创新**：
- LLM通过自生成函数调用控制数据在主外存储间的移动
- 学习何时调用特定函数来管理记忆
- OS风格的事件循环处理：Event（用户消息触发）→ Yielding（等待LLM请求）→ Function Chaining（多函数串联）

**关键特性**：
- 支持unbounded context（无限制上下文）
- 自适应记忆管理策略
- 中断处理机制

**来源**：
- [GitHub - deductive-ai/MemGPT](https://github.com/deductive-ai/MemGPT)
- [MemGPT官方研究](https://research.memgpt.ai/)
- [MemGPT论文 - arxiv 2310.08560](https://arxiv.org/abs/2310.08560)
- [DigitalOcean教程 - MemGPT with Real-life Example](https://www.digitalocean.com/community/tutorials/memgpt-llm-infinite-context-understanding)

### 2.4 Agent框架中的Token计数与预算管理

**Goose的上下文管理** (80%-95%阈值策略)
- **80%阈值**：自动对对话进行摘要，保留关键部分同时压缩冗余信息
- **95%阈值**：自动compaction系统激活，实现无限长度会话
- 目标：在保持会话连续性的前提下，避免频繁新建会话

**GitHub Copilot Agent**：
- 当前Token限制：64K tokens
- 限制导致长期任务失败
- 官方对增加上限的支持有限

**通用的Token预算策略**
- 模型返回剩余容量提示（remaining capacity）
- 开发者可根据此信息动态调整工作策略
- 预留缓冲：不要在达到限制时才停止，而要提前保存进度

**来源**：
- [Goose博客 - The AI Skeptic's Guide to Context Windows](https://block.github.io/goose/blog/2025/08/18/understanding-context-windows/)
- [Claude API文档 - Context Windows](https://platform.claude.com/docs/en/build-with-claude/context-windows)
- [GitHub Copilot Cloud Agent讨论](https://github.com/orgs/community/discussions/180198)

### 2.5 Agent Skills for Context Engineering框架

**GitHub开源项目**
- [Agent-Skills-for-Context-Engineering](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering)
- 专为context engineering、多Agent架构、生产级Agent系统而设计
- 包含具体的token计数API调用实现

**来源**：GitHub仓库

---

## 搜索方向3：技术KOL的深度分析与实战洞察

### 3.1 Simon Willison的Context Engineering倡议

**核心观点**（发表于2025年6月27日）
- "Context engineering" 正在取代 "Prompt engineering" 成为业界共识术语
- Prompt engineering的问题：被误解为"向聊天机器人输入文本"的笑话
- Context engineering的优势：**明确表达了"填充上下文窗口使任务可解"的核心目标**

**Context Engineering的完整定义**（来自Willison）
> "Context engineering is the delicate art and science of filling the context window with just the right information for the next step"

**核心成分**
1. 任务描述和解释
2. Few-shot示例
3. RAG检索的外部信息
4. 相关的多模态数据
5. 工具定义
6. 系统状态和执行历史
7. 压缩机制

**与Prompt Engineering的区别**
- Prompt Engineering：假设输入数据固定，优化单个提示
- Context Engineering：动态应对变化的数据，动态构建上下文
- **关键差异**：Context Engineering体现了"前面对话的响应是过程的关键部分"，而Prompt Engineering只强调用户提示

**来源**：
- [Simon Willison个人博客 - Context Engineering](https://simonwillison.net/2025/jun/27/context-engineering/)
- [Techmeme讨论](https://www.techmeme.com/250627/p29)

### 3.2 Simon Willison的Agentic Engineering Patterns指南（2026年最新）

**发布时间**：2026年3月4日
**核心文档**：https://simonwillison.net/guides/agentic-engineering-patterns/

**两大基础原则**
1. **"Code is now inexpensive"** - 生成代码不再昂贵，成本低廉
2. **"Preserve domain expertise"** - 保留人类的知识工作，让Agent处理例行实现任务

**最新趋势观察**（2025年的大进步）
- **推理能力引入**：推理(reasoning)被纳入frontier模型系列
- **长期Agent可行性**：基于Prompt Caching的突破使得Claude Code等长期运行的Agent成为可能
- Claude Code的核心：**整个harness围绕Prompt Caching构建**

**来源**：
- [Simon Willison - Agentic Engineering Patterns](https://simonwillison.net/guides/agentic-engineering-patterns/)
- [SimpleNews.ai - Simon Willison Publishes Agentic Engineering Patterns Guide](https://www.simplenews.ai/news/simon-willison-publishes-agentic-engineering-patterns-guide-yut1)

### 3.3 Martin Fowler的Context Engineering与Harness Engineering理论

**Context Engineering for Coding Agents文章**
- 发表在Martin Fowler官方博客
- 核心观点：**"Context is the bottleneck for coding agents now"**（上下文是编码Agent的瓶颈）
- 定义：上下文工程就是"策划模型看到的内容以获得更好的结果"

**Configuration与使用**
- 基础：工具提供的configuration features（rules、skills等）
- 实践：概念层的使用（specs、各种workflow）
- **现状**：几乎所有AI编码上下文工程都涉及markdown文件和prompts

**Harness Engineering理论**（Fowler在2026年2月的新作）
- 定义：将确定性规则与LLM基础检查结合保持Agent对齐
- 三个核心组件：
  1. **Context Engineering** - 上下文管理与优化
  2. **Architectural Constraints** - 架构级别的边界约束
  3. **Garbage Collection** - 无用信息的清理机制

**关键洞察**：
- 更大的上下文窗口≠更好的Agent表现
- 需要战略性的上下文管理
- Harness Engineering是生产级Agent的必需品

**来源**：
- [Martin Fowler - Context Engineering for Coding Agents](https://martinfowler.com/articles/exploring-gen-ai/context-engineering-coding-agents.html)
- [Martin Fowler - Harness Engineering](https://martinfowler.com/articles/exploring-gen-ai/harness-engineering.html)

### 3.4 Swyx与Latent Space播客

**Swyx背景**：
- 主要作品：Latent Space AI Engineer播客（与Alessio合办）
- 关注重点：如何leading labs构建Agents、Models、Infra、AI for Science

**Latent Space特色**：
- 技术深度分析
- 业界实践者访谈（in-person recording）
- 2023年创办至今的顶级AI工程播客

**相关主题**：
- "Context Graphs and Agent Traces" 作为特色话题被讨论
- 专业人士对Agent架构的深度分析

**来源**：
- [Latent Space官方](https://www.latent.space/)
- [Swyx个人主页](https://www.swyx.io/)

---

## 搜索方向4：Anthropic官方指导与最佳实践

### 4.1 "Building Effective Agents"官方研究（核心文献）

**发布机构**：Anthropic官方研究部门
**作者**：Erik Schluntz和Barry Zhang
**发布地址**：https://www.anthropic.com/research/building-effective-agents

**核心架构观**
- 基础单元：LLM + 增强功能（retrieval、tools、memory）
- **关键区分**：
  - **Workflows**：LLM和工具通过预定义代码路径编排（确定性）
  - **Agents**：LLM动态指导自己的过程和工具使用（自适应）

**设计哲学**
- 找到最简单的可行方案
- 仅在需要时增加复杂性
- 警示：**构建agentic系统会牺牲延迟和成本以换取性能**
- 可能的替代方案：完全不用agentic系统

**参考实现**
- Anthropic官方Cookbook提供实现代码
- GitHub地址：https://github.com/anthropics/anthropic-cookbook/tree/main/patterns/agents

**来源**：
- [Anthropic - Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)
- [Anthropic Cookbook](https://github.com/anthropics/anthropic-cookbook)

### 4.2 Prompt Engineering最佳实践（进化版）

**Anthropic的五阶梯方法**（从低到高）
1. **清晰直接** (be clear & direct) - 移除废话，使用平白语言
2. **清除冗余** (strip out fluff)
3. **避免歧义** (avoid ambiguity)
4. **提供示例** (use examples) - Few-shot学习格式和tone
5. **思维链** (chain of thought) - 鼓励逐步推理

**进阶技巧**
- XML标记：`<thinking>`、`<answer>`等结构化推理标记
- 角色分配：让模型扮演特定身份（但优先级较低）
- **注意**：基础做好后再加进阶技巧

**安全与伦理关注**
- 减少偏见
- 提高安全性
- 人道主义应用优化

**来源**：
- [Anthropic Prompt Engineering Guide评论](https://scalablehuman.com/2025/07/02/review-anthropics-prompt-engineering-guide/)
- [Anthropic官方 - Prompt Engineering for Business Performance](https://www.anthropic.com/news/prompt-engineering-for-business-performance)

### 4.3 Effective Context Engineering for AI Agents（Anthropic工程部文章）

**长期运行Agent的核心问题**：上下文污染约束

**三大解决方案**
1. **Compaction** - 上下文压缩
2. **Structured Note-Taking** - 结构化记录
3. **Multi-Agent Architectures** - 多Agent系统

### 4.4 工具设计最佳实践

**常见失败模式**：
- 工具集过大，功能冗余
- 工具选择歧义（Agent无法判断用哪个）
- 测试标准：如果人类工程师都不确定应该用哪个工具，Agent也做不好

**Few-shot设计最佳实践**
- **不要**：把所有边界情况列入提示
- **应该**：精心挑选多样化的代表性示例
- 目标：用少量示例展现预期行为

**来源**：[Anthropic - Effective Context Engineering for AI Agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)

### 4.5 长文档处理的最优策略

**关键发现**：文档位置很重要
- **最优放置**：长文档（~20K+ tokens）放在提示顶部
- **在其上方**：放置查询、指令、示例
- **性能改进**：对所有Claude模型都显著提升

**引用-验证策略**
- 先让Claude引用文档的相关部分
- 再让Claude执行任务
- 这样Claude可以快速过滤"噪音"，专注核心内容

**来源**：[Claude API文档 - Long Context Prompting Tips](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/long-context-tips)

### 4.6 多Agent架构设计（Subagent模式）

**核心思想**：为长任务和超大上下文提供解决方案
- 每个Subagent获得独立的上下文窗口
- 自定义系统提示、工具访问权限、独立权限
- Claude自动识别与Subagent匹配的任务并委托

**委托机制**
- Claude读取Subagent描述
- 当任务匹配时自动调度
- Subagent独立工作并返回结果

**来源**：[Claude Code文档 - Create Custom Subagents](https://docs.anthropic.com/en/docs/claude-code/sub-agents)

### 4.7 上下文自动压缩机制

**工作原理**
- 接近上下文限制时自动触发压缩
- 保留关键信息的同时压缩冗余
- **允许无限期工作**：继续在压缩后的新窗口中工作

**用户最佳实践**
- **不要**因为担心Token预算而早期停止任务
- **应该**：在接近预算时保存进度和状态
- 系统会在上下文刷新时自动处理

**来源**：Claude官方文档中的自动压缩机制描述

### 4.8 Claude模型规格（Model Card信息）

**Claude 3系列上下文窗口**
- Claude 3 Opus：200K tokens（训练中可达1M）
- Claude 3 Sonnet：200K tokens
- 最大输出：4,096 tokens

**长上下文性能**
- 99.4%平均recall（Haystack评估）
- 200K tokens时维持98.3%平均recall
- **关键发现**：模型在大上下文上的recall衰减轻微

**已知限制**
- 在大型代码库上下文中维持上下文困难
- 修订能力在新信息下表现不佳
- 缺乏找到简单解决方案的"品味"

**来源**：
- [Claude 3模型卡](https://www-cdn.anthropic.com/de8ba9b01c9ab7cbabf5c33b80b7bbc618857627/Model_Card_Claude_3.pdf)
- [Anthropic官方规格页面](https://platform.claude.com/docs/en/build-with-claude/context-windows)

---

## 与C1（上下文工程框架）的关系映射

### 概念对应关系

| C1框架层级 | 对应的研究发现 | 来源方向 |
|-----------|-------------|---------|
| **上下文来源层** | RAG检索、工具定义、状态信息 | 方向1：中文社区分类 |
| **上下文处理层** | 压缩、过滤、隔离策略 | 方向1 + 方向2代码实现 |
| **上下文管理层** | 92%阈值、compaction机制、多Agent | 方向2实现 + 方向4官方 |
| **模型感知层** | 模型特性（Recall衰减、长文档处理） | 方向4：模型卡 |
| **权衡决策层** | 延迟vs成本vs性能的三角形 | 方向3：KOL洞察 |

### 关键发现对C1的启示

1. **92%压缩阈值的正当性**
   - 科学依据：多目标优化中的帕累托最优解
   - 用户体验："静默"压缩点，大多数用户无感知
   - Claude Code的经验验证

2. **Harness Engineering与C1的关系**
   - C1是Foundation：上下文工程
   - Harness是全体系：context + constraints + garbage collection
   - 三层架构（短期/中期/长期记忆）是C1的具体实现

3. **开源框架的启示**
   - Aider的AST分析：代码结构化上下文的最佳实践
   - MemGPT的OS类比：操作系统级上下文管理的可能性
   - LangChain Middleware：通用的上下文编辑框架

4. **KOL共识**
   - Willison：Context Engineering是term winner（已定）
   - Fowler：Context is the bottleneck（明确了问题）
   - 行业确认：C1的问题界定是正确的

5. **官方指导的实践指南**
   - 文档放置策略：信息架构对模型性能影响显著
   - Subagent模式：超长任务的系统解决方案
   - 自动压缩机制：大规模部署的可靠性基础

---

## 总体研究价值评估

### 新增的关键信息

1. **中文社区的系统化分析** - 对比西方单点分析的整体观
2. **代码级实现细节** - 从理论到工程化的具体方案
3. **2025-2026年的最新进展** - Prompt Caching、Reasoning纳入、Subagent等
4. **官方的生产级指导** - 而非学术或个人观点

### 对后续研究的建议

- **实验方向**：验证92%阈值对不同模型的普适性
- **工程方向**：实现Harness Engineering的完整框架
- **社区方向**：推进Context Engineering的标准化术语
- **产品方向**：将Subagent模式集成到更多场景

---

**本文档将根据最新的研究进展持续更新。**
