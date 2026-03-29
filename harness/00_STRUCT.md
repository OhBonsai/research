第一部分：Harness Engineering 方法论深度解析

1.1 定义与核心公式：Agent = Model + Harness
1.2 Harness 的五大要素：记忆（Memory）、上下文（Context）、工具与沙箱（Tools & Sandbox）、编排与协作（Orchestration）、验证与反馈闭环（Verification）
1.3 设计原则归纳：渐进式披露、仓库即操作系统、机械验证优先于直觉、协调者不写代码、熵控制
1.4 系统约束：上下文窗口有限性、模型非确定性、知识腐烂、漂移不可避免

第二部分：OpenCode 架构的 Harness 实现分析

2.1 OpenCode 架构总览：Go + BubbleTea + SQLite + LSP + MCP
2.2 Harness 要素在 OpenCode 中的映射：AGENTS.md / Skills / Agents / Tools / Permissions
2.3 OpenCode 的"变"与"不变"：哪些是 Harness 的通用工程、哪些是 Coding 场景特化

第三部分：从 Coding Agent 到 Office Agent 的迁移分析

3.1 场景差异分析：代码仓库 vs 企业办公空间，验证闭环的本质变化
3.2 Harness 五要素的"变与不变"逐一推演
3.3 新引入的企业级约束：多租户、合规审计、权限分级、数据隔离

第四部分：企业办公 AI Agent 产品架构设计

4.1 以 OpenCode 为底座的集成架构
4.2 分层设计：底座引擎层 → Harness 层 → 企业管控层 → 场景应用层
4.3 核心模块设计：记忆系统、知识库、Agent 编排、安全沙箱、审计系统
4.4 进化机制：知识进化、默契进化、结构进化

第五部分：研究方向与持续努力路线图

5.1 需要深入研究的方向（按优先级排列）
5.2 分阶段实施路线图
5.3 关键风险与开放问题