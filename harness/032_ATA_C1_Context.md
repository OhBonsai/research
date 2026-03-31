# 上下文管理：AI Agent 最容易被忽视的性能瓶颈

---

## 一个反直觉的数据

200K token 窗口的模型，真正可用的高质量空间可能只有 80K。

这不是猜测。arXiv:2601.11564 的多模型实测显示，不同模型的性能崩塌阈值在 20%-50% 之间——Gemini 2.5 Flash 低至 20%，Claude 系列在 40-50%。超过这个阈值，塞进去的信息不仅没用，反而有害。

我在做企业办公 AI Agent 时撞上了这个问题。最初以为"窗口够大就行"，后来发现 Agent 在长对话中越来越蠢，根因不是模型不好，是上下文管理出了问题。这篇文章记录我对这个问题的完整梳理——从理论到算法到工程实现。

---

## 核心假设与结论

先把底牌亮出来。以下是本文依赖的核心假设，以及从中推导出的结论。

**假设 1：上下文窗口的有效容量远小于名义容量。** 所有 Transformer 模型都存在性能崩塌阈值（20-50%），超过后推理质量显著下滑。这不是某个模型的 bug，而是架构层面的约束。

**假设 2：信息的位置会影响利用效率。** Stanford 团队发现的 Lost in the Middle 效应——模型对开头和结尾信息的利用效果好，中间部分准确率下降超过 20%。ICLR 2025 的后续研究（arXiv:2502.01951）证明这是 Transformer 因果掩码的固有几何属性，不是训练不足。

**假设 3：信息量增加会导致全局衰减。** Chroma Research 2025 的测试覆盖了 18 个模型，发现一个独立于位置的问题：Context Rot——随着输入 token 增加，模型回忆信息的能力全局下降。没有模型能免疫这个效应。

**假设 4：任务相关信息可以和噪声信息分离。** 这条在结构化任务（"修这个 bug"）中基本成立，但在探索性任务（"理解这个系统的架构"）中很弱——你不知道哪些信息后面会用到。

**结论：上下文管理的本质是在有限容量和衰减约束下，最大化任务相关信息密度。** 窗口扩大不能解决这个问题。PagedAttention 把 KV 缓存内存浪费从 60-80% 降到 4%，Flash Attention 3 在 H100 上跑出 1.3 PFLOPs，Ring Attention 理论上实现无限上下文——这些技术解决的是存储和计算效率，不是信息利用效率。

说白了，硬盘从 1TB 扩到 10TB，找文件反而更慢了，因为你没有索引。

---

## 策略全景：三个方向

上下文管理的核心策略分两条路：**压缩**（减少信息量）和**组织**（让模型只看到需要的信息）。

### 压缩算法

**硬截断。** 按位置或 token 数直接裁剪。压缩率可控，信息损失高，无差别丢弃。唯一的优点是简单可靠，适合作为兜底方案。所有产品都保留了这条退路。<sup>[18]</sup>

**摘要压缩。** 用 LLM 对对话历史生成摘要。ChatGPT 和 Claude Code 的 compaction 都用这个思路。典型压缩率 60-80%——Claude Code 能把 150K token 压到 30-50K。代价是细节丢失，而且摘要本身消耗推理算力。<sup>[15][18]</sup>

**Token 级剪枝（LLMLingua）。** 不按段落或句子粒度，直接移除低信息量的 token。压缩率 2-5 倍，信息损失低。关键思路是用一个小模型评估每个 token 的 perplexity，去掉"可预测的"token（冠词、连接词等），保留"意外的"token（关键实体、数值等）。<sup>[9]</sup>

**注意力导向压缩（Sentinel）。** 先探测模型在全量上下文上的注意力分布，找出哪些句子获得了最多注意力，只保留这些高注意力句子。在 LongBench 上做到 5 倍压缩、性能不损失。关键思路是"让模型自己告诉你什么重要"，而不是用启发式规则猜。<sup>[11]</sup>

**信息瓶颈压缩（QUITO-X）。** 把信息瓶颈理论（Tishby 1999<sup>[24]</sup>）直接用于上下文压缩——在保持任务相关信息的同时最大化压缩。效果是压缩率比当时的 SOTA 高 25%，推理加速 40%。关键思路是"任务导向的最优压缩"，而非无差别缩减。<sup>[10]</sup>

**故障驱动压缩（ACON）。** 这个我觉得特别值得关注。传统压缩是"提前决定什么重要"，ACON 是"从失败中学习什么重要"。先跑一轮完整推理，记录所有决策点；如果失败了，分析失败原因，找出哪些信息真正影响了决策；然后用优化后的策略重新压缩。效果是 26-54% 的峰值 token 减少，性能不损失。<sup>[12]</sup>

压缩算法的演进路径很清楚：硬截断 → 摘要 → Token 剪枝 → 注意力导向 → 信息论最优 → 故障驱动。方向是从"无差别丢弃"走向"任务导向的选择性保留"。

### 组织策略

组织策略的核心是"不压缩也能省"——让模型只看到它需要的信息。

**渐进式披露。** Claude Code 的核心策略。session 开始时只加载一个约 100 行的"导航地图"（AGENTS.md），列出有哪些文件、工具、规则。当模型需要某个工具的详情时，才动态加载完整定义。按需加载后可用上下文空间为 191,300 tokens，而传统全量加载只剩 122,800 tokens 可用，多出 35% 给实际任务使用。<sup>[15][18]</sup>

**语义检索注入。** Cursor 的方式。用向量数据库索引整个代码库，用户通过 @file、@codebase 显式指定上下文，系统用 embedding 最近邻搜索匹配相关代码块。这个方案完全放弃了压缩——不把信息塞进窗口再压，而是按需从索引中召回。隐含假设是检索的信息损失比压缩低。<sup>[15]</sup>

**图排序注入。** Aider 的方式。用 Tree-sitter 解析代码结构，提取类/函数/类型签名，然后用 PageRank 算法对代码引用图排序。被多方引用的文件（核心接口、工具类）排名更高。关键思路是借鉴了"被广泛引用 = 重要"这个网页排序直觉。<sup>[19]</sup>

组织策略比压缩策略更优先。能不压缩就不压缩，因为压缩总是有损的。

---

## 成本约束：Prompt 缓存

Prompt 缓存不改善模型对上下文的理解能力，但它深刻影响了上下文的工程设计——因为它改变了经济账。

问题很简单：系统提示、工具定义这些静态内容，每次请求都一模一样，但每次都要重新计算注意力。Prompt 缓存让这部分只算一次，后面复用 KV 缓存结果。

这跟上下文管理的关系是间接但重要的：**因为缓存把静态内容的边际成本降到了 10%，你才敢把系统提示写得丰富**。没有缓存，24,000 tokens 的系统提示每次按全价算，成本压力会逼你砍内容。有了缓存，你就敢放更完整的规则、更多的工具定义、更详细的行为约束。

但缓存有一个硬约束：**布局纪律**。静态内容必须放在最前面，且保持稳定。动态内容放后面。对前缀的任何微小改动——哪怕只是两个工具定义交换了顺序——都会导致缓存失效。<sup>[16]</sup> OpenAI Codex 把这个做到极端——整个架构设计为无状态（Zero Data Retention 合规），但靠激进的前缀缓存把容器启动从 48 秒降到 5 秒。<sup>[15]</sup>

**缓存依赖模型厂商的 API 支持，不是通用能力。** 目前三大厂商都已支持，但实现方式不同：

- **Anthropic**：需要开发者显式标记缓存断点（`cache_control` 字段）。写入有 25% 溢价（5 分钟 TTL）或 100% 溢价（1 小时 TTL），读取仅 10%。控制力强，但需要主动管理。<sup>[16]</sup>
- **OpenAI**：完全自动，不需要改代码。前缀超过 1,024 tokens 自动触发缓存，读取价格打一折。缓存保留最长 24 小时。对开发者最友好，但没有细粒度控制。
- **Google Gemini**：混合模式。Gemini 2.5 系列默认自动缓存（implicit），也支持手动创建缓存（explicit）。读取同样约 10%。最低触发门槛 1,024-2,048 tokens。

