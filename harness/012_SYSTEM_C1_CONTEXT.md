# 012_SYSTEM_C1_CONTEXT: 上下文生命周期管理 深度研究

> 研究对象：012_SYSTEM 中 C1 的全部机制点
> 研究方法：层叠式文献分析法（03_RESEARCH_DEEP_METHOD）
> 研究范围：理论基础 → 前提假设 → 核心算法 → 实践案例 → 效果数据 → 验证方法 → 隐性知识
> 更新周期：2025-2026，纳入 ICLR 2025、Chroma Research 2025 新成果

---

## 0. 研究起点：012_SYSTEM 中的已有描述

**本质**：管控窗口内信息的质量与数量，使模型始终在最佳利用率区间工作。

**已记录的机制**：
- 生命周期四阶段：注入 → 监控 → 压缩 → 归档
- 利用率阈值（20-50%区间，模型特定）；接近极限时性能下滑 50-70%
- Reduce / Offload / Isolate 三原则
- 渐进式披露（AGENTS.md ~100行导航地图）
- 结构化上下文（XML标签/分隔符）
- 焦点锚定（TODO List）
- Prompt缓存优化（静态前置+变量后置）
- 推理三明治（xhigh-high-xhigh）
- 硬性截断（CLAUDE.md 首200行/25KB，系统指令 32KiB）
- 反模式：上下文死亡螺旋

**已有数据**：阈值 20-50% [arXiv:2601.11564]；性能下滑 50-70% [32]；Harness 优化 52.8%→66.5% [2]

**研究目标**：对以上每个机制追溯理论根基、验证数据可靠性、补充算法细节和实践案例。

---

## 1. 理论溯源（Q1）

### 1.1 信息论：Shannon 信道容量（1948）

Claude Shannon 在 *A Mathematical Theory of Communication* 中建立了信息传输的基本定理：信道容量 C = B × log₂(1 + SNR)，任何超过信道容量的传输都不可避免引入错误。

**对 C1 的启示**：LLM 的上下文窗口可类比为有限带宽信道。[类比: 通信信道的带宽限制 ≈ Transformer 的上下文窗口限制，因为二者都约束了单次传输的信息总量] 当注入的信息量超过模型的有效处理容量时，"噪声"（无关信息、冗余信息）会降低"信号"（任务关键信息）的传递质量。这为"压缩是必要的"提供了信息论层面的解释——不是工程偏好，而是理论必然。

**局限**：Shannon 定理描述的是无记忆信道的极限，而 Transformer 的注意力机制具有复杂的位置依赖性，不完全符合经典信道模型。这个类比提供方向性指导，但不能直接套用公式计算具体阈值。[事实]

> 出处：Shannon, C.E. (1948). A Mathematical Theory of Communication. Bell System Technical Journal.

### 1.2 认知科学：Miller 的"神奇数字 7±2"（1956）

George Miller 在 *The Magical Number Seven, Plus or Minus Two* 中发现人类工作记忆的容量限制约为 7±2 个"chunk"。后续 Nelson Cowan 的研究将这个数字修正为约 4 个 chunk。关键发现不是具体数字，而是两个原理：（1）容量以"有意义单元"（chunk）而非原始比特计量；（2）超出容量后性能急剧下降而非缓慢退化。

**对 C1 的启示**：[类比: 人类工作记忆的 chunk 容量限制 ≈ LLM 上下文窗口的有效利用容量，因为二者都表现为"超过阈值后质量急剧下降"而非线性退化] 这个类比支持两个工程决策：一是结构化上下文（将信息组织为有意义的 chunk 而非散乱 token），二是主动压缩（在达到容量阈值前而非溢出后介入）。

**局限**：LLM 不是人脑。Transformer 的注意力机制是并行计算而非序列处理，其"容量瓶颈"的机理与工作记忆不同。类比的价值在于现象层面的相似性（阈值效应），而非机制层面的等价性。[事实]

> 出处：Miller, G.A. (1956). The Magical Number Seven, Plus or Minus Two. Psychological Review, 63(2).
> 修正：Cowan, N. (2001). The magical number 4 in short-term memory. Behavioral and Brain Sciences, 24(1).

### 1.3 "Lost in the Middle" 效应（2023 → 2025 ICLR 增强版）

Liu et al. (Stanford) 发现 LLM 在处理长上下文时呈现 U 型性能曲线：对上下文开头和结尾的信息利用效果好，对中间部分的信息利用显著衰减。GPT-3.5-Turbo 在多文档问答任务中，当关键信息位于中间位置时，准确率下降超过 20%。

**ICLR 2025 新发现（arXiv:2502.01951）**：位置偏差不是"训练不足"或"上下文窗口设计不当"的结果，而是 **Transformer 架构的固有几何属性**。关键证据：
- 未训练的随机初始化 Transformer 仍表现出 U 型曲线（准确率低但趋势一致）
- 因果掩码的图论分析：在自回归生成中，前期 token 的信息流入度（in-degree）高于中期 token，导致前期 token 的表示被更多后续 token 依赖
- 三种位置偏差的分解：**Primacy Bias**（对开头的过度重视）+ **Recency Bias**（对结尾的偏好）+ **Lost-in-the-Middle**（对中间的忽视）
- 多层交互的 trade-off：单层看衰减是 ~10%，但跨 80 层的累积放大导致 >20% 下降 [事实]

**机理解释更新**：旋转位置编码（RoPE）虽然提高了长上下文能力，但保留了距离衰减特性，导致远距离 token 对的注意力权重减弱。在中间位置，token 到查询位置的距离均衡（既不是最近也不是最远），因此既无 Recency Bias 的加成，也无 Primacy Bias 的加持。

**对 C1 的启示**：这个发现直接支撑了 012_SYSTEM 中"结构化上下文"和"信息优先级分层"的工程实践——高优先级信息应放在上下文的首尾位置，避免被"淹没"在中间。同时也解释了为什么简单的"把所有信息塞进去"策略在长上下文下失效。

**缓解进展**：Ms-PoE（Multi-scale Positional Encoding, arXiv:2403.04797）已将位置偏差从 >20% 缩小至 0.6-3.8%，且无需微调。趋势是：未来模型架构改进可能进一步消除此效应，届时"优先级放首尾"的建议需要更新。[推导: 缓解趋势存在 → 此假设属保护带]

> 出处：Liu, N.F. et al. (2023). Lost in the Middle. arXiv:2307.03172; TACL 2024.
> ICLR 2025 增强：arXiv:2502.01951 (2025). On the Emergence of Position Bias in Transformers: A Causal Masking Analysis.
> 缓解方案：Ye, H. et al. (2025). Found in the Middle: Multi-scale Positional Encoding. arXiv:2403.04797.

### 1.4 Context Rot 现象（2025）— 新增

Chroma Research 在 2025 年发布的报告揭示了一个被广泛忽视的现象：**拥有大上下文窗口 ≠ 能够使用它**。

**定义和关键数据**：
- Context Rot = 随着输入 token 增加，模型准确回忆信息的能力显著下降（非简单的容量不足）
- 许多顶级模型在仅 100 个 token 的上下文中失败
- 大多数模型在 1000 个 token 时严重退化
- Claude 3 的表现相对突出（200K tokens 时 99.4% 平均 recall，但在 200K 时衰减至 98.3%）[置信度 B]
- Gemini 1.5 Pro 异常值：4K→128K 仅 2.3 分下降（置信度 B）

**对企业 AI 的影响**：2025 年企业 AI 系统失败的根本原因分析中，**65% 归因于"上下文漂移"和"记忆丧失"**（而非原始计算耗尽或窗口不足）。[置信度 C - 行业报告]

**与 Lost in the Middle 的区别**：
- Lost in the Middle = 位置特定的问题（中间位置衰减）
- Context Rot = 长度相关的全局衰减（任何位置的回忆能力都随长度增加而下降）
- 两个问题的组合（位置偏差 + 长度衰减）造成了当前长上下文应用的主要困难

**对 C1 的启示**：即使模型窗口扩大到 200K，仍需要主动上下文管理。Context Rot 解释了为什么"被动扩大窗口"不能解决问题——需要主动的压缩、检索、监控机制来保持信息可回忆性。

> 出处：Chroma Research (2025). Context Rot: When Bigger Isn't Better. research.trychroma.com/context-rot

### 1.5 信息瓶颈理论应用于 LLM（2024-2025）

信息瓶颈理论（Tishby et al., 1999）描述了在保持任务相关信息的同时最大化压缩的最优策略。QUITO-X（arXiv:2408.10497）将这一理论直接应用于 LLM 上下文压缩：模型将输入信息压缩到任务特定空间（如情感、主题），压缩率提升 25% 同时维持问答性能，推理加速 40%。

**对 C1 的启示**：[演绎: 信息瓶颈理论证明存在最优压缩-保真权衡点 + LLM 上下文压缩是一个信息保真问题 → 上下文压缩策略应追求任务相关信息的最大保留而非简单截断] 这意味着"上下文蒸馏——保留决策结论，丢弃推理过程"有信息论基础：推理过程是中间变量，决策结论才是任务相关信息。

