# § C7 可拆卸性与模块化 - 增强研究笔记

**研究日期**：2026-03-30
**研究助手**：Claude (Haiku 4.5)
**信息源分类**：Anthropic 官方、GitHub 开源、古典软件架构、2025-2026 工业趋势、学术文献
**笔记风格**：[事实]/[推导]/[假说]/[开放问题]

---

## § A. Model Context Protocol (MCP) - 规范化工具抽象

### A.1 MCP 核心设计 [事实]

**来源**：[Anthropic MCP 官方说明](https://anthropic.skilljar.com/introduction-to-model-context-protocol) | [MCP 规范 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25) | [GitHub MCP](https://github.com/modelcontextprotocol)

**关键发现**：

1. **三元基本体**（Three Primitives）[事实]
   - **Tools**：模型控制（Model-controlled）
   - **Resources**：应用控制（App-controlled）
   - **Prompts**：用户控制（User-controlled）

2. **工具装载的两种范式** [事实]

   **传统范式（All-in-Context）**：
   - 客户端启动时装载所有工具定义到上下文中
   - 优点：简单，低延迟
   - 缺点：上下文膨胀，模型需处理不相关工具列表

   **高级范式（On-Demand Loading）**：[事实]
   - 工具定义存储在文件系统，模型按需读取
   - 通过 `search_tools(query)` 进行工具发现，支持 detail_level 参数
   - 允许 Agent 仅加载必要工具到上下文
   - **对 C7 启示**：Harness 应支持"声明式工具检索"而非"静态工具列表"

3. **代码执行的上下文效率** [推导]
   - MCP 通过允许 Agents 在单步操作中执行复杂逻辑来提高上下文利用率
   - 数据可在到达模型前被过滤，减少噪音

### A.2 MCP 生态成熟度（2025-2026）[事实]

**来源**：[MCP 一周年回顾](https://blog.modelcontextprotocol.io/posts/2025-11-25-first-mcp-anniversary/) | [企业级 MCP 采纳 2026](https://www.cdata.com/blog/2026-year-enterprise-ready-mcp-adoption)

**行业现状** [事实]：
- **时间线**：2024 年 11 月发布 → 2025 年成为行业标准 → 2026 年期望企业级成熟度
- **生态规模**：1000+ 活跃连接器（connectors），跨数据源、API、企业工具
- **厂商支持**：Anthropic、OpenAI、Google、Microsoft、AWS、Linux 基金会治理

**标准化进度** [事实]：
- 2025 年 11 月规范发布，向超出同步工具调用的能力扩展
- 支持安全的长期运行工作流、现代授权、异步执行
- 多框架互操作性层计划（LangChain、AutoGen、Haystack、Semantic Kernel）

**工具互操作性的变革意义** [推导]：
- 开发人员可构建"一次，在任何地方工作"的连接器
- 消除了以前困扰 AI 进展的冗余
- 模型无关性：同一连接器可在任何支持 MCP 的 LLM 中使用

### A.3 MCP 与传统工具适配的对比 [推导]

| 维度 | OpenAI Function Calling | MCP |
|------|------------------------|-----|
| 模型绑定 | 紧密耦合（model="gpt-4"） | 模型无关（protocol 定义） |
| 工具定义格式 | JSON Schema（OpenAI 特定） | 统一协议，适配多格式 |
| 装载策略 | 静态（启动时全部）| 动态（按需发现） |
| 生态可扩展性 | 提供商驱动 | 社区驱动（1000+ 连接器） |
| 执行效率 | 模型处理所有工具列表 | 上下文感知过滤 |

**C7 设计建议** [推导]：应采纳 MCP 的"协议优先"思路，而非"API 适配"思路

---

## § B. Claude Code 的模型无关设计

### B.1 框架架构 [事实]

**来源**：[Claude Code 插件文档](https://code.claude.com/docs/en/plugins) | [官方仓库](https://github.com/anthropics/claude-code) | [Medium 深度分析](https://thamizhelango.medium.com/beyond-function-calling-how-claude-codes-plugin-architecture-is-redefining-ai-development-tools-67ccec9b5954)

**核心特性** [事实]：
- **模型无关的工具套件**：为任何支持工具调用的 LLM 提供文件系统访问、Shell、分层内存、声明式可扩展性
- **有界自主循环**（Bounded Autonomous Loop）：通过组合权限进行治理
- **插件优先架构**：插件是主要扩展点，定义在 `plugin.json` 清单中

### B.2 原始工具（Primitive Tools）哲学 [事实]

**设计原则** [事实]：
- 不提供 80 个专业工具或 800 个临时工具
- 而是提供小的能力原始体（Bash、Grep、Edit）来组合任何人类工程师可执行的工作流
- **模块化程度**：最小化工具集 + 最大化组合性

**对 C7 的启示** [推导]：
- Harness 的工具抽象应遵循"原始性"而非"全面性"
- 工具定义的粒度应支持组合而非覆盖所有用例
- 减少每个模型适配器需要理解的"特殊工具"数量

### B.3 插件系统 [事实]

**扩展点**：
1. Skills（自定义斜杠命令 `/command`）
2. Hooks（特定生命周期事件的执行逻辑）
3. MCP Servers（外部工具定义）
4. 持久化状态

**生态** [事实]：
- 官方 Plugin Marketplace
- 社区贡献：400,000+ 通过 SkillKit、150+ 插件、19 个 Hooks、8 个 MCP 配置

---

## § C. 模型路由与抽象层模式

### C.1 LiteLLM 架构 [事实]

**来源**：[LiteLLM 文档](https://docs.litellm.ai/) | [对比分析](https://medium.com/next-token/litellm-the-swiss-army-knife-for-your-llm-integrations-abstraction-or-router-0ead365367fd)

**定位** [事实]：
- 开源路由器，统一接口到 100+ LLM API
- 自托管代理、GitOps 策略、深度观测集成
- 支持请求日志、故障回退、成本追踪、速率限制

**核心概念** [事实]：
- **抽象层策略**：应用代码不绑定特定提供商标识符
- **稳定命名**：应用使用内部标准名称（e.g., "general-purpose-llm"），映射到具体模型
- **动态映射**：幕后将内部名称映射到具体实现

**OpenRouter 支持** [事实]：
- LiteLLM 支持所有 OpenRouter 模型，通过 `openrouter/<model-name>` 命名约定
- 两个平台的组合：OpenRouter 提供托管边缘服务 + LiteLLM 提供本地路由灵活性

### C.2 LiteLLM vs OpenRouter vs 自构建 [事实]

| 维度 | OpenRouter | LiteLLM | 自构建 |
|------|-----------|---------|--------|
| 托管模式 | 完全托管 SaaS | 自托管代理 | 自定义 |
| 模型数量 | 200+ | 100+ | 依赖集成 |
| 路由灵活性 | 受限（预配置） | 高（GitOps） | 最高 |
| 成本追踪 | 基础 | 高级 | 自定义 |
| 部署复杂性 | 最低 | 中等 | 最高 |
| 可观测性集成 | 有限 | 深度（Prometheus等） | 自定义 |

**C7 设计建议** [推导]：
- 采纳 LiteLLM 的"内部标准名称"概念
- Harness 配置应使用"逻辑模型标识符"，在运行时映射到具体提供商

### C.3 工具互操作性标准化 [推导]

**多框架支持计划** [事实]：
- MCP 未来版本计划提供标准互操作层
- 支持 LangChain、AutoGen、Haystack、Semantic Kernel 等框架
- 目标：工具无关的 Agent 编排

**标准化方向** [推导]：
- JSON Schema 作为工具定义的通用格式
- 模型提供商支持多种工具格式：OpenAI、Anthropic、MCP、自定义
- Harness 应在这三个层级上建立适配器：协议层、格式层、语义层

---

## § D. 经典软件架构原则在 AI 时代的再发现

### D.1 Parnas 信息隐藏 - 现代应用 [事实]

**核心再解读** [推导]：
在 AI Agent 系统中，信息隐藏的"设计决策"包括：
1. **模型选择决策**：哪个提供商、哪个版本
2. **工具格式决策**：OpenAI vs Anthropic vs MCP 格式
3. **Prompt 工程决策**：系统提示、Few-shot 示例、格式指示
4. **执行策略决策**：Sequential vs Agentic Loop vs Tree Search

**模块化原则** [推导]：
- 每个决策应被隐藏在单个模块（Adapter 或 Registry）中
- 一旦决策变化，只有该模块受影响
- Agent 逻辑对这些决策应"相对独立"

### D.2 SOLID 原则与 AI 系统 [推导]

#### D.2.1 单一职责原则（SRP）
- **模型适配器**：仅负责 API 翻译
- **工具注册表**：仅负责工具发现与元数据
- **执行引擎**：仅负责 Agent 循环逻辑

#### D.2.2 开放-闭合原则（OCP）
- **开放扩展**：新模型适配器无需修改 Harness 核心
- **闭合修改**：Harness 核心逻辑不变

#### D.2.3 Liskov 替换原则（LSP）
- **模型提供商的互换性**：任何 IModelProvider 的实现应能替换其他实现
- **工具格式的互换性**：JSON Schema 适配器应与 OpenAI 适配器互换

#### D.2.4 接口分离原则（ISP）
- **细粒度接口**：Agent 仅依赖它需要的接口部分
- 反例：暴露"完整 API 特性"给只需"基础推理"的 Agent

#### D.2.5 依赖反演原则（DIP） - 最关键 [事实]
```
高层模块（Agent 逻辑）
    ↑
    | 依赖抽象
    ↓
[IModelProvider] ← 抽象接口
    ↑
    | 实现
    |
[OpenAI 适配器] [Anthropic 适配器] [本地 Ollama] [OpenRouter]
```

**实施检验** [推导]：
- Agent 代码中不应出现 `if model_provider == "openai"`
- 不应导入 `openai_client` 或 `anthropic_client` 到 Agent 层
- 所有提供商具体类应在底层注册表中实例化

### D.3 六边形架构在 Harness 中的具体映射 [推导]

```
        [用户应用]
            ↓
    ╔═══════════════════╗
    ║  Harness Core     ║  业务逻辑
    ║  Agent Logic      ║
    ╚═══════════════════╝
            ↑ ↓
    ┌───────┴─┴──────────┐
    |                    |
[模型调用 Port]    [工具定义 Port]    [执行策略 Port]
    ↓ ↓ ↓              ↓ ↓ ↓                ↓ ↓
  OpenAI  Anthropic   JSON  OpenAI       Sequential
  Google  Ollama      MCP   Custom        Agentic
  AWS                 Custom Format       Tree Search
```

**Port 与 Adapter 的完整对应** [推导]：

| Port | 目的 | Adapter 示例 | 拆换场景 |
|------|------|-----------|--------|
| **Model Invocation** | 与 LLM 通信 | OpenAI / Anthropic / Ollama | 模型升级、供应商切换 |
| **Tool Definition** | 工具元数据格式 | OpenAI JSON / Anthropic / MCP | 模型支持新工具格式 |
| **Context Assembly** | 构建输入上下文 | RAG Pipeline / Memory / Static | 改进检索或内存策略 |
| **Execution Loop** | Agent 控制流 | Sequential / Agentic / Tree Search | 不同任务需要不同策略 |
| **Prompt Engineering** | 提示词处理 | Few-shot / Chain-of-thought / Persona | 优化提示效果 |
| **Output Parsing** | 模型输出解析 | JSON / Markdown / XML / Tool Call | 模型输出格式差异 |
| **Error Handling** | 异常恢复 | Retry / Fallback / User Escalation | 不同 API 错误语义 |

### D.4 Unix 哲学 - Agent 工具设计 [事实/推导]

**三个原则的应用** [推导]：

1. **做一件事，并做得很好（Do One Thing Well）**
   - 每个工具只执行单一职责
   - 例：`SearchTool` 只搜索，不解释；`ParseTool` 只解析，不执行
   - vs 反例：`UniversalAgent` 做所有事

2. **写程序使其互相合作（Make Programs Cooperate）**
   - 工具输出格式标准化（JSON / Markdown）
   - 允许链式调用（Pipeline）
   - 例：`SearchTool` → `ParseTool` → `VerifyTool`

3. **处理文本流作为通用接口（Universal Interface）**
   - 工具间通过结构化文本（JSON / Markdown）通信
   - 不依赖二进制格式或特定数据结构
   - 降低耦合

**McIlroy 原则的应用** [推导]：
> "40% 工程师解决问题，60% 工程师把解决方案组合在一起"

在 Harness 中：
- 40%：建立基础能力原语（Bash、Grep、Edit 等）
- 60%：通过工具组合、Prompt 工程、执行策略来处理具体应用

---

## § E. 软件模块化指标与耦合-内聚分析

### E.1 耦合与内聚的定义与度量 [事实]

**来源**：[TechTarget 耦合指标](https://www.techtarget.com/searchapparchitecture/tip/The-basics-of-software-coupling-metrics-and-concepts) | [ACM 论文](https://dl.acm.org/doi/10.1145/1027092.1027094) | [软件网络度量](https://pmc.ncbi.nlm.nih.gov/articles/PMC7514828/)

**核心定义** [事实]：
- **内聚**：模块内部的相互依赖程度（LCOM - Lack of Cohesion in Methods）
- **耦合**：模块间的依赖程度
  - **遗出耦合**（Efferent）：当前模块依赖其他模块数
  - **传入耦合**（Afferent）：有多少模块依赖当前模块

**度量方法** [事实]：
- **信息论方法**：将软件表示为网络（Feature Coupling Network）
  - 节点：方法和属性
  - 边：方法/属性间的耦合
  - 权重：耦合强度

**设计目标** [事实]：
- **高内聚**：模块内的元素紧密相关
- **低耦合**：模块间依赖最少
- 这是"模块化"最重要的原则

### E.2 模块化对质量属性的影响 [事实]

| 质量属性 | 受影响机制 | 耦合的负面影响 |
|---------|---------|------------|
| **可重用性** | 高耦合 → 难以在其他项目复用 | 拖带过多依赖 |
| **可维护性** | 高耦合 → 一个变更波及多个模块 | 改动成本高 |
| **可测试性** | 高耦合 → 需要复杂的 Mock 设置 | 单元测试困难 |
| **可理解性** | 高耦合 → 需理解多个模块的交互 | 认知负荷高 |
| **灵活性** | 高耦合 → 难以替换实现 | 适配新需求困难 |

**C7 实施建议** [推导]：
- 计算 Harness 各层的 Efferent/Afferent 耦合比
- Agent 层 → Harness 层的耦合应尽可能低
- Harness 层 → 模型层的耦合应完全通过接口抽象

### E.3 AI 系统中的模块化度量 [推导]

**新维度**：
1. **模型无关性指数**：Agent 代码中有多少行包含模型名称/API 调用？
   - 目标：0（所有模型相关逻辑在适配器中）

2. **工具格式耦合**：支持多少种工具定义格式而无需修改 Agent？
   - 目标：N（通过 Adapter 支持任意格式）

3. **执行策略灵活性**：不修改 Agent 代码能切换执行策略吗？
   - 目标：是（通过配置）

4. **上下文组装独立性**：RAG、内存、静态提示是否可互换？
   - 目标：是（通过 Port）

---

## § F. OpenAI 函数调用标准化与互操作性

### F.1 标准 JSON Schema 格式 [事实]

**来源**：[OpenAI 函数调用 API](https://developers.openai.com/api/docs/guides/function-calling) | [结构化输出](https://developers.openai.com/api/docs/guides/structured-outputs)

**基本结构** [事实]：
```json
{
  "type": "function",
  "function": {
    "name": "search_documents",
    "description": "Search documents by keyword",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "Search query"
        },
        "limit": {
          "type": "integer",
          "description": "Max results"
        }
      },
      "required": ["query"]
    }
  }
}
```

**工具调用响应** [事实]：
- 模型返回 `tool_calls` 数组，每个包含：
  - `id`：用于后续结果提交的标识符
  - `function.name`：调用的函数名
  - `function.arguments`：JSON 编码的参数

### F.2 Strict 模式与标准化 [事实]

**严格模式（Strict: true）**：
- 保证模型生成的参数 100% 匹配定义的 JSON Schema
- 适用于函数调用（Tool Use）
- 适用于响应格式（Structured Outputs）

**对互操作性的意义** [推导]：
- 标准化了"期望的工具调用格式"
- 不同模型都需支持同一 JSON Schema
- 创造了"工具定义的通用语言"

### F.3 与 Anthropic Tool Use 的对比 [推导]

| 特性 | OpenAI Functions | Anthropic Tool Use |
|------|-----------------|-------------------|
| 格式 | JSON Schema | XML-based (tools) |
| 严格模式 | 支持（strict: true） | 支持（约束） |
| 流式处理 | 流式工具调用 | 流式工具输入 |
| 嵌套工具 | 有限 | 完整支持 |
| 模型意图表达 | 隐含（模型选择调用） | 显式（reasoning 标记） |

**C7 设计建议** [推导]：
- Harness 应支持"多工具格式适配"（Adapter Pattern）
- 内部标准化到单一格式（建议 JSON Schema）
- 每个模型适配器负责双向转换（Harness ↔ 模型格式）

---

## § G. 工具和插件生态的互操作性标准化

### G.1 2025-2026 标准化进展 [事实]

**来源**：[MCP 生态成熟度](https://www.cdata.com/blog/2026-year-enterprise-ready-mcp-adoption) | [Thoughtworks MCP 影响分析](https://www.thoughtworks.com/en-us/insights/blog/generative-ai/model-context-protocol-mcp-impact-2025)

**核心进展** [事实]：
1. **MCP 成为行业标准**（2025-2026）
   - OpenAI、Google、Microsoft、AWS 都支持或集成 MCP
   - Linux 基金会治理宣布

2. **超越同步工具的架构**（2025-11 规范）
   - 支持长期运行工作流
   - 现代授权机制
   - 异步执行支持

3. **多框架互操作性层**
   - LangChain、AutoGen、Haystack、Semantic Kernel 的标准集成点
   - 工具"一次构建，到处运行"

### G.2 1000+ 连接器生态的启示 [推导]

**生态规模** [事实]：1000+ 活跃连接器跨越：
- 数据源（数据库、Web API、消息队列）
- 企业工具（CRM、ERP、协作工具）
- 云平台服务（AWS、Google Cloud、Azure）

**成功因素分析** [推导]：
1. **协议优先**而非"API 适配"
   - 一个 MCP 服务器 → 所有支持 MCP 的 LLM
   - vs OpenAI Functions → 只能用 OpenAI 模型

2. **生态驱动开发**
   - 开发人员贡献新连接器无需 Anthropic 参与
   - 标准化的扩展机制（tools、resources、prompts）

3. **格式无关性**
   - 连接器定义内部格式，MCP 协议统一翻译
   - 模型适配器只需理解 MCP，不需针对每个连接器

**C7 对标建议** [推导]：
- 将 Harness 视为"平台工程工具"，而非"模型适配库"
- 建立社区贡献机制（工具、执行策略、提示模板）
- 定义稳定的 Harness Plugin Protocol，而非只支持预定义的适配器

---

## § H. 依赖反演原则的深化应用

### H.1 四层依赖反演映射 [推导]

**第一层：模型提供商**
```
正确: Agent → [IModelProvider] ← OpenAI Adapter
错误: Agent → OpenAI Client (紧耦合)
```

**第二层：工具定义格式**
```
正确: Agent → [IToolFormat] ← OpenAI Adapter
                          ← Anthropic Adapter
                          ← MCP Adapter
错误: Agent → if tool_format == "openai": ... (条件耦合)
```

**第三层：执行策略**
```
正确: Agent → [IExecutionStrategy] ← Sequential
                                 ← Agentic Loop
                                 ← Tree Search
错误: Agent → case execution_mode: ... (硬编码)
```

**第四层：上下文组装**
```
正确: Agent → [IContextAssembler] ← RAG Pipeline
                              ← Memory System
                              ← Static Prompts
错误: Agent → RAG Pipeline (混合业务逻辑)
```

### H.2 接口设计指导 [推导]

**接口应该**：
1. 代表"一类设计决策"（Parnas 意义）
2. 足够通用以容纳多种实现
3. 足够具体以保证实现的互换性（Liskov）
4. 避免暴露实现细节的参数

**反例** [推导]：
```python
# 坏：接口暴露提供商细节
class IModelProvider:
    def call(self, messages, openai_functions, anthropic_tools, ...): pass

# 好：接口隐藏格式细节
class IModelProvider:
    def call(self, messages, tools): pass
    def format_tools(self, tools: List[Tool]) -> Any: pass
```

---

## § I. 平台工程与 Harness 的配置优于编码

### I.1 IDP（内部开发平台）模型在 Harness 中的应用 [推导]

**三层抽象** [推导]：

```yaml
Layer 1（用户接口）：
  agent.run(task, config_name="high_reasoning")

Layer 2（Harness 平台 API）：
  config.yml:
    model: "general_purpose_llm"
    model_mapping:
      general_purpose_llm: "claude-opus-4"
    execution_strategy: "agentic_loop"
    tools:
      - name: "search"
        format: "mcp"

Layer 3（底层实现）：
  [Model Providers] [Tool Registries] [Execution Engines]
```

### I.2 配置驱动设计原则 [推导]

**不应出现在应用代码中**：
- `model="openai/gpt-4-turbo"`
- `if provider == "anthropic": use_vision = False`
- `tool_format = "openai" if model.startswith("gpt") else "anthropic"`

**应出现在配置中**：
```yaml
models:
  gpt-4-turbo:
    provider: openai
    capabilities:
      vision: true
      tool_format: openai

  claude-opus-4:
    provider: anthropic
    capabilities:
      vision: true
      tool_format: anthropic
```

**关键好处** [推导]：
1. **运行时模型切换**：无需重新部署代码
2. **A/B 测试**：通过配置选择不同模型进行对比
3. **成本优化**：通过配置动态选择成本/性能最优模型
4. **合规性**：通过配置限制特定地域模型的使用

---

## § J. 开放问题与研究方向

### J.1 模型能力抽象的粒度问题 [开放问题]

**问题**：`IModelProvider.capabilities` 应包括哪些字段？

**已知选项**：
- **粗粒度**：`{ vision, tool_use, streaming }`
  - 优点：简洁
  - 缺点：无法表达细节（e.g., "支持 3 种工具格式"）

- **细粒度**：`{ max_context_length, vision, tool_formats: [...], reasoning_effort: [...], ... }`
  - 优点：精确
  - 缺点：需频繁维护，新模型发布时需更新

**假说**：能力应该是声明式的、支持版本化的元数据，而非枚举值

### J.2 工具格式的标准化困境 [开放问题]

**问题**：应该统一到单一格式（如 JSON Schema）还是支持多格式?

**对比**：
- **单一格式**：简化 Agent 代码，但限制模型选择
- **多格式**：支持最优模型，但增加适配器复杂度

**假说**：应该有"核心格式"（JSON Schema）+ 可选格式支持，通过 Adapter 无缝切换

### J.3 热交换执行策略的可行性 [开放问题]

**问题**：能否在运行时无缝切换执行策略（Sequential → Agentic Loop）而无需重新初始化状态？

**关键约束**：
- 状态兼容性（某些策略需要额外状态）
- 上下文窗口管理
- 工具调用历史的一致性

**假说**：需要"执行策略适配器"，将不同策略的状态表示标准化

### J.4 MCP 与传统 Agent 框架的融合点 [开放问题]

**问题**：Harness 应该内置 MCP 支持还是通过适配器层支持?

**权衡**：
- **内置**：native 性能，但增加 Harness 核心复杂度
- **适配器**：更模块化，但可能性能开销

**假说**：MCP 应该作为"默认优先"的适配器，但 Harness 核心应该协议无关

### J.5 成本与性能的多目标优化 [开放问题]

**问题**：如何动态选择模型权衡成本、性能和质量？

**维度**：
- 成本：$/token
- 性能：推理延迟
- 质量：任务成功率

**假说**：需要"模型选择器"（Model Router）的高阶策略，基于历史性能和成本数据

---

## § K. 综合设计建议总结

### K.1 采纳的原则 [推导]

1. **Parnas 信息隐藏**：设计决策隐藏在模块内
2. **SOLID DIP**：Harness 层对所有实现无依赖
3. **六边形架构**：明确的 Port 和可插拔 Adapter
4. **Unix 哲学**：小工具、高组合性
5. **MCP 协议优先**：工具定义格式标准化
6. **配置优于编码**：运行时灵活性

### K.2 分层清晰性 [推导]

```
应用层（Agent Logic）
    ↓ 依赖抽象 ↓
Harness 层（IModelProvider, IToolFormat, IExecutionStrategy）
    ↓ 实现 ↓
适配器层（OpenAI Adapter, Anthropic Adapter, MCP Adapter）
    ↓ 调用 ↓
模型层（LLM API、本地模型）
```

### K.3 可扩展点（Extension Points） [推导]

1. **新模型提供商**：实现 `IModelProvider`
2. **新工具格式**：实现 `IToolFormatter`
3. **新执行策略**：实现 `IExecutionStrategy`
4. **新 Prompt 工程**：实现 `IPromptTemplate`
5. **新上下文源**：实现 `IContextAssembler`

---

## 参考资源

### Anthropic 与 MCP
- [Model Context Protocol 官方](https://modelcontextprotocol.io/)
- [MCP GitHub 仓库](https://github.com/modelcontextprotocol)
- [Claude Code 插件文档](https://code.claude.com/docs/en/plugins)

### 模型路由与抽象
- [LiteLLM 官方文档](https://docs.litellm.ai/)
- [OpenRouter 官方](https://openrouter.ai/)

### 经典架构
- [Parnas 原论文](https://dl.acm.org/doi/10.1145/361598.361623)
- [Alistair Cockburn 六边形架构](https://alistair.cockburn.us/hexagonal-architecture/)

### 标准化与互操作性
- [OpenAI 函数调用 API](https://developers.openai.com/api/docs/guides/function-calling)
- [2026 MCP 企业采纳预期](https://www.cdata.com/blog/2026-year-enterprise-ready-mcp-adoption)

### 模块化度量
- [软件耦合度量](https://www.techtarget.com/searchapparchitecture/tip/The-basics-of-software-coupling-metrics-and-concepts)
- [模块化与代码耦合关系](https://pmc.ncbi.nlm.nih.gov/articles/PMC7514828/)

---

**笔记完成时间**：2026-03-30
**后续行动**：用本笔记的内容充实 012_SYSTEM_C7_MODULARITY.md 的"工程实现"和"算法与Hook映射"章节