如果你用的是开源模型自部署，Prompt 缓存需要推理框架支持（vLLM 的 Automatic Prefix Caching 已实现<sup>[13]</sup>）。但定价优惠就不存在了——成本取决于你自己的 GPU 利用率。

对我们做企业办公 Agent 来说，这意味着：上下文的布局设计不只是"什么信息放哪"的质量问题，还是一个直接影响 API 账单的经济问题。系统提示写得好但布局不利于缓存，每个月多烧的钱可能比优化上下文质量带来的收益还大。

---

## 六个产品怎么做的

理论和算法讲完了，看看真实产品的选择。

**Claude Code** 直到上下文用了 95% 才触发压缩。<sup>[15][18]</sup> 这个数字很激进——说明 Anthropic 相信 Claude 的 200K 窗口在高利用率下仍能保持质量。系统提示约 24,000 tokens，110+ 个组件，用 XML 标签结构化。<sup>[18]</sup> 支持 `/compact` 手动压缩和自动 compaction。压缩后，CLAUDE.md 中的规则保留，对话细节被摘要替代。<sup>[15]</sup>

**LangChain Deep Agent** 在剩余 10-20% 可用空间时就开始压缩，比 Claude Code 保守得多。<sup>[17]</sup> 他们采用中间件架构——LocalContextMiddleware 做本地状态管理，SummarizationMiddleware 做摘要压缩，LoopDetectionMiddleware 追踪文件编辑次数。不换模型只改 Harness，Terminal Bench 成绩从 52.8% 涨到 66.5%。<sup>[17]</sup>

**Cursor** 完全放弃压缩，选了检索路线。<sup>[15]</sup> 向量数据库索引整个代码库，用户通过 @-mentions 手动指定上下文。这个方案的隐含判断是：在代码场景下，检索的信息损失比压缩低。

**Aider** 用 PageRank 对代码实体排序，构建精简的仓库地图。<sup>[19]</sup> token 预算通过 `--map-tokens` 控制，默认 1K，根据对话状态动态调整。

**MemGPT/Letta** 走了一条完全不同的路。<sup>[21]</sup> 把上下文管理类比为操作系统的内存管理——主上下文是 RAM，外部存储是磁盘。LLM 通过自生成的函数调用（save/load/delete）主动管理数据在两层之间的移动。这是唯一一个让模型自己决定"什么该留、什么该丢"的方案。

**Goose**（Block/Square）用两层阈值——80% 时自动摘要，95% 时完整 compaction。<sup>[20]</sup> 两级策略避免了单点触发的风险。

这六个产品独立开发，但有四条没人写进文档、所有人都遵守的规则：

压缩尽量推迟。即使最积极的 LangChain，触发点也在 80% 以上。结构信息比内容信息更值得保留——CLAUDE.md 在压缩后保留，Aider 保留的是代码结构而非内容。没有产品尝试修改注意力机制，都在模型外部解决问题。从单一策略走向多层级自适应——没有银弹。

---

## OpenCode 的实现

OpenCode 是一个开源的 TypeScript CLI Agent 框架，我们的企业办公 Agent 基于它封装。以下分析基于源码阅读（`packages/opencode/src/session/` 目录），这是我们实际要改的代码。<sup>[25]</sup>

### 溢出检测

`overflow.ts` 只有 22 行，逻辑很直接。`isOverflow()` 每轮计算累计 token（input + output + cache read + cache write），跟模型的 context limit 比较。可用空间 = 模型输入上限 - 安全缓冲。安全缓冲默认 `COMPACTION_BUFFER = 20_000` tokens，可通过配置 `compaction.reserved` 覆盖。模型窗口大小从 models.dev 外部数据库加载，不是硬编码。

### 双策略压缩

`compaction.ts` 约 420 行，是上下文管理的核心。分两步走：

**先剪枝（prune）。** 从消息历史末尾倒着扫描，找到已完成的工具调用输出，标记旧的为"已压缩"。三个控制参数：`PRUNE_MINIMUM = 20_000`（累计可回收量低于 2 万 token 不执行，避免做无用功）、`PRUNE_PROTECT = 40_000`（保护最近 4 万 token 内的工具调用不被动）、`PRUNE_PROTECTED_TOOLS = ["skill"]`（skill 类工具永远不删）。还有一个隐含条件：至少需要 2 轮用户对话才会启动剪枝。剪枝不删消息本身，只是把旧工具的输出内容标记为已压缩（`time.compacted = Date.now()`），后续序列化时跳过。

**再摘要（compaction）。** 剪枝释放的空间不够时，启动一个专门的 compaction agent 生成结构化摘要。摘要模板写死在代码里，包含五个字段：Goal（对话目标）、Instructions（用户指令）、Discoveries（发现）、Accomplished（完成的工作）、Relevant files（涉及的文件）。摘要完成后，如果是自动触发（`auto: true`），还会尝试重放上一条用户消息（去掉媒体附件），让对话能继续。如果连摘要本身也溢出了，返回 `"stop"` 停止会话。

值得注意的是，compaction agent 可以用跟主对话不同的模型——通过 `agent.model` 配置。这意味着可以用便宜的模型做摘要。

插件可以通过 `experimental.session.compacting` hook 注入自定义上下文或替换摘要 prompt。这是我们封装时的主要扩展入口。

### 模型特定提示

`session/system.ts` 根据 `model.api.id` 做字符串匹配，选择不同的系统提示文件。匹配逻辑是：包含 `"claude"` 用 `anthropic.txt`，包含 `"gemini-"` 用 `gemini.txt`，包含 `"gpt-4"` 或 `"o1"` 或 `"o3"` 用 `beast.txt`，其他 GPT 用 `gpt.txt`，兜底用 `default.txt`。一共 7 个提示文件。

不同提示之间的差异主要在语气和工作方式，不在上下文管理参数上。比如 `anthropic.txt` 强调 TodoWrite 工具的使用和 Task 子 agent 做搜索（"prefer to use the Task tool in order to reduce context usage"），`default.txt` 则更简洁直接。但没有模型特定的崩塌阈值、位置敏感度这类参数。

### Prompt 缓存

`llm.ts` 中的缓存处理很轻量。系统提示被拆成两部分：header（第一段，通常是 prompt 文件内容）和 rest（拼接的额外内容）。如果 header 在 plugin 处理后没变，就保持两部分结构——这样 provider 侧的前缀缓存可以命中 header 部分。没有显式的 `cache_control` 标记注入，依赖 provider SDK 的自动缓存（OpenAI 和 Gemini 都支持自动前缀缓存）。

token 计费上分开追踪了 cache read/write，但这主要是成本统计用途，不影响上下文管理决策。

### 循环检测

`processor.ts` 里的 "doom loop" 检测，阈值 `DOOM_LOOP_THRESHOLD = 3`。逻辑是：看当前 assistant 消息的最近 3 个 tool part，如果全部是同一个工具、状态不是 pending、且都完成了——触发 `permission.ask({ permission: "doom_loop" })`，让用户确认是否继续。

这个检测只抓"完全相同的工具被连续调用"这种最明显的循环。"同一个文件被不同方式反复编辑"这种更隐蔽的模式，抓不到。

### Skill 渐进式披露

Skill 系统实现了两级加载。系统提示（`system.ts:61-73`）通过 `Skill.fmt(list, { verbose: true })` 只注入每个 skill 的名称、描述和文件位置，不注入完整内容。当模型判断某个任务匹配某个 skill 时，调用 skill 工具（`tool/skill.ts`），这时才把完整的 SKILL.md 内容注入上下文（`skill.ts:87`）。同时还会扫描 skill 目录下的附属文件列表（最多 10 个），让模型知道有哪些脚本和模板可用。

这个设计跟 Claude Code 的 ToolSearch 思路一致——元数据先行，详情按需。但覆盖范围不同：OpenCode 的渐进披露只覆盖了 skill（通常是领域特定的工作流指令），tool 定义层面仍是全量加载。

### OpenCode 还没做的

