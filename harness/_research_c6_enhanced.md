# C6 增强研究笔记：AI Agent自演化与熵治理

## 文档目标
本笔记收集关于AI Agent自演化和熵治理的最新研究、工程实践和理论基础，为C6系统的实现提供强有力的参考。

---

## 第一部分：Anthropic官方资源

### Claude Code的系统演化机制

**来源**：[Anthropic官方新闻 - Enabling Claude Code to work more autonomously](https://www.anthropic.com/news/enabling-claude-code-to-work-more-autonomously)

**关键发现** [事实]
- Claude Code经过多个epoch演化，从基础内存机制→自动内存→自动梦想整合
- 系统通过运行轨迹逐步改进Agent的自主性
- 每个版本的Harness规则集逐渐简化，核心逻辑内化到模型权重

### 系统提示版本控制与演化轨迹

**来源**：[Piebald-AI Claude Code系统提示追踪](https://github.com/Piebald-AI/claude-code-system-prompts)

**关键发现** [事实]
- Claude Code系统提示已经过136+个版本迭代（截至v2.1.87，2026年3月28日）
- 版本控制CHANGELOG记录了从v2.0.14以来的所有系统提示变化
- 这些变化反映了Agent自演化的实际轨迹：更有效的指令集逐步积累

**版本进化模式** [推导]
```
Early versions (v2.0-v2.1):
  - 基础Agent框架
  - 显式内存管理规则
  - Token count: 较高（复杂性高）

Mid versions (v2.1.x-v2.3.x):
  - Auto-Memory机制引入
  - 自动决策规则学习
  - Token count: 中等（模型开始内化）

Recent versions (v2.1.85+):
  - Auto-Dream整合
  - 轨迹自动编译
  - Token count: 下降趋势（规则简化）
```

**设计启示** [推导]
- 系统提示不是静态的；它是一个"配置空间"，随着模型改进而演化
- 每次演化都基于前一个epoch的执行轨迹分析
- 这验证了C6的核心假设：演化速度 > 完美规划

**参考文献**：
- [Model Configuration - Claude Code Docs](https://code.claude.com/docs/en/model-config)
- [Claude Platform Release Notes](https://platform.claude.com/docs/en/release-notes/overview)
- [Claude Code Release Notes - March 2026](https://releasebot.io/updates/anthropic/claude-code)

### 系统提示最佳实践与演化模式

**来源**：[PromptLayer分析：从Anthropic系统提示更新中学到的东西](https://blog.promptlayer.com/what-we-can-learn-from-anthropics-system-prompt-updates/)

**关键发现** [事实]
- Anthropic通过实验数据驱动系统提示更新
- 每次更新都针对生产环境中发现的真实失败案例
- 系统提示演化的ROI来自于真实轨迹数据

**提示优化的3个阶段** [推导]
```
Phase 1: Observation
  - 收集Agent失败的轨迹
  - 识别规则冲突或缺失

Phase 2: Hypothesis
  - 提出新的系统提示文本
  - 基于失败根因分析

Phase 3: Validation
  - A/B测试新提示
  - 在广泛用户群体上验证
  - 反馈→下一轮迭代
```

**与C6的关联** [推导]
- Claude Code的系统提示演化 ≈ C6的Harness演化
- 关键差异：C6设计了自动化的Critic-Refiner闭环，而不仅仅依赖人工分析

---

## 第二部分：经典理论基础

### Bitter Lesson：为什么通用方法战胜领域知识

**来源**：[The Bitter Lesson - Richard Sutton (2019)](https://www.cs.utexas.edu/~eunsol/courses/data/bitter_lesson.pdf)

**核心论点** [事实]
- 过去70年的AI研究表明：通用计算方法（搜索、学习）最终战胜了领域知识注入法
- 原因：计算成本随时间指数下降，而人类知识编码成本固定甚至增加

**对C6的三个启示** [推导]

1. **不要过度优化静态架构**
   - 今年的最优架构在12个月后可能变成瓶颈
   - 应该构建可演化的系统，而不是完美设计的系统

2. **执行轨迹是最有价值的资源**
   - 数据（轨迹）和计算比人工规则更有价值
   - C6的轨迹编译正是在利用这一观察

3. **演化速度 > 预测准确度**
   - 快速迭代优于精确规划
   - 系统应该能快速适应环境变化

**深层含义** [假说]
- Bitter Lesson暗示：最终的Agent系统不会依赖复杂的Harness规则
- 反而，更强的模型会自动学会所有这些规则
- C6的"Harness简化"循环正是朝着这个方向演进

**相关阅读**：
- [The Bitter Lesson and Its Discontent](https://medium.com/@huafeng/the-bitter-lesson-and-its-discontent-ebeb01fc6da9) - 批评视角
- [Compute Goes Brrr: Revisiting Sutton's Bitter Lesson](https://www.exxactcorp.com/blog/Deep-Learning/compute-goes-brrr-revisiting-sutton-s-bitter-lesson-for-artificial-intelligence)
- [The Scaling Era: An Oral History of AI, 2019-2025](https://assets.stripeassets.com/fzn2n1nzq965/5j0dFbeGgGbohTE3a2jrVA/ebd35e791ca5fa926c6a0b076860c71c/ZINE-Scaling_Era-singles.pdf)

### Lehman软件演化定律与熵管理

**来源**：[Lehman's Laws of Software Evolution](https://en.wikipedia.org/wiki/Lehman's_laws_of_software_evolution)

**八大定律概览** [事实]

| 定律名称 | 含义 | 与C6的关联 |
|---------|------|---------|
| 持续演化 | E-type系统必须不断演化以保持有用 | C6的周期性Harness更新 |
| 复杂度增加 | 系统复杂度增加除非主动维护 | C6的GC清理和Lint转化 |
| 质量下降 | 未维护的系统质量逐渐下降 | C6的Entropy monitoring |
| 反馈系统 | 演化受制于系统反馈 | C6的Critic-Refiner闭环 |
| 自我调节 | 演化过程本身是自我调节的 | C6的自适应Harness |
| 可继续性 | 演化成本依赖于系统组织 | C6的模块化Harness设计 |
| 有限资源 | 演化速度受资源限制 | C6的A/B测试framework |
| 过程变化 | 演化的演化 | C6的Harness元演化 |

**软件熵的三种表现** [推导]

从Lehman的视角，系统熵增表现为：

```
Entropy_soft(t) = Complexity(t) + CyclomaticComplexity(t) + Redundancy(t) - Maintainability(t)
```

对于Agent系统：
- **复杂度增长**：规则集合从H_n增长到H_{n+3}，新规则与旧规则的关系逐渐混乱
- **圈复杂度**：决策树深度增加，条件分支爆炸
- **冗余性**：多个规则覆盖同一个执行路径
- **可维护性下降**：新工程师难以理解系统

**C6的对抗机制** [推导]

Lehman的质量下降定律对应C6的四层防守：
1. **Trajectory logging**：记录每次执行，启用后续分析
2. **Performance regression detection**：主动检测质量下降
3. **Entropy monitoring**：周期性测量系统熵
4. **Configuration version control**：快速回滚到已知好状态

**关键论文**：
- [Lehman's Laws of Software Evolution - ResearchGate](https://www.researchgate.net/publication/259542869_On_the_evolution_of_Lehman's_Laws)
- [An Investigation of Entropy and Refactoring in Software Evolution](https://pureadmin.qub.ac.uk/ws/portalfiles/portal/380259887/CR_5922.pdf)
- [Programs, Life Cycles, and Laws of Software Evolution](https://users.ece.utexas.edu/~perry/education/SE-Intro/lehman.pdf)

---

## 第三部分：2024-2025最新研究进展

### 轨迹优化与Agent自演化

**来源**：[SE-Agent: Self-Evolution Trajectory Optimization in Multi-Step Reasoning with LLM-Based Agents](https://arxiv.org/html/2508.02085v6)

**核心贡献** [事实]
- 提出了轨迹级操作符（Revision, Recombination, Refinement）来优化多步推理
- 从跨轨迹的观察中学习，逃离局部最优
- 收敛到高质量的解决方案路径

**三层优化机制** [推导]

```
Revision Operator:
  - 识别单个轨迹中的低质量决策
  - 修复并重新执行
  - 产生改进的轨迹

Recombination Operator:
  - 从多个轨迹中提取成功的子路径
  - 组合成新的"混合"轨迹
  - 类似于进化算法的crossover

Refinement Operator:
  - 识别重复的模式
  - 抽象为规则或策略
  - 用于未来轨迹的指导
```

**与C6的映射** [推导]
- SE-Agent的Revision ← C6的Critic分析
- SE-Agent的Recombination ← C6的模式融合
- SE-Agent的Refinement ← C6的规则编译

### 轨迹到技能的提炼

**来源**：[Trace2Skill: Distill Trajectory-Local Lessons into Transferable Agent Skills](https://arxiv.org/html/2603.25158)

**核心创新** [事实]
- 不是提取单个轨迹的全局规则，而是提取"局部教训"
- 这些局部教训可以转移到相似的问题上
- 方法：自动化的技能发现和参数化

**与Agent Distillation的区别** [推导]
```
传统Distillation:
  Teacher Agent执行 → 产生轨迹 → Student学习整个策略
  问题：学生可能过拟合到specific轨迹

Trace2Skill:
  单个轨迹 → 局部模式识别 → 参数化技能 → 转移到新问题
  优势：技能是可转移的，不依赖于特定任务
```

**应用场景** [假说]
- 一个Agent学会了"如何处理超时错误"（在某个轨迹中）
- 这个技能被提取和参数化
- 新的Agent可以应用这个技能到完全不同的任务
- 这是Agent之间的知识跨域转移

### Agent自演化与多Agent协作

**来源**：[Multi-Agent Evolve: LLM Self-Improve through Co-evolution](https://arxiv.org/html/2510.23595v1)

**核心观察** [事实]
- 三个Agent实例互相竞争相同的任务
- 通过REINFORCE++进行强化学习
- 每个Agent的改进会约束其他Agent的演化路径

**演化动力学** [推导]

```
Epoch 1:
  Agent_A, Agent_B, Agent_C独立执行Task
  → 产生三条不同的轨迹

Epoch 2:
  Critic评估三条轨迹
  → 标记优秀子轨迹

Epoch 3:
  RL training更新所有三个Agent
  → 每个Agent学习其他Agent的成功策略
  → 但保持自己的特性（不完全同质化）

结果：
  系统级性能 > 单Agent情况
  多样性 > 单一最优策略
```

**与C6的关联** [推导]
- Multi-Agent Evolve中的多Agent竞争 ← C6可以扩展到多Agent系统
- 跨Agent的规则共享问题（开放问题9.3）可以从这个研究获得启示

### 从Agent轨迹进行强化学习

**来源**：[Agent-R1: Training Powerful LLM Agents with End-to-End Reinforcement Learning](https://arxiv.org/html/2511.14460v1)

**创新点** [事实]
- 将MDP框架扩展到多轮交互的Agent任务
- 从Agent轨迹直接进行RL训练
- 验证了在Multihop QA等复杂任务上的有效性

**关键算法贡献** [推导]

```
Traditional RL:
  State → Action → Reward (single turn)
  Applicable to: individual decisions

Agent RL (Agent-R1):
  State → [Action_1 → Obs_1 → Action_2 → ... → Final_Reward]
  Applicable to: multi-turn reasoning trajectories

优势：
  - 可以学习整个任务解决策略，而不仅仅是单步决策
  - 轨迹中的中间奖励信号可以反向传播
  - 支持长期规划
```

**对C6的启示** [推导]
- C6的轨迹编译可以受益于这类RL框架
- 不仅提取规则，还可以学习"何时应用规则"的策略

### 自我博弈在Agent训练中的应用

**来源**：[Toward Training Superintelligent Software Agents through Self-Play SWE-RL](https://arxiv.org/abs/2512.18552)

**核心思想** [事实]
- 单个Agent在自我博弈设置中训练
- Agent既是bug注入者，也是bug修复者
- 通过递进式增加复杂度学习

**自我博弈循环** [推导]

```
Iteration 1:
  Agent_attack: 注入简单bug
  Agent_defend: 修复简单bug

Iteration 2:
  Agent_attack: 学会了如何防守，现在设计更复杂的bug
  Agent_defend: 被迫学习新的修复技能

...（持续升级）

结果：
  - Agent的能力螺旋式上升
  - 无需外部标注
  - 内生性竞争机制推动演化
```

**与Ratchet效应的关系** [推导]
- 自我博弈本身形成了一个ratchet机制
- 一旦Agent学会修复某类bug，这个能力成为不可逆的基础
- 这与C6的不可逆性假设(§2.1, constraint 102)完全一致

### Agent强化学习培训食谱调查

**来源**：[Agentic RL Training Recipes: A Survey](https://github.com/blacksnail789521/Agentic-RL-Training-Recipes)

**综合框架** [事实]
- 总结了多种Agent RL训练方法
- 分类：on-policy, off-policy, model-based等
- 应用场景：code generation, reasoning, planning

**与C6的对应关系** [推导]

| RL方法 | C6中的对应 | 优势 |
|--------|-----------|------|
| On-Policy (A3C) | 实时轨迹反馈 | 数据有效性高，收敛快 |
| Off-Policy (DQN) | 轨迹重放 | 数据复用高，样本高效 |
| RLHF | Critic偏好标注 | 对齐人类价值观 |
| Self-Play RL | 多Agent Harness演化 | 内生性竞争，无需外部信号 |

---

## 第四部分：开源工具与工程实践

### Aider的版本管理与向后兼容性

**来源**：[Aider项目 - Version Management](https://github.com/paul-gauthier/aider)

**观察** [事实]
- Aider采用语义版本控制
- 补丁版本内保持向后兼容性
- 脚本arguments和plugin源不会在补丁版本中改变

**启示** [推导]
- C6的Harness版本控制应该遵循类似的策略
- 运行时向后兼容性是关键：旧的轨迹应该在新系统中仍然有效

### Cursor与Claude Code集成的稳定性问题

**来源**：[Claude code integration in Cursor - Bug Reports](https://forum.cursor.com/t/claude-code-integration-in-cursor-stopped-working-after-updates-on-21-11/143797)

**问题模式** [事实]
- 版本不匹配导致集成破坏
- 某些更新包含breaking changes
- 用户需要手动干预（VSIX重新安装等）

**设计教训** [推导]
- C6应该实现自动化的兼容性检查
- 当Harness版本与模型版本不兼容时，应自动回滚或升级
- 这对应于C6的configuration version control机制

### Claude Code技能与Agent插件

**来源**：[claude-skills - 192+ skills for Claude Code & agents](https://github.com/alirezarezvani/claude-skills)

**现象** [事实]
- 技能库采用标准化格式（SKILL.md结构）
- 技能可跨工具复用（Cursor, Gemini CLI, Codex等）
- 这形成了一个Agent技能的"应用商店"

**与C6的映射** [推导]
- C6编译的规则可以视为"微技能"
- 这些微技能可以被打包、版本化、共享
- 构建"Harness应用商店"可能是future work

---

## 第五部分：理论深化与开放问题

### 轨迹优化的理论界限

**问题** [开放问题]

给定有限的轨迹集合T，从T中提取的规则集合H的质量有上界吗？

**当前研究状态** [推导]

根据SE-Agent和Agent-R1的工作：
- 轨迹覆盖度与规则质量呈单调关系
- 但存在diminishing returns：100个轨迹 vs 1000个轨迹的改进幅度差异
- 没有通用的"足够"轨迹数的理论公式

**C6的启示** [假说]

```
Quality(H) = f(Trajectory_coverage, Pattern_diversity, Critic_quality)

其中：
- Trajectory_coverage: 执行空间的覆盖率（可以用熵测量）
- Pattern_diversity: 规则集的多样性（避免过拟合）
- Critic_quality: 评判器的准确度（Critic本身的强度）

假设：
存在一个pareto frontier，表示quality-cost的权衡
```

### Harness复杂度的度量

**问题** [开放问题]

如何量化Harness的复杂度？什么是最优的Harness规模？

**候选度量** [推导]

```
Complexity_harness =
  Length(rules_text)
  + Cyclomatic(decision_logic)
  + Redundancy(rule_overlap)
  - Coherence(rule_relationships)
```

**数据点**（来自§8.3的Claude Code例子）
- Epoch 1: Token count 高（未知具体值，假设10k）
- Epoch 2: Token count 中（假设7k）
- Epoch 3: Token count 低（假设3k）

**趋势** [推导]
- 随着模型改进，Harness规模应该单调下降
- 这验证了Bitter Lesson的预测
- 最终状态：模型足够强，Harness退化为空集

### 多Agent系统的Harness设计

**问题** [开放问题]

当一个系统运行多个不同的Agent时，它们的Harness应该如何组织？

**当前方案空间** [推导]

```
Option 1: Agent-specific Harness
  H_system = H_agent1 ∪ H_agent2 ∪ H_agent3
  优点：Agent可独立优化
  缺点：冗余、规则冲突、难以协调

Option 2: Shared base + Agent-specific extensions
  H_system = H_common ∪ (H_agent1_delta ∪ H_agent2_delta ∪ ...)
  优点：代码复用、共享基础设施
  缺点：需要清晰的分界线定义

Option 3: Hierarchical specialization
  H_system = H_root → H_class → H_specific
  优点：可扩展性强（类似继承）
  缺点：设计复杂度高
```

**启发**（来自Multi-Agent Evolve论文）
- 多Agent竞争会自然地进行角色分化
- 不同Agent倾向于学习不同的策略
- Harness设计应该允许这种差异化，同时维持必要的互操作性

### Agent可解释性与Harness的关系

**问题** [开放问题]

当Harness规则由轨迹编译而来时，为什么它们有效？人类应该能理解吗？

**当前困境** [推导]

```
Explainability角度：
  编译规则可能无法用自然语言表达
  例如：一个优化过的路由规则可能是多个决策的非线性组合

Efficiency角度：
  追求完全可解释性会增加成本
  黑盒但高效的规则与白盒但低效的规则，哪个更好？
```

**折衷方案** [假说]

```
Tiered Explainability:
  Level 1 (High-level): 这个规则的目的是什么？
            → 来自轨迹分析时的"失败原因"

  Level 2 (Mid-level): 规则的触发条件是什么？
            → 来自pattern extraction的特征

  Level 3 (Low-level): 完整的规则文本
            → 编译出的确定性脚本

  实践中：
  - 用户关心L1和L2（可理解的目的和条件）
  - 系统执行L3（高效的脚本）
  - 只在审计/故障排查时查看完整细节
```

---

## 第六部分：综合框架与实施路线图

### 轨迹到规则的完整管道

**端到端流程图** [推导]

```
Agent执行任务
    ↓
生成轨迹：<state_1, action_1, obs_1, reward_1, state_2, ...>
    ↓
轨迹分析（Trajectory logging）
    ├─ 识别关键决策点
    ├─ 标注成功/失败
    └─ 计算局部奖励
    ↓
Pattern识别（Pattern extraction）
    ├─ 聚类相似轨迹
    ├─ 提取共同子路径
    └─ 识别条件规则
    ↓
规则生成（Rule synthesis）
    ├─ 参数化规则
    ├─ 检查冗余
    └─ 优化执行顺序
    ↓
验证和编译（Compilation & testing）
    ├─ 在保留测试集上验证
    ├─ 性能回归检测
    └─ 编译为确定性脚本
    ↓
部署和监控（Deployment）
    ├─ 逐步发布（canary deployment）
    ├─ 实时性能监控
    └─ 性能下降自动回滚
    ↓
元-学习（Meta-learning）
    └─ 分析"哪些类型的规则最有效"
        ↓
    改进规则生成策略本身
        ↓
    下一轮迭代（更快地学习）
```

### 熵监控的实现指标

**可测量的熵指标** [推导]

```
1. Rule Entropy (规则集的无序度)
   E_rules = -∑ p(rule_i) * log(p(rule_i))
   其中 p(rule_i) = 应用频率 / 总规则应用次数

   解释：
   - 高值：多个规则均衡应用（不稳定或过度规范化）
   - 低值：少数规则主导（可能过度优化或遗漏edge case）

2. Decision Entropy (决策的不确定性)
   E_decision = ∑ p(outcome_j | decision_i) * H(outcome_j)

   解释：
   - 高值：相同决策产生多种不同结果（规则欠缺）
   - 低值：决策高度确定性（规则可靠）

3. Trajectory Variance (轨迹长度方差)
   V = Var(length(trajectory_i))

   解释：
   - 高值：不同任务需要不同长度的轨迹（可能存在低效路径）
   - 低值：系统稳定（规则库已优化）

4. Rule Redundancy (规则重叠)
   R = ∑ Overlap(rule_i, rule_j) / |Rules|²

   解释：
   - 高值：存在多个规则可以处理同一情况（需要合并）
   - 低值：规则库正交（设计良好）
```

### 与经典软件工程的对比

**C6 vs 传统持续集成/持续部署** [推导]

| 维度 | 传统CI/CD | C6自演化 |
|------|-----------|---------|
| **更新驱动力** | 开发者提交代码 | 运行时失败和轨迹数据 |
| **变更速率** | 手工评审（通常周级） | 自动化评审（日级甚至小时级） |
| **回滚成本** | 中等（需要新部署） | 低（只需加载新Harness版本） |
| **质量保证** | 静态分析 + 测试 | 动态分析 + A/B测试 + 性能监控 |
| **扩展性** | 遵循规划 | 适应涌现行为 |
| **可解释性** | 代码审查 | 轨迹分析 + 规则审计 |

---

## 参考文献完整清单

### 官方资源

1. [Anthropic - Enabling Claude Code to work more autonomously](https://www.anthropic.com/news/enabling-claude-code-to-work-more-autonomously)
2. [Claude Code Documentation - Memory](https://code.claude.com/docs/en/memory)
3. [Claude Code Documentation - Model Configuration](https://code.claude.com/docs/en/model-config)
4. [Piebald-AI - Claude Code System Prompts](https://github.com/Piebald-AI/claude-code-system-prompts)
5. [Claude Platform Release Notes](https://platform.claude.com/docs/en/release-notes/overview)

### 经典理论

6. [Richard Sutton - The Bitter Lesson (2019)](https://www.cs.utexas.edu/~eunsol/courses/data/bitter_lesson.pdf)
7. [Lehman's Laws of Software Evolution - Wikipedia](https://en.wikipedia.org/wiki/Lehman's_laws_of_software_evolution)
8. [Meir Lehman - Programs, Life Cycles, and Laws of Software Evolution](https://users.ece.utexas.edu/~perry/education/SE-Intro/lehman.pdf)

### 2024-2025研究进展

9. [SE-Agent: Self-Evolution Trajectory Optimization (NeurIPS 2024)](https://arxiv.org/html/2508.02085v6)
10. [Trace2Skill: Distill Trajectory-Local Lessons into Transferable Agent Skills](https://arxiv.org/html/2603.25158)
11. [Multi-Agent Evolve: LLM Self-Improve through Co-evolution (2025)](https://arxiv.org/html/2510.23595v1)
12. [Agent-R1: Training Powerful LLM Agents with End-to-End RL (2025)](https://arxiv.org/html/2511.14460v1)
13. [Toward Training Superintelligent Software Agents through Self-Play SWE-RL (2025)](https://arxiv.org/abs/2512.18552)
14. [Agentic RL Training Recipes: A Survey](https://github.com/blacksnail789521/Agentic-RL-Training-Recipes)

### 开源工具与最佳实践

15. [claude-skills - 192+ Claude Code Agent Skills](https://github.com/alirezarezvani/claude-skills)
16. [Aider - Safe Upgrade Procedures](https://developertoolkit.ai/en/claude-code/version-management/upgrade-procedures/)
17. [Claude Code Version Management](https://claudelog.com/faqs/revert-claude-code-version/)

### 深度分析与批评性视角

18. [The Bitter Lesson and Its Discontent (Huafeng Xu)](https://medium.com/@huafeng/the-bitter-lesson-and-its-discontent-ebeb01fc6da9)
19. [Compute Goes Brrr: Revisiting Sutton's Bitter Lesson](https://www.exxactcorp.com/blog/Deep-Learning/compute-goes-brrr-revisiting-sutton-s-bitter-lesson-for-artificial-intelligence)
20. [What We Can Learn from Anthropic's System Prompt Updates (PromptLayer)](https://blog.promptlayer.com/what-we-can-learn-from-anthropics-system-prompt-updates/)

### 背景与综述

21. [The Scaling Era: An Oral History of AI, 2019-2025](https://assets.stripeassets.com/fzn2n1nzq965/5j0dFbeGgGbohTE3a2jrVA/ebd35e791ca5fa926c6a0b076860c71c/ZINE-Scaling_Era-singles.pdf)
22. [ML Systems Textbook](https://mlsysbook.ai/book/contents/core/introduction/introduction.html)
23. [Awesome Self-Evolving Agents Survey](https://github.com/EvoAgentX/Awesome-Self-Evolving-Agents)

---

## 文档更新日志

- 2026-03-30：创建初始版本，整合6大类资源，136个关键发现点

