# 观测-测试-评价：Harness 算法的工程验证框架

> 本文定位：所有 Category（C1 上下文、C2 记忆、C3 约束……）算法改进的**通用验证方法论**。
> 依赖文档：032_ATA_C1_Context.md（以 C1 为首个实例）、032_ATA_C1_Context_CODE.md（30 个测试 case）
> 工程基座：OpenCode Plugin 机制（TypeScript）、Codex Hook 机制（Rust）

---

## 问题陈述

032_ATA_C1_Context.md 定义了 6 个上下文管理算法，032_ATA_C1_Context_CODE.md 定义了 30 个测试 case。但从"算法定义"到"量化验证"之间，存在三个未回答的工程问题：

**问题 1：算法运行时发生了什么？** 6 个算法在 Plugin 中执行，但运行时的状态（触发次数、参数值、处理时长）是黑盒。不打开黑盒，优化就是盲调。

**问题 2：怎么实现这些算法？** 032 文档给了伪代码和 TypeScript 片段，但没有回答"算法在 Plugin 生命周期的哪个 hook 中执行""hook 之间如何共享状态""多算法耦合时的执行顺序"。

**问题 3：测试用例怎么跑？** 30 个 case 定义了场景和 probe，但执行需要一套端到端的工具链：种子数据加载 → 自动化对话驱动 → 观测数据采集 → probe 评分 → 结果聚合。

本文的任务是回答这三个问题，形成一套可复用的框架——不只为 C1 上下文管理，而是为后续所有 Category 的算法改进提供统一的"观测-测试-评价"工程方法。

推导逻辑：三个问题之间存在依赖关系。问题 2 依赖问题 1（不理解 Plugin 机制就无法设计算法实现），问题 3 依赖问题 1 和 2（不能观测和运行算法就无法测试）。因此本文的结构按依赖链展开：先机制，再观测，再实现，再测试，最后评价。

---

## 一、OpenCode 的 Plugin 机制

### 1.1 架构位置

OpenCode 是一个 TypeScript CLI Agent 框架。其处理链为：用户输入 → Session Processor → LLM 调用 → 工具执行 → 响应输出。Plugin 不是处理链的一个阶段，而是**横切所有阶段的拦截层**——可以在每个阶段的关键节点注入逻辑，但不改变阶段本身的调用关系。

这种设计借鉴了 Web 框架中间件模式（Express/Koa），但有一个关键区别：Plugin 不是串行管道（request → middleware1 → middleware2 → response），而是**事件驱动的 hook 集合**。每个 hook 独立触发，hook 之间不通过管道传递控制权，而是通过修改共享的 `output` 对象来协作。