对照前面的策略全景和产品对比，OpenCode 有几个明显的缺失：

**工具定义没有渐进式披露。** Skill 层面，OpenCode 已经实现了两级渐进披露：系统提示只注入 skill 的名称和描述（`Skill.fmt(list, { verbose: true })`），完整的 SKILL.md 内容只在模型主动调用 skill 工具时才注入上下文（`skill.ts:87`）。但在 tool 定义层面，所有非 skill 工具的 schema 仍是在 session 初始化时一次性全量加载的（`registry.ts:179`），没有 Claude Code 那种 ToolSearch 按需加载机制。anthropic.txt 里提到"prefer to use the Task tool in order to reduce context usage"，说明开发者用子 agent 隔离来缓解上下文压力，但工具定义本身占用的上下文空间没有被优化。

**没有位置敏感的上下文组装。** `llm.ts` 里系统提示在前，对话历史按时间顺序在后，没有按 Lost in the Middle 效应调整信息位置。

**没有死亡螺旋检测。** doom loop 只检测连续 3 次完全相同的工具调用。错误率上升 + 上下文膨胀 + 反复编辑同一文件的耦合检测——没有。

**溢出阈值不按模型调整。** 安全缓冲固定 20,000 tokens（或 `maxOutputTokens`，取较小值），不区分 Gemini 的 20% 崩塌阈值和 Claude 的 45%。溢出检测是"到了极限才动"，不是"接近崩塌阈值就预警"。

这些缺失就是我们在 OpenCode 基础上要扩展的方向。

---

## Codex 的实现

Codex（OpenAI 的开源 CLI Agent）用 Rust 写成，代码量比 OpenCode 大一个数量级，上下文管理也更成熟。以下分析基于 `codex-rs/core/src/` 目录的源码阅读。<sup>[26]</sup>

### 溢出检测与自动压缩触发

Codex 的溢出检测比 OpenCode 精细。`ModelInfo` 结构体包含两个关键字段：`context_window`（模型窗口大小）和 `auto_compact_token_limit`（压缩触发阈值）。阈值的计算逻辑：

```rust
// codex-rs/protocol/src/openai_models.rs
pub fn auto_compact_token_limit(&self) -> Option<i64> {
    let context_limit = self
        .context_window
        .map(|context_window| (context_window * 9) / 10);
    let config_limit = self.auto_compact_token_limit;
    if let Some(context_limit) = context_limit {
        return Some(
            config_limit.map_or(context_limit, |limit| std::cmp::min(limit, context_limit)),
        );
    }
    config_limit
}
```

如果配置了显式值，取该值与窗口 90% 的较小值；没配置则默认窗口的 90%。另外还有一个 `effective_context_window_percent` 字段，默认 95%，用于区分"名义容量"和"可用容量"。

对比 OpenCode 固定 20,000 tokens 的安全缓冲，Codex 的比例制阈值意味着：128K 窗口的模型在约 115K 时触发压缩，而 32K 窗口的模型在约 29K 时触发。这更合理——小模型不应该等到只剩 20K 才动手。

### 双路压缩：本地与远端

OpenCode 只有一种压缩路径（本地 prune + summarize）。Codex 有两条路：

**本地压缩（`compact.rs`）。** 启动一个专门的 compact turn，把当前对话历史作为输入，用压缩专用 prompt（`compact/prompt.md`）让模型生成摘要。摘要完成后，用 `summary_prefix.md` 的模板拼成新历史，保留所有用户消息和摘要文本，丢弃工具调用记录。如果压缩过程本身触发了 context window exceeded 错误，会从历史开头逐条删除，直到 prompt 能放进去。

压缩完成后还会发一条警告："长线程和多次压缩会降低模型准确性，尽量开新线程。"这条警告本身就是一个产品决策——承认压缩有损，引导用户主动控制对话长度。

**远端压缩（`compact_remote.rs`）。** 仅 OpenAI provider 走这条路（`should_use_remote_compact_task` 检查 `provider.is_openai()`）。调用模型服务端的 `/responses/compact` 端点处理压缩<sup>[27]</sup>。压缩后的历史还要经过 `process_compacted_history` 过滤：删掉 developer 角色消息（防止陈旧指令），删掉非用户内容的 user 消息（session 前缀包装），只保留真正的用户消息、hook prompt 和 assistant 消息。

两条路的触发条件相同：总 token 使用量超过 `auto_compact_token_limit`。mid-turn 压缩（模型还要继续执行时触发）和 pre-turn 压缩（新一轮开始前触发）的区别在于初始上下文注入位置不同。

### Token 估算

`ContextManager` 的 token 估算基于字节启发式：先用 `serde_json` 序列化每个 item 得到字节数，再用 4 bytes/token 的经验比例转换。

```rust
// codex-rs/core/src/context_manager/history.rs
fn estimate_item_token_count(item: &ResponseItem) -> i64 {
    let model_visible_bytes = estimate_response_item_model_visible_bytes(item);
    approx_tokens_from_byte_count_i64(model_visible_bytes)
}

const RESIZED_IMAGE_BYTES_ESTIMATE: i64 = 7373;  // ≈ 1,844 tokens
const ORIGINAL_IMAGE_PATCH_SIZE: u32 = 32;
```

对于内联 base64 图像，不按原始 payload 大小算，而是用固定的 7,373 bytes（约 1,844 tokens）替代——因为 provider 会先 resize 图像。对 `detail: "original"` 的图像，还会解码后按 32px patch 网格计算 token 数，结果缓存在 LRU cache 里。

相比之下，OpenCode 直接用 provider 返回的 `token_usage` 做判断，不做本地估算。Codex 的本地估算让它能在 API 返回之前就预判溢出——比如在用户输入一个巨大的工具输出后，不用等模型回复就能决定是否压缩。

### 工具输出截断

Codex 对工具输出有系统性的截断策略。`output-truncation` 模块提供 `TruncationPolicy`，支持按字节或按 token 截断。截断方式是"中间截断"（`truncate_middle`）——保留输出的头尾，删掉中间部分，这样模型能同时看到命令开头和最终结果。

```rust
// codex-rs/utils/output-truncation/src/lib.rs
pub fn formatted_truncate_text(content: &str, policy: TruncationPolicy) -> String {
    if content.len() <= policy.byte_budget() {
        return content.to_string();
    }
    let total_lines = content.lines().count();
    let result = truncate_text(content, policy);
    format!("Total output lines: {total_lines}\n\n{result}")
}

pub fn truncate_text(content: &str, policy: TruncationPolicy) -> String {
    match policy {
        TruncationPolicy::Bytes(bytes) => truncate_middle_chars(content, bytes),
        TruncationPolicy::Tokens(tokens) => truncate_middle_with_token_budget(content, tokens).0,
    }
}
```

截断后在开头加一行"Total output lines: N"，让模型知道完整输出有多长。每个模型可以在 `ModelInfo.truncation_policy` 里配置自己的截断策略。`ContextManager.record_items` 在录入历史时就执行截断，给截断预算乘以 1.2 的序列化余量系数。这意味着工具输出在进入上下文之前就已经被控制住了，不是等溢出再处理。

### 渐进式披露

Codex 的渐进式披露分两层：

**工具层。** Codex 实现了 `tool_search` 工具（`tools/handlers/tool_search.rs`），用 BM25 全文检索在已注册的 MCP 工具中搜索。模型发起搜索请求，带上查询词和数量限制（默认 8），handler 用工具名、描述、connector 名称和参数属性名构建搜索文档，返回匹配的工具定义。这跟 Claude Code 的 ToolSearch 机制对等——MCP 工具的 schema 不预加载到 prompt，只在需要时按需检索注入。系统提示里只放一段描述（`search_tool/tool_description.md`）："有以下 app/connector 的工具可用，用 tool_search 去搜索加载。"

**Skill 层。** 系统提示里列出所有 skill 的名称、描述和文件路径（`core-skills/src/render.rs`），明确写了 "progressive disclosure" 的使用流程：先看 SKILL.md 的工作流，再按需加载引用的文件，不要批量加载。当用户消息里提到某个 skill（`$SkillName` 语法或纯文本匹配），`injection.rs` 才读取完整的 SKILL.md 内容注入上下文。

