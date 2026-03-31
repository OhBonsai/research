# C2补充研究：Agent Persona与用户偏好的分离设计

> 归属：012_SYSTEM → C2 Layered Memory Architecture
> 研究问题：Agent个性（Persona）与用户偏好（User Preference）在产品设计中如何区分？分离的理由是什么？交互形式如何设计？业界实践如何？

---

## 1. 问题起源

C2记忆架构中，Persona和User Preference是两类需要持久化的信息。初始建议是**分开存储**，理由是更新频率不同：

- Persona：由系统/管理员定义，极少变动（季度级）
- User Preference：由用户行为积累，持续变动（周级甚至每轮）

但这个二分法是否足够？业界是否有更精细的模型？在B端企业办公场景下，交互形式应如何设计？

---

## 2. 业界实践横向分析

### 2.1 ChatGPT：三层模型（最成熟参考）

[事实] OpenAI将个性化拆成三个独立设置入口：

| 层级 | 名称 | 配置者 | 更新方式 | 作用域 |
|------|------|--------|---------|--------|
| Personality | 沟通风格模板（"鼓励型""直接型"等） | 用户选择 | 手动切换 | 全局 |
| Custom Instructions | "关于我"+"你应该怎么回应" | 用户填写 | 手动编辑 | 全局 |
| Memory | AI从对话中自动提取的事实记忆 | AI自动+用户审核 | 自动积累 | 全局 |

**冲突解决优先级**：当次对话指令 > Memory > Custom Instructions > Personality。

[事实] ChatGPT文档明确说："如果Memory中包含与Personality风格冲突的指导，Memory可能会覆盖或减弱该Personality的可见特征。"