来源：[`packages/opencode/src/plugin/index.ts`](https://github.com/anomalyco/opencode/blob/dev/packages/opencode/src/plugin/index.ts)（Plugin 加载与触发逻辑），[`packages/plugin/src/index.ts`](https://github.com/anomalyco/opencode/blob/dev/packages/plugin/src/index.ts)（Hook 类型定义）。

### 1.2 Plugin 的定义与注册

一个 Plugin 是一个异步函数，接收运行时环境信息，返回一个 Hooks 对象：

```typescript
// packages/plugin/src/index.ts
export type Plugin = (input: PluginInput, options?: PluginOptions) => Promise<Hooks>
```

`PluginInput` 包含项目根路径、配置信息等运行时环境。`Hooks` 是一个接口，定义了所有可用的 hook 名称及其签名。每个 hook 的签名统一为 `(input, output) => Promise<void>`——`input` 是只读的上下文信息，`output` 是可修改的结果对象。

注册方式有两种：内置 Plugin（在代码中直接 import）和外部 Plugin（从 npm 或本地文件加载）。加载顺序由 `config.plugin` 数组决定，顺序加载保证 hook 执行的确定性。

### 1.3 完整的 Hook 生命周期

以下是一次完整对话轮次中 hook 的触发顺序，以及每个 hook 能观测和修改的内容。这是理解后续所有算法实现的基础。

```
用户发送消息
  │
  ├─① chat.message(input: {sessionID, agent, model}, output: {message, parts})
  │    观测：原始用户输入内容
  │    可修改：消息内容和附件
  │
  ├─② experimental.chat.system.transform(input: {sessionID, model}, output: {system: string[]})
  │    观测：当前系统提示的完整内容
  │    可修改：系统提示数组（追加、替换、重排）
  │
  ├─③ experimental.chat.messages.transform(input: {}, output: {messages: [{info, parts}]})
  │    观测：即将发送给 LLM 的完整消息历史
  │    可修改：消息的排列顺序和内容
  │
  ├─④ chat.params(input: {sessionID, agent, model, provider}, output: {temperature, topP, topK, options})
  │    观测：LLM 调用参数
  │    可修改：温度、采样参数
  │
  ├─⑤ chat.headers(input: {同上}, output: {headers: Record<string, string>})
  │    观测/可修改：HTTP 请求头（用于认证、追踪标记等）
  │
  ├─ [LLM 调用执行]
  │
  ├─⑥ tool.definition(input: {toolID}, output: {description, parameters})
  │    （在 LLM 选择工具前触发，修改工具描述和参数 schema）
  │
  ├─⑦ tool.execute.before(input: {tool, sessionID, callID}, output: {args})
  │    观测：工具名称和参数
  │    可修改：工具参数（可拦截或重写）
  │
  ├─⑧ [工具执行]
  │
  ├─⑨ tool.execute.after(input: {tool, sessionID, callID, args}, output: {title, output, metadata})
  │    观测：工具执行结果
  │    可修改：输出内容（截断、格式化、注入错误上下文）
  │
  └─ [下一轮或会话结束]

跨轮次 hook：
  ├─ experimental.session.compacting(input: {sessionID}, output: {context: string[], prompt?: string})
  │    在自动压缩触发时执行，可注入额外上下文或替换压缩 prompt
  │
  ├─ permission.ask(input: Permission, output: {status: "ask"|"deny"|"allow"})
  │    权限请求拦截
  │
  └─ event(input: {event: Event})
       Bus 事件订阅（session.created, session.updated, session.diff, session.error）
```

### 1.4 Hook 触发机制的关键特性

**顺序执行，共享 output。** 当一个 hook 被触发时，所有注册了该 hook 的 Plugin 按加载顺序依次执行。每个 Plugin 接收到的 `output` 是前一个 Plugin 修改后的版本。这意味着 Plugin 的加载顺序决定了算法的优先级。

```typescript
// https://github.com/anomalyco/opencode/blob/dev/packages/opencode/src/plugin/index.ts#L285-L298
for (const hook of state.hooks) {
  const fn = hook[name] as any
  if (!fn) continue
  yield* Effect.promise(async () => fn(input, output))
}
return output
```

**无返回值约定。** hook 函数返回 `void`，所有效果通过修改 `output` 参数实现。这设计意味着 hook 不能"阻止"后续 hook 的执行——如果算法 A 需要阻止工具执行，它只能通过修改 `output.args` 为无操作来间接实现，不能直接中断链条。

**跨 hook 状态共享。** Hook 之间没有内置的状态传递机制。但因为所有 hook 定义在同一个 Plugin 闭包内，闭包变量天然可以跨 hook 共享。这是实现多算法协作的基础——例如 `tool.execute.after` 中记录的错误率，可以在 `tool.execute.before` 中用来判断是否进入螺旋检测。

### 1.5 与 Codex Hook 机制的对比

Codex（OpenAI 的 Rust CLI Agent）提供了 5 个 hook 事件：`sessionStart`、`userPromptSubmit`、`preToolUse`、`postToolUse`、`stop`。Handler 类型分三种：`command`（执行 shell 命令）、`prompt`（注入上下文）、`agent`（修改 agent 状态）。

关键差异在于粒度：OpenCode 有 12+ 个 hook 点，覆盖系统提示、消息历史、LLM 参数、工具定义等；Codex 只有 5 个，集中在工具执行前后和会话生命周期。OpenCode 的 `experimental.chat.messages.transform` 和 `experimental.chat.system.transform` 在 Codex 中没有直接对应物——Codex 不允许 Plugin 修改消息历史的排列顺序。

对我们的算法实现而言，这意味着：算法 4（缓存友好布局）和算法 6（结构化装配）在 OpenCode 上可以通过 `experimental.chat.system.transform` 和 `experimental.chat.messages.transform` 直接实现，但在 Codex 上需要找其他路径或等待 hook 扩展。

下表总结了两套 hook 机制对 6 个算法的支持情况：

| 算法 | 所需能力 | OpenCode Hook | Codex Hook | 差异影响 |
|------|---------|--------------|------------|---------|
| 1 渐进式披露 | 修改系统提示 | `experimental.chat.system.transform` | `userPromptSubmit` (prompt handler) | Codex 只能追加，不能重排 |
| 2 上下文压缩 | 自定义压缩策略 | `experimental.session.compacting` | 无直接对应，需自建 | Codex 依赖内置压缩，Plugin 不可介入 |
| 3 螺旋检测 | 工具执行前后拦截 | `tool.execute.before` + `after` | `preToolUse` + `postToolUse` | 基本等价 |
| 4 缓存友好布局 | 控制系统提示排序 | `experimental.chat.system.transform` | 无 | Codex 无法实现 |
| 5 工具输出回压 | 修改工具输出 | `tool.execute.after` | `postToolUse` | 基本等价 |
| 6 结构化装配 | 重排消息历史 | `experimental.chat.messages.transform` | 无 | Codex 无法实现 |

归纳：OpenCode 的 hook 机制是目前唯一能支持全部 6 个算法的工程基座。Codex 能支持 3 个（算法 1/3/5），另外 3 个受限于 hook 粒度不足。这一结论决定了我们的算法验证工作以 OpenCode 为主实施平台。

---

## 二、基于 Plugin 的观测能力

### 2.1 为什么需要观测

算法效果评价依赖可量化的运行时数据。032_ATA_C1_Context.md 的度量指标体系定义了四类需要采集的数据：

- **效率指标**：总 token 消耗、缓存命中率、压缩触发次数——这些只能从运行时采集。
- **质量指标**：probe 回答的准确性——依赖 probe 评分，但评分需要关联到"probe 触发时的上下文状态"才能解释因果。
- **行为指标**：工具调用频次、相同文件编辑次数、错误率——用于螺旋检测等算法的验证。
- **因果指标**：压缩前后的信息差异、位置重排前后的注意力变化——需要记录算法介入前和介入后的状态快照。

推导：这四类数据分别对应 Plugin hook 链中的不同采集点。效率指标在 `chat.params` 和 LLM 返回后采集；行为指标在 `tool.execute.before/after` 采集；质量指标在 probe 执行时采集；因果指标需要在算法 hook 的执行前后各做一次快照。

### 2.2 观测 Plugin 架构

观测能力实现为一个独立的 Plugin，与算法 Plugin 分离。分离的理由：观测 Plugin 在所有配置（Baseline、Full、消融组）中都要运行，而算法 Plugin 在 Baseline 中关闭。混在一起会导致 Baseline 也没有观测数据。

```typescript
// observe-plugin/index.ts — 结构骨架

interface ObservationRecord {
  timestamp: number
  sessionId: string
  turnIndex: number
  hookName: string
  event: string
  data: Record<string, unknown>
}

const observations: ObservationRecord[] = []
let turnIndex = 0

function record(sessionId: string, hookName: string, event: string, data: Record<string, unknown>) {
  observations.push({
    timestamp: Date.now(),
    sessionId,
    turnIndex,
    hookName,
    event,
    data,
  })
}

export default async (input: PluginInput): Promise<Hooks> => ({
  // 用户消息观测：记录每轮输入的 token 估算
  "chat.message": async (inp, out) => {
    turnIndex++
    record(inp.sessionID, "chat.message", "user_input", {
      contentLength: JSON.stringify(out.parts).length,
      estimatedTokens: Math.ceil(JSON.stringify(out.parts).length / 4),
    })
  },

  // 系统提示观测：记录 system prompt 的长度和组成
  "experimental.chat.system.transform": async (_inp, out) => {
    record("", "system.transform", "system_prompt_snapshot", {
      segmentCount: out.system.length,
      totalLength: out.system.reduce((sum, s) => sum + s.length, 0),
      segments: out.system.map((s, i) => ({ index: i, length: s.length, prefix: s.slice(0, 60) })),
    })
  },

  // 消息历史观测：记录发送给 LLM 的完整消息数和 token 分布
  "experimental.chat.messages.transform": async (_inp, out) => {
    const msgStats = out.messages.map((m, i) => ({
      index: i,
      role: m.info.role,
      partCount: m.parts.length,
      estimatedTokens: Math.ceil(JSON.stringify(m.parts).length / 4),
    }))
    record("", "messages.transform", "message_history_snapshot", {
      messageCount: out.messages.length,
      totalEstimatedTokens: msgStats.reduce((s, m) => s + m.estimatedTokens, 0),
      distribution: msgStats,
    })
  },

  // 工具调用观测：记录调用频次、参数特征
  "tool.execute.before": async (inp, out) => {
    record(inp.sessionID, "tool.execute.before", "tool_call", {
      tool: inp.tool,
      callId: inp.callID,
      argsLength: JSON.stringify(out.args).length,
    })
  },

  // 工具结果观测：记录输出大小、成功/失败状态
  "tool.execute.after": async (inp, out) => {
    const outputStr = typeof out.output === "string" ? out.output : JSON.stringify(out.output)
    const isError = outputStr.includes("Error") || outputStr.includes("error") || outputStr.includes("failed")
    record(inp.sessionID, "tool.execute.after", "tool_result", {
      tool: inp.tool,
      callId: inp.callID,
      outputLength: outputStr.length,
      estimatedTokens: Math.ceil(outputStr.length / 4),
      isError,
      title: out.title,
    })
  },

  // 压缩事件观测
  "experimental.session.compacting": async (inp, out) => {
    record(inp.sessionID, "session.compacting", "compaction_triggered", {
      contextSegments: out.context.length,
      hasCustomPrompt: !!out.prompt,
    })
  },

  // Bus 事件观测
  event: async ({ event }) => {
    record("", "bus.event", event.type, {
      eventType: event.type,
    })
  },
})
```

### 2.3 采集点与度量指标的映射

下表是 032_ATA_C1_Context_CODE.md 中所有度量指标到 hook 采集点的映射。这个映射关系不仅适用于 C1，也是后续 Category 设计观测方案时的参考模板。

| 度量指标 | 所属算法 | 采集 Hook | 采集方式 |
|---------|---------|-----------|---------|
| 总 token 消耗 | 全局 | `messages.transform` | 每轮统计消息历史的 token 总量 |
| 缓存命中率 | 算法 4 | `system.transform` | 比较连续两轮 system prompt 的前缀相同长度 |
| 压缩触发次数 | 算法 2 | `session.compacting` | 计数器 |
| 工具输出截断次数 | 算法 5 | `tool.execute.after` | 记录原始长度 vs 修改后长度 |
| 相同文件编辑次数 | 算法 3 | `tool.execute.before` | 按文件路径聚合编辑工具调用 |
| 错误率 | 算法 3 | `tool.execute.after` | 滑动窗口内的错误比例 |
| 上下文利用率 | 算法 2 | `messages.transform` | 总 token / 模型窗口大小 |
| 导航地图命中次数 | 算法 1 | `tool.execute.before` | 统计 `skill_search` 工具的调用次数 |
| 消息位置分布 | 算法 6 | `messages.transform` | 记录关键消息（决策、错误）在序列中的位置 |
| 螺旋风险值 | 算法 3 | `tool.execute.after` | 计算文件编辑 + 错误率 + 利用率的加权分 |

### 2.4 观测数据的输出格式

观测数据以 JSONL 格式输出到 `eval_logs/` 目录，每行一个 `ObservationRecord`。选择 JSONL 而非 JSON 的理由：JSONL 支持流式追加写入，不需要在会话结束时才序列化整个数组；且方便用 `grep`、`jq` 做行级过滤。

文件命名约定：`eval_logs/{case_id}_{config}_{run_index}.jsonl`，例如 `eval_logs/SHORT-01_full_1.jsonl`。

每次运行结束后，观测 Plugin 在 Bus 的 `session.deleted` 事件中将 `observations[]` 刷写到文件。

### 2.5 从 C1 到通用：观测框架的可扩展性

上述 hook → 度量映射是 C1 上下文管理的具体实例。对其他 Category，观测框架的结构不变，变化的只是"关心哪些 hook 的哪些字段"。

以 C2 记忆管理为例：核心度量可能是"记忆检索命中率"和"记忆写入频次"。这两个指标在 `tool.execute.before`（记录 memory_search 工具调用）和 `tool.execute.after`（记录 memory_write 工具结果）中采集，使用完全相同的观测 Plugin 骨架。

以 C3 约束管理为例：核心度量可能是"约束违反拦截次数"和"约束检查通过率"。在 `tool.execute.before`（拦截违规操作）和 `permission.ask`（权限请求统计）中采集。

归纳原则：**观测框架的不变量是 hook 采集点和 JSONL 输出格式；变量是每个 Category 关心的字段集合。** 新增 Category 时，只需在观测 Plugin 中添加新的字段提取逻辑，不需要修改框架本身。

---

## 三、基于 Plugin 的算法实现

### 3.1 实现原则

032_ATA_C1_Context.md 已经给出了 6 个算法的伪代码和 TypeScript 片段。本节不重复算法逻辑，而是回答"怎么把这些代码组织成可维护、可测试、可消融的 Plugin 架构"。

**原则 1：单一 Plugin，多算法共存。** 6 个算法共享状态（上下文利用率、错误率、文件编辑计数），如果分成 6 个独立 Plugin，状态同步会变得复杂。将它们放在同一个 Plugin 闭包中，通过闭包变量直接共享状态。

**原则 2：算法开关通过配置控制。** 每个算法有一个 `enabled` 布尔开关，消融实验只需修改配置文件，不需要改代码。

```typescript
interface AlgorithmConfig {
  progressiveDisclosure: { enabled: boolean }
  contextCompaction:     { enabled: boolean; gentleThreshold: number; standardThreshold: number; aggressiveThreshold: number }
  spiralDetection:       { enabled: boolean; fileEditLimit: number; errorRateLimit: number; utilizationLimit: number }
  cacheFriendlyLayout:   { enabled: boolean }
  toolBackpressure:      { enabled: boolean; successMaxTokens: number; errorEnrichment: boolean }
  structuredAssembly:    { enabled: boolean }
}
```

**原则 3：观测 Plugin 在算法 Plugin 之前加载。** 加载顺序：观测 Plugin → 算法 Plugin。这样观测 Plugin 的 `tool.execute.after` 记录的是原始工具输出，算法 Plugin 的 `tool.execute.after` 修改后的输出也能通过比较两者差异来量化回压效果。

### 3.2 算法与 Hook 的映射总表

```
Plugin 加载时（初始化）
  └─ 算法 1：构建 skill 索引（扫描 .opencode/skills/）

chat.message
  └─ 全局状态：turnCount++

experimental.chat.system.transform
  ├─ 算法 1：只注入导航地图（skill 索引摘要），不注入完整定义
  └─ 算法 4：按频率将 system 段落分为 static / semi-static / dynamic，
             static 部分强制置顶保持前缀缓存

experimental.chat.messages.transform
  ├─ 算法 2：计算上下文利用率，决定是否标记需要压缩
  └─ 算法 6：按优先级重排消息——高优（任务指令、当前错误）置首尾，
             低优（背景参考）置中间

tool.execute.before
  ├─ 算法 1：如果调用的是 skill_search，标记该 skill 为"已加载"
  └─ 算法 3：检查螺旋风险值，如果超阈值则拦截危险操作（文件写入、删除）

tool.execute.after
  ├─ 算法 3：更新文件编辑计数、错误率滑动窗口、螺旋风险值
  └─ 算法 5：成功输出截断到 successMaxTokens；失败输出注入结构化错误上下文

experimental.session.compacting
  └─ 算法 2：注入保留规则（结构信息 > 推理步骤），替换压缩 prompt
```

### 3.3 状态结构与算法间耦合

6 个算法在运行时共享以下状态。这个状态结构既是算法实现的核心，也是观测 Plugin 需要定期快照的对象。

```typescript
interface ContextState {
  // 全局计数
  turnCount: number
  totalTokens: number
  utilization: number           // totalTokens / modelWindow
  compactionCount: number

  // 算法 1：渐进式披露
  skillIndex: Array<{ name: string; loaded: boolean }>

  // 算法 3：螺旋检测
  fileEditCounts: Record<string, number>   // 文件路径 → 编辑次数
  errorCountWindow: boolean[]              // 最近 N 次工具调用的成功/失败
  spiralRisk: number                       // 0-1，加权风险值

  // 算法 4：缓存布局
  staticPrefixHash: string                 // 上一轮 static 段的 hash，用于检测缓存失效

  // 算法 5：回压
  truncationCount: number                  // 本会话累计截断次数
  enrichmentCount: number                  // 本会话累计错误富化次数
}
```

算法间的耦合通过共享状态实现，不存在算法之间的直接函数调用。耦合关系为：

- 算法 2（压缩）的触发条件 `utilization` 由 `messages.transform` 中计算，算法 3（螺旋）和算法 5（回压）也读这个值来调整行为。
- 算法 3（螺旋）的 `spiralRisk` 由 `tool.execute.after` 更新，算法 2 在判断压缩策略激进程度时会参考螺旋风险——高螺旋风险时倾向更激进的压缩。
- 算法 1（渐进式）的 `skillIndex.loaded` 状态影响算法 4（缓存布局）——已加载的 skill 定义是 semi-static 内容，需要调整缓存边界。

### 3.4 消融实验的实现

消融实验的目标是量化每个算法的独立贡献。方法是"关闭一个，保留其余五个"，加上两个对照组（全关 Baseline、全开 Full）。

配置矩阵：

| 配置名 | 算法 1 | 算法 2 | 算法 3 | 算法 4 | 算法 5 | 算法 6 |
|--------|--------|--------|--------|--------|--------|--------|
| Baseline | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Full | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Ablate-1 | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Ablate-2 | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ |
| Ablate-3 | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ |
| Ablate-4 | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ |
| Ablate-5 | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ |
| Ablate-6 | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |

总共 8 种配置 × 30 个 case × 3 次重复 = 720 次运行。每次运行的观测日志独立保存。

从 C1 到通用的推广：这个消融矩阵的结构对所有 Category 通用。C2 记忆管理如果有 4 个算法，消融矩阵就是 4+2=6 种配置。框架不变，算法数量变。

---

## 四、测试用例的设计方法

### 4.1 从 032_CODE 到可执行：测试用例的完整生命周期

032_ATA_C1_Context_CODE.md 定义了 30 个 case 的**规格**（场景、种子数据、指令序列、probe、成功标准）。从规格到可执行的评测，还需要三层工程：

```
规格文档 (032_CODE.md)
    ↓ [种子数据生成]
种子数据目录 (benchmark/seeds/{case-id}/)
    ↓ [Testcase YAML 生成]
执行脚本 (testcase/{case-id}.yaml)
    ↓ [评测引擎驱动]
观测日志 + Probe 评分 + 结果聚合
```

这个流程已经通过 agent-bench-gen Skill 自动化。本节讨论的不是"怎么跑"（Skill 已解决），而是"怎么设计好的测试用例"——这是后续 Category 扩展时需要反复使用的方法论。

### 4.2 测试用例的四个设计维度

**维度 1：轮次深度。** SHORT（5-10 轮）测试算法在短交互中的开销是否合理——算法不应该在短任务中引入明显的 token 浪费。MID（20-50 轮）测试算法的核心价值——压缩、螺旋检测、回压开始产生可度量的效果。LONG（100+ 轮）测试极端场景——多次压缩后信息是否严重丢失、螺旋检测能否及时介入。

设计 30 个 case 的轮次分布为 10-10-10 的逻辑：三档各占三分之一，确保每档有足够的统计样本。每档 10 个 case 的最小样本量，在 3 次重复后产生 30 个数据点，足以计算均值和标准差。

**维度 2：算法覆盖。** 每个 case 标注了"主要验证哪些算法"。30 个 case 的算法覆盖矩阵如下（从 032_CODE.md 归纳）：

| 算法 | SHORT 覆盖 | MID 覆盖 | LONG 覆盖 | 总计 |
|------|-----------|----------|----------|------|
| 1 渐进式披露 | 5 | 3 | 4 | 12 |
| 2 上下文压缩 | 0 | 7 | 9 | 16 |
| 3 螺旋检测 | 0 | 5 | 7 | 12 |
| 4 缓存友好布局 | 6 | 4 | 3 | 13 |
| 5 工具输出回压 | 7 | 5 | 5 | 17 |
| 6 结构化装配 | 2 | 6 | 8 | 16 |

每个算法至少在 12 个 case 中被测试，确保消融实验有足够的对比数据。

**维度 3：Probe 类型分布。** 四类 probe（recall、artifact、plan、decision）的分布应该匹配轮次深度：SHORT 侧重 recall 和 artifact（信息是否被正确处理）；MID 增加 decision（推理链是否保留）；LONG 全覆盖，特别强调 plan（长任务中的规划能力）。

设计依据：recall 和 artifact 测试的是"信息是否还在上下文中"，这在短对话中就有意义。decision 和 plan 测试的是"跨多轮的推理一致性"，这在中长对话中才有足够的推理链可供验证。

**维度 4：种子数据管线。** 032_CODE.md 使用了 4 类种子数据生成管线（A=结构化数据、B=文档缺陷注入、C=矛盾对、D=因果图）。管线选择取决于场景需求：

| 管线 | 适用场景 | Ground Truth 机制 | 适用 Category |
|------|---------|------------------|-------------|
| A（SQLite+Faker） | 需要表格/记录数据的场景 | SQL 查询验证 | C1, C2, C5 |
| B（规则注入） | 需要"正确答案"嵌入文档的场景 | 注入规则匹配 | C1, C3, C4 |
| C（矛盾对） | 需要检测不一致的场景 | 矛盾对列表匹配 | C1, C3 |
| D（因果图） | 需要多步推理的场景 | 因果路径匹配 | C1, C5 |

对其他 Category 的推广：C2 记忆管理需要新增管线 E（时间序列记忆注入），C3 约束管理需要新增管线 F（权限规则矩阵）。管线本身是可扩展的，框架只定义了接口（输入→种子数据 + ground truth），不绑定具体实现。

### 4.3 Testcase YAML Schema

每个 testcase 的 YAML 文件包含以下字段（完整 schema 见 `skills/agent-bench-gen/references/yaml_schema.md`）：

```yaml
id: SHORT-01
title: 会议纪要整理
scenario: 将原始会议录音转写文本整理为结构化会议纪要
algorithms: [5, 4]                    # 主要验证的算法编号
turns_target: 5                       # 目标轮次数
seed_data:
  directory: benchmark/seeds/short-01
  files: [transcript.txt, template.md]
seed_files: [transcript.txt, template.md]
ground_truth_facts:                   # 从种子数据中可程序化验证的事实
  - key: budget_decision
    value: "市场部增加 15%，研发部维持不变"

system_prompt: |
  你是一个企业办公助手。用户会提供会议转写文本和模板，
  请按要求整理为结构化会议纪要。

turns:
  - role: user
    content: "读取 transcript.txt，按 template.md 的格式整理成会议纪要"
    expected_behavior: "加载两个文件，开始结构化整理"
  - role: user
    content: "补充每个待办事项的负责人和截止日期"
    expected_behavior: "从转写文本中提取行动项，填充负责人"
  # ...

probes:
  - type: recall
    question: "Q2 预算分配的具体决议是什么？"
    expected_answer: "市场部增加 15%，研发部维持不变"
  - type: artifact
    question: "最终生成了什么文件？模板中的哪些字段被填充了？"
    expected_answer: "meeting_notes.md，包含参会人、议题、决议、待办四个字段"

success_criteria:
  - "meeting_notes.md 存在且包含 3 个议题的决议"
  - "每个待办事项有负责人和截止日期"

metrics:
  - total_tokens
  - tool_output_truncation_count
  - cache_hit_rate
```

### 4.4 Probe 设计的三个原则

**原则 1：每个 probe 必须有确定性预期答案。** 模糊的 probe（"整体效果怎么样？"）无法自动评分。每个 probe 的 `expected_answer` 必须能与模型回答做字符串或语义匹配。

**原则 2：probe 应该跨越压缩边界。** 在 MID 和 LONG case 中，probe 提问的信息应该来自可能已被压缩的早期轮次。如果所有 probe 都问最近几轮的信息，就无法测试压缩是否保留了关键事实。

**原则 3：每种 probe 类型至少对应一个可程序化验证的 ground truth。** recall probe 的预期答案可以从种子数据的 `_ground_truth.yaml` 中提取；artifact probe 可以通过检查文件系统验证；plan probe 可以通过检查 WBS 依赖关系验证；decision probe 需要因果图匹配。

---

## 五、算法效果评价

### 5.1 评价流程

完整的评价流程分 5 步：

```
Step 1: 生成种子数据
  输入：032_CODE.md 中的种子数据规格
  工具：4 条管线（A/B/C/D）
  输出：benchmark/seeds/{case-id}/ 目录

Step 2: 驱动执行
  输入：testcase/{case-id}.yaml + 种子数据 + 算法配置（8 种）
  工具：评测引擎（调用 OpenCode API，按 turns 序列发送消息）
  输出：eval_logs/{case_id}_{config}_{run}.jsonl

Step 3: Probe 评分
  输入：每次运行结束后的上下文状态 + probe 问题
  工具：LLM 盲测（独立模型评分，避免自评偏差）
  输出：eval_scores/{case_id}_{config}_{run}.json
  评分维度（6 维度 × 0-5 分）：
    准确性、上下文意识、工件追踪、完整性、连贯性、指令遵循

Step 4: 自动化判定
  输入：成功标准（文件存在性、内容匹配、格式校验）
  工具：脚本检查（validate_suite.py）
  输出：pass/fail 判定 + 明细

Step 5: 结果聚合
  输入：所有 JSONL 日志 + 所有评分 JSON
  工具：统计脚本
  输出：benchmark.json（按配置聚合的通过率、token 消耗、效率指标）
```

### 5.2 评价指标体系

指标分三层：

**第一层：任务完成率（Task Completion Rate, TCR）。** 每个 case 的成功标准是否全部满足。这是最终指标——算法改进如果降低了 TCR，无论效率多高都不可接受。

**第二层：效率指标。** 在 TCR 不下降的前提下，比较不同配置的资源消耗。

| 指标 | 计算方式 | 预期方向 |
|------|---------|---------|
| Token 消耗比 | Full的总token / Baseline的总token | <1.0（更省） |
| 缓存命中率 | 缓存读取token / 总输入token | 越高越好 |
| 压缩效率 | 压缩前token - 压缩后token / 压缩前token | 越高越好 |
| 轮次效率 | 实际轮次 / 目标轮次 | 接近1.0 |

**第三层：行为健康度。** 检验算法是否引入了副作用。

| 指标 | 正常范围 | 异常信号 |
|------|---------|---------|
| 螺旋触发率 | <5% 的 MID/LONG case | 频繁误报 |
| 回压截断率 | 30-60% 的工具输出被截断 | <10%（回压没生效）或>90%（过度截断） |
| Probe 分数衰减 | LONG vs SHORT 差异<15% | 差异>30%（信息严重丢失） |
| 消融独立贡献 | 每个算法关闭后 TCR 下降<10% | 某算法关闭后 TCR 不变（算法可能是冗余的） |

### 5.3 统计方法

**均值与置信区间。** 每个 case 跑 3 次，取均值和标准差。3 次重复是成本与精度的折中——足以检测大效应（>10% 差异），但可能遗漏小效应。如果初步结果显示某对比接近显著性边界，增加到 5 次重复。

**消融显著性检验。** 每个消融配置 vs Full 配置的比较，使用配对 t 检验（paired t-test，30 个 case 作为配对样本）。显著性阈值 p<0.05。如果某个算法关闭后 TCR 没有显著下降，说明该算法的独立贡献不显著——可能是其效果被其他算法覆盖了。

**效果量（Cohen's d）。** 除了 p 值，还需要报告效果量。d<0.2 是小效应，0.2-0.8 是中等效应，>0.8 是大效应。这避免了"统计显著但实际差异很小"的陷阱。

### 5.4 结果展示

评价结果通过两种形式呈现：

**benchmark.json**——机器可读的完整结果，包含所有配置的所有指标。格式已在 agent-bench-gen Skill 的 eval 流程中定义。

**eval-viewer.html**——人工审阅的可视化界面，包含：配置间的对比表格、每个 case 的详细 probe 评分、消融实验的柱状图。

### 5.5 从 C1 到全 Category 的推广路径

以上所有设计——观测 Plugin、算法 Plugin 架构、测试用例 4 维度、评价 3 层指标——都是为通用性设计的。推广到新 Category 时，需要做的工作和不需要做的工作如下：

**不变（直接复用）：**
- 观测 Plugin 骨架（hook 采集点、JSONL 输出格式）
- 消融实验矩阵模板（Baseline + Full + Ablate-N）
- 评价流程 5 步骤
- 统计方法（3 次重复、配对 t 检验、Cohen's d）
- Testcase YAML Schema
- Probe 评分维度（6 维度 × 0-5 分）

**变化（需要新设计）：**
- 算法 Plugin 的 hook 实现（不同 Category 使用不同的 hook 组合）
- 种子数据管线（可能需要新管线 E/F/...）
- 度量指标集合（不同 Category 关心不同的运行时数据）
- Probe 的 expected_answer 来源（不同 Category 的 ground truth 结构不同）
- 算法配置参数（阈值、窗口大小等）

**推广清单——新 Category 接入步骤：**
1. 定义该 Category 的算法集合（类似 032 文档中的 6 个算法）
2. 映射算法到 OpenCode hook（使用本文 §1.3 的 hook 生命周期作为参考）
3. 定义度量指标并映射到 hook 采集点（使用 §2.3 的映射表作为模板）
4. 设计 testcase（使用 §4.2 的 4 维度方法）
5. 生成种子数据（使用 agent-bench-gen Skill 或新管线）
6. 配置消融矩阵（使用 §3.4 的模板）
7. 执行评价流程（使用 §5.1 的 5 步骤）
8. 产出 benchmark.json 和 eval-viewer.html

---

## 附录 A：Codex Hook 机制的观测适配

Codex 的 5 个 hook 无法支持全部 6 个算法的实现，但对于观测目的，其覆盖度是足够的。Codex 还内置了 OpenTelemetry 集成（[`codex-rs/otel/`](https://github.com/openai/codex/tree/main/codex-rs/otel)），提供分布式追踪、指标收集和日志导出能力，这在 OpenCode 中需要通过 Plugin 自建。

对于以 Codex 为基座的实施方案，推荐的观测路径是：用 OpenTelemetry 采集全局指标（token、延迟、错误率），用 `postToolUse` hook 采集工具级指标（输出大小、成功/失败），用外部日志分析补充缺失的消息级指标（消息排列、系统提示变化）。

## 附录 B：与项目其他文档的关系

| 本文章节 | 上游输入 | 下游输出 |
|---------|---------|---------|
| §1 Plugin 机制 | OpenCode 源码 [`packages/plugin/`](https://github.com/anomalyco/opencode/tree/dev/packages/plugin) | →为 §3 算法实现提供工程基座 |
| §2 观测能力 | 032_ATA_C1_Context.md §度量指标 | →为 §5 评价提供数据采集 |
| §3 算法实现 | 032_ATA_C1_Context.md §6个算法 | →为 §4 测试用例提供被测对象 |
| §4 测试用例 | 032_ATA_C1_Context_CODE.md 30个case | →产出 testcase/*.yaml |
| §5 评价方法 | benchmark/seeds/ + testcase/*.yaml | →产出 benchmark.json |
| agent-bench-gen Skill | 本文全流程 | →自动化 §4-§5 |

## 附录 C：术语表

| 术语 | 定义 | 首次出现 |
|------|------|---------|
| Hook | Plugin 中注册的回调函数，在特定生命周期事件触发时执行 | §1.2 |
| 消融实验 | 关闭单个算法、保留其余的对比实验设计 | §3.4 |
| Probe | 任务结束后用于评估信息保留质量的标准化问题 | §4.3 |
| Ground Truth | 种子数据中预埋的确定性答案，用于 probe 自动评分 | §4.4 |
| 管线 | 种子数据的程序化生成方法（A/B/C/D） | §4.2 |
| 回压 | 对工具输出的不对称处理——截断成功输出、富化失败输出 | §3.2 |
| 螺旋检测 | 基于多信号耦合判断 Agent 是否陷入重复失败模式 | §3.3 |
| TCR | Task Completion Rate，任务完成率 | §5.2 |

---

> 本文不包含算法的具体代码实现（见 032_ATA_C1_Context.md）和具体测试 case 定义（见 032_ATA_C1_Context_CODE.md）。本文的职责是回答"这些算法和测试 case 如何在工程层面运转起来"。