### 历史规范化

`normalize.rs` 在每轮模型调用前做三件事：（1）确保每个 function call 都有对应的 output——缺失的补一个 "aborted"；（2）删除孤立的 output（没有对应 call 的）；（3）如果模型不支持图像输入，把所有图像内容替换成占位文本。这避免了"残缺的工具调用对"导致模型困惑的问题。

OpenCode 的 `normalize.ts` 做类似的事情，但 Codex 还多了 `remove_corresponding_for`——当删除一条历史记录时，自动找到并删除它的配对记录（call 对 output，output 对 call），避免产生新的孤立项。

### 上下文增量更新

`updates.rs` 实现了一套基于 diff 的上下文注入机制。每轮不是重新注入所有上下文，而是跟上一轮的 `reference_context_item` 做对比，只注入变化的部分：环境变化（cwd、shell）、权限变化（sandbox policy、approval policy）、协作模式变化、实时模式开关、个性化设置变化、模型切换指令。如果没有变化，对应的 developer 消息就不注入，省掉上下文空间。

OpenCode 没有这个机制——每轮都重新拼接完整的系统提示。

### Codex 没有的

对照同样的维度，Codex 也有缺失：

**没有位置敏感组装。** 历史按时间顺序，没有按 Lost in the Middle 效应重排。

**没有显式的死亡螺旋检测。** 代码里搜不到 doom loop 相关逻辑。mid-turn 压缩客观上能打断一些恶性循环（压缩后重新开始），但没有 OpenCode 那种"连续 3 次相同工具调用"的显式检测。

**压缩模型不可配置。** 本地压缩复用当前对话模型，不像 OpenCode 可以配置一个更便宜的 `agent.model` 做摘要。

---

## 常见陷阱：上下文死亡螺旋

这是上下文管理中最危险的失败模式，我花了不少时间才真正理解它的机理。

触发过程是这样的：Agent 犯了一个错 → 错误信息（日志、重试提示）被加入上下文 → 上下文膨胀，信噪比下降 → 决策质量进一步下降 → 产生更多错误 → 更多错误信息注入。这是一个正反馈循环，一旦启动就会自我加速。

LangChain 在 Terminal Bench 上发现了一个典型信号：Agent 对同一文件反复修改。当一个文件被编辑超过 N 次时，大概率不是"差一点就对了"，而是方向错了。正确的干预是注入"换一种方法"的建议，而不是让它继续修修补补。

死亡螺旋的本质是一个控制论问题：错误信号被放大而非衰减。解决方案不是"压缩掉错误信息"——那只是治标。根本的做法是检测到正反馈环路后打断它，要么切换策略，要么重置上下文从头来过。

另一个容易踩的坑是**探索性任务中的积极压缩**。当任务边界模糊时（比如"帮我理解这个系统的架构"），你不知道哪些信息后面会用到。这时候压缩掉的"无关信息"可能恰恰是后面的关键线索。正确做法是用隔离策略——拆成多个小任务，每个有干净的上下文。

---

## 工程实现：基于 OpenCode Plugin 的核心算法

我的产品基于 [OpenCode](https://opencode.ai) 开发。OpenCode 提供了一套 Plugin 机制（[文档](https://opencode.ai/docs/zh-cn/plugins/)），允许在 Agent 执行的各个阶段注入自定义逻辑，而不需要修改核心代码。Plugin 是 JavaScript/TypeScript 模块，导出一个异步函数，返回 Hook 实现。

类比 Web 开发中的中间件：HTTP 请求到达之前可以做身份验证，响应发出之前可以做日志记录。OpenCode Plugin Hook 也是一样——在模型推理之前可以整理上下文，之后可以检测异常。

OpenCode 目前支持的上下文相关 Hook：

```
Plugin 初始化（加载时执行一次）
    ↓
[每轮循环]
  experimental.chat.system.transform   — 改写 system prompt
  experimental.chat.messages.transform — 改写消息历史
  chat.params                          — 调整推理参数
      ↓ [模型推理]
  tool.execute.before                  — 工具调用前（可修改参数/阻断）
  tool.execute.after                   — 工具调用后（可修改输出）
      ↓
  experimental.session.compacting      — 压缩时注入上下文/覆盖 prompt
    ↓
event("session.idle")                  — session 空闲时
```

下面是 6 个核心算法的 OpenCode Plugin 实现。每个算法以实际可运行的 TypeScript 代码给出。先定义全局状态和模型配置：

```typescript
// .opencode/plugins/context-manager.ts
import type { Plugin } from "opencode/plugin"

// 每个模型一份上下文参数配置
interface ModelContextProfile {
  modelId: string
  effectiveWindow: number       // 实际有效窗口（非声称值）
  collapseThreshold: number     // 性能崩塌阈值（0.0-1.0）
  positionSensitivity: "high" | "medium" | "low"
  cachingSupport: "prefix" | "none"
}

// 贯穿整个 session 的上下文状态
interface ContextState {
  totalTokens: number
  utilization: number
  compactionCount: number
  turnCount: number
  fileEditCounts: Record<string, number>
  errorCountWindow: number[]
  spiralRisk: number
}

const MODEL_PROFILES: Record<string, ModelContextProfile> = {
  "claude-sonnet-4": {
    modelId: "claude-sonnet-4",
    effectiveWindow: 180_000,
    collapseThreshold: 0.45,
    positionSensitivity: "medium",
    cachingSupport: "prefix",
  },
  "gemini-2.5-flash": {
    modelId: "gemini-2.5-flash",
    effectiveWindow: 800_000,
    collapseThreshold: 0.20,
    positionSensitivity: "high",
    cachingSupport: "prefix",
  },
}

// Plugin 级别的状态（跨 hook 共享）
const state: ContextState = {
  totalTokens: 0,
  utilization: 0,
  compactionCount: 0,
  turnCount: 0,
  fileEditCounts: {},
  errorCountWindow: [],
  spiralRisk: 0,
}
```

`ModelContextProfile` 的设计基于一个关键发现：上下文管理策略不是完全模型无关的。原则（"压缩尽量推迟"、"保留结构"）对所有模型通用，但参数（崩塌阈值、位置敏感度）因模型而异。换模型时，只更新配置，压缩和组织逻辑不变。

---

### 算法 1：渐进式披露（Plugin 初始化 + `experimental.chat.system.transform`）

核心思路：session 开始时只加载导航地图，每轮按需展开详情。OpenCode 的 `experimental.chat.system.transform` 钩子在每轮模型调用前触发，允许修改 system prompt 数组——正好用来控制注入量。

```typescript
// 算法 1：渐进式披露
// 技术点：OpenCode Plugin 初始化 + experimental.chat.system.transform + 自定义 tool

import { readFileSync, readdirSync } from "fs"
import { join } from "path"
import { tool } from "opencode/plugin"

// skill 索引（Plugin 加载时构建，不注入模型）
interface SkillEntry {
  name: string
  oneLine: string
  fullDefinition: string
  loaded: boolean
}
let skillIndex: SkillEntry[] = []

// --- Plugin 初始化（加载时执行一次） ---
function initProgressiveDisclosure(projectRoot: string) {
  const skillDir = join(projectRoot, ".opencode", "skills")
  for (const name of readdirSync(skillDir)) {
    const content = readFileSync(join(skillDir, name, "SKILL.md"), "utf-8")
    skillIndex.push({
      name,
      oneLine: content.split("\n")[0].slice(0, 80),
      fullDefinition: content,
      loaded: false,
    })
  }
}

// --- Hook: experimental.chat.system.transform（每轮执行） ---
// 只注入导航地图和 skill 索引，不注入完整定义
const systemTransformForDisclosure: Hooks["experimental.chat.system.transform"] =
  async (_input, output) => {
    // 在 system prompt 数组末尾追加导航地图
    output.system.push(
      `## 可用 Skills（仅索引，需要时用 skill_search 加载）\n` +
      skillIndex.map(s => `- ${s.name}: ${s.oneLine}`).join("\n")
    )
  }