**来源**：[OpenAI: Customizing Your ChatGPT Personality](https://help.openai.com/en/articles/11899719-customizing-your-chatgpt-personality) | [OpenAI: Memory FAQ](https://help.openai.com/en/articles/8590148-memory-faq)

### 2.2 Claude：三层+项目作用域

[事实] Anthropic的个性化方案：

| 层级 | 名称 | 说明 | 作用域 |
|------|------|------|--------|
| Styles | 沟通风格模板，可自定义或选择预设 | 全局，可按对话切换 |
| Profile Preferences | 用户背景信息（角色、偏好） | 全局 |
| Project Instructions | 项目级约束和上下文 | **项目级**（关键差异） |

[推导] Claude引入**项目级作用域**是对ChatGPT模型的重要改进。同一用户在"代码审查"项目和"文档写作"项目中可以有完全不同的指令，而Styles保持一致。这暗示了一个设计原则：**越具体的约束，作用域越窄**。

**来源**：[Claude: Understanding Personalization Features](https://support.claude.com/en/articles/10185728-understanding-claude-s-personalization-features) | [Claude: Configure and Use Styles](https://support.anthropic.com/en/articles/10181068-configuring-and-using-styles)

### 2.3 Microsoft Copilot：Declarative Agent模式

[事实] Microsoft采取了完全不同的路径——不在一个Agent上切换Persona，而是**将每个Persona封装为独立的Declarative Agent**。

每个Declarative Agent包含：
- `name` + `description`：Agent身份
- `instructions`：行为指令（"做什么"而非"不做什么"）
- `knowledge`：可访问的知识源
- `actions`：可执行的操作

[推导] 这种"一个Persona = 一个Agent"的模式对B端场景很有启发——"财务助手"和"IT运维助手"不是同一个Agent的两种Persona，而是两个独立的Agent实体。用户**切换Agent**而非**切换Persona**。

**来源**：[Microsoft: Declarative Agents for M365 Copilot](https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/overview-declarative-agent) | [Microsoft: Write Effective Instructions](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/declarative-agent-instructions)

### 2.4 AWS：企业角色驱动的Persona框架

[事实] AWS Generative AI Innovation Center发布的企业Agentic AI指南中，Persona不仅是语气风格，还包含**权限范围和合规约束**：

- P&L Owner → 关注KPI绑定的Agent行为
- CISO → 要求Agent被视为"同事"而非"代码"，需安全审计
- CDO → 关注数据可操作性
- Compliance Leader → 要求审计先于部署

[推导] AWS的框架揭示了B端Persona的本质——它不是"AI说话的语气"，而是**角色绑定的能力边界和责任范围**。这与C端"选择一个可爱的/严肃的风格"完全不同。

**来源**：[AWS: Agentic AI Enterprise Part 2 - Guidance by Persona](https://aws.amazon.com/blogs/machine-learning/agentic-ai-in-the-enterprise-part-2-guidance-by-persona/)

### 2.5 NetSuite：ERP中的Persona驱动Agent

[事实] Oracle NetSuite将Persona驱动推入ERP系统：CFO、仓库经理、SaaS运营者可以问同一个问题，但Agent根据角色返回不同的分析视角和数据粒度。

**来源**：[NetSuite Persona-Driven AI Agents](https://erp.today/netsuite-pushes-persona-driven-ai-agents-to-make-erp-intelligence-contextual-actionable/)

---

## 3. 归纳分析：从二分到四层模型

### 3.1 为什么两层不够

[推导] 通过对比5个产品的实践，原始的"Persona vs User Preference"二分法存在两个盲区：

1. **组织约束被忽略**：B端场景中，很多"Persona"实际上是IT管理员/团队负责人定义的，不属于用户个人也不属于AI自带。二分法无法区分"组织要求Agent不能执行删除操作"和"AI的默认沟通风格"。

2. **作用域未区分**：ChatGPT的全局Memory与Claude的项目级Instructions的差异说明，不同层级的信息需要不同的作用域。二分法将所有"偏好"混在一起，无法支持"在A项目中用简洁风格，在B项目中用详细风格"。

### 3.2 四层模型

[推导] 综合业界实践，建议采用**四层模型**：

```
┌─────────────────────────────────────────────────────┐
│  L1: Agent模板 (Agent Template)                      │
│  配置者：IT管理员/平台运营                              │
│  内容：角色定义、能力边界、合规约束、基础Persona           │
│  更新频率：极低（季度级）                                │
│  作用域：租户级/组织级                                   │
│  交互形式：管理后台，表单+YAML                           │
│  类比：Microsoft Declarative Agent                     │
├─────────────────────────────────────────────────────┤
│  L2: 团队规范 (Team Convention)                       │
│  配置者：团队负责人                                     │
│  内容：工作流偏好、术语表、输出格式、领域知识               │
│  更新频率：低（月级）                                    │
│  作用域：项目级/团队级                                   │
│  交互形式：Markdown编辑器（类Claude Project Instructions）│
│  类比：Claude Project Instructions                     │
├─────────────────────────────────────────────────────┤
│  L3: 个人偏好 (Personal Preference)                   │
│  配置者：最终用户                                       │
│  内容：沟通风格、语言习惯、工作背景                       │
│  更新频率：中（周级，含自动学习）                          │
│  作用域：用户级                                         │
│  交互形式：设置面板（选择题）+ AI自动记忆（可审阅列表）     │
│  类比：ChatGPT Custom Instructions + Memory            │
├─────────────────────────────────────────────────────┤
│  L4: 会话上下文 (Session Context)                      │
│  配置者：AI自动                                        │
│  内容：当前任务临时记忆、对话历史摘要                      │
│  更新频率：高（每轮）                                    │
│  作用域：会话级                                         │
│  交互形式：无显式UI，自动管理（用户可查看）                 │
│  类比：ChatGPT Memory自动提取                           │
└─────────────────────────────────────────────────────┘
```

### 3.3 四层模型的逻辑推导过程

**推导方法**：归纳法（从5个产品实践中提取共性维度）+ 演绎法（从B端场景需求推导缺失层级）

1. **维度提取**：所有产品都至少区分了"系统级风格"和"用户级偏好"→ 确认分离的必要性
2. **作用域发现**：Claude的Project Instructions证明需要"项目级"作用域 → L2的独立性
3. **B端特有需求**：Microsoft/AWS的企业框架证明需要"组织级约束" → L1独立于L3
4. **自动化程度分级**：ChatGPT的Memory自动提取 vs Custom Instructions手动编辑 → L3和L4的分离

---

## 4. 产品交互形式详细设计

### 4.1 L1 Agent模板：管理后台

**目标用户**：IT管理员（你的10万云桌面场景中，这是运维团队）

**交互形式**：

```
┌── Agent模板管理 ──────────────────────────┐
│                                           │
│  [+ 新建Agent模板]                         │
│                                           │
│  📋 办公文档助手                            │
│     角色：帮助用户撰写、编辑、格式化文档       │
│     能力：文档编辑 ✅ | 文件删除 ❌ | 网络访问 ❌│
│     风格：专业、简洁                         │
│     合规：禁止处理机密文件                    │
│     [编辑] [复制] [停用]                     │
│                                           │
│  🔧 IT运维助手                              │
│     角色：协助排查桌面问题、执行运维脚本        │
│     能力：命令执行 ✅ | 系统配置 ⚠️需审批      │
│     风格：技术性、步骤化                      │
│     合规：操作日志全量记录                    │
│     [编辑] [复制] [停用]                     │
│                                           │
└───────────────────────────────────────────┘
```

[推导] 参考Microsoft Declarative Agent的做法，不让用户在一个通用Agent上配置Persona，而是预定义**场景化Agent模板**。每个模板有固定的能力边界和沟通风格。理由：你的10万用户大多数不会写prompt，预定义模板大幅降低认知负担。

### 4.2 L2 团队规范：项目设置页

**目标用户**：团队负责人/项目经理

**交互形式**：

```
┌── 项目设置 > AI助手规范 ─────────────────────┐
│                                             │
│  📝 团队规范（Markdown编辑器）                 │
│  ┌─────────────────────────────────────┐    │
│  │ ## 术语表                            │    │
│  │ - VDI = 虚拟桌面基础设施               │    │
│  │ - Golden Image = 标准桌面镜像          │    │
│  │                                      │    │
│  │ ## 输出格式                           │    │
│  │ - 运维工单必须包含：问题描述、影响范围、 │    │
│  │   建议方案、预计耗时                   │    │
│  │                                      │    │
│  │ ## 工作流偏好                         │    │
│  │ - 代码变更必须先在测试环境验证          │    │
│  │ - 涉及超过10台桌面的操作需主管确认      │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  💡 提示：这些规范对项目内所有成员生效         │
│  [保存] [历史版本]                            │
│                                             │
└─────────────────────────────────────────────┘
```

[推导] 这是B端特有的层级。C端产品（ChatGPT/Claude个人版）没有这一层。交互形式参考Claude的Project Instructions——Markdown编辑器，足够灵活但有结构引导。

### 4.3 L3 个人偏好：双通道设计

**目标用户**：最终用户（10万云桌面用户）

**交互形式A：显式设置（选择题为主）**

```
┌── 个人设置 > AI偏好 ────────────────────────┐
│                                             │
│  🎨 回答风格                                 │
│  ○ 简洁直接    ● 适中平衡    ○ 详细解释       │
│                                             │
│  🌐 语言偏好                                 │
│  [中文（简体）         ▼]                     │
│                                             │
│  💼 我的角色                                 │
│  [IT运维工程师         ▼]                     │
│                                             │
│  📋 常用操作（可多选）                        │
│  ☑ 桌面故障排查   ☑ 软件分发                  │
│  ☐ 镜像制作       ☐ 策略配置                  │
│                                             │
└─────────────────────────────────────────────┘
```

**交互形式B：隐式学习（AI自动记忆 + 可审阅列表）**

```
┌── 个人设置 > AI记住的信息 ───────────────────┐
│                                             │
│  AI从对话中学到了以下信息：                    │
│                                             │
│  • 你负责华东区域的VDI集群运维    [编辑] [删除]│
│  • 你偏好用表格形式查看对比信息    [编辑] [删除]│
│  • 你常用的镜像版本是Win11-2024H2 [编辑] [删除]│
│  • 你习惯先看摘要再看详情         [编辑] [删除]│
│                                             │
│  [清除全部]  [暂停自动记忆]                    │
│                                             │
│  ℹ️ AI会自动从对话中提取有用信息。              │
│     你可以随时编辑或删除这些记忆。              │
│                                             │
└─────────────────────────────────────────────┘
```

[推导] 双通道的设计逻辑：**显式通道**降低冷启动成本（新用户立刻可用），**隐式通道**持续优化体验（老用户越用越好）。选择题而非自由文本是关键——10万用户规模下，自由文本的质量方差极大。

### 4.4 L4 会话上下文：无显式UI

[推导] L4不需要专门的设置界面。用户可以在对话中看到"AI正在使用N条记忆"的提示，点击可展开查看，但不需要主动配置。这与C2中的Working Memory层对应。

---

## 5. 冲突解决机制

### 5.1 优先级规则

```
冲突解决优先级（从高到低）：

  L1硬约束（安全/合规）    ← 不可覆盖，永远生效
       ↓
  L4 当次会话指令          ← 用户实时意图
       ↓
  L3 个人偏好              ← 用户长期习惯
       ↓
  L2 团队规范              ← 团队共识
       ↓
  L1软约束（风格/默认行为）  ← 可被上层覆盖
```

### 5.2 关键设计决策

[推导] L1需要区分**硬约束**和**软约束**：

| 类型 | 示例 | 可被覆盖？ |
|------|------|-----------|
| 硬约束 | "禁止执行rm -rf" "禁止访问机密文件" | ❌ 永远生效 |
| 软约束 | "默认使用简洁风格" "默认中文回答" | ✅ 可被L2/L3/L4覆盖 |

[事实] 这与Claude Code的权限系统一致——Claude Code区分"Allow"（可覆盖）和"Deny"（不可覆盖）两类权限规则。

### 5.3 冲突提示

当层级间发生冲突时，Agent应透明告知用户：

```
用户："帮我删除这个配置文件"
Agent："我无法执行文件删除操作——这是您的IT管理员设定的安全策略。
       建议您联系管理员，或通过运维工单系统提交删除请求。"
```

[推导] 透明告知冲突来源（"IT管理员的策略"而非"我不能做"）是信任建立的关键。参考Bainbridge自动化悖论——用户需要理解系统为什么拒绝，否则会丧失对系统的信任。

---

## 6. 与C2记忆架构的映射

四层模型直接映射到C2的记忆存储层级：

| 产品层级 | C2记忆层级 | 存储方式 | 生命周期 |
|----------|-----------|---------|---------|
| L1 Agent模板 | 系统记忆（System Memory） | 配置文件/DB，管理员写入 | 与Agent实体同生命周期 |
| L2 团队规范 | 项目记忆（Project Memory） | Markdown文件，团队维护 | 与项目同生命周期 |
| L3 个人偏好 | 用户记忆（User Memory） | 结构化存储+向量索引 | 用户可管理，自动衰减 |
| L4 会话上下文 | 工作记忆（Working Memory） | 内存/临时存储 | 会话结束后压缩归档 |

### 6.1 Hook注入映射

```python
# session_init阶段：按层级顺序加载
def load_persona_and_preferences(session, user, project, agent_template):
    """四层个性化信息的加载顺序"""

    # L1: Agent模板（最先加载，包含硬约束）
    system_prompt = agent_template.base_instructions
    hard_constraints = agent_template.security_constraints  # 不可覆盖
    soft_defaults = agent_template.style_defaults            # 可覆盖

    # L2: 团队规范（覆盖L1软约束）
    if project and project.team_conventions:
        system_prompt = merge_with_override(
            system_prompt,
            project.team_conventions,
            protected=hard_constraints  # 硬约束不可覆盖
        )

    # L3: 个人偏好（覆盖L2）
    user_prefs = load_user_preferences(user.id)  # 显式设置
    user_memory = retrieve_user_memory(user.id)    # 隐式积累
    system_prompt = merge_with_override(
        system_prompt,
        user_prefs + user_memory,
        protected=hard_constraints
    )

    # L4: 会话上下文（在before_model中动态注入）
    session.context_state.persona_layers = {
        "L1_hard": hard_constraints,
        "L1_soft": soft_defaults,
        "L2_team": project.team_conventions if project else None,
        "L3_explicit": user_prefs,
        "L3_implicit": user_memory,
    }

    return system_prompt
```

---

## 7. 开放问题

### 7.1 自动学习的偏好与显式设置的共存

[开放问题] 目前所有主流产品都未完美解决：AI自动学习的偏好如何与显式设置共存？例如：用户在Custom Instructions中写"请简洁回答"，但Memory中记录了用户某次要求详细解释的偏好。ChatGPT的做法是Memory优先，但这可能违背用户的长期意图。

**可能的解决方向**：区分"规则型偏好"（"我总是想要简洁回答"）和"情境型偏好"（"上次那个问题需要详细解释"），规则型优先于情境型。

### 7.2 B端的多角色切换

[开放问题] 同一个用户可能在不同时间扮演不同角色（早上是IT运维，下午做项目管理）。L3的个人偏好是否需要支持"角色切换"？还是依赖L2的项目作用域自动切换？

### 7.3 Persona的可组合性

[开放问题] 是否允许"组合Persona"？例如，一个Agent同时具备"IT运维专家"的知识和"友善导师"的沟通风格。如果允许组合，如何防止组合爆炸和行为不一致？

### 7.4 隐式学习的企业数据安全

[开放问题] L3的隐式学习（AI自动提取偏好）在B端面临数据安全挑战：AI从对话中提取的"偏好"可能包含敏感业务信息。如何在个性化和数据安全之间取得平衡？

---

## 8. 参考文献

### 产品实践

1. OpenAI. Customizing Your ChatGPT Personality. [OpenAI Help Center](https://help.openai.com/en/articles/11899719-customizing-your-chatgpt-personality)
2. OpenAI. Memory FAQ. [OpenAI Help Center](https://help.openai.com/en/articles/8590148-memory-faq)
3. OpenAI. Memory and New Controls for ChatGPT. [openai.com](https://openai.com/index/memory-and-new-controls-for-chatgpt/)
4. Anthropic. Understanding Claude's Personalization Features. [Claude Help Center](https://support.claude.com/en/articles/10185728-understanding-claude-s-personalization-features)
5. Anthropic. Configure and Use Styles. [Anthropic Help Center](https://support.anthropic.com/en/articles/10181068-configuring-and-using-styles)
6. Anthropic. Claude Code Now Lets You Customize Its Communication Style. [ainativedev.io](https://ainativedev.io/news/claude-code-now-lets-you-customize-its-communication-style)

### 企业框架

7. Microsoft. Declarative Agents for Microsoft 365 Copilot. [Microsoft Learn](https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/overview-declarative-agent)
8. Microsoft. Write Effective Instructions for Declarative Agents. [Microsoft Learn](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/declarative-agent-instructions)
9. Microsoft. Best Practices for Building Declarative Agents. [Microsoft Learn](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/declarative-agent-best-practices)
10. Microsoft. UX Design for Agents. [microsoft.design](https://microsoft.design/articles/ux-design-for-agents/)
11. AWS. Agentic AI in the Enterprise Part 2: Guidance by Persona. [AWS ML Blog](https://aws.amazon.com/blogs/machine-learning/agentic-ai-in-the-enterprise-part-2-guidance-by-persona/)
12. NetSuite. Persona-Driven AI Agents to Make ERP Intelligence Contextual. [erp.today](https://erp.today/netsuite-pushes-persona-driven-ai-agents-to-make-erp-intelligence-contextual-actionable/)

### Agent Persona设计

13. Azilen. Agent Persona in Agentic AI: Architecture & Implementation. [azilen.com](https://www.azilen.com/learning/agent-persona/)
14. Mosher, G. (2026). AI Agent Personas: Service Design, Updated. [Medium](https://medium.com/@iamgeoffmosher/ai-agent-personas-service-design-updated-787a7eb62e8f)
15. Fuselab Creative. AI Agents, UI Design Trends for Agents. [fuselabcreative.com](https://fuselabcreative.com/ui-design-for-ai-agents/)
16. Agentic Design Patterns. UI/UX & Human-AI Interaction. [agentic-design.ai](https://agentic-design.ai/patterns/ui-ux-patterns)

### 学术与理论

17. Bainbridge, L. (1983). Ironies of Automation. Automatica, 19(6). — 自动化悖论：用户需要理解系统拒绝的原因
18. Sheridan, T.B. & Verplank, W.L. (1978). Human and Computer Control of Undersea Teleoperators. — 10级自动化层级模型
19. Sweller, J. (1988). Cognitive Load During Problem Solving. Cognitive Science, 12(2). — 认知负荷理论，指导交互复杂度设计
