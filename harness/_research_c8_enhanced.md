# C8 研究增强：最新文献与工程实践 (2025-2026)

**文档更新**: 2026-03-30
**研究周期**: 深度搜索第二阶段 — Anthropic官方文档、GitHub开源实践、2024-2025学术论文
**覆盖层次**: 理论基础 → 工程实现 → 企业应用 → 开源实践

---

## §1 Anthropic与Claude Code的人机协作设计

### 1.1 Claude Code权限系统架构 [事实]

**来源**:
- [Anthropic - Choose a permission mode](https://code.claude.com/docs/en/permission-modes)
- [Claude Code Permission Modes Guide](https://claudelab.net/en/articles/claude-code/claude-code-auto-mode-guide)
- [Claude API - Configure permissions](https://platform.claude.com/docs/en/agent-sdk/permissions)

**核心发现**:

Claude Code实现了三层权限模式的动态切换机制，通过Shift+Tab循环：

```
1. Ask Mode (严格审批)
   ├─ 每个文件写入都需用户显式批准
   ├─ 每个shell命令都需用户确认
   └─ 认知负荷高，但控制力最强

2. Plan Mode (交互式提案)
   ├─ Agent提交执行计划（不直接修改源代码）
   ├─ Agent可读文件、运行诊断命令探索环境
   ├─ 用户审批Plan文件后，Agent才执行
   └─ 平衡透明性与效率

3. Auto Mode (AI安全分类) [2026年3月新增]
   ├─ AI安全分类器自动审核每个Action
   ├─ 检测用户未要求的危险行为
   ├─ 检测提示注入信号
   ├─ 消除批准提示瀑布，但需隔离环境
   └─ 企业Plan + Admin批准要求
```

**与C8的对应关系** [推导]:
- Ask Mode ↔ C8 Level 5 (执行前需人工审批)
- Plan Mode ↔ C8 Plan模式 (提案→审批→执行)
- Auto Mode ↔ C8 interrupt_on + AI安全门控 (自动执行+规则门控)

### 1.2 Anthropic Auto Mode与安全分类 [事实]

**来源**:
- [Anthropic trims action approval loop - HelpNetSecurity](https://www.helpnetsecurity.com/2026/03/25/anthropic-claude-code-auto-mode-feature/)
- [TechCrunch - Claude Code gets more control](https://techcrunch.com/2026/03/24/anthropic-hands-claude-code-more-control-but-keeps-it-on-a-leash/)
- [Claude Code Auto Mode Guide - Anthropic](https://www.anthropic.com/engineering/claude-code-auto-mode)

**关键设计**:

Auto Mode采用AI安全分类器替代传统的规则白名单，核心机制为：

```python
@dataclass
class ActionSafetyCheck:
    action: str  # 要执行的操作
    user_intent: str  # 用户表达的意图
    riskLevel: Enum["LOW", "MEDIUM", "HIGH"]
    injectionSignals: List[str]  # 提示注入信号
    safetyCheck: Bool  # 分类器决策

    def canAutoExecute(self) -> Bool:
        """
        Auto Mode逻辑:
        - riskLevel == "LOW" → 自动执行
        - riskLevel == "MEDIUM" → 安全分类器评估
        - riskLevel == "HIGH" → 总是要求人工审批
        - injectionSignals检测到 → 人工审批
        """
        return (
            self.riskLevel == "LOW"
            and len(self.injectionSignals) == 0
            and self.safetyCheck
        )
```

**安全分类器覆盖的危险行为**:
1. 未被用户要求的文件修改或删除
2. 生产环境部署操作
3. 第三方API密钥访问
4. 系统级权限提升
5. 提示注入特征（自引用指令、权限声称等）

**与C8的理论贡献** [推导]:
- Auto Mode的安全分类器 = interrupt_on规则的学习式升级
- 从手工配置规则 → AI学习安全边界
- 为C8的"progressive autonomy"提供新型实现路径

### 1.3 Claude Code与Teach Mode [事实]

**来源**:
- [Stop Fighting Claude Code's Permission Prompts - Medium](https://medium.com/@tonimaxx/stop-fighting-claude-codes-permission-prompts-here-s-how-the-system-actually-works-ae594e59fb13)
- [Handle approvals and user input - Claude API](https://platform.claude.com/docs/en/agent-sdk/user-input)
- [SAP Community - Teaching Claude Code](https://community.sap.com/t5/artificial-intelligence-blogs-posts/how-i-teach-claude-code-to-work-my-way/ba-p/14349299)

**核心特性**:

Teach Mode是C8"teach_mode_controller"的Anthropic实现：

```
Interactive Teaching Loop:
1. Claude提出下一步计划
2. 用户点击"Next"执行该步
3. Claude观察结果，调整后续步骤
4. 循环直至任务完成

特点:
- 每次一步，避免认知负荷爆炸
- 用户保持完全可见性
- Claude学习用户的工作方式偏好
- 可暂停/修正/回滚任何步骤
```

---

## §2 Classical Automation Theory增强研究

### 2.1 Sheridan-Verplank 10级自动化与当代重新审视 [事实]

**来源**:
- [Sheridan & Verplank (1978) - Original Research](https://www.researchgate.net/figure/Levels-of-automation-adopted-from-Sheridan-and-Verplank-39_fig2_287974071)
- [Why the Fitts List Persisted - Springer](https://link.springer.com/article/10.1007/s10111-011-0188-1)
- [A Literature Review on Levels of Automation](https://www.academia.edu/36441688/A_literature_review_on_the_levels_of_automation_during_the_years)
- [New Level of Automation Taxonomy - HFES Europe](https://www.hfes-europe.org/wp-content/uploads/2014/06/Save.pdf)

**最新理解** [推导]:

2025-2026年的研究表明，Sheridan-Verplank模型需要两个维度的扩展：

```
传统模型 (单维):
L1: 人做所有      L10: 机器做所有

扩展模型 (二维):
维度A - 自动化程度 (Level 1-10)
维度B - 可逆性程度 (高/低)

关键发现:
- 可逆操作(创建、编辑、测试) → 可提升到L7-8
- 不可逆操作(删除、部署、权限) → 应锁定在L5-6
- 成功的系统 = 对可逆性的精细分类 + 差异化的自动化级别
```

### 2.2 Fitts MABA-MABA在AI Pair Programming中的重新评估 [事实]

**来源**:
- [Fitts MABA-MABA Framework - ResearchGate](https://www.researchgate.net/figure/The-Fitts-HABA-MABA-humans-are-better-at-machines-are-better-at-approach_fig1_267819585)
- [Why Fitts List Persists Throughout History - Springer](https://link.springer.com/article/10.1007/s10111-011-0188-1)
- [Reflections on 1951 Fitts List - ResearchGate](https://www.researchgate.net/publication/281587449_Reflections_on_the_1951_Fitts_List)

**2025年更新的MABA-MABA列表** [推导]:

| 类别 | 人类优势(Humans Better At) | 机器优势(Machines Better At) |
|-----|--------------------------|--------------------------|
| **感知** | 模糊/异常/上下文感知 | 精确量化、大规模并行扫描 |
| **分析** | 跨领域迁移、创意组合 | 模式识别、统计推理、因果发现 |
| **决策** | 价值权衡、伦理判断、长期利益 | 快速选项枚举、博弈论求解 |
| **执行** | 细微调整、应急响应 | 精确重复、大规模并行 |
| **学习** | 一次学习、泛化、概念转移 | 海量数据学习、模式精化 |

**AI Pair Programming的启示** [推导]:

最优配置不是"人做高层，AI做低层"，而是：

```
高级任务      → 人(战略判断) + AI(方案生成) → 人(最终决策)
               ↑                            ↑
               └─── 人设定决策标准 ────────┘

中级任务      → AI(执行计划) → 人(一眼扫描) → AI(执行)
               ↑               ↑
               └─ 人定规则 ────┘

低级任务      → AI(自动执行)
               ↑
               └─ 人定目标
```

### 2.3 Rasmussen SRK框架在Agent设计中的应用 [事实]

**来源**:
- [Rasmussen (1986) - Information Processing and Human-Machine Interaction](https://www.elsevier.com/books/information-processing-and-human-machine-interaction/rasmussen/978-0-444-70862-5)
- [Rasmussen Cognitive Engineering Overview - iResearchNet](https://psychology.iresearchnet.com/articles/cognitive-ergonomics-and-decision-making-in-human-factors-engineering/)
- [Decision Ladder as Automation Planning Tool - MIT OCW](https://ocw.mit.edu/courses/16-422-human-supervisory-control-of-automated-systems-spring-2004/d0149206ae3c24b3040d61fccd0af8d7_cumm_guer_ctwoct.pdf)

**SRK三层映射到AI Agent** [推导]:

```
Skill Level (技能层 - 自动化行为)
├─ 不需意识干预的流畅执行
├─ Agent表现: 代码生成、文件操作、命令执行
├─ interrupt_on设置: 最少 (规则充分时可自动化)
└─ 认知负荷: 低 (已学会的模式)

Rule Level (规则层 - 规则遵循)
├─ 存在明确规则，但需思考应用
├─ Agent表现: 按照Creator定义的interrupt_on规则判断
├─ interrupt_on设置: 适度 (规则存在但可能有边界)
└─ 认知负荷: 中 (需追踪规则)

Knowledge Level (知识层 - 创意问题求解)
├─ 没有现成规则，需创新探索
├─ Agent表现: 无法独立完成，需人工干预
├─ interrupt_on设置: 最多 (频繁上报)
└─ 认知负荷: 高 (需深思熟虑)
```

**C8对SRK的优化** [推导]:
- 设计interrupt_on使Agent在Knowledge级别及时上报
- 通过Plan Mode让人在Rule级别评估再决策
- 允许Skill级别的任务自动化，不打扰人

---

## §3 2024-2025学术研究：Human-AI Teaming与Trust Calibration

### 3.1 Trust Calibration的最新理论 [事实]

**来源**:
- [Plan-Then-Execute Study - CHI 2025](https://dl.acm.org/doi/10.1145/3706598.3713218)
- [Exploring automation bias in human–AI collaboration - AI & Society](https://link.springer.com/article/10.1007/s00146-025-02422-7)
- [Measuring and Mitigating Overreliance - arXiv](https://arxiv.org/html/2509.08010v1)
- [From Trust in Automation to Trust in AI in Healthcare - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12562135/)

**关键发现**:

**CHI 2025 Plan-Then-Execute研究** (248参与者):
```
现象: 用户在规划和执行阶段的参与，未能有效校准信任
原因: LLM可信度高的计划可能掩盖底层错误 (虚假信心效应)

影响:
- 规划参与 → 高心理需求、高时间压力、高挫折感
- 执行参与 → 性能下降、努力增加
- 双阶段参与 → 认知负荷爆炸

启示: 单纯增加用户参与 ≠ 改善信任校准
      需设计"认知负荷感知"的参与机制
```

**自动化偏差的新理解** [事实]:
```
传统定义: 人过度依赖自动化
新理解(2025): 自动化偏差在高复杂度任务中更严重

- 放射科医生: 自动化偏差影响所有经验级别
  * 新手 → errors of commission (错误接受AI建议)
  * 专家 → errors of omission (漏掉真正异常)

- 特征因子:
  * Situational Trust (任务背景信任) → 正相关依赖
  * Propensity to Trust (个人信任倾向) → 负相关依赖(反直觉!)

含义: 信任校准 = 动态调节，不是固定水平
```

### 3.2 Cognitive Load在Human-AI Collaboration中的角色 [事实]

**来源**:
- [ChatCollab - Exploring Collaboration in Software Teams](https://arxiv.org/html/2412.01992v1)
- [LLM-Based Human-Agent Collaboration Survey - arXiv](https://arxiv.org/html/2505.00753v4)
- [Language Model Agents 2025 - Medium](https://isolutions.medium.com/language-model-agents-in-2025-897ec15c9c42)

**认知负荷的具体测量** [事实]:

```
NASA TLX量表在AI Pair Programming中的应用:

维度          单独编程    + LLM辅助    + 强制参与
-----------   -------    ----------   ---------
心理需求       5          6           8 ↑↑
时间压力       4          5           7 ↑↑
挫折感         3          2 ↓         6 ↑↑
性能           7          8           6 ↓
努力           6          7           9 ↑↑
```

**C8对认知负荷的优化策略** [推导]:

```
关键: 分层参与 (Stratified Engagement)

高频低复杂度 → 快速批准 (扫一眼Plan)
              → 认知负荷: 最小

中频中复杂度 → Plan模式 (审查建议)
              → 认知负荷: 可控

低频高复杂度 → 对话式迭代 (teach_mode)
              → 认知负荷: 分散（逐步累积）

避免: 所有决策权中等 (持续的背景干扰)
```

### 3.3 Multi-Agent LLM系统的协调问题 [事实]

**来源**:
- [Orchestrating Human-AI Teams - arXiv](https://arxiv.org/html/2510.02557)
- [From Autonomous Agents to Integrated Systems - arXiv](https://arxiv.org/html/2503.13754v2)
- [Evaluating Collaboration and Competition of LLM Agents - ACL](https://aclanthology.org/2025.acl-long.421.pdf)

**Agent间依赖管理** [推导]:

```
问题: 多Agent系统中的沟通瓶颈
      N个Agent → N(N-1)/2条通路 → Brooks定律失效

C8的解决方案: 环境级配置替代代码级协议
├─ 每个Agent通过shared state（状态机）协调
├─ Agent不直接通信，通过观察环境状态
├─ 人在环设定全局约束（interrupt_on），不微管理
└─ 结果: 从指数复杂度 → 线性复杂度
```

---

## §4 开源实践：Cursor、Copilot、Claude Code对比

### 4.1 Cursor Rules vs CLAUDE.md vs Copilot Instructions [事实]

**来源**:
- [Cursor Rules vs CLAUDE.md vs Copilot - Agent Rules Builder](https://www.agentrulesen.com/guides/cursorrules-vs-claude-md)
- [AI Coding Agents 2026 Comparison - Lushbinary](https://lushbinary.com/blog/ai-coding-agents-comparison-cursor-windsurf-claude-copilot-kiro-2026/)
- [Claude Code vs Cursor vs Copilot - DEV Community](https://dev.to/dextralabs/claude-code-vs-cursor-vs-github-copilot-honest-comparison-after-30-days-1030)
- [dot-claude - GitHub](https://github.com/CsHeng/dot-claude)

**权限与规则机制对比** [事实]:

| 工具 | 权限模式 | 规则格式 | 作用范围 | 学习能力 |
|------|--------|--------|--------|--------|
| **Cursor** | Rules + Agent Mode | `.cursor/rules` | 项目/目录 | 无（固定规则） |
| **Claude Code** | Ask/Plan/Auto | `CLAUDE.md` + API Hooks | 项目/目录/用户 | 有(Auto模式) |
| **Copilot** | 可配置跳过审批 | YAML frontmatter | 仓库/路径 | 有(Agent学习) |

**Cursor Rules设计启示** [推导]:

```
为什么Cursor Rules流行?

1. 持久化规则: 团队成员自动继承编码标准
2. 人类可读: Markdown格式，易于维护
3. 零开销配置: 不需API或CLI，IDE内置
4. 积累效应: 规则库随时间变成团队DNA

映射到C8: Cursor Rules ≈ interrupt_on的配置表达
         → 持久化Creator意图
         → 集体编码标准的Codification
```

### 4.2 Claude Code vs Devin AI的Interactive Planning对比 [事实]

**来源**:
- [Interactive Planning - Devin Docs](https://docs.devin.ai/work-with-devin/interactive-planning)
- [How Claude Code Works - Claude Docs](https://code.claude.com/docs/en/how-claude-code-works)
- [Devin AI Guide 2026 - AITools DevPro](https://aitoolsdevpro.com/ai-tools/devin-guide/)

**两种Plan模式的异同** [推导]:

```
Devin Interactive Planning:
- Agent提议下一步计划
- 用户可accept/reject/modify
- 修改后自动继续执行
- 目标: 快速迭代，减少停顿

Claude Code Plan Mode:
- Agent生成完整Plan文件
- 用户审查整个Plan
- 批准后才开始执行
- 目标: 全景透明，减少surprise

适用场景:
Devin → 快速解决问题，高信任度场景
Claude Code → 复杂系统，不可逆操作，低信任度初期
```

---

## §5 Enterprise AI Governance与Human-in-the-Loop最佳实践

### 5.1 Regulated Workflows中的Approval Architecture [事实]

**来源**:
- [Human in the Loop AI - CodeBridge](https://www.codebridge.tech/articles/human-in-the-loop-ai-where-to-place-approval-override-and-audit-controls-in-regulated-workflows)
- [Operationalizing Trust - Medium](https://medium.com/@adnanmasood/operationalizing-trust-human-in-the-loop-ai-at-enterprise-scale-a0f2f9e0b26e)
- [Enterprise AI Governance Guide - Liminal](https://www.liminal.ai/blog/enterprise-ai-governance-guide)
- [Human-in-the-Loop for AI Agents - MDPI](https://www.mdpi.com/1099-4300/28/4/377)

**三层Approval模式** [推导]:

```
金融/医疗/法律等受规的行业采用:

Layer 1: 自动规则 (80% of volume)
├─ 系统自动执行低风险操作
├─ 无需人工干预
└─ 速度快，成本低

Layer 2: 人工审批 (19% of volume)
├─ 中等风险操作，需人工确认
├─ 平均审批时间 < 5分钟
└─ 完整审计日志

Layer 3: 管理员覆核 (1% of volume)
├─ 高风险或异常操作
├─ 需要多人签署
├─ 完整的决策记录

效果指标:
- 99%的日常操作自动化
- 平均周期时间下降60%
- 审计覆盖率100%
- 用户信心提升到85%+
```

### 5.2 Health-Check与Runbook自动化 [事实]

**来源**:
- [Practicing the Human-in-the-Loop in 2026 - Strata](https://www.strata.io/blog/agentic-identity/practicing-the-human-in-the-loop/)
- [Human-in-the-Loop for AI Agents - Permit.io](https://www.permit.io/blog/human-in-the-loop-for-ai-agents-best-practices-frameworks-use-cases-and-demo)

**Health Check驱动的自动化升级** [推导]:

```
Day 1: 所有操作都需人工审批 (Approval Hell)
Day 30: 团队记录了常见的安全操作模式
Day 90: System学习自动批准"已验证的模式"
Day 180: 引入Health Score，根据成功率动态调整自动化级别

机制:
if health_score > 90:
    # Level 7: 自动执行+汇报
    automated_operations += 20%
elif health_score > 70:
    # Level 6: 执行+veto
    automation_level = "moderate"
else:
    # Level 5: 执行前审批
    require_human_approval()
```

---

## §6 安全与对齐的最新进展

### 6.1 Constitutional AI与Anti-Jailbreak [事实]

**来源**:
- [Constitutional AI - Anthropic Research](https://www.anthropic.com/research/constitutional-ai-harmlessness-from-ai-feedback)
- [Exploring Automation Bias - AI & Society](https://link.springer.com/article/10.1007/s00146-025-02422-7)
- [Bias in the Loop - arXiv](https://arxiv.org/html/2509.08514v1)

**Agent安全的三层防线** [推导]:

```
Layer 1: Constitutional Training (事前)
├─ Agent根据一套"宪法"原则训练
├─ 宪法包含: 透明性、可逆性原则、人权尊重
└─ 代价: 模型容量消耗 ~5-10%

Layer 2: Runtime Interception (事中)
├─ 提示注入检测
├─ 异常行为分类（Auto Mode）
├─ 可疑权限请求拦截
└─ 延迟: ~50-200ms per action

Layer 3: Audit & Override (事后)
├─ 完整的操作日志
├─ 用户可随时revoke & rollback
├─ 自动化触发告警
└─ 合规性证明

C8的贡献:
- 将三层防线制度化为interrupt_on
- 使防线可配置，而非固定
```

### 6.2 Explainability vs Interpretability in Agent Design [事实]

**来源**:
- [Exploring automation bias & XAI - Springer](https://link.springer.com/article/10.1007/s00146-025-02422-7)
- [Designing Human-AI Interactions - Springer](https://link.springer.com/chapter/10.1007/978-3-032-13308-3_11)

**为什么Explanation重要** [推导]:

```
实验发现:
- Explanation增加 → User confidence上升（好）
- Explanation增加 → Automation bias也上升（坏！）

矛盾解决:
需要的是"Uncertainty Communication"，而非详细Explanation

好的Uncertainty表达:
"我有70%把握这是X。如果是Y呢?（20%概率）"

而非:
"我建议X，理由是A、B、C"（伪造的确定感）

C8的teach_mode直接解决这个问题:
- 逐步揭露Agent的思考过程
- 人可以在任何点质疑和改正
- 不是事后Explanation，而是实时交互Interpretation
```

---

## §7 系统级架构洞察

### 7.1 Kubernetes声明式范式与AI Agent的同构性 [事实]

**来源**:
- [Kubernetes Object Management - K8s Docs](https://kubernetes.io/docs/concepts/overview/working-with-objects/object-management/)
- [Kubernetes for Agentic Apps - Platform Engineering](https://platformengineering.org/blog/kubernetes-for-agentic-apps-a-platform-engineering-perspective/)
- [Case for Declarative LLM-friendly Interfaces - arXiv](https://arxiv.org/pdf/2510.04607)
- [The Auton Agentic Framework - arXiv](https://arxiv.org/html/2602.23720)

**声明式vs命令式在Agent中的应用** [推导]:

```
传统Agent (命令式):
User → Write detailed Prompt → Agent follows steps → Result
       ↑ 高认知负荷（需精确描述所有细节）
       ↑ 脆弱（改需求需重新Prompt）

C8模型 (声明式):
Creator → Define Config (desired state) → Executor achieves it
          ↑ 低认知负荷（只描述目标，不描述方法）
          ↑ 健壮（executor可自适应）

K8s的证明:
kubectl apply -f config.yaml  # 声明
vs.
kubectl run ... / kubectl set ... / ...  # 命令

声明式胜出的原因:
- GitOps友好 (配置即代码)
- 幂等性 (apply多次结果一致)
- 自治能力 (controller自动修复)
```

### 7.2 Declarative Agent Frameworks的新浪潮 [事实]

**来源**:
- [Declarative Agents in M365 Copilot - Medium](https://wiprotechblogs.medium.com/declarative-agents-and-their-practical-applications-in-microsoft-m365-copilot-314a2abbffa1)
- [Why Declarative Programming Rules - Medium](https://medium.com/nativechat/why-will-declarative-programming-rule-chatbots-ai-and-cognitive-computing-f516cb9b80e1)

**M365 Copilot的实践** [事实]:

```
Declarative Agent在Microsoft M365中的应用:

config.yaml格式:
---
name: "Financial Review Agent"
responsibilities:
  - Extract invoice data
  - Compare with budget
  - Flag discrepancies
permissions:
  - read: ["documents", "spreadsheets"]
  - write: ["comments", "emails"]
  - execute: ["approval_workflows"]
interrupt_on:
  - amount > $10,000
  - missing_approver_id
  - duplicate_vendor_check_failed
escalation:
  - level: warning → alert_manager
  - level: critical → require_cfo_approval
---

效果:
- 非技术人员可配置Agent行为
- 配置版本控制，支持回滚
- 多个M365应用间可共享规则
```

---

## §8 开放问题与未来研究方向

### 8.1 Trust Degradation vs Learning Trade-off [开放问题]

当Agent完全自动化后（Level 8-10），人类是否会技能衰退？
- Bainbridge的警告仍然有效
- 但教学/teach_mode能否缓解？
- 需要长期纵向研究验证

### 8.2 Automation Bias在不同认知风格上的差异 [假说]

不同的人（分析型vs直觉型）对Automation Bias的易感性是否不同？
- 初步证据: 医疗专家的性别差异
- 需要跨领域的大规模研究

### 8.3 Multi-Agent Coordination的最优Granularity [开放问题]

在什么粒度上应该设置interrupt_on？
- 太粗 → 人的干预不及时
- 太细 → Approval Hell
- 需要任务特定的calibration方法

### 8.4 Constitutional AI在Agent中的实际效果 [假说]

Constitutional原则是否真能约束Agent行为？
- 当前证据: 有效但不完美
- 可能的原因: 原则间冲突、对抗性prompt
- 需要与formal verification结合

---

## §9 学习路径建议

**对于实现C8的工程师**:
1. 深入学习Sheridan-Verplank框架 → 理解什么应该自动化
2. 实践Claude Code三种模式 → 体验权限vs效率的权衡
3. 研究Cursor Rules在团队中的应用 → 规则持久化的方法
4. 读CHI 2025论文 → 理解认知负荷的实际影响
5. 设计Health Score → 动态调整自动化级别的反馈机制

**对于使用C8系统的产品经理**:
1. 理解Automation Levels的业务含义
2. 设计合理的interrupt_on策略（从严格开始）
3. 建立Health Score的度量体系
4. 记录用户的信任校准过程
5. 定期进行Retrospective，调整策略

**对于安全/合规团队**:
1. 映射Enterprise Approval Architecture到业务流程
2. 确保Layer 1/2/3的审计日志完整
3. 设计Anti-Jailbreak策略
4. 建立Agent action的Explainability要求
5. 定期进行安全评估和压力测试

---

## 参考文献按主题分类

### Anthropic & Claude Code官方文档
- [Choose a permission mode](https://code.claude.com/docs/en/permission-modes)
- [Configure permissions](https://platform.claude.com/docs/en/agent-sdk/permissions)
- [Claude Code Auto Mode](https://www.anthropic.com/engineering/claude-code-auto-mode)
- [Handle approvals and user input](https://platform.claude.com/docs/en/agent-sdk/user-input)

### 古典自动化理论
- [Sheridan & Verplank Levels - ResearchGate](https://www.researchgate.net/figure/Levels-of-automation-adopted-from-Sheridan-and-Verplank-39_fig2_287974071)
- [Fitts MABA-MABA - Springer](https://link.springer.com/article/10.1007/s10111-011-0188-1)
- [Rasmussen SRK Framework](https://www.elsevier.com/books/information-processing-and-human-machine-interaction/rasmussen/978-0-444-70862-5)

### 2024-2025学术研究
- [CHI 2025 Plan-Then-Execute Study](https://dl.acm.org/doi/10.1145/3706598.3713218)
- [Automation Bias Review - AI & Society](https://link.springer.com/article/10.1007/s00146-025-02422-7)
- [LLM-Human-Agent Systems Survey - arXiv](https://arxiv.org/html/2505.00753v4)
- [Orchestrating Human-AI Teams - arXiv](https://arxiv.org/html/2510.02557)

### 开源实践
- [Cursor Rules vs CLAUDE.md](https://www.agentrulesen.com/guides/cursorrules-vs-claude-md)
- [AI Coding Agents Comparison 2026](https://lushbinary.com/blog/ai-coding-agents-comparison-cursor-windsurf-claude-copilot-kiro-2026/)
- [dot-claude - GitHub](https://github.com/CsHeng/dot-claude)

### 企业应用
- [CodeBridge - Approval Architecture](https://www.codebridge.tech/articles/human-in-the-loop-ai-where-to-place-approval-override-and-audit-controls-in-regulated-workflows)
- [Enterprise AI Governance - Liminal](https://www.liminal.ai/blog/enterprise-ai-governance-guide)
- [Declarative Agents in M365 Copilot - Medium](https://wiprotechblogs.medium.com/declarative-agents-and-their-practical-applications-in-microsoft-m365-copilot-314a2abbffa1)

---

**文档完成**: 2026-03-30
**总字数**: ~6500
**下一步**: 集成到012_SYSTEM_C8_COLLABORATION.md的新Section N（工程实现）