// --- 自定义工具：skill_search（按需加载完整定义） ---
const skillSearchTool = tool({
  description: "搜索并加载 skill 的完整定义。模型应在需要某个 skill 时调用此工具。",
  args: { query: tool.schema.string() },
  async execute(args) {
    const matched = skillIndex.filter(s =>
      s.name.includes(args.query) || s.oneLine.includes(args.query)
    )
    if (matched.length === 0) return "未找到匹配的 skill"
    // 标记为已加载，返回完整定义
    for (const s of matched) s.loaded = true
    return matched.map(s => s.fullDefinition).join("\n---\n")
  },
})
```

导航地图约 100 行（几百 token），完整的工具定义可能上万 token。按需加载把初始上下文占用降了一个数量级。OpenCode 本身的 Skill 层已经实现了这个模式（`Skill.fmt` 只输出名称和描述），这里通过 Plugin 将同样的思路扩展到自定义工具。

---

### 算法 2：上下文压缩（`experimental.session.compacting`）

核心思路：利用率超过阈值时触发，注入领域上下文帮助压缩保留关键信息。OpenCode 的压缩触发时机由内部逻辑控制（类似 Codex 的 `auto_compact_token_limit`），Plugin 通过 `experimental.session.compacting` 钩子参与压缩过程——可以注入额外上下文，也可以覆盖压缩 prompt。

```typescript
// 算法 2：上下文压缩
// 技术点：experimental.session.compacting

const compactionHook: Hooks["experimental.session.compacting"] =
  async (_input, output) => {
    // 根据当前状态决定压缩策略
    const strategy = decideStrategy(state)

    if (strategy === "aggressive") {
      // 覆盖压缩 prompt：只保留结论，丢弃推理过程
      output.prompt = [
        "你正在执行上下文压缩。创建一份交接摘要，供另一个 LLM 继续任务。",
        "保留：决策结论、文件路径、错误信息、任务进度。",
        "丢弃：中间推理过程、工具输出细节、重复尝试。",
        "摘要必须包含当前 TODO 列表的完整状态。",
      ].join("\n")
    }

    // 注入领域上下文（不论哪种策略都有用）
    output.context.push(
      `## 压缩时的上下文状态\n` +
      `- 已压缩次数: ${state.compactionCount}\n` +
      `- 文件编辑热点: ${JSON.stringify(state.fileEditCounts)}\n` +
      `- 螺旋风险: ${state.spiralRisk.toFixed(2)}`
    )
    state.compactionCount++
  }

function decideStrategy(ctx: ContextState): "aggressive" | "standard" | "gentle" {
  if (ctx.utilization >= 0.95) return "aggressive"
  if (ctx.utilization >= 0.45) return "standard"
  return "gentle"
}
```

为什么分三级？因为压缩是有损的。能用温和策略解决的问题，不该上激进策略。Goose 的两层阈值（80% 摘要 + 95% compaction）就是这个思路。注意：OpenCode 的压缩触发时机目前不可 hook，Plugin 只能在压缩发生时参与过程。如果需要自定义触发阈值，需要修改 OpenCode 核心代码或等待 API 开放。

---

### 算法 3：死亡螺旋检测（`tool.execute.after` + `tool.execute.before`）

核心思路：单一信号不可靠，三个信号耦合检测。OpenCode 的 `tool.execute.after` 在每次工具调用后触发，提供工具名、参数和输出——正好用来追踪编辑计数和错误率。当检测到螺旋时，通过 `tool.execute.before` 抛出异常阻断后续危险操作。

```typescript
// 算法 3：死亡螺旋检测
// 技术点：tool.execute.after（追踪） + tool.execute.before（阻断）

const EDIT_THRESHOLD = 5
const ERROR_WINDOW_SIZE = 10
let spiralDetected = false
let spiralMessage = ""

// --- Hook: tool.execute.after（每次工具调用后追踪状态） ---
const afterToolForSpiral: Hooks["tool.execute.after"] =
  async (input, output) => {
    // 信号 A：反复编辑同一文件
    if (input.tool === "edit" || input.tool === "write") {
      const path = input.args?.filePath ?? ""
      state.fileEditCounts[path] = (state.fileEditCounts[path] ?? 0) + 1
    }
    const hasLoop = Object.values(state.fileEditCounts)
      .some(v => v >= EDIT_THRESHOLD)

    // 信号 B：持续高错误率（从 output 判断是否失败）
    const isError = output.output.startsWith("Error") ||
                    output.output.startsWith("FAILED")
    state.errorCountWindow.push(isError ? 1 : 0)
    if (state.errorCountWindow.length > ERROR_WINDOW_SIZE)
      state.errorCountWindow.shift()

    let highErrorRate = false
    if (state.errorCountWindow.length >= 5) {
      const recent = state.errorCountWindow.slice(-5)
      const rate = recent.reduce((a, b) => a + b, 0) / 5
      highErrorRate = rate >= 0.6
    }

    // 信号 C：上下文膨胀但没有压缩
    const contextBloating = state.utilization > 0.7 &&
                            state.compactionCount === 0

    // 耦合判定：任意两个信号 = 螺旋
    const signals = [hasLoop, highErrorRate, contextBloating]
      .filter(Boolean).length

    if (signals >= 2) {
      spiralDetected = true
      spiralMessage = signals >= 3
        ? "强制重置：检测到死亡螺旋（循环编辑+高错误率+上下文膨胀）"
        : "检测到重复错误模式。停下来，重新分析问题，换一种方法。"
    }
  }

// --- Hook: tool.execute.before（螺旋时阻断危险操作） ---
const beforeToolForSpiral: Hooks["tool.execute.before"] =
  async (input, _output) => {
    if (!spiralDetected) return
    if (input.tool === "edit" || input.tool === "write") {
      throw new Error(spiralMessage)
    }
  }
```

为什么不能靠单一信号？"反复编辑同一文件"可能只是复杂重构。"错误率高"可能是任务本身困难。但两个以上信号同时出现时，大概率是螺旋了。LangChain 的 LoopDetectionMiddleware 只看文件编辑计数——我们加了错误率和上下文膨胀率两个维度，误报率低很多。

---

### 算法 4：缓存友好布局（`experimental.chat.system.transform`）

核心思路：静态内容前置，变量内容后置，最大化前缀缓存命中。OpenCode 的 `experimental.chat.system.transform` 提供 `output.system` 数组——就是最终发给模型的 system prompt 各部分。Plugin 可以对这个数组重新排序。

```typescript
// 算法 4：缓存友好布局
// 技术点：experimental.chat.system.transform

// 用关键词判断 system prompt 片段的变化频率
function classifyChangeFrequency(part: string): "static" | "semi" | "dynamic" {
  // 行为规则、安全指令几乎不变
  if (part.includes("IMPORTANT:") || part.includes("安全") ||
      part.includes("rules") || part.includes("instructions"))
    return "static"
  // skill 索引、工具描述 session 内不变
  if (part.includes("Skills") || part.includes("tool") ||
      part.includes("可用"))
    return "semi"
  // 其他都是动态内容
  return "dynamic"
}

const systemTransformForCache: Hooks["experimental.chat.system.transform"] =
  async (_input, output) => {
    const staticParts: string[] = []
    const semiParts: string[] = []
    const dynamicParts: string[] = []

    for (const part of output.system) {
      const freq = classifyChangeFrequency(part)
      if (freq === "static") staticParts.push(part)
      else if (freq === "semi") semiParts.push(part)
      else dynamicParts.push(part)
    }

    // 静态前置 → 半静态 → 动态后置
    // 保证 "old prompt is exact prefix of new prompt"
    output.system = [...staticParts, ...semiParts, ...dynamicParts]
  }