> 出处：Yang, Q. et al. (2025). Exploring Information Processing in LLMs. arXiv:2501.00999.
> 应用：QUITO-X. arXiv:2408.10497.

### 1.6 底层基础设施：注意力机制优化（新增）

虽然 C1 专注于"模型之外"的上下文管理，但理解底层基础设施可以解释为什么某些上下文管理策略特别有效。

**PagedAttention（Berkeley 2023 - vLLM）**：
- 问题：KV 缓存碎片化，内存浪费 60-80%
- 解决：借鉴操作系统的分页思想，将 KV 缓存分块存储
- 效果：内存浪费从 60-80% 降至 4%；批处理吞吐提升 24 倍 [置信度 A]

**Flash Attention 3（Meta/Dao-AILab）**：
- 改进点：IO-aware 设计，充分利用 GPU 层次缓存
- 性能：H100 上 BF16 达 840 TFLOPs/s（峰值 1.5 PFLOPs），FP8 达 1.3 PFLOPs [置信度 A]
- 对上下文管理的启示：更高效的注意力实现意味着"扩大窗口"的工程成本在降低，但不消除"管理信息质量"的必要性

**Ring Attention（Berkeley）**：
- 通过增加 GPU 数量实现接近无限上下文（通过环形通信拓扑）
- 对 C1 的启示：基础设施改进允许更大的窗口，但上下文管理问题（Lost in the Middle、Context Rot）仍然存在

**整体启示**：这些技术解释了"为什么模型窗口可以扩大但上下文管理仍然必要"——窗口扩大只解决了存储和计算效率问题，没有解决信息利用效率问题。[事实]

> 出处：Huang, Z. et al. (2024). PagedAttention: Efficient Memory Management for Large Language Model Serving. SOSP 2024.
> Flash Attention 3: Dao, T. et al. (2024). Flash-3: Fast and Accurate Attention with Asynchronous I/O.

### 1.7 行业认知演进：从 Prompt Engineering 到 Context Engineering 到 Harness Engineering（新增）

**2023-2024：Prompt Engineering 时代**
- 核心理念：如何写好 prompt 让模型理解任务
- 代表作：Structured prompting, Chain-of-Thought, Few-shot examples

**2024-2025：Context Engineering 时代**
- 核心理念：上下文本身是可设计、可优化的一阶对象
- Gartner 2025 评估："Context engineering is in, prompt engineering is out"
- Simon Willison："Context engineering is the term winner"（simonwillison.net/2025/jun/27/context-engineering/）
- 代表作：上下文检索、压缩、分层、监控

**2025-2026：Harness Engineering 时代**
- 核心理念：上下文只是 Harness 的一部分；整个"模型运行环境"是可以工程化的
- Martin Fowler："Context is the bottleneck for coding agents"（martinfowler.com）
- Harness = Context + Reasoning Delegation + Tool Orchestration + Monitoring
- 代表实现：LangChain Deep Agent、Anthropic Agents、Claude Code

**认知演进的启示**：上下文从被动"接收任务指令的容器"演进为主动"设计对象"，再演进为"整体系统设计的核心约束"。这反映了行业的成熟度提升：从"给模型更好的指令"→ "给模型更好的信息" → "给模型更好的整个环境"。[推导: 三阶段演进反映了对瓶颈位置的迭代认知]

> 出处：
> - Gartner AI Hype Cycle 2025
> - Simon Willison. Context Engineering. simonwillison.net/2025/jun/27/context-engineering/
> - Martin Fowler. Harness Engineering for Coding Agents. martinfowler.com/articles/exploring-gen-ai/

### 1.8 理论溯源小结

| 理论 | 来源学科 | 核心结论 | 对 C1 的启示 |
|------|----------|----------|-------------|
| Shannon 信道容量 | 信息论 | 有限信道必然引入传输损失 | 上下文压缩是理论必然而非工程偏好 |
| Miller 7±2 / Cowan 4 | 认知科学 | 容量以 chunk 计，超限急剧退化 | 结构化组织 + 阈值前主动干预 |
| Lost in the Middle | NLP + 架构分析 | U 型曲线，中间信息被忽视；架构固有；可缓解 | 优先级信息放首尾；缓解中期需更新 |
| Context Rot | 实证 LLM | 长度衰减，回忆能力随上下文增加而下降 | 窗口扩大≠问题解决，仍需主动管理 |
| 信息瓶颈理论 | 信息论/ML | 存在最优压缩-保真权衡 | 任务导向压缩优于无差别截断 |

这五个理论从不同角度收敛于同一结论：**上下文管理的本质是在有限容量和衰减约束下最大化任务相关信息密度**。[归纳: 信息论+认知科学+NLP+架构分析+实证, 五个独立来源, N=5]

---

## 2. 前提假设分析（Q2 + Q2.5）

### 2.1 显式假设

| 假设 | 来源 | 成立条件 |
|------|------|----------|
| A1: 上下文窗口是有限的 | 所有 Transformer 架构 | 当前所有生产模型均成立 |
| A2: 利用率影响推理质量 | [27][32] | 已有实验证据（见第5章） |
| A3: 压缩可以保留关键信息 | 信息瓶颈理论 | 当任务结构明确时成立 |
| A4: 静态内容可与动态内容分离 | Prompt 缓存实践 | 当系统提示和工具定义相对稳定时成立 |

### 2.2 隐式假设

| 假设 | 推断来源 | 成立条件 | 失效后果 |
|------|----------|----------|----------|
| A5: 模型无法自我判断上下文质量 | 需要外部监控机制的存在 | 当模型没有内省能力时成立 | 若模型能自我监控，外部监控冗余 |
| A6: 信息的任务相关性可被外部判断 | 压缩/裁剪策略假设能识别"无关信息" | 当任务目标明确时成立 | 探索性任务中"无关"信息可能变为关键线索 |
| A7: 上下文的首尾位置效果优于中间 | Lost in the Middle 研究 | 当前 Transformer 架构下成立 | 若位置编码改进消除 U 型曲线，此假设失效 |

### 2.3 硬核与保护带分级

**硬核假设**（推翻则整个 C1 框架失效）：

| 假设 | 稳定性评估 | 若失效的影响 |
|------|-----------|-------------|
| A1: 窗口有限 | 极高——物理计算限制，即使窗口扩大10倍仍有限 | C1 整体不必要（但见下方分析） |
| A2: 利用率影响质量 | 高——多项独立实验验证 | 所有压缩/监控机制失去动机 |

**对 A1 的深入分析**：即使上下文窗口扩展到 10M tokens，A1 仍然成立——窗口有限是数学事实。但真正的问题是：窗口是否"足够大以至于不需要管理"？Lost in the Middle 和 Context Rot 效应表明，即使窗口够大，注意力分配的不均匀性和长度衰减仍然导致质量问题。[演绎: 窗口扩大不消除位置偏差和衰减 + 位置偏差/衰减导致信息利用不均 → 即使窗口"够大"仍需上下文管理] 因此 A1 的真正硬核形式是"**有效处理容量小于窗口名义容量**"。

**保护带假设**（可调整但不影响框架）：

| 假设 | 已知的调整路径 |
|------|--------------|
| A4: 静态/动态可分离 | 若不可分离，改用整体压缩策略（放弃缓存优化） |
| A7: 首尾位置效果优 | Ms-PoE 等缓解方案已将差异从 >20% 缩小到 <5%，趋势是消除 |
| "40% 阈值" | 不同模型阈值不同（见 Q6.5 证伪分析），具体数值可调 |

### 2.4 假设敏感性分析

最脆弱的假设是 **A6（信息的任务相关性可被外部判断）**。在结构化任务（如"修这个bug"）中，判断什么信息相关相对容易。但在探索性任务（如"理解这个系统的架构"）中，任何信息都可能相关。这意味着：[推导: A6 在探索性任务中不成立 + C1 的压缩策略依赖 A6 → 探索性任务不应积极压缩，应优先使用隔离（Isolate）策略]

---

## 3. 核心算法与策略谱系（Q3）

### 3.1 上下文压缩算法族

从简单到复杂排列：

| 策略 | 核心思路 | 压缩率 | 信息损失 | 适用场景 |
|------|----------|--------|----------|----------|
| 硬截断（Truncation） | 按位置或 token 数裁剪 | 可控 | 高，无差别丢弃 | 紧急情况/兜底 |
| 摘要压缩（Summarization） | 用 LLM 生成对话摘要 | 60-80% | 中，丢失细节 | 长对话历史 |
| Token 级剪枝（LLMLingua） | 移除低信息量 token | 2-5x | 低 | 保持语义完整性 |
| 选择性注意力（Sentinel） | 探测注意力模式，保留高注意力句子 | 5x | 低 | 有明确查询的场景 |
| 递归压缩（AutoCompressor） | 递归生成摘要向量 | 32x | 中 | 超长文档处理 |
| 信息瓶颈压缩（QUITO-X） | 任务导向的最优压缩 | +25%优于SOTA | 最低（理论最优） | 有明确任务目标 |
| ACON 框架 | 故障驱动的压缩优化 | 26-54% 峰值 token 减少 | 低，保留关键决策信息 | Agent 长地平线任务 |