```

这个算法看起来简单，但有个容易忽略的坑：工具定义的顺序也必须稳定。哪怕两个工具交换了位置，整个前缀缓存就失效了。Codex 为了保证这一点，把系统指令、工具定义、沙箱配置全部固定顺序。OpenCode 的 Plugin 排序只能控制 system prompt 部分，消息历史的顺序由核心引擎管理。

---

### 算法 5：工具输出回压（`tool.execute.after`）

核心思路：成功时精简输出，失败时丰富输出。用一句话概括就是"静默成功，大声失败"。OpenCode 的 `tool.execute.after` 钩子提供 `output.output` 字段（工具返回的文本），Plugin 可以直接修改这个字段来控制注入上下文的信息量。

```typescript
// 算法 5：工具输出回压
// 技术点：tool.execute.after

const MAX_OUTPUT_CHARS = 20_000  // 约 5000 tokens

function truncateMiddle(text: string, maxLen: number): string {
  if (text.length <= maxLen) return text
  const totalLines = text.split("\n").length
  const half = Math.floor(maxLen / 2)
  const head = text.slice(0, half)
  const tail = text.slice(-half)
  return `Total output lines: ${totalLines}\n\n` +
         `${head}\n\n... [truncated] ...\n\n${tail}`
}

const toolOutputBackpressure: Hooks["tool.execute.after"] =
  async (input, output) => {
    const isError = output.output.startsWith("Error") ||
                    output.output.startsWith("FAILED") ||
                    output.output.includes("permission denied")

    if (!isError) {
      // 成功：精简输出
      if (output.output.length > MAX_OUTPUT_CHARS) {
        output.output = truncateMiddle(output.output, MAX_OUTPUT_CHARS)
      }
      // 简单成功只需一行确认
      if (input.tool === "bash" && output.output.trim() === "") {
        output.output = `OK: ${input.tool} completed (no output)`
      }
    } else {
      // 失败：丰富输出（结构化报错，帮助模型下一步决策）
      output.output = [
        `FAILED: ${input.tool}`,
        `  args: ${JSON.stringify(input.args)}`,
        `  error: ${output.output.slice(0, 2000)}`,
        `  hint: 检查参数是否正确，尝试换一种方法`,
      ].join("\n")
    }
  }
```

这个设计背后有个不对称逻辑：成功的工具调用对后续决策的信息量很低（"文件已保存"没什么可学的），但失败的工具调用信息量很高（Agent 需要从错误中学习下一步怎么做）。所以成功时省 token，失败时花 token。

---

### 算法 6：结构化上下文组装（`experimental.chat.messages.transform`）

核心思路：根据 Lost in the Middle 效应的严重程度，按优先级组织信息位置。OpenCode 的 `experimental.chat.messages.transform` 提供完整的消息数组，Plugin 可以重新排列消息顺序。

```typescript
// 算法 6：结构化上下文组装
// 技术点：experimental.chat.messages.transform

type MsgEntry = { info: any; parts: any[] }

function classifyPriority(msg: MsgEntry): 0 | 1 | 2 {
  const text = msg.parts.map((p: any) => p.text ?? "").join(" ")
  // 高优先级：任务指令、当前错误、关键约束
  if (text.includes("Error") || text.includes("TODO") ||
      text.includes("current_task"))
    return 0
  // 低优先级：背景信息、参考文档
  if (text.includes("reference") || text.includes("背景") ||
      text.length > 5000)
    return 2
  // 中优先级：普通对话
  return 1
}

const messagesTransformForAssembly: Hooks["experimental.chat.messages.transform"] =
  async (_input, output) => {
    const high: MsgEntry[] = []
    const medium: MsgEntry[] = []
    const low: MsgEntry[] = []

    for (const msg of output.messages) {
      const p = classifyPriority(msg)
      if (p === 0) high.push(msg)
      else if (p === 1) medium.push(msg)
      else low.push(msg)
    }

    // 默认策略：重要信息前置
    // 位置敏感性高的模型可以用 U 型策略（high + low + medium + high[-1]）
    output.messages = [...high, ...medium, ...low]
  }
```

Ms-PoE（Multi-scale Positional Encoding, arXiv:2403.04797）已经把位置偏差从 >20% 缩小到 0.6-3.8%，不需要微调。这意味着未来模型架构改进可能让 U 型组装策略变得没必要。但现在生产环境中，重要信息放首尾仍然是有效的。注意 `experimental.chat.messages.transform` 是实验性接口，API 可能变化。

---

### 组装为完整 Plugin

以上 6 个算法最终导出为一个 OpenCode Plugin：

```typescript
// .opencode/plugins/context-manager.ts — 完整导出
export const ContextManagerPlugin: Plugin = async ({ directory }) => {
  // Plugin 初始化（算法 1）
  initProgressiveDisclosure(directory)

  return {
    // 算法 1: 渐进式披露（system prompt 注入 skill 索引）
    // 算法 4: 缓存友好布局（重排 system prompt）
    "experimental.chat.system.transform": async (input, output) => {
      await systemTransformForDisclosure(input, output)
      await systemTransformForCache(input, output)
    },

    // 算法 6: 结构化上下文组装（重排消息）
    "experimental.chat.messages.transform": messagesTransformForAssembly,

    // 算法 2: 上下文压缩（注入领域上下文）
    "experimental.session.compacting": compactionHook,

    // 算法 3: 死亡螺旋检测（阻断）+ 算法 5: 回压
    "tool.execute.before": beforeToolForSpiral,
    "tool.execute.after": async (input, output) => {
      await afterToolForSpiral(input, output)
      await toolOutputBackpressure(input, output)
    },

    // 算法 1: 按需加载的自定义工具
    tool: { skill_search: skillSearchTool },
  }
}
```

一轮完整的 Agent 执行中，这些 Hook 的调用顺序是：

```
Plugin 初始化: 渐进式披露（构建 skill 索引）
    ↓
experimental.chat.system.transform: skill 索引注入 → 缓存友好排序
    ↓
experimental.chat.messages.transform: 结构化上下文组装
    ↓
[模型推理]
    ↓
tool.execute.before: 死亡螺旋阻断检查
    ↓
[工具执行]
    ↓
tool.execute.after: 螺旋状态追踪 → 工具输出回压
    ↓
experimental.session.compacting: 压缩时注入领域上下文（触发时）
    ↓
[下一轮 experimental.chat.system.transform ...]
```

---

## 对企业办公场景的启示

以上分析主要来自 Coding Agent 领域。我做的是企业办公 AI Agent，和代码场景有两个关键差异。

**信息结构化程度低。** 代码有语法结构、import 图谱、类型系统，系统能自动判断相关性。办公场景（邮件、文档、会议记录）的信息松散得多。这意味着假设 4（任务相关性可被外部判断）在办公场景中更弱。推论是办公 Agent 应更多依赖用户显式指定上下文（类似 Cursor 的 @-mentions 模式），而非自动压缩。

**任务边界更模糊。** "帮我整理这个项目的进展"这种需求，什么信息相关，连用户自己都不一定说得清。在这种探索性任务中，积极压缩很危险。推论是探索性任务应优先使用隔离策略（拆成多个小任务，每个有干净的上下文），而非压缩策略。

我目前的设计方向是混合模式：用户主导选择上下文，系统建议补充。通过任务分类和优先级标签帮系统理解"相关性"。定期生成主动摘要让用户审阅，而不是到了极限才被动压缩。

---

## 验证方法：如何证明改进有效

算法写完了，怎么知道它们真的有用？上下文管理的改进不像 UI 改动那样肉眼可见，需要系统性的验证方法。以下方案基于业界已有实践，适配到 OpenCode Plugin 场景。

### 评估维度与指标

Factory AI 在 2025 年底发布了针对上下文压缩的评估框架<sup>[29]</sup>，用 probe-based evaluation 替代传统的文本相似度指标（ROUGE）。这个思路对我们同样适用——不评估"压缩后的文本像不像原文"，而是评估"压缩后模型还能不能回答关键问题"。

结合我们 6 个算法的特点，定义四类指标：

**效果指标（改进是否有效）：** 任务完成率（同一组任务，开启/关闭 Plugin 对比）、压缩后信息保留率（用 probe 问题测试，下面详述）、死亡螺旋触发次数（算法 3 的直接指标）。

**效率指标（代价是否可控）：** 每任务总 token 消耗、缓存命中率（算法 4 的直接指标）、平均任务耗时、每次压缩的 token 节省量。

**质量指标（副作用是否可接受）：** 压缩后任务回溯次数（Jason Liu 提出的 momentum 指标<sup>[30]</sup>——压缩不应该打断 Agent 的工作势头）、误报率（算法 3 的螺旋检测是否错杀了正常重构）。

**观测指标（系统是否健康）：** 上下文利用率分布、工具输出截断率、渐进式披露的 skill 加载频次。

### Probe-Based 评估：怎么测压缩质量

Factory 的方法<sup>[29]</sup>很实用：拿一段真实的长对话，压缩前半部分，然后用四类 probe 问题测试模型是否还记得关键信息。

```typescript
// probe 问题示例（用于评估压缩后的信息保留）
const probes = {
  recall:   "最初的错误信息是什么？",          // 事实性保留
  artifact: "我们修改了哪些文件，怎么改的？",    // 工件追踪
  plan:     "下一步应该做什么？",              // 任务规划
  decision: "我们为什么选择了方案 A 而不是 B？", // 推理链保留
}
```

评分用 LLM 盲测（GPT 或 Claude 评估），6 个维度各 0-5 分：准确性、上下文意识、工件追踪、完整性、连贯性、指令遵循。Factory 在 36,000+ 条生产消息上跑了这个评估，结果显示结构化摘要（3.70）优于 OpenAI compact 端点（3.35）和 Anthropic 内置压缩（3.44）。

对我们来说，最重要的改编是：probe 问题要覆盖企业办公场景特有的信息类型——会议决议、审批流程、文档版本关系——而不只是代码路径和错误信息。

### 消融实验设计

消融实验（ablation study）是验证每个算法独立贡献的标准方法。设计如下：

| 实验组 | 启用的算法 | 测量目标 |
|--------|-----------|---------|
| Baseline | 无 Plugin | 基准线 |
| Full | 全部 6 个 | 完整效果 |
| -渐进式披露 | 2,3,4,5,6 | 算法 1 的独立贡献 |
| -压缩 | 1,3,4,5,6 | 算法 2 的独立贡献 |
| -螺旋检测 | 1,2,4,5,6 | 算法 3 的独立贡献 |
| -缓存布局 | 1,2,3,5,6 | 算法 4 的独立贡献 |
| -回压 | 1,2,3,4,6 | 算法 5 的独立贡献 |
| -组装 | 1,2,3,4,5 | 算法 6 的独立贡献 |

在 OpenCode Plugin 中实现算法开关：

```typescript
// opencode.json 配置
{
  "plugin": [
    ["context-manager", {
      "enableDisclosure": true,
      "enableCompaction": true,
      "enableSpiralDetection": true,
      "enableCacheLayout": true,
      "enableBackpressure": true,
      "enableAssembly": true
    }]
  ]
}
```

```typescript
// Plugin 中读取配置
export const ContextManagerPlugin: Plugin = async (ctx, options) => {
  const opts = {
    enableDisclosure: true,
    enableCompaction: true,
    enableSpiralDetection: true,
    enableCacheLayout: true,
    enableBackpressure: true,
    enableAssembly: true,
    ...options,
  }

  return {
    "experimental.chat.system.transform": async (input, output) => {
      if (opts.enableDisclosure)
        await systemTransformForDisclosure(input, output)
      if (opts.enableCacheLayout)
        await systemTransformForCache(input, output)
    },
    "tool.execute.after": async (input, output) => {
      if (opts.enableSpiralDetection)
        await afterToolForSpiral(input, output)
      if (opts.enableBackpressure)
        await toolOutputBackpressure(input, output)
    },
    // ... 其余算法同理
  }
}
```

每组跑相同的任务集（至少 30 个任务保证统计显著性），记录上述所有指标。如果某个算法关闭后指标没有显著下降，说明它的贡献不大，可以考虑移除以降低复杂度。

### 观测埋点：OpenCode Plugin 实现

观测是验证的基础。没有数据，一切评估都是猜测。OpenCode Plugin 提供了 `client.app.log` 接口记录结构化日志，结合 `tool.execute.after` 和 `event` 钩子，可以构建完整的观测体系。

```typescript
// .opencode/plugins/observability.ts
// 观测埋点 Plugin（独立于算法 Plugin，避免耦合）
import type { Plugin, Hooks } from "opencode/plugin"

interface Metrics {
  sessionId: string
  turnCount: number
  totalInputTokens: number
  totalOutputTokens: number
  cacheHits: number
  cacheMisses: number
  toolCalls: { tool: string; duration: number; success: boolean }[]
  compactionEvents: { timestamp: number; tokensBefore: number; tokensAfter: number }[]
  spiralAlerts: { timestamp: number; signals: string[] }[]
  skillLoads: { name: string; timestamp: number }[]
  truncations: { tool: string; originalLen: number; truncatedLen: number }[]
}

export const ObservabilityPlugin: Plugin = async ({ client }) => {
  const metrics: Metrics = {
    sessionId: "",
    turnCount: 0,
    totalInputTokens: 0,
    totalOutputTokens: 0,
    cacheHits: 0,
    cacheMisses: 0,
    toolCalls: [],
    compactionEvents: [],
    spiralAlerts: [],
    skillLoads: [],
    truncations: [],
  }

  return {
    // --- 工具调用追踪 ---
    "tool.execute.before": async (input, _output) => {
      // 记录调用开始时间（存在 metadata 中）
      ;(input as any)._startTime = Date.now()
    },

    "tool.execute.after": async (input, output) => {
      const duration = Date.now() - ((input as any)._startTime ?? Date.now())
      const success = !output.output.startsWith("Error")

      metrics.toolCalls.push({
        tool: input.tool,
        duration,
        success,
      })

      // 检测截断（算法 5 的效果观测）
      if (output.output.includes("[truncated]")) {
        metrics.truncations.push({
          tool: input.tool,
          originalLen: parseInt(
            output.output.match(/Total output lines: (\d+)/)?.[1] ?? "0"
          ),
          truncatedLen: output.output.length,
        })
      }

      // 每 10 次工具调用输出一次摘要日志
      if (metrics.toolCalls.length % 10 === 0) {
        await client.app.log({
          body: {
            service: "context-observability",
            level: "info",
            message: JSON.stringify({
              type: "tool_summary",
              totalCalls: metrics.toolCalls.length,
              successRate: metrics.toolCalls.filter(t => t.success).length
                / metrics.toolCalls.length,
              avgDuration: metrics.toolCalls.reduce((a, t) => a + t.duration, 0)
                / metrics.toolCalls.length,
            }),
          },
        })
      }
    },

    // --- 全局事件监听 ---
    event: async ({ event }) => {
      if (event.type === "session.compacted") {
        metrics.compactionEvents.push({
          timestamp: Date.now(),
          tokensBefore: 0, // OpenCode 暂不暴露 token 数
          tokensAfter: 0,
        })
        await client.app.log({
          body: {
            service: "context-observability",
            level: "info",
            message: JSON.stringify({
              type: "compaction",
              count: metrics.compactionEvents.length,
              sessionId: event.properties.sessionID,
            }),
          },
        })
      }

      // session 结束时输出完整报告
      if (event.type === "session.idle") {
        await client.app.log({
          body: {
            service: "context-observability",
            level: "info",
            message: JSON.stringify({
              type: "session_report",
              ...metrics,
              toolCallCount: metrics.toolCalls.length,
              successRate: metrics.toolCalls.filter(t => t.success).length
                / Math.max(metrics.toolCalls.length, 1),
              compactionCount: metrics.compactionEvents.length,
              spiralAlertCount: metrics.spiralAlerts.length,
              truncationCount: metrics.truncations.length,
            }),
          },
        })
      }
    },
  }
}
```

这个观测 Plugin 和算法 Plugin 是独立的。观测不依赖算法是否启用——消融实验时关掉某个算法，观测照常工作。日志通过 `client.app.log` 写入 OpenCode 的日志系统，可以用 `jq` 或任何日志分析工具离线处理。

### 运行测试：任务集构建

验证需要一组可重复的测试任务。Jason Liu 指出<sup>[30]</sup>，公开 benchmark 缺乏足够长的 Agent 轨迹（trajectories），这是上下文管理评估的核心困难——你需要的不是"回答一个问题"，而是"在 50 轮对话中完成一个复杂任务"。

对企业办公场景，我设计三类测试任务：

**短任务（5-10 轮，测算法 1/4/5）：** 整理会议纪要、格式化报告、审批流程查询。这类任务不太可能触发压缩或螺旋，主要验证渐进式披露、缓存布局和回压是否降低了 token 消耗。

**中等任务（20-50 轮，测算法 2/3）：** 跨文档信息汇总、项目进展报告生成、多人邮件线程分析。这类任务会自然触发压缩，是测压缩质量和螺旋检测的主战场。

**长任务（100+ 轮，测全部算法）：** 大型文档审阅与修订、复杂项目排期规划、多轮谈判记录分析。只有这类任务能暴露上下文管理的极限情况。

每类至少 10 个任务，每个任务跑 3 次（控制随机性），总共 90+ 次实验。用 shell 脚本批量执行：

```bash
#!/bin/bash
# run_eval.sh — 批量执行评估任务
TASKS_DIR="./eval_tasks"
RESULTS_DIR="./eval_results/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