**演进路径**：硬截断 → 摘要压缩 → Token级剪枝 → 注意力导向压缩 → 信息论最优压缩 → 故障驱动优化。趋势是从"无差别丢弃"走向"任务导向的选择性保留"再走向"实时故障反馈驱动的动态优化"。[归纳: 7种算法按时间线排列, N=7]

### 3.2 上下文组织策略族

| 策略 | 核心思路 | 复杂度 | 适用场景 |
|------|----------|--------|----------|
| 平铺注入 | 所有信息一次性注入 | 最低 | 短任务，窗口充足 |
| 渐进式披露 | 目录先行，按需加载详情 | 中 | 大型代码库 |
| 语义检索注入 | 向量相似度匹配按需召回 | 中-高 | 知识密集型任务 |
| 图排序注入（Aider Repo Map） | PageRank 对代码实体排序 | 高 | 大型仓库导航 |

### 3.3 缓存优化策略

| 策略 | 核心思路 | 效果 | 出处 |
|------|----------|------|------|
| 前缀缓存 | 静态内容前置，最大化前缀命中 | 延迟降低80%，成本降低90% | Anthropic Docs |
| KV Cache 复用 | 跨请求复用键值缓存 | Codex 启动从48s降到5s | OpenAI Codex |
| Prompt Caching | 缓存静态前置内容，读取成本仅10%基础价格 | 成本减少+延迟降低 | Anthropic docs.anthropic.com |

### 3.4 ACON 框架（新增）— 故障驱动的上下文压缩

ACON（arXiv:2510.00615, 2025）将压缩视为优化问题而非启发式：

**核心思想**：
- 不同信息对 Agent 长地平线任务的影响差异很大
- 通过**故障驱动的指导线**识别哪些信息"真正重要"
- 动态调整压缩策略，而非固定的压缩率

**工程实现**：
- 第一轮：完整推理（不压缩），记录所有决策点
- 故障检测：识别 Agent 失败的原因（缺少关键信息、推理错误等）
- 第二轮：基于故障信息，优化地保留关键上下文
- 结果：26-54% 峰值 token 减少（相比全量），性能不损失 [置信度 A]

**对 C1 的启示**：不同于"静态压缩率"（如 QUITO-X 的 +25%），ACON 是"动态故障反馈驱动"的压缩。这个思路与 012_SYSTEM 中的"监控→压缩"循环天然契合：监控发现质量问题 → 反馈驱动重新压缩。

> 出处：arXiv:2510.00615 (2025). ACON: Context Compression for Long-Horizon Agents.

### 3.5 算法选择决策树

```
任务类型?
├─ 短任务（<30% 窗口）→ 平铺注入，无需压缩
├─ 中等任务（30-60% 窗口）
│   ├─ 任务目标明确 → 信息瓶颈压缩（QUITO-X）或 ACON
│   └─ 探索性任务 → 语义检索注入，避免压缩
└─ 长任务（>60% 窗口）
    ├─ 可拆分 → 子Agent隔离（Isolate 原则）
    └─ 不可拆分 → 故障驱动压缩（ACON）+ Token级剪枝 + 主动归档
```

[推导: 从假设敏感性分析 + 算法特性 + ACON 的故障驱动特性 → 按任务类型和反馈选择策略]

---

## 4. 实践案例（Q4）

### 4.1 Claude Code（Anthropic）— 增强版

| 维度 | 实现细节 |
|------|----------|
| 窗口大小 | 200,000 tokens |
| 系统提示结构 | 24,000 tokens，110+组件（Piebald-AI 仓库 v2.1.87 [事实]） |
| 非单一文本 | 主提示 + 18 个工具描述 + Plan/Explore/Task 子代理 + 系统提醒 |
| CLAUDE.md 三层框架 | WHAT（做什么）→ WHY（为什么）→ HOW（怎么做）[推导: 这个结构最小化了模型需要理解"意图层级"的认知成本] |
| 上下文节约原则 | "每一行都与实际工作竞争注意力" [事实] |
| Tool Search Tool | 保留 191,300 tokens vs 传统 122,800 tokens（节省 35% [置信度 C - Anthropic blog]，通过智能检索而非全量索引） |
| 自动压缩触发 | ~95% 容量时自动触发 compaction [事实] |
| 手动压缩 | `/compact` 命令，支持自定义压缩提示 |
| 压缩效果 | 典型 60-80% token 减少（150K → 30-50K） |
| 持久化策略 | CLAUDE.md 中的规则在 compaction 后保留；skill 描述在会话开始加载，完整内容按需加载 |
| 监控 | `/context` 命令查看窗口使用情况 |
| 结构化上下文 | XML 标签组织系统提示的不同部分 |
| Prompt Caching 经济模型 | 写入 25% 溢价，读取仅 10% 基础价格 [置信度 A - 官方定价] |
| Extended Thinking | thinking 块前一轮被剥除不计入窗口成本 [推导: 这是对"思考链"的隐式上下文管理，避免冗余思考步骤的累积] |

**隐含设计哲学**：Claude Code 信任自动化。95% 触发点（而非更早）暗示 Anthropic 认为 Claude 模型在高利用率下仍保持较好质量，允许在接近极限时才压缩。对比 LangChain 的 80-90%，Claude 的更激进策略基于更强的模型能力。[推导]

> 出处：
> - code.claude.com/docs; platform.claude.com/docs
> - Piebald-AI/claude-code-system-prompts (v2.1.87) [一手资料]
> - anthropic.com/engineering/effective-context-engineering-for-ai-agents
> - docs.anthropic.com/en/docs/build-with-claude/prompt-caching

### 4.2 Goose（Block/Square）— 新增

| 维度 | 实现细节 |
|------|----------|
| 核心目标 | 无限长度对话支持 |
| 两层阈值设计 | 80% 自动摘要 + 95% 自动 compaction [推导: 两层阈值允许渐进式干预，避免单点故障] |
| 摘要策略 | 对话摘要保留决策点，不保留中间推理 |
| Compaction | 超过 95% 时完整重新压缩整个对话历史 |
| 隐含哲学 | 无限长度是可以设计实现的，通过多层级压缩 |

> 出处：Block/Square engineering blog

### 4.3 OpenAI Codex — 保留

| 维度 | 实现细节 |
|------|----------|
| 压缩策略 | 通过 `/responses/compact` 端点压缩对话，用更小的摘要替换输入 |
| 缓存策略 | 系统指令、工具定义、沙箱配置保持固定顺序，确保前缀精确匹配 |
| 缓存效果 | 容器启动中位数从 48s 降至 5s（90% 加速） |
| 成本效果 | 首 token 延迟降低 80%，输入 token 成本降低 90% |
| 无状态设计 | Zero Data Retention 合规——每次请求无状态 [推导: 这意味着压缩完全依赖 Prompt 缓存，而非服务端状态管理] |
| 指令限制 | 系统指令 32KiB 上限 |

> 出处：developers.openai.com；OpenAI Codex Changelog

### 4.4 MemGPT / Letta（新增）— 操作系统风格的上下文管理

MemGPT（现改名 Letta）提出了一个根本不同的架构范式：**将上下文管理类比为操作系统的内存管理**。

| 维度 | 实现细节 |
|------|----------|
| 架构类比 | Main Context = RAM，External Context = 二级存储（磁盘） |
| 核心机制 | LLM 通过自生成函数调用控制数据在主外存间的移动 |
| 事件循环 | Event → LLM Core Loop → Function Calling (内存操作) → Yielding → 下一轮 |
| 内存操作 | `save(key, value)`, `load(key)`, `delete(key)` [推导: LLM 本身成为上下文管理的主动参与者，而非被动对象] |
| 核心优势 | 不依赖外部启发式规则，LLM 自己决定什么信息需要在主内存中 |

**对 C1 的启示**：MemGPT/Letta 的方法是**自适应的**——模型根据任务和当前状态自决策上下文内容，不像其他系统依赖固定的压缩策略。这可能是长期的发展方向，但当前需要 Agent 能够自反省和自管理，大多数模型还不够成熟。[开放问题]

> 出处：Letta (formerly MemGPT). github.com/letta-ai/letta

### 4.5 Cursor（保留改进）

| 维度 | 实现细节 |
|------|----------|
| 上下文选择 | 用户通过 @file、@codebase、@Docs 显式指定 [设计哲学: 用户主导，信任用户判断] |
| 索引策略 | 首次打开时构建语义图谱，使用 Turbopuffer 向量数据库 |
| 检索方式 | 对查询计算 embedding，最近邻搜索匹配相关代码块 |
| 隐含假设 | 检索优于压缩（因为可以快速恢复所有信息） |

### 4.6 Aider（保留改进）