for config in full baseline no-disclosure no-compaction no-spiral; do
  for task in "$TASKS_DIR"/*.md; do
    for run in 1 2 3; do
      task_name=$(basename "$task" .md)
      echo "Running: $config / $task_name / run $run"
      # 用不同 opencode.json 配置运行
      OPENCODE_CONFIG="./configs/$config.json" \
      opencode run --input "$task" \
        2>&1 | tee "$RESULTS_DIR/${config}_${task_name}_${run}.log"
    done
  done
done
```

### 参考的业界基准

除了自建任务集，还可以参考以下公开基准进行交叉验证：

**Context-Bench<sup>[31]</sup>**（Letta, 2025.10）专注于长运行上下文的维护和推理能力，测试 Agent 能否跨多步骤工作流保持一致性。是最接近我们场景的公开 benchmark。

**SWE-bench Verified<sup>[32]</sup>** 是 Coding Agent 的标准基准。虽然是代码场景，但可以测试压缩和螺旋检测是否影响了基础代码能力——改进上下文管理不应该降低 baseline 性能。

**ACON 框架<sup>[12]</sup>** 提出了 failure-driven 的压缩评估方法：找到"完整上下文成功但压缩上下文失败"的配对案例，分析丢失了什么信息，然后改进压缩策略。这不是一次性测试，而是持续改进循环。

**ABBench<sup>[33]</sup>**（arXiv:2503.06745）是第一个针对 agentic system 可观测性的 benchmark，提出了执行流图编辑距离等新指标。虽然数据集只有 30 条日志，但方法论值得借鉴——特别是"被动分析→探索性分析→干预性分析"的三层分类。

---

## 参考文献

<small>

1. Shannon, C.E. (1948). A Mathematical Theory of Communication. [Wiley](https://onlinelibrary.wiley.com/doi/abs/10.1002/j.1538-7305.1948.tb01338.x)
2. Miller, G.A. (1956). The Magical Number Seven, Plus or Minus Two. [PubMed](https://pubmed.ncbi.nlm.nih.gov/13310704/)
3. Liu, N.F. et al. (2023). Lost in the Middle. [arXiv:2307.03172](https://arxiv.org/abs/2307.03172)
4. Wu, X. et al. (2025). On the Emergence of Position Bias in Transformers. ICLR 2025. [arXiv:2502.01951](https://arxiv.org/abs/2502.01951)
5. Zhang, Z. et al. (2024). Found in the Middle (Ms-PoE). [arXiv:2403.04797](https://arxiv.org/abs/2403.04797)
6. Chroma Research (2025). Context Rot. [research.trychroma.com](https://research.trychroma.com/context-rot)
7. Ponnusamy et al. (2025). Context Discipline and Performance Correlation. [arXiv:2601.11564](https://arxiv.org/abs/2601.11564)
8. RULER Benchmark. [arXiv:2404.06654](https://arxiv.org/abs/2404.06654)
9. Jiang et al. (2023). LLMLingua: Compressing Prompts for Accelerated Inference. [arXiv:2310.05736](https://arxiv.org/abs/2310.05736)
10. QUITO-X (2024). Context Compression from Information Bottleneck Theory. [arXiv:2408.10497](https://arxiv.org/abs/2408.10497)
11. Sentinel (2025). Context Compression via Attention Probing. [arXiv:2505.23277](https://arxiv.org/abs/2505.23277)
12. ACON (2025). Context Compression for Long-Horizon Agents. [arXiv:2510.00615](https://arxiv.org/abs/2510.00615)
13. PagedAttention / vLLM (2023). [arXiv:2309.06180](https://arxiv.org/abs/2309.06180)
14. FlashAttention-3 (2024). [arXiv:2407.08608](https://arxiv.org/abs/2407.08608)
15. Anthropic. Effective Context Engineering for AI Agents. [anthropic.com](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
16. Anthropic. Prompt Caching Guide. [platform.claude.com](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
17. LangChain (2026). Improving Deep Agents with Harness Engineering. [blog.langchain.com](https://blog.langchain.com/improving-deep-agents-with-harness-engineering/)
18. Piebald-AI. Claude Code System Prompts. [GitHub](https://github.com/Piebald-AI/claude-code-system-prompts)
19. Aider. Repository Map. [aider.chat](https://aider.chat/docs/repomap.html)
20. Block. Goose Smart Context Management. [GitHub](https://github.com/block/goose)
21. Letta (MemGPT). [GitHub](https://github.com/letta-ai/letta)
22. Simon Willison (2025). Context Engineering. [simonwillison.net](https://simonwillison.net/2025/jun/27/context-engineering/)
23. Böckeler / Fowler (2025). Context Engineering for Coding Agents. [martinfowler.com](https://martinfowler.com/articles/exploring-gen-ai/context-engineering-coding-agents.html)
24. Tishby, N. et al. (1999). The Information Bottleneck Method. [arXiv:physics/0004057](https://arxiv.org/abs/physics/0004057)
25. Anomaly. OpenCode: Open-source AI coding agent. [GitHub](https://github.com/anomalyco/opencode)
26. OpenAI. Codex: Open-source AI coding agent (Rust). [GitHub](https://github.com/openai/codex)
27. OpenAI. Compaction API Guide. [developers.openai.com](https://developers.openai.com/docs/guides/compaction)
28. badlogic. Context Compaction Strategies: Comparative Analysis. [GitHub Gist](https://gist.github.com/badlogic/cd2ef65b0697c4dbe2d13fbecb0a0a5f)
29. Factory AI (2025). Evaluating Context Compression Strategies for Long-Running AI Agent Sessions. [docs.factory.ai](https://docs.factory.ai/guides/power-user/evaluating-context-compression)
30. Jason Liu (2025). Two Experiments We Need to Run on AI Agent Compaction. [jxnl.co](https://jxnl.co/writing/2025/08/30/context-engineering-compaction/)
31. Letta (2025). Context-Bench: Benchmarking LLMs on Agentic Context Engineering. [letta.com](https://www.letta.com/blog/context-bench)
32. SWE-bench Verified. [epoch.ai](https://epoch.ai/benchmarks/swe-bench-verified)
33. Harari et al. (2025). Beyond Black-Box Benchmarking: Observability, Analytics, and Optimization of Agentic Systems. [arXiv:2503.06745](https://arxiv.org/abs/2503.06745)
34. OpenTelemetry (2025). AI Agent Observability - Evolving Standards and Best Practices. [opentelemetry.io](https://opentelemetry.io/blog/2025/ai-agent-observability/)
35. OpenCode. Plugins Documentation. [opencode.ai](https://opencode.ai/docs/zh-cn/plugins/)

</small>