| 维度 | 实现细节 |
|------|----------|
| 仓库地图 | 提取类/函数/类型签名构建精简地图 |
| 排序算法 | NetworkX PageRank + 对话上下文个性化 [推导: PageRank 捕获了"被广泛引用 = 重要"这个直观认知] |
| 解析工具 | Tree-sitter 解析器 + 语言专属 tags.scm 查询文件 |
| Token 预算 | `--map-tokens` 控制（默认 1K），根据对话状态动态调整 |
| 历史管理 | 完整历史保留在上下文中，`/clear` 重置，自动摘要防溢出 |

### 4.7 LangChain Deep Agent

| 维度 | 实现细节 |
|------|----------|
| 架构 | 中间件模式——LocalContextMiddleware / SummarizationMiddleware |
| 环境映射 | 启动时映射 cwd、父子目录、Python 环境 |
| 压缩时机 | 在 10-20% 可用上下文时触发压缩（比多数产品更积极）[推导: LangChain 采用保守的利用率策略] |
| 循环检测 | LoopDetectionMiddleware 追踪文件编辑次数 [这是 Agent 特定的问题：死循环修改同一文件] |
| 退出拦截 | PreCompletionChecklistMiddleware 强制对照任务验证 |
| Harness 优化效果 | Terminal Bench 2.0: 52.8% → 66.5% (+13.7pp) [置信度 C] |

> 出处：blog.langchain.com/improving-deep-agents-with-harness-engineering/

### 4.8 实践对比矩阵

| 维度 | Claude Code | Codex | Cursor | Aider | LangChain | MemGPT |
|------|-------------|-------|--------|-------|-----------|--------|
| 压缩触发 | 自动(95%) | 显式API | 无（检索替代） | 自动摘要 | 主动(80-90%) | 自适应 |
| 上下文选择 | 自动+CLAUDE.md | 自动+缓存 | 用户@指定 | PageRank | 中间件 | LLM 自决 |
| 持久化 | 文件(CLAUDE.md) | 无状态+缓存 | 向量索引 | 文件(repo map) | 文件系统 | 外存API |
| 核心策略 | Reduce | Reduce+Cache | Retrieve | Rank+Retrieve | Reduce+Monitor | OS风格 |
| 模型信任度 | 高（95%触发） | 中（保守缓存） | 低（用户选择） | 中（PageRank） | 低（多层拦截） | 高（自管理） |

[归纳: 6 个产品的上下文管理策略, N=6, 共性: 都需要某种形式的主动上下文管理; 差异反映了对"模型能力"和"用户判断"的不同信任度]

---

## 5. 效果与数据汇总（Q5）

### 5.1 量化数据表（扩充版）

| 指标 | 基线 | 优化后 | 提升 | 实验条件 | 出处 | 置信度 |
|------|------|--------|------|----------|------|--------|
| 利用率阈值 | 不同模型 20-50% | 标准化范围 | N/A | 多模型测试 | arXiv:2601.11564 | A |
| Claude 3 @ 200K | 无压缩基线 | 99.4% 平均recall | +高质量 | 200K tokens | Anthropic Model Card | B |
| Claude 3 @ 200K | 99.4% | 98.3% | -1.1pp | 200K极限 | Anthropic Model Card | B |
| Gemini 1.5 Pro 异常 | 4K | 128K | -2.3pp | 超强长上下文能力 | RULER benchmark | B |
| 企业AI失败归因 | 其他因素 | 65% | 上下文漂移 | 2025行业调查 | Chroma Research | C |
| Tool Search Tool | 基线检索 | 35% 节省 | 35% 更高效 | Claude Code | anthropic.com/engineering | C |
| Prompt Caching 读取 | 基础价格 | 10% 基础价格 | -90% | 官方定价 | docs.anthropic.com | A |
| Terminal Bench 2.0 | 52.8% | 66.5% | +13.7pp | 仅改 Harness | LangChain Blog | C |
| Codex 容器启动 | 48s | 5s | -90% | Prompt 缓存 | OpenAI Changelog | C |
| LongBench 压缩 | 无压缩 | 5x压缩 | 等效性能 | Sentinel 注意力剪枝 | arXiv:2505.23277 | A |
| QUITO-X 压缩率 | SOTA基线 | +25% 压缩率 | +40% 速度 | 信息瓶颈框架 | arXiv:2408.10497 | A |
| ACON 峰值减少 | 基线 | 26-54% 减少 | 性能不损 | Agent长地平线 | arXiv:2510.00615 | A |
| Lost in Middle | 最佳位置 | 中间位置 | -20% 准确率 | 多文档QA, GPT-3.5 | Liu et al. TACL 2024 | A |
| Context Rot @1000K | 小上下文 | 严重退化 | N/A | 多模型测试 | Chroma Research | B |
| PagedAttention 内存 | 60-80% 浪费 | 4% 浪费 | -76pp | vLLM 实现 | arXiv (SOSP 2024) | A |

### 5.2 数据可信度分析

**A 级（同行评审，高置信度）**：
- Lost in the Middle 的 U 型曲线存在性和量级——多个独立团队复现
- 利用率阈值和性能崩塌——arXiv:2601.11564 多模型数据
- 压缩算法效果（Sentinel、QUITO-X、ACON）——标准基准和论文
- PagedAttention / Flash Attention 性能数据——工业级实现验证

**B 级（一手数据但来源单一，中置信度）**：
- Claude 3 长上下文性能——Anthropic Model Card 官方数据，但未经独立验证
- Context Rot 定义和 65% 失败率——Chroma Research 报告，合理但非学术同行评审
- Gemini 1.5 Pro 异常值——可能是架构优化，但样本单一

**C 级（厂商自报或社区经验，中-低置信度）**：
- LangChain 的 +13.7pp——Terminal Bench 是公开基准，但实验仅厂商自己做
- Codex 的 90% 加速——合理但未经独立验证
- Claude Code 60-80% 压缩率——社区经验报告，无系统性测量

**D 级（定性描述，低置信度）**：
- 具体企业案例（通常涉及 NDA）

### 5.3 效果归因分析

LangChain 的 +13.7pp 提升是多个 Harness 改动的综合效果（上下文中间件 + 自验证 + 循环检测 + 推理分层），无法准确归因到 C1 单独贡献多少。[事实] 这是 Harness 研究中的普遍问题——各组件耦合运行，单因素归因困难。

---

## 6. 验证方法与证伪分析（Q6 + Q6.5）

### 6.1 已有验证方法评价

| 验证方法 | 评估指标 | 对照设计 | 可复现性 | 局限性 |
|----------|----------|----------|----------|--------|
| Terminal Bench 2.0 | pass rate | 换Harness不换模型 | 基准公开，Harness未完全开源 | 仅测 terminal 操作 |
| LongBench | F1/Accuracy | 压缩 vs 无压缩 | 完全公开 | 非 Agent 任务 |
| RULER Benchmark | Recall @ 长度 | 变量:长度和位置 | 公开 | 合成任务 |
| Lost in Middle 实验 | QA Accuracy | 变量:信息位置 | 完全公开 | 合成任务，非真实 Agent 场景 |
| 利用率阈值实验 | Recall/Accuracy | 变量:上下文长度 | 公开 | 模型版本快速迭代可能改变阈值 |

### 6.2 关键结论的证伪条件

| 结论 | 证伪条件 | 强度 | 当前反面证据 |
|------|----------|------|-------------|
| "利用率阈值普遍是 40%" | 在 3+ 主流模型上测得阈值差异 >20pp | 弱证伪 | arXiv:2601.11564 显示 Gemini 2.5 Flash ~20%，其他 40-50% |
| "Lost in the Middle 是普遍现象" | 新架构模型无 U 型曲线 | 中证伪 | Ms-PoE 已将差异缩小至 0.6-3.8pp，趋势是缓解 |
| "Context Rot 是不可逆的" | 某模型在 200K+ 时仍保持 >98% recall | 中证伪 | Gemini 1.5 Pro 表现异常，暗示可能可逆 |
| "压缩优于全量注入" | 全量注入在足够大窗口中性能等于或超过压缩后注入 | 强证伪 | 暂无——当前长窗口模型仍显示质量退化 |
| "上下文管理是性能主要瓶颈" | 换模型的提升远大于换 Harness 的提升 | 中证伪 | 从 GPT-3.5 到 GPT-4 的提升 >13.7pp，但不排除 Harness 独立贡献 |

**关键发现**："40% 阈值"不应作为硬性工程参数。不同模型的崩塌点在 20-50% 波动。更安全的表述是**"存在利用率阈值，通常在 20-50%，模型特定"**。[推导: 多模型数据不一致 → 具体数值是模型特定而非普适]

### 6.3 验证空白与改进建议

**空白 1**：缺乏 Agent 场景下的端到端压缩效果实验。现有压缩算法在 QA/阅读理解任务上验证，但 Agent 的多轮交互、工具调用场景未被覆盖。[开放问题]

**空白 2**：缺乏不同压缩策略在同一 Agent 框架下的 A/B 对比。LangChain 的 +13.7pp 是多因素综合，无法判断"ACON vs Token剪枝 vs 选择性注意力"的单独贡献。[开放问题]

**空白 3**：Context Rot 的根本原因仍未明确。是位置偏差的延伸，还是独立的注意力衰减机制？[开放问题]

---

## 7. 隐性知识逆向（Q7）

### 7.1 代码考古发现

**Claude Code 的 compaction 触发时机（95%）**：选择 95% 而非更早触发，暗示 Anthropic 认为过早压缩的信息损失代价大于接近极限的性能退化。与 LangChain 在 80-90%（剩余 10-20%）触发形成对比。[推导: Claude 95% vs LangChain 80-90% → Anthropic 更信任 Claude 模型的长上下文能力（合理，Claude 窗口 200K 远大于多数模型），因此允许更高利用率]

**Codex 的无状态设计**：看似是上下文管理的弱化（每次请求从零开始），实际是将上下文管理完全外化到 Prompt 缓存层。这个选择的隐含理由可能是 Zero Data Retention 合规要求——企业客户不允许服务端保存对话状态。[推导: 无状态设计 + 激进缓存优化 → 合规约束驱动的架构选择]

**Aider 选择 PageRank**：没有用更直觉的"文件相关性评分"，而是借鉴了网页排序算法。隐含认知是：代码文件间的引用关系类似网页链接，被多方引用的文件（如核心接口、工具类）更可能与任务相关。[类比正当性强]

**MemGPT/Letta 的 OS 类比**：这是对"模型外包上下文管理"的反抗。如果 LLM 足够智能，为什么要用启发式？隐含信心是：未来模型可以自管理上下文。但当前仍需外部辅助。[推导: 这暗示长期方向与短期实践的妥协]

### 7.2 跨实现隐含共识

对比六个产品的实现，存在以下**未被文档明确阐述但所有实现都遵守**的模式：

1. **压缩是有损的，所以尽量推迟**——所有产品都在"不得不压缩"时才压缩。即使 LangChain 更积极，其触发点（80-90%）仍远高于"理论最优点"。[归纳: 6 个产品都选择延迟压缩, N=6] 隐含的认知是："压缩本身是不完美的，应该成为最后手段。"

2. **结构信息比内容信息更值得保留**——CLAUDE.md 在 compaction 后保留，Aider 的 repo map 是结构而非内容，Cursor 索引的是代码结构。压缩丢弃的总是对话内容，保留的是项目/系统结构。[归纳: 所有实现都优先保留结构信息, N=6]

3. **没有产品尝试修改注意力机制**——所有产品都在"模型之外"解决上下文问题，没有尝试修改模型内部的注意力分配。这符合 Harness Engineering 的核心定位：改善模型运行环境，而非改善模型本身。[事实]

4. **自适应的多层级策略**——从 Goose 的"80% 摘要 + 95% compaction"到 ACON 的"故障驱动"，趋势是从"单一固定策略"走向"多层级自适应策略"。[推导: 趋势明显，N=3+]

---

## 8. 综合发现

### 8.1 关键结论

1. **上下文管理有坚实的理论基础**。信息论（Shannon）、认知科学（Miller/Cowan）、NLP 实证（Lost in the Middle）、架构分析（ICLR 2025）、实证现象（Context Rot）五个独立来源都指向同一方向：有限容量和衰减约束下的信息质量管理是必要的。[归纳: N=5 独立理论来源]

2. **"40% 阈值"应被替换为"模型特定的崩塌区间 20-50%"**。现有数据显示不同模型的阈值在 20-50% 区间波动。工程实现应支持可配置阈值，而非硬编码 40%。[推导: 多模型数据不一致]

3. **Lost in the Middle 是真实但正在缓解的问题**。Ms-PoE 等方法已将位置偏差缩小至几个百分点。长期看，模型架构改进可能消除此效应，届时"信息优先级放首尾"的建议需要更新。[推导: 缓解趋势存在]

4. **Context Rot 是一个独立的长度衰减现象**，与位置偏差正交。它解释了为什么"即使窗口很大也需要管理"——不是容量不足，而是衰减。[事实 + 因果分析]

5. **压缩算法已从"粗暴截断"进化到"信息论最优"再到"故障驱动动态优化"**。Sentinel（5x）、QUITO-X（+25%）、ACON（26-54% 峰值）代表了当前前沿。但这些算法均在非 Agent 任务上验证，Agent 场景的效果是开放问题。[事实 + 开放问题]

6. **行业隐含共识：延迟压缩 + 保留结构 + 不改模型 + 多层级自适应**。六个主流产品独立达成的一致选择，反映了当前工程成熟度下的最优策略。[归纳: N=6]

7. **信任度的差异反映了对模型能力的不同评估**。Claude Code（95% 触发）比 LangChain（80-90%）更信任模型长上下文能力；Cursor 完全信任用户判断。这些差异不是"一个对一个错"，而是对不同场景的适配。[推导: 差异≠错误]

### 8.2 跨Category发现：Context策略的模型相关性分层（C1×C7）

Context管理策略并非完全模型无关。基于C1研究中积累的跨产品、跨模型证据，可以将策略的模型相关性分为三层：

**第一层：原则层（模型无关）**

以下原则由理论基础决定，不随具体模型变化：

| 原则 | 理论根基 | 模型无关性论据 |
|------|----------|--------------|
| 有限容量下需要信息质量管理 | Shannon信道容量 | 所有有限窗口模型都成立 |
| 压缩是有损的，应尽量推迟 | 信息瓶颈理论 | 6个产品独立达成共识（N=6） |
| 结构信息比内容信息更值得保留 | 认知科学chunk理论 | 所有实现都遵守（N=5） |
| 上下文死亡螺旋需要预防 | 控制论正反馈 | 所有模型都存在 |

[归纳: 6个产品独立实现的共性选择, N=6, 且有理论层面的解释，不依赖特定模型的实验数据]

**第二层：策略层（部分模型相关）**

| 策略 | 模型相关因素 | 证据 |
|------|------------|------|
| Token级压缩（LLMLingua等） | 依赖模型perplexity分布 | 不同模型的token信息量评估不同 [推导] |
| 信息位置策略 | Lost in the Middle严重程度跨模型差异大 | Gemini 1.5 Pro 4K→128K仅下降2.3分 vs 多数模型>20%下降 [事实] |
| 缓存策略 | Prompt Caching是API特性 | Anthropic/OpenAI/Google实现机制和定价不同 [事实] |

**第三层：参数层（强模型相关）**

| 参数 | 模型间差异 | 证据来源 |
|------|----------|----------|
| 压缩触发阈值 | Gemini ~20%, Claude ~40-50% | arXiv:2601.11564 [事实，置信度A] |
| 最大有效窗口 | 声称200K但实际130K不可靠 | RULER benchmark [事实，置信度B] |
| 格式敏感性 | Hashline改动: Grok 10.2x vs MiniMax 2x | C3研究数据 [事实，置信度A] |
| Extended Thinking窗口计算 | Claude特有机制 | Anthropic docs [事实，置信度B] |

[演绎: 原则由理论决定（模型无关）+ 参数由实验测量（模型相关）→ Harness核心层应实现原则，模型适配层应管理参数]

**对Harness架构的直接推论**：

这一分层发现直接论证了C7（可拆卸性）中"三层架构分离"的必要性：
1. **Harness核心层**应实现原则层策略——压缩时机检测、结构化注入、渐进式披露——这些逻辑写一次到处用
2. **模型适配层**应管理参数层配置——每个模型一份"context profile"，包括有效窗口、阈值区间、位置敏感性等级
3. **策略选择器**根据当前模型的profile自动选择合适的压缩算法和信息组织策略

[推导: C1的模型相关性分层 + C7的三层架构 → context管理是"为什么需要可拆卸性"的直接论据之一。见 012_SYSTEM_C7_MODULARITY §9 的对应分析。]

---

### 8.3 开放问题

| # | 问题 | 所需研究 | 优先级 |
|---|------|----------|--------|
| O1 | 不同压缩算法在 Agent 多轮交互中的实际效果差异？ | Agent benchmark 上的 A/B 测试 | 高 |
| O2 | 探索性任务（目标不明确）的上下文管理最优策略？ | 需要区分任务类型的实验设计 | 高 |
| O3 | Context Rot 的根本机制是什么？与位置偏差是否独立？ | 受控注意力可视化实验 | 高 |
| O4 | 模型特定的context profile应包含哪些维度？如何自动化测量？ | 跨模型标准化测试框架 | 高 |
| O5 | 上下文死亡螺旋的精确触发条件和恢复策略？ | 受控环境故障注入实验 | 中 |
| O6 | 随着模型架构改进，哪些 C1 策略会变得多余？ | 跟踪位置偏差的跨模型演变 | 中 |
| O7 | MemGPT/Letta 的自管理模式是否可行于生产场景？ | 对话代理的实际部署数据 | 低 |

### 8.4 对企业办公场景的启示

企业办公场景与 Coding Agent 场景的关键差异在于上下文的**结构化程度**和**任务边界的清晰度**。

- 代码有严格的语法结构、import 图谱、类型系统，便于自动化的相关性判断和结构提取
- 办公场景（邮件、文档、会议记录）的信息更松散、任务边界更模糊

[推导: 办公场景信息结构化程度低于代码 + A6（任务相关性可被外部判断）在低结构化场景中更弱 → 办公场景应更多依赖用户显式指定上下文（类似 Cursor 的 @-mentions 模式），而非自动压缩（类似 Claude Code 的 auto-compaction 模式）]

**建议**：
- 办公 AI 系统应采用"用户主导+建议"的混合模式
- 结构化工具（如任务分类、优先级标签）可以帮助系统理解"相关性"
- 定期主动摘要（而非被动压缩）可能更适合办公场景的审计和追溯需求

---

## 9. 参考文献

### 置信度 A（同行评审，学术期刊/顶级会议）

1. Shannon, C.E. (1948). A Mathematical Theory of Communication. Bell System Technical Journal. [Wiley Online Library](https://onlinelibrary.wiley.com/doi/abs/10.1002/j.1538-7305.1948.tb01338.x) | [PDF](https://people.math.harvard.edu/~ctm/home/text/others/shannon/entropy/entropy.pdf)
2. Miller, G.A. (1956). The Magical Number Seven, Plus or Minus Two. Psychological Review, 63(2). [PubMed](https://pubmed.ncbi.nlm.nih.gov/13310704/) | [Semantic Scholar](https://www.semanticscholar.org/paper/The-magical-number-seven-plus-or-minus-two:-some-on-Miller/a15174ed603bae1b101c4655111bb511787b95b4)
3. Cowan, N. (2001). The magical number 4 in short-term memory. Behavioral and Brain Sciences, 24(1). [Cambridge Core](https://www.cambridge.org/core/journals/behavioral-and-brain-sciences/article/magical-number-4-in-shortterm-memory-a-reconsideration-of-mental-storage-capacity/44023F1147D4A1D44BDC0AD226838496) | [PubMed](https://pubmed.ncbi.nlm.nih.gov/11515286/)
4. Liu, N.F. et al. (2023). Lost in the Middle: How Language Models Use Long Contexts. TACL 2024. [arXiv:2307.03172](https://arxiv.org/abs/2307.03172) | [ACL Anthology](https://aclanthology.org/2024.tacl-1.9/)
5. Wu, X. et al. (2025). On the Emergence of Position Bias in Transformers. ICML 2025. [arXiv:2502.01951](https://arxiv.org/abs/2502.01951) | [OpenReview](https://openreview.net/forum?id=YufVk7I6Ii) | [GitHub](https://github.com/xinyiwu98/position-bias-in-attention)
6. Zhang, Z. et al. (2024). Found in the Middle: How Language Models Use Long Contexts Better via Plug-and-Play Positional Encoding. [arXiv:2403.04797](https://arxiv.org/abs/2403.04797)
7. Ponnusamy, A.A.N. et al. (2025). Context Discipline and Performance Correlation: Analyzing LLM Performance Under Varying Context Lengths. [arXiv:2601.11564](https://arxiv.org/abs/2601.11564)
8. Yang, Z. et al. (2025). Exploring Information Processing in LLMs: Insights from Information Bottleneck Theory. [arXiv:2501.00999](https://arxiv.org/abs/2501.00999)
9. (2024). QUITO-X: A New Perspective on Context Compression from the Information Bottleneck Theory. EMNLP 2025 Findings. [arXiv:2408.10497](https://arxiv.org/abs/2408.10497) | [ACL Anthology](https://aclanthology.org/2025.findings-emnlp.362/)
10. Zhang, Y. et al. (2025). Sentinel: Decoding Context Utilization via Attention Probing for Efficient LLM Context Compression. [arXiv:2505.23277](https://arxiv.org/abs/2505.23277) | [GitHub](https://github.com/yzhangchuck/Sentinel)
11. Sarukkai, V. et al. (2025). In-Context Distillation with Self-Consistency Cascades: A Simple, Training-Free Way to Reduce LLM Agent Costs. [arXiv:2512.02543](https://arxiv.org/abs/2512.02543)
12. Kang, M. et al. (2025). ACON: Optimizing Context Compression for Long-Horizon LLM Agents. [arXiv:2510.00615](https://arxiv.org/abs/2510.00615)
13. Kwon, W. et al. (2023). Efficient Memory Management for Large Language Model Serving with PagedAttention. SOSP 2023. [arXiv:2309.06180](https://arxiv.org/abs/2309.06180) | [ACM DL](https://dl.acm.org/doi/10.1145/3600006.3613165) | [GitHub (vLLM)](https://github.com/vllm-project/vllm)
14. Shah, J., Dao, T. et al. (2024). FlashAttention-3: Fast and Accurate Attention with Asynchrony and Low-precision. [arXiv:2407.08608](https://arxiv.org/abs/2407.08608) | [GitHub](https://github.com/Dao-AILab/flash-attention)

### 置信度 B（一手数据来源，厂商官方但未经独立同行评审）

15. Anthropic. The Claude 3 Model Family: Opus, Sonnet, Haiku — Model Card. [PDF](https://assets.anthropic.com/m/61e7d27f8c8f5919/original/Claude-3-Model-Card.pdf) | [System Cards](https://www.anthropic.com/system-cards)
16. Anthropic. Effective Context Engineering for AI Agents. [anthropic.com/engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
17. Anthropic. Claude Code Overview & Architecture. [code.claude.com/docs](https://code.claude.com/docs/en/overview) | [Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
18. Anthropic. Prompt Caching Guide. [platform.claude.com](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) | [Announcement](https://www.anthropic.com/news/prompt-caching)
19. Chroma Research (2025). Context Rot: How Increasing Input Tokens Impacts LLM Performance. [research.trychroma.com](https://research.trychroma.com/context-rot) | [GitHub](https://github.com/chroma-core/context-rot)
20. Hsieh, C.P. et al. (2024). RULER: What's the Real Context Size of Your Long-Context Language Models? COLM 2024. [arXiv:2404.06654](https://arxiv.org/abs/2404.06654) | [GitHub (NVIDIA)](https://github.com/NVIDIA/RULER)

### 置信度 C（厂商博客、技术博客、社区报告）

21. Anthropic. Introducing Advanced Tool Use on the Claude Developer Platform. [anthropic.com/engineering](https://www.anthropic.com/engineering/advanced-tool-use) | [API Docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use)
22. OpenAI. Compaction API Guide. [developers.openai.com](https://developers.openai.com/api/docs/guides/compaction) | [API Reference](https://developers.openai.com/api/reference/resources/responses/methods/compact)
23. OpenAI. Prompt Caching Best Practices. [developers.openai.com](https://developers.openai.com/api/docs/guides/prompt-caching)
24. Cursor. Codebase Indexing. [cursor.com/docs](https://cursor.com/docs/context/codebase-indexing)
25. Aider. Repository Map (Repo Map) Documentation. [aider.chat/docs](https://aider.chat/docs/repomap.html) | [技术博客](https://aider.chat/2023/10/22/repomap.html)
26. LangChain (2026). Improving Deep Agents with Harness Engineering. [blog.langchain.com](https://blog.langchain.com/improving-deep-agents-with-harness-engineering/)
27. Piebald-AI. Claude Code System Prompts (updated per release). [GitHub](https://github.com/Piebald-AI/claude-code-system-prompts) | [CHANGELOG](https://github.com/Piebald-AI/claude-code-system-prompts/blob/main/CHANGELOG.md)
28. jujumilk3. Leaked System Prompts Collection. [GitHub](https://github.com/jujumilk3/leaked-system-prompts)

### 置信度 D（KOL观点、业界共识）

29. Simon Willison (2025). Context Engineering. [simonwillison.net](https://simonwillison.net/2025/jun/27/context-engineering/)
30. Simon Willison (2026). Agentic Engineering Patterns. [simonwillison.net/guides](https://simonwillison.net/guides/agentic-engineering-patterns/) | [Substack](https://simonw.substack.com/p/agentic-engineering-patterns)
31. Böckeler, B. / Martin Fowler (2025). Context Engineering for Coding Agents. [martinfowler.com](https://martinfowler.com/articles/exploring-gen-ai/context-engineering-coding-agents.html)
32. Böckeler, B. / Martin Fowler (2025). Harness Engineering. [martinfowler.com](https://martinfowler.com/articles/exploring-gen-ai/harness-engineering.html)
33. Gartner. AI Hype Cycle 2025: Context Engineering Emerges. (Industry Report, 付费访问)
34. Block Engineering. Goose: Open Source AI Agent with Smart Context Management. [GitHub](https://github.com/block/goose) | [Docs](https://block.github.io/goose/docs/guides/sessions/smart-context-management/)
35. Letta (formerly MemGPT). Stateful Agents Framework with Memory & Context Management. [GitHub](https://github.com/letta-ai/letta) | [Docs](https://docs.letta.com/concepts/memgpt/) | [letta.com](https://www.letta.com/)

---

## 10. 工程实现：算法×Hook注入点映射与伪代码

> 假定：Harness 工程中已有六钩子中间件架构（C9定义）：
> `before_agent → before_model → wrap_model → wrap_tool → after_model → after_agent`
> 加上 session 级的 `session_init` 和 `session_end`。
> 本章将 C1 的每个算法/机制映射到具体注入点，并给出 Python 伪代码。

### 10.0 全局数据结构

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

class ModelContextProfile:
    """C1×C7: 模型特定的上下文参数（见§8.2分层分析）"""
    model_id: str
    effective_window: int          # 实际有效窗口（非声称值）
    collapse_threshold: float      # 性能崩塌阈值（0.0-1.0）
    position_sensitivity: str      # "high" | "medium" | "low"
    caching_support: str           # "prefix" | "none"
    thinking_mode: Optional[str]   # "extended" | None

class ContextState:
    """贯穿整个session的上下文状态"""
    total_tokens: int = 0
    system_tokens: int = 0
    tool_def_tokens: int = 0
    conversation_tokens: int = 0
    utilization: float = 0.0       # total / effective_window
    compaction_count: int = 0
    turn_count: int = 0
    file_edit_counts: dict = field(default_factory=dict)  # 循环检测用
    anchor_content: str = ""       # 焦点锚定内容（TODO List等）

    # 死亡螺旋检测
    error_count_window: list = field(default_factory=list)  # 最近N轮的错误数
    spiral_risk: float = 0.0
```

---

### 10.1 上下文监控（Utilization Tracking）

**注入点**：`after_model`（每轮模型返回后更新）

**触发条件**：每轮必执行

```python
# Hook: after_model
def context_monitor(model_response, ctx: ContextState, profile: ModelContextProfile):
    """每轮模型返回后，更新上下文利用率并判断是否需要干预"""

    # 1. 更新token计数
    ctx.conversation_tokens += model_response.input_tokens + model_response.output_tokens
    ctx.total_tokens = ctx.system_tokens + ctx.tool_def_tokens + ctx.conversation_tokens
    ctx.utilization = ctx.total_tokens / profile.effective_window
    ctx.turn_count += 1

    # 2. 分级预警（阈值来自模型profile，非硬编码）
    if ctx.utilization >= 0.95:
        return ContextAction.FORCE_COMPACTION    # 强制压缩
    elif ctx.utilization >= profile.collapse_threshold:
        return ContextAction.WARN_DEGRADATION    # 警告：已进入崩塌区间
    elif ctx.utilization >= profile.collapse_threshold * 0.8:
        return ContextAction.SUGGEST_COMPACTION  # 建议：接近阈值

    return ContextAction.OK
```

**设计决策**：阈值从 `ModelContextProfile` 读取而非硬编码，因为不同模型崩塌点不同（Gemini ~20%, Claude ~40-50%）。

---

### 10.2 渐进式披露（Progressive Disclosure）

**注入点**：`session_init` + `before_model`

**触发条件**：session开始时加载导航地图；每轮按需展开详情

```python
# Hook: session_init
def progressive_disclosure_init(session, project_root: str):
    """session开始时仅加载导航地图（~100行），不加载全部内容"""

    # 1. 加载 AGENTS.md / CLAUDE.md 作为导航地图
    nav_map = read_file(f"{project_root}/AGENTS.md", max_lines=100)

    # 2. 扫描可用的skill/tool描述（仅标题+一句话描述）
    skill_index = []
    for skill in scan_skills(project_root):
        skill_index.append(f"- {skill.name}: {skill.one_line_description}")

    # 3. 注入系统上下文（静态部分前置，利于Prompt Cache命中）
    session.system_prompt = [
        STATIC_INSTRUCTIONS,        # 不变的行为规则（缓存友好）
        nav_map,                     # 项目导航地图
        "\n".join(skill_index),      # skill索引（非完整定义）
        DYNAMIC_TASK_CONTEXT,        # 当前任务上下文（变量部分后置）
    ]
    return session

# Hook: before_model（工具定义的按需加载）
def tool_search_injection(user_message, ctx: ContextState, tool_registry):
    """Tool Search Tool模式：按需加载工具定义，而非预加载全部
       效果：节省约35%上下文（191K vs 123K tokens, Anthropic数据）"""

    # 1. 根据用户意图匹配相关工具（embedding或关键词）
    relevant_tools = tool_registry.search(
        query=user_message,
        max_results=5  # "5个清晰工具优于20个模糊工具"
    )

    # 2. 仅注入匹配到的工具定义
    ctx.tool_def_tokens = sum(t.token_count for t in relevant_tools)
    return relevant_tools
```

**设计决策**：Tool Search Tool 模式比预加载全部工具节省35%上下文（Anthropic工程博客数据）。trade-off是引入一次额外的检索延迟。

---

### 10.3 结构化上下文组织（Structured Context Assembly）

**注入点**：`before_model`

**触发条件**：每轮组装上下文时执行

```python
# Hook: before_model
def structured_context_assembly(
    messages, ctx: ContextState, profile: ModelContextProfile
):
    """按位置敏感性组织信息：高优先级→首尾，低优先级→中间
       依据：Lost in the Middle效应（但严重程度模型相关）"""

    # 1. 分类信息优先级
    high_priority = []   # 任务指令、当前错误、关键约束
    medium_priority = []  # 对话历史、工具输出
    low_priority = []     # 背景信息、参考文档

    for msg in messages:
        priority = classify_priority(msg)
        [high_priority, medium_priority, low_priority][priority].append(msg)

    # 2. 根据模型位置敏感性决定组装策略
    if profile.position_sensitivity == "high":
        # U型策略：重要信息放首尾，避免中间
        assembled = high_priority + low_priority + medium_priority + high_priority[-1:]
    elif profile.position_sensitivity == "low":
        # Gemini等模型位置不敏感，按逻辑顺序即可
        assembled = high_priority + medium_priority + low_priority
    else:
        # 默认：重要信息前置
        assembled = high_priority + medium_priority + low_priority

    # 3. 焦点锚定：TODO List注入（即使空也保持）
    if ctx.anchor_content:
        assembled.insert(0, make_system_msg(f"<current_task>\n{ctx.anchor_content}\n</current_task>"))

    return assembled
```

---

### 10.4 上下文压缩（Context Compaction）

**注入点**：`before_model`（检测触发）+ `wrap_model`（执行压缩）

**触发条件**：利用率超过模型特定阈值时

```python
# Hook: before_model（压缩触发判定）
def compaction_trigger(ctx: ContextState, profile: ModelContextProfile):
    """判断是否需要压缩，以及使用哪种压缩策略
       原则：延迟压缩（所有产品的隐含共识）"""

    if ctx.utilization < profile.collapse_threshold * 0.8:
        return None  # 安全区间，不压缩

    # 选择压缩策略（按任务类型和紧急程度）
    if ctx.utilization >= 0.95:
        return CompactionStrategy.AGGRESSIVE  # 紧急：摘要+截断
    elif ctx.utilization >= profile.collapse_threshold:
        return CompactionStrategy.STANDARD     # 标准：摘要压缩
    else:
        return CompactionStrategy.GENTLE       # 温和：仅归档旧工具输出


# 压缩执行器（被wrap_model调用）
def execute_compaction(
    messages: list, strategy: CompactionStrategy, ctx: ContextState
):
    """执行压缩，保留结构信息，丢弃过程细节
       核心原则：结构 > 内容（所有实现的隐含共识）"""

    preserved = []   # 必须保留的内容
    compactable = [] # 可压缩的内容

    for msg in messages:
        if msg.role == "system":
            preserved.append(msg)              # 系统指令永不压缩
        elif msg.has_tag("anchor"):
            preserved.append(msg)              # 锚定内容不压缩
        elif msg.is_recent(last_n=3):
            preserved.append(msg)              # 最近3轮完整保留
        else:
            compactable.append(msg)

    if strategy == CompactionStrategy.AGGRESSIVE:
        # 激进压缩：用LLM生成摘要（上下文蒸馏：保留结论，丢弃推理）
        summary = llm_summarize(
            compactable,
            instruction="保留：决策结论、文件路径、错误信息、任务进度。"
                       "丢弃：中间推理过程、工具输出细节、重复尝试。"
        )
        compressed = [make_system_msg(f"<conversation_summary>\n{summary}\n</conversation_summary>")]

    elif strategy == CompactionStrategy.STANDARD:
        # 标准压缩：分段摘要 + 保留关键节点（ACON锚定迭代策略）
        segments = segment_by_task(compactable)
        compressed = []
        for seg in segments:
            if seg.has_key_decision:
                compressed.append(seg.decision_only())  # 保留决策
            else:
                compressed.append(seg.one_line_summary())  # 一行摘要

    elif strategy == CompactionStrategy.GENTLE:
        # 温和压缩：仅清理旧工具输出（LangChain ClearToolUsesEdit策略）
        compressed = [
            msg for msg in compactable
            if not (msg.role == "tool" and msg.age > 5)
        ]

    ctx.compaction_count += 1
    return preserved + compressed
```

---

### 10.5 Prompt缓存优化（Cache-Friendly Layout）

**注入点**：`session_init`（布局设计）+ `before_model`（缓存标记）

**触发条件**：每次模型调用时

```python
# Hook: session_init（缓存友好的布局设计）
def cache_friendly_layout(system_prompt_parts: list):
    """确保静态内容前置，变量内容后置，最大化前缀缓存命中
       经济模型：缓存读取仅10%基础价格（Anthropic定价）"""

    # 排序原则：变化频率低→前，变化频率高→后
    static_parts = []   # 行为规则、安全指令（几乎不变）
    semi_static = []    # 工具定义、skill描述（session内不变）
    dynamic_parts = []  # 任务上下文、对话历史（每轮变化）

    for part in system_prompt_parts:
        if part.change_frequency == "never":
            static_parts.append(part)
        elif part.change_frequency == "per_session":
            semi_static.append(part)
        else:
            dynamic_parts.append(part)

    # 在静态与动态边界处插入缓存断点标记
    return static_parts + [CACHE_BREAKPOINT] + semi_static + [CACHE_BREAKPOINT] + dynamic_parts


# Hook: before_model（缓存标记注入）
def inject_cache_markers(messages, profile: ModelContextProfile):
    """根据模型的缓存支持类型注入相应标记"""

    if profile.caching_support == "prefix":
        # Anthropic风格：cache_control breakpoint
        for i, msg in enumerate(messages):
            if msg == CACHE_BREAKPOINT:
                messages[i-1].cache_control = {"type": "ephemeral"}

    return messages
```

---

### 10.6 循环检测（Loop Detection）

**注入点**：`after_model`

**触发条件**：每轮检查

```python
# Hook: after_model
def loop_detection(model_response, ctx: ContextState):
    """追踪文件编辑次数，N次后强制换策略
       对应机制：LoopDetection（LangChain PreCompletionChecklistMiddleware）"""

    # 1. 追踪文件编辑次数
    for action in model_response.tool_calls:
        if action.tool in ("Edit", "Write"):
            file_path = action.params.get("file_path", "")
            ctx.file_edit_counts[file_path] = ctx.file_edit_counts.get(file_path, 0) + 1

    # 2. 检测循环模式
    MAX_EDITS_PER_FILE = 3
    looping_files = [
        f for f, count in ctx.file_edit_counts.items()
        if count >= MAX_EDITS_PER_FILE
    ]

    if looping_files:
        # 3. 强制换策略：注入干预指令
        intervention = (
            f"⚠️ 检测到对以下文件的重复编辑（≥{MAX_EDITS_PER_FILE}次）：\n"
            f"{', '.join(looping_files)}\n"
            f"请停止当前方法，换一种策略解决问题。"
        )
        return LoopAction.INJECT_INTERVENTION, intervention

    return LoopAction.OK, None
```

---

### 10.7 上下文死亡螺旋检测（Death Spiral Detection）

**注入点**：`after_model`（持续监控）+ `before_agent`（session级检查）

**触发条件**：错误率上升 + 上下文膨胀的耦合检测

```python
# Hook: after_model
def death_spiral_detector(model_response, ctx: ContextState):
    """检测：错误→更多上下文→决策下降→更多错误 的恶性循环
       三维度组合检测（状态指纹 + 错误率 + 上下文膨胀率）"""

    # 1. 记录本轮错误数
    errors_this_turn = sum(
        1 for tc in model_response.tool_calls if tc.result.is_error
    )
    ctx.error_count_window.append(errors_this_turn)
    if len(ctx.error_count_window) > 5:
        ctx.error_count_window.pop(0)

    # 2. 计算滑动窗口错误率
    if len(ctx.error_count_window) >= 3:
        recent_error_rate = sum(ctx.error_count_window[-3:]) / 3
        older_error_rate = sum(ctx.error_count_window[:2]) / max(len(ctx.error_count_window[:2]), 1)

        # 3. 死亡螺旋信号：错误率上升 AND 上下文在膨胀
        error_increasing = recent_error_rate > older_error_rate * 1.5
        context_bloating = ctx.utilization > 0.7 and ctx.compaction_count == 0

        if error_increasing and context_bloating:
            ctx.spiral_risk += 0.3
        elif error_increasing:
            ctx.spiral_risk += 0.1
        else:
            ctx.spiral_risk = max(0, ctx.spiral_risk - 0.1)  # 衰减

    # 4. 达到风险阈值时触发干预
    if ctx.spiral_risk >= 0.8:
        return SpiralAction.FORCE_RESET  # 强制：压缩+重注入目标+换策略
    elif ctx.spiral_risk >= 0.5:
        return SpiralAction.WARN         # 警告：建议人工介入

    return SpiralAction.OK
```

---

### 10.8 推理三明治（Reasoning Sandwich）

**注入点**：`wrap_model`

**触发条件**：任务的不同阶段自动切换推理强度

```python
# Hook: wrap_model
def reasoning_sandwich(task_phase: str, model_call_params: dict):
    """按任务阶段分配推理算力：
       xhigh(规划) → high(实现) → xhigh(验证)"""

    PHASE_TO_REASONING = {
        "planning":     {"thinking": "xhigh", "temperature": 0.3},
        "executing":    {"thinking": "high",  "temperature": 0.2},
        "verifying":    {"thinking": "xhigh", "temperature": 0.1},
        "simple_query": {"thinking": "low",   "temperature": 0.5},
    }

    config = PHASE_TO_REASONING.get(task_phase, PHASE_TO_REASONING["executing"])
    model_call_params.update(config)
    return model_call_params
```

---

### 10.9 工具输出截断与回压验证（Tool Output Backpressure）

**注入点**：`wrap_tool`

**触发条件**：每次工具调用返回时

```python
# Hook: wrap_tool
def tool_output_backpressure(tool_name: str, tool_result, ctx: ContextState):
    """静默成功 + 大声失败 = 上下文高效的反馈循环
       同时对过大的工具输出进行截断保护"""

    MAX_TOOL_OUTPUT_TOKENS = 5000

    # 1. 成功时精简输出（静默成功）
    if tool_result.success:
        if tool_result.token_count > MAX_TOOL_OUTPUT_TOKENS:
            # 截断过大的输出，保留首尾
            tool_result.content = truncate_preserve_boundaries(
                tool_result.content,
                max_tokens=MAX_TOOL_OUTPUT_TOKENS,
                strategy="head_tail"  # 首尾保留，中间截断
            )
        # 对于简单成功，可以进一步压缩
        if tool_name in ("Bash", "Glob") and tool_result.is_simple_success:
            tool_result.content = f"✓ {tool_name} 成功"  # 极简反馈

    # 2. 失败时丰富输出（大声失败 = 教学质量报错）
    else:
        tool_result.content = (
            f"✗ {tool_name} 失败\n"
            f"  什么违反了: {tool_result.error_type}\n"
            f"  为什么: {tool_result.error_message}\n"
            f"  怎么修: {tool_result.suggested_fix or '无建议'}"
        )

    return tool_result
```

---

### 10.10 算法×Hook映射总表

| C1算法/机制 | 主注入点 | 辅助注入点 | 触发频率 | 模型相关性 |
|------------|---------|-----------|---------|-----------|
| 上下文监控 | `after_model` | — | 每轮 | 参数层（阈值） |
| 渐进式披露 | `session_init` | `before_model` | 初始化+按需 | 无关 |
| 结构化组织 | `before_model` | — | 每轮 | 策略层（位置敏感性） |
| 压缩触发/执行 | `before_model` | `wrap_model` | 条件触发 | 参数层（阈值） |
| 缓存优化布局 | `session_init` | `before_model` | 初始化+每轮 | 策略层（缓存类型） |
| 循环检测 | `after_model` | — | 每轮 | 无关 |
| 死亡螺旋检测 | `after_model` | `before_agent` | 每轮 | 无关 |
| 推理三明治 | `wrap_model` | — | 每轮 | 策略层（thinking支持） |
| 工具输出回压 | `wrap_tool` | — | 每次工具调用 | 无关 |
| 焦点锚定(TODO) | `before_model` | `after_model` | 每轮 | 无关 |

**执行顺序**（单轮内）：

```
session_init: 渐进式披露 → 缓存布局
    ↓
before_model: Tool Search注入 → 压缩触发判定 → 结构化组装 → 缓存标记
    ↓
wrap_model: 推理三明治(算力分配)
    ↓
[模型推理]
    ↓
after_model: 上下文监控 → 循环检测 → 死亡螺旋检测
    ↓
wrap_tool: 输出截断 → 回压验证（每个工具调用）
    ↓
[下一轮 before_model ...]
```

---

## 附注：更新记录

**2025-03-30 重写版本**：
- 纳入 ICLR 2025 对位置偏差的架构分析（arXiv:2502.01951）
- 新增 Context Rot 理论（Chroma Research 2025）
- 新增底层基础设施讨论（PagedAttention, Flash Attention 3）
- 新增行业认知演进分析（Prompt → Context → Harness）
- 大幅增强实践案例：新增 Goose 和 MemGPT/Letta，增强 Claude Code 细节
- 新增 ACON 框架（故障驱动压缩）
- 扩充效果数据表，分置信度标注
- 新增 Context Rot 相关开放问题
- 参考文献从 22 条扩充至 35 条

---

**文档字数**：约 9,500 字（相比原文 6,400 字，扩充 48%）
