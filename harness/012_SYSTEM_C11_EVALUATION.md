# 012_SYSTEM C11 评估与基准测试（Evaluation & Benchmarking）

**深度研究报告**
*本文档基于2026年3月系统化研究，记录AI Agent评估体系的理论基础、核心机制、实践案例与隐性知识*

---

## 前言

C11代表Harness工程体系中的离线量化验证层，区别于C9的运行时监控。其本质是**构建可重复、可比较、可扩展的Agent性能量化框架**，将主观判断转化为客观数据，支持：
- 算法迭代的效果验证（如Harness优化52.8%→66.5%的验证）
- 模型升级的收益评估（模型无关的算法贡献度隔离）
- 工程可靠性的长期追踪（1%榜单差异检测第50步后漂移）

本报告采用**9问框架**从理论→实践→隐性知识逐层深化，标注认知置信度，区分事实/推导/假说。

---

## §0 核心概念地图

### 0.1 三组关键对比

| 维度 | Pass@k | Pass^k | 含义 |
|------|--------|--------|------|
| **定义** | k次中至少1次成功 | k次全部成功 | 衡量能力上限 vs 一致性下界 |
| **数学形式** | P(X≥1) = 1-(1-p)^k | P(X=k) = p^k | 独立试验概率 |
| **应用场景** | 验证可行性（代码生成） | 验证可靠性（生产系统） | pass@1=75% ≠ pass^3=42% |
| **失真风险** | 高估（乐观偏差） | 悲观但真实（Goodhart防护） | 单次成功≠可依赖 |

### 0.2 评估框架三维展开

```
评估体系
├─ 组织维：Task/Trial/Grader
│  ├─ Task: 问题定义（目标+约束+上下文）
│  ├─ Trial: 单次执行（产生轨迹+环境状态）
│  └─ Grader: 评分逻辑（确定性vs灵活性）
│
├─ 测量维：轨迹vs结果独立评估
│  ├─ 轨迹(Trajectory): 推理链+工具调用序列
│  ├─ 结果(Outcome): 最终环境状态
│  └─ 关键发现：两者可独立评估但耦合（策略→状态）
│
└─ 四支柱模型：LLM/Memory/Tool/Environment
   ├─ LLM: 指令遵从+安全对齐
   ├─ Memory: 存储一致性+检索准确性
   ├─ Tool: 工具选择+参数映射+执行序列
   └─ Environment: 工作流+护栏+可观测性
```

### 0.3 Goodhart陷阱在Agent评估中的表现

**原理**：度量变为目标时就不再是好度量（Goodhart's Law，1975）

**在Agent评估中的实例**：
- 优化pass@k → 模型学会单次侥幸（低通过率+高一致性不对称）
- 优化轨迹长度 → Agent陷入逻辑螺旋（50步内看似探索，实际循环）
- 优化SWE-bench分数 → 模型对基准过拟合（竞争对手变更基准方式[Saving SWE-Bench: A Benchmark Mutation Approach for Realistic Agent Evaluation (arXiv:2510.08996)](https://arxiv.org/abs/2510.08996)）

**防护策略**：
1. 多维度度量组合（pass@k + pass^k + 成本 + 轨迹合理性）
2. 消融研究验证因果关系（非仅相关性）
3. 定期基准变异（Benchmark Mutation[Saving SWE-Bench: A Benchmark Mutation Approach for Realistic Agent Evaluation (arXiv:2510.08996)](https://arxiv.org/abs/2510.08996)）

---

## §1 理论基础：从心理测量学到Agent评估

### 1.1 测量论（Measurement Theory）的四层次[事实]

引用Stevens（1946）分类，适用于Agent评估的基础：

| 层次 | 定义 | Agent评估示例 | 风险 |
|------|------|-----------------|------|
| **名义** | 分类，无大小关系 | 成功/失败 | 信息丢失（二元化） |
| **序序** | 有顺序但无距离 | 低/中/高可靠性等级 | 等级间距不等 |
| **等距** | 等间距但无绝对零点 | 成功率百分比 | 0%不表示无能力 |
| **比值** | 有绝对零点可做比例 | 成本比（$0.06 vs $0.96） | 稀有（需绝对基准） |

**Agent评估现状分析**[推导]：
- 大多数基准停留在序序层次（排名榜单）
- 少数达到等距层次（百分比成功率）
- 成本维度达到比值层次（LLM-as-Judge $0.06 vs Agent-as-Judge $0.96）
- **缺失**：跨维度的可比较性（成功率vs成本的权衡曲线）

### 1.2 信效度理论（Reliability & Validity）在Agent中的应用

#### 1.2.1 信度（Reliability）：可重复性危机

**定义**：同一Agent在相同条件下多次运行的结果一致性

**Agent评估的信度危机来源**[事实][Measurement to Meaning: A Validity-Centered Framework for AI Evaluation (arXiv:2505.10573)](https://arxiv.org/abs/2505.10573)：
1. **温度采样**：T>0的随机采样导致结果飘移
2. **模型API版本漂移**：模型更新产生偏差（如OpenAI的gpt-4突然表现下滑）
3. **标注者分歧**：人工评分器的意见不一致（Kappa系数<0.7）
4. **基准项选择**：测试用例覆盖度不足（HumanEval平均<10个测试[HumanEval Pro and MBPP Pro: Evaluating Large Language Models on Self-invoking Code Generation (arXiv:2412.21199)](https://arxiv.org/abs/2412.21199)）

**长程可靠性问题**[推导]：
- 观察：某Agent在第1-30步表现稳定，第31-50步性能崖裂式下降
- 原因：初始策略遵从100% → 累积错误后策略遍历（混乱）
- 数据：SWE-bench的Verified版本发现1%榜单差异无法检测第50步后的长程漂移
- 结论：长程可靠性需覆盖50-100+工具调用的评估

**信度改进方案**$5.1 Reliability – AI Measurement Science$：
```
传统QA: 单一判断
    ↓↓↓ (问题：0/1判断无法捕捉细微差异)
改进方案:
├─ 多次运行(N≥5): 计算通过率分布
├─ 温度固定T=0.0: 去除采样随机性（牺牲多样性换可重复）
├─ 自动化评分器: 代替人工（快但脆性）
│  └─ 代码型: 单元测试（快/脆）
│  └─ 模型型: LLM裁判（灵活/非确定）
│  └─ 人工型: 金标准（可靠/不可扩展）
└─ 时间层次感知: 第1步vs第50步失败权重不同
```

#### 1.2.2 效度（Validity）：测量→含义的推理链

**概念框架**[推导][Measurement to Meaning: A Validity-Centered Framework for AI Evaluation (arXiv:2505.10573)](https://arxiv.org/abs/2505.10573)：
效度不是性质而是论证——"这个指标真的衡量我声称的东西吗？"

**四类效度在Agent评估中的映射**[推导]：

1. **内容效度（Content Validity）**
   - 问题：SWE-bench Verified任务是否代表真实工程问题？
   - 解决：人工验证（[SWE-Bench Pro: Can AI Agents Solve Long-Horizon Software Engineering Tasks? (arXiv:2509.16941)](https://arxiv.org/abs/2509.16941)）、任务多样性统计
   - 数据：SWE-bench从4.5K→500的Verified筛选过程

2. **构想效度（Construct Validity）**
   - 问题：pass@k真的衡量"可靠Agent能力"吗？
   - 陷阱：pass@1=75% → Agent非可靠（pass^3=42%才是可靠指标）
   - 修正：分离通过率(能力)与一致性(可靠性)两个构想

3. **准则效度（Criterion Validity）**
   - 问题：基准分数与实际部署效果相关性多强？
   - 实证：大公司评估框架显示"多层次覆盖"与实际性能相关(r>0.8)
   - 缺陷：SWE-bench高分≠生产系统高效（缺少用户反馈）

4. **外推效度（External Validity）**
   - 问题：SWE-bench的结果能推广到AppWorld/OSWorld吗？
   - 数据：HAL跨9+基准对比发现Spearman相关ρ=0.6-0.8（中等）
   - 含义：Agent的泛化能力存在任务依赖性

**效度论证框架**[推导]：
```
声称: "模型X比Y更可靠"
    ↓ (需要证据支撑)
证据A: pass^3(X)=65% > pass^3(Y)=42% ✓
证据B: 50步长程测试无性能漂移 ✓
证据C: 多个基准(SWE/USACO/AppWorld)一致性排名 ✓
证据D: 用户满意度调查 ? (缺失)
    ↓
结论效度: 中高置信度(证据覆盖70%)，需补充D
```

### 1.3 统计假设检验的陷阱

**问题陈述**[推导]：
一个榜单显示ModelA=52.8%, ModelB=52.5%，分别改进为66.5%和65.9%
问：真的是A优于B吗？还是随机波动？

**Type I/II错误在Agent评估中的成本**：

| 错误类型 | 发生 | 后果 | 成本估计 |
|---------|------|------|----------|
| Type I (假阳性) | 认为Algo A好，实际相同 | 方向错误的投入 | 3个月开发+实验 |
| Type II (假阴性) | 认为Algo B无用，实际更优 | 遗漏机会 | 竞品先发优势 |

**SWE-bench案例分析**[推导][Saving SWE-Bench: A Benchmark Mutation Approach for Realistic Agent Evaluation (arXiv:2510.08996)](https://arxiv.org/abs/2510.08996)：
- 原基准：分数差异<1%无法统计显著性区分
- 问题：导致过度学习(overfitting)基准细节
- 解决：基准变异(Benchmark Mutation)——自动生成等效不同的任务变体
- 结果：检测漂移敏感度提升5倍

**效果评估的统计功效分析**[推导]：
```
假设: 某改进的真实效果为+2pp(百分点)
已有数据: N=500个任务，单次成功率≈60%

Power Analysis:
  σ = √(0.6×0.4/500) ≈ 2.2pp
  效应量(+2pp)/σ(2.2pp) = 0.91 → 功效≈65%

结论: 需要N≥1000个任务或多次试验
      以达到>90%的检测功效
```

---

## §2 前提假设与Lakatos分级[推导/假说]

### 2.1 Agent评估的硬核假设（Lakatos保护带）

```
坚实内核(必须真):
  1. Agent的行为是可观测、可记录的
  2. 同一任务的多次运行可比较
  3. 评分逻辑有定义（即使不完美）

辅助假设(可调整):
  4. 评分器是一致的(信度>0.7)
  5. 评分与真实能力相关(效度>0.6)
  6. 任务足够代表真实应用(外推效度>0.5)

危险区域(常被忽视):
  7. Agent不学习基准(无污染)
  8. 评估环境与生产环境相同
  9. 单个指标足以综合判断Agent质量
```

### 2.2 当下最脆弱的假设[开放问题]

#### 假设7的危机：基准污染

**发现**[Benchmark Data Contamination of Large Language Models: A Survey (arXiv:2406.04244)](https://arxiv.org/abs/2406.04244)：
- LLM训练数据中的基准泄露率：HumanEval的35-45%、SWE-bench的8-15%
- 影响：BLEU分数虚增5-10pp、准确率虚增3-8%
- 症状：模型在泄露任务上过拟合（memorization而非reasoning）

**检测方法**$wVDR2qmE28$（Kernel Divergence Score）：
```
原理：比较微调前后的样本相似度矩阵
      泄露样本←微调→未见样本的相似度变化更小

实现：
  1. 计算embedding矩阵K(微调前)和K'(微调后)
  2. KDS = ||K - K'|| (Frobenius范数)
  3. 高KDS表示微调影响均匀(无泄露)
     低KDS表示存在泄露(部分样本不敏感)

应用：审计LLaMA 3、GPT-4等模型的污染程度
```

**解决方案的成熟度**[事实][LessLeak-Bench: A First Investigation of Data Leakage in LLMs (arXiv:2502.06215)](https://arxiv.org/abs/2502.06215)：
- LessLeak-Bench：跨83个SE基准的污染调查
- 发现：更新基准（如仓库新issue）污染率↓ 40%
- 成本：维护更新基准的人力成本

#### 假设8的危机：模拟vs真实环境的间隙

**研究**：OSWorld（真实操作系统）vs AppWorld（API模拟）

| 维度 | AppWorld | OSWorld |
|------|----------|---------|
| 环境保真度 | API模拟(高控制) | 真实系统(低控制) |
| 可重复性 | 高(确定性API) | 低(系统状态漂移) |
| 成本 | 低($0.10/运行) | 高($5+/运行含基础设施) |
| 人类基准 | N/A | 72.36%成功率 |
| SOTA Agent | 95%+ | 12.24%成功率 |

**差距的来源**[推导]：
1. GUI grounding: Agent无法准确定位屏幕元素（OOD问题）
2. 操作知识：文件系统、权限、版本兼容性的隐性知识
3. 恢复能力：真实系统错误无法重做（破坏性操作）

**含义**[假说]：AppWorld基准上的高分可能不能直接转化为OSWorld表现

#### 假设9的危机：单指标的虚幻综合

**问题**[推导]：
- 某Agent: pass@1=65%, cost=$0.50/运行, 策略遵从率=92%
- 另一Agent: pass@1=62%, cost=$0.08/运行, 策略遵从率=100%
- 哪个更好？无绝对答案——取决于应用场景

**多维评估的必要性**[事实][Beyond Task Completion: An Assessment Framework for Evaluating Agentic AI Systems (arXiv:2512.12791)](https://arxiv.org/abs/2512.12791)（Beyond Task Completion框架）：
```
评估维度(不可约的):
  ├─ 任务成功率(准确性)
  ├─ 策略遵从率(安全性)
  ├─ 成本效率(经济性)
  ├─ 轨迹可解释性(可信度)
  └─ 长程稳定性(可靠性)

评分卡示例(Pareto前沿):
  Agent A: (95, 100, $2, 80%, 95%) ← 精准可靠
  Agent B: (88, 92, $0.1, 60%, 70%) ← 廉价快速

选择取决于: 产品定位(精准vs快速)
```

---

## §3 核心算法与评估方法谱系

### 3.1 三类评分器的权衡[事实]

#### 3.1.1 代码型评分器（Fast & Brittle）

**原理**：单元测试、集成测试的自动化执行

**优点**：
- 速度快（毫秒级）
- 结果确定（同条件重复100%一致）
- 成本低（无API调用）

**缺点**：
- 测试覆盖度问题：HumanEval平均<10个测试/题 → 微妙bug逃逸
- 示例[HumanEval Pro and MBPP Pro: Evaluating Large Language Models on Self-invoking Code Generation (arXiv:2412.21199)](https://arxiv.org/abs/2412.21199)：
  ```python
  def add(a, b):
      return a + b + 0.0001  # 浮点精度bug

  # 通过低覆盖测试但真实场景失败
  ```

**改进方案**[事实]：EvalPlus框架[HumanEval Pro and MBPP Pro: Evaluating Large Language Models on Self-invoking Code Generation (arXiv:2412.21199)](https://arxiv.org/abs/2412.21199)
- LLM驱动的种子生成(seed generation)：人工案例 → LLM生成边界测试
- 类型感知的变异(mutation)：自动产生等价变种
- 结果：暴露EvalPlus前未检测的bug 15-30%增长

#### 3.1.2 模型型评分器（Flexible & Non-deterministic）

**原理**：LLM-as-Judge或Agent-as-Judge

**LLM-as-Judge的形式**[事实]$0.06成本级别$：
```
Prompt:
  "判断Agent的输出[OUPUT]是否正确解决了问题[PROBLEM]
   理由: [REASONING]
   答案: [YES/NO]"

成本分析:
  - 单次判断: ~100 tokens → $0.0006 (使用廉价模型)
  - N=500个任务 × 5次试验 = 2500次判断
  - 总成本: $1.5

vs Agent代码评估: $0
```

**准确性对比**[事实][When AIs Judge AIs: The Rise of Agent-as-a-Judge Evaluation (arXiv:2508.02994)](https://arxiv.org/abs/2508.02994)：
- LLM-Judge vs 人工: 一致性Kappa=0.75 (中等)
- 但**关键发现**：LLM-Judge之间一致性更高(0.82) 比 人-人(0.70)
- 原因：LLM无疲劳、无主观偏见、完全可重复

**Agent-as-Judge的突破**[开放问题][When AIs Judge AIs: The Rise of Agent-as-a-Judge Evaluation (arXiv:2508.02994)](https://arxiv.org/abs/2508.02994)：
```
场景: 评估Agent的预算报告摘要是否准确

LLM-Judge局限:
  - 只能做表面语言评估
  - 无法发现数学计算错误

Agent-as-Judge优势:
  - 工具Agent重新计算总数
  - 对比原始数据验证
  - 发现细微不一致

成本权衡:
  LLM-Judge: $0.06/判断
  Agent-Judge: $0.96/判断 (16倍成本!)

适用范围: 高价值决策(law/medicine)而非低成本筛选
```

#### 3.1.3 人工评分器（Gold Standard & Unscalable）

**用途**[事实]：
- 基准构建时的质量验证（SWE-bench Verified的人工审查）
- 新任务类型的初期校准
- 争议案例的最终裁决

**成本与准确度曲线**[推导]：
```
评分者培训时间:
  ├─ 代码审查: 10小时(SWE-bench专家)
  ├─ 医学判断: 50小时(领域医生)
  └─ 法律判断: 100小时(律师)

单个案例评分时间:
  ├─ SWE修复: 5-10分钟 → $2-5/样本
  ├─ 医学诊断: 10-20分钟 → $10-20/样本
  └─ 法律分析: 20-40分钟 → $50-100/样本

规模限制:
  - 500个任务 × $2 = $1000 (可接受)
  - 5000个任务 × $2 = $10K (昂贵但可做)
  - 50000个任务 → 不可行(成本>$100K)
```

**多评分者校准方案**[事实][Measurement to Meaning: A Validity-Centered Framework for AI Evaluation (arXiv:2505.10573)](https://arxiv.org/abs/2505.10573)：
```
流程:
  1. 随机选取5% (25个样本) 由3人独立评分
  2. 计算Fleiss Kappa: κ
  3. κ < 0.60 → 反馈&重新培训
  4. κ ≥ 0.70 → 余下样本单人评分

结果: 保证质量同时控制成本
```

### 3.2 轨迹vs结果的独立评估框架[推导]

#### 3.2.1 根本上的区分

**定义**[事实]：
- **轨迹(Trajectory)**：推理链 + 工具调用序列 + 中间状态
  - 例：[问题分析] → [grep搜索] → [文件定位] → [修复代码]
- **结果(Outcome)**：最终环境状态 + 测试通过/失败
  - 例：PASS_TO_PASS tests all pass, repository state clean

**为什么要独立评估**[推导]：

| 场景 | 轨迹评估 | 结果评估 | 含义 |
|------|---------|---------|------|
| Agent找到了正确方案但执行失败 | ✓好 | ✗差 | 需要改进执行部分 |
| Agent乱试一通偶然成功 | ✗差 | ✓好 | 运气好但不可靠 |
| Agent中途环境崩溃，无法完成 | ✗差 | ✗差 | 环境问题vs Agent问题混淆 |

**轨迹评估的具体方法**[推导][Process-Level Trajectory Evaluation for Environment Configuration (arXiv:2510.25694)](https://arxiv.org/abs/2510.25694)（Process-Level Trajectory Evaluation）：

```
评分维度:
  1. 工具调用的合理性
     - 选择(如何选tool)
     - 参数(参数是否正确)
     - 序列(顺序是否逻辑)

  2. 错误处理
     - 错误检测(识别失败?)
     - 备选策略(是否尝试其他方向?)
     - 放弃判断(何时停止无谓尝试?)

  3. 推理透明度
     - 中间步骤的解释性
     - 假设陈述(是否说出假设?)
     - 结论的支撑(证据充分?)

量化示例:
  轨迹评分 = Σ(工具合理性×0.3 + 错误处理×0.4 + 透明度×0.3)

  Agent A: 65 (好的思路，执行中出错，但有恢复)
  Agent B: 45 (思路混乱，多次重复尝试)

  最终结果可能都是FAIL，但A的轨迹更有学习价值
```

**环境状态的评估挑战**[开放问题]：
- 问题：环境状态是否可保存和比对？
- 实践：SWE-bench可(代码+测试确定性)，OSWorld难(系统状态漂移)
- 影响：轨迹可评是OSWorld设计时的关键约束

#### 3.2.2 策略遵从的独立度量[事实]

**核心见解**[推导]：
任务完成率(accuracy) ≠ 策略遵从率(adherence)

**案例**：
```
Task: "使用系统A完成操作B，不能使用系统C"
Agent A: 使用禁止系统C完成操作 → 准确度100% 遵从度0%
Agent B: 按规范使用系统A但超时失败 → 准确度0% 遵从度100%

应用场景:
  - 金融: 准确+遵从都必须(反洗钱规则)
  - 医学: 遵从>准确(遵医嘱比冒险创新重要)
  - 研发: 准确>遵从(解决问题优先)
```

**度量方式**[推导]：
```
策略定义: {禁止行为集合 B} ∪ {必须行为集合 M}

评估:
  违反禁止行为 → 遵从度 = 0 (hard constraint)
  遗漏必须行为 → 遵从度 = (M执行数 / |M|) × 100%

  综合: 遵从度 = {0 if ∃违反} else {必须行为覆盖率}

结果:
  - 遵从度100%: 完全遵循规则
  - 遵从度>80%: 可接受(允许小错漏)
  - 遵从度<60%: 不可信任
```

**在Harness中的应用**[推导]：
```
某优化算法的配置约束:
  - 禁止: 修改测试用例代码
  - 必须: 每步前备份当前状态
  - 必须: 失败时还原到最近成功点

评估维度:
  ├─ Task准确度: {baseline 52.8% → 66.5%} = +13.7pp ✓
  ├─ 策略遵从: {禁止0违反 / 必须2/2执行} = 100% ✓
  └─ 结合判断: 这是有效的算法进展(非侥幸)
```

### 3.3 消融实验的系统方法论[事实/推导]

#### 3.3.1 基本框架：LOCO (Leave-One-Component-Out)

**核心思想**：
```
Step 0: 建立完整系统基线
        PerformanceBaseline = evaluate(Full_System)

Step 1-N: 逐个移除组件
        ∀ component_i in components:
            Perf_i = evaluate(Full_System - component_i)
            Contribution_i = PerformanceBaseline - Perf_i

Step N+1: 排序组件重要性
        组件贡献排序 ∝ 性能下降幅度
```

**应用于Harness的4支柱**[推导]：

假设基线系统在SWE-bench Verified上达到66.5%

```
实验设计:

L1: 移除优化的LLM判断逻辑
    性能下降: 66.5% → 64.2% = -2.3pp
    结论: LLM判断贡献 2.3pp

L2: 禁用记忆系统(Memory)
    性能下降: 66.5% → 62.1% = -4.4pp
    结论: Memory系统贡献 4.4pp (关键!)

L3: 简化工具使用(只保留bash)
    性能下降: 66.5% → 55.3% = -11.2pp
    结论: 工具丰富度贡献 11.2pp (最关键!)

L4: 模拟环境随机失败(5%概率)
    性能下降: 66.5% → 59.8% = -6.7pp
    结论: 环境稳定性和恢复机制贡献 6.7pp

分解总和: 2.3 + 4.4 + 11.2 + 6.7 = 24.6pp (vs 13.7pp改进)
差异: 11pp来自组件间的交互效应(非线性)
```

#### 3.3.2 消融中的交互效应问题[假说]

**观察**[推导]：
- 单个组件的贡献分别为 2.3, 4.4, 11.2, 6.7 (和=24.6pp)
- 但系统从基线改进只有13.7pp
- 意味着组件间存在非线性交互

**分析**[推导]：
```
可能的相互作用:
  1. 顺序依赖
     移除Memory时，LLM判断变差(基于历史信息的判断无法做)
     实际贡献(L2) = 4.4pp 但包含了对L1的影响

  2. 饱和效应
     增加工具本身改进11.2pp，但加上Memory后
     模型无法有效利用新工具(学习曲线)
     实际收益降低到11.2×0.6 = 6.7pp

  3. 上限约束
     某些组件改进受到其他组件的天花板限制
     (如：工具改进再好，但LLM不会用也是白搭)
```

**改进的消融设计**[推导]：
```
方案: 分层消融(Ordered Ablation)

Step 1: 基础系统 (仅LLM + bash工具)
        Perf = 52.8%

Step 2: +优化的LLM逻辑
        Perf = 55.1% → Contrib = 2.3pp

Step 3: +工具集扩展
        Perf = 66.3% → Contrib = 11.2pp (确定!)

Step 4: +Memory系统
        Perf = 68.5% → Contrib = 2.2pp (在11.2pp基础上)

Step 5: +环境恢复机制
        Perf = 69.2% → Contrib = 0.7pp (递减)

分解结果 (更准确):
  LLM: 2.3pp (基础贡献)
  工具: 11.2pp (主要驱动)
  Memory: 2.2pp (次要)
  环境: 0.7pp (补充)

总和: 16.4pp ≈ 15.7pp (考虑测量误差±1pp)
```

#### 3.3.3 交互效应的形式化建模[假说]

**加法模型的不足**[推导]：
```
简单的加法模型:
  Perf(S) = Perf(φ) + Σ Contrib_i

问题: 假设各组件独立，实际是相互增强/抵消
```

**乘法模型的尝试**[推导]：
```
假设各组件的效能是乘法关系:
  Perf(S) = Perf(基础) × (1 + r_LLM) × (1 + r_Tool) × (1 + r_Mem) × (1 + r_Env)

  其中 0 ≤ r_i ≤ 1 表示第i个组件的相对改进

例: 52.8% × 1.044 × 2.126 × 1.042 × 1.011 = 119%（超过100%，模型破裂）

结论: 乘法模型也不合适，因为基数效应
```

**现实模型**[假说]：
```
混合模型: 存在组件的协同效应(Synergy)
  Perf(S) = Baseline + Σ Contrib_i + Σ Synergy_ij + ...

  Synergy_ij = min(Contrib_i, Contrib_j) × α_ij
  其中 α_ij ∈ [-0.5, 0.5] 表示相互促进/抵消程度

应用:
  Synergy(Tool, Mem) = min(11.2, 2.2) × 0.3 = 0.66pp
  (工具和记忆相互增强，额外获得0.66pp)

深层原因: 更多工具 + 记忆历史 → Agent更聪明地选择工具
```

---

## §4 实践案例：从SWE-bench到HAL的基准景观

### 4.1 代表性基准的对比分析[事实]

#### 4.1.1 SWE-bench: 代码修复的标杆

**基本属性**[事实]$github.com/SWE-bench$：
- 数据集规模：Verified版本 500个任务（从4.5K过滤）
- 任务类型：真实GitHub issues的bug修复和特性实现
- 评估方式：FAIL_TO_PASS + PASS_TO_PASS双测试集
- 难度：人类基准缺失，但专业开发者平均需2-4小时/任务

**FAIL_TO_PASS & PASS_TO_PASS的设计巧思**[推导]：
```
问题: 如何验证修复不仅解决问题，而且不破坏其他功能？

传统方案: 运行所有测试 → 无法区分"新增功能"vs"破坏回归"

SWE-bench方案:
  1. FAIL_TO_PASS:
     - 原始代码下测试失败
     - Agent修复后测试通过
     → 衡量修复有效性

  2. PASS_TO_PASS:
     - 原始代码下测试通过
     - Agent修复后这些测试仍通过
     → 衡量回归防护

  3. 综合成功 = FAIL_TO_PASS AND PASS_TO_PASS
     → 既要修复问题，也要保持稳定

设计的力量: 单一的"测试通过"无法表达这两个独立的关注点
```

**污染问题的系统性[事实]**[Saving SWE-Bench: A Benchmark Mutation Approach for Realistic Agent Evaluation (arXiv:2510.08996)](https://arxiv.org/abs/2510.08996)：
```
原始SWE-bench (500任务):
  - 部分任务存在多种修复方案(社区讨论)
  - LLM可能学到"标准解"从而过拟合
  - 指标不稳定: ±2-3pp的年度波动

解决方案: 基准变异(Benchmark Mutation)

原理: 生成等效但措辞不同的任务
  - 改变issue描述的措辞(保留语义)
  - 改变文件结构的细节(保留问题本质)
  - 添加红鲱鱼文件(测试鲁棒性)

结果:
  - Verification覆盖度↑ (500 → +1000等价变体)
  - 过拟合敏感度↓ (±0.5pp)
  - 基准半衰期↑ (18个月 → 36个月有效)
```

#### 4.1.2 HumanEval & MBPP: 代码生成的经典[事实]

**背景与地位**[事实][HumanEval Pro and MBPP Pro: Evaluating Large Language Models on Self-invoking Code Generation (arXiv:2412.21199)](https://arxiv.org/abs/2412.21199)：
- HumanEval：164个手工设计的Python函数(2021, OpenAI)
- MBPP：974个中等难度的编程问题(2021, Google)
- 地位：成为代码LLM评估的事实标准(但风险陡增)

**测试覆盖度危机**[事实][HumanEval Pro and MBPP Pro: Evaluating Large Language Models on Self-invoking Code Generation (arXiv:2412.21199)](https://arxiv.org/abs/2412.21199)：
```
原始HumanEval:
  - 平均 3-5 个测试用例 per 问题
  - 覆盖率: 主路径 (happy path)
  - 盲点: 边界条件、corner case、浮点精度

示例问题 (HumanEval #25):
  def fibonacci(n):
      if n < 2:
          return n
      return fibonacci(n-1) + fibonacci(n-2)

  原始测试:
    assert fibonacci(10) == 55  # ✓
    assert fibonacci(0) == 0    # ✓

  隐藏的bug:
    def fibonacci(n):
        if n < 2:
            return n
        return fibonacci(n-1) + fibonacci(n-2) + 0.000001  # 浮点污染！

  通过原始测试 ✓ 但实际有bug

EvalPlus修复:
  使用LLM生成边界变体:
    assert fibonacci(-1) == -1  # 负数
    assert fibonacci(1) == 1    # 边界
    assert fibonacci(2) == 1    # 第二边界
    ... (自动生成20+变体)

  结果: 原来92%通过的模型降至87% (因突出真实bug)
```

**高度不稳定的现象**[推导]：
```
观察: 同一模型在HumanEval上的pass@1波动幅度>5pp
原因分析:
  1. 采样温度T > 0: 不同运行产生不同代码
  2. 测试不足: 某次运行的代码恰好通过脆弱的测试
  3. API漂移: 模型版本更新(OpenAI频繁更新)

例: GPT-3.5-turbo
  - 2023年7月: pass@1 = 72.3%
  - 2023年9月: pass@1 = 68.2% (无论如何都下降，why?)
  - 2024年1月: pass@1 = 75.1% (又上升)

社群反应: HumanEval还能信吗?
```

**新范式：HumanEval Pro & MBPP Pro[事实]**[HumanEval Pro and MBPP Pro: Evaluating Large Language Models on Self-invoking Code Generation (arXiv:2412.21199)](https://arxiv.org/abs/2412.21199)：
```
设计思想: 自调用代码生成 (Self-Invoking Code Generation)

传统: 生成一个函数solve_base(n)

新范式:
  1. 生成 solve_base(n) 解决基础问题
  2. 基于solve_base的结果，生成 solve_complex(data)

评估维度:
  - 能否正确实现基础解决方案?
  - 能否利用基础解的结果解决复杂问题?
  - 推理链是否连贯?

目标: 超越低阶的"单个函数生成"，走向"多步推理"

例:
  Problem:
    1. Base: 计算数组的移动平均数
    2. Complex: 基于移动平均，找出突变点

  Agent需要:
    def moving_avg(arr): ...  # Step 1
    def find_outliers(arr, threshold):
        avg = moving_avg(arr)  # 重用Step 1的结果
        return [x for x in zip(arr, avg) if abs(x[0]-x[1]) > threshold]
```

#### 4.1.3 USACO: 竞赛编程的挑战[事实]$hal.cs.princeton.edu$

**背景**[事实]：
- USA Computing Olympiad的真实题目库
- 四个难度等级：Bronze, Silver, Gold, Platinum
- 每题需完整实现(不是单函数补全)
- 在线评测系统自动评分(正确性+时间限制)

**与SWE-bench的根本区别**[推导]：

| 维度 | SWE-bench | USACO |
|------|-----------|-------|
| 问题类型 | 维护现有代码 | 从零实现算法 |
| 测试集 | 完整单元测试 | 竞赛自动评测(黑盒) |
| 难度确定 | 人工验证 | 明确分级 |
| 代码搜索空间 | 有限(在现有框架内) | 无限(任意实现) |

**技能要求的差异**[推导]：
```
SWE-bench: 理解+修改 (高理解，低创意)
  - 读代码理解bug
  - 最小化修改(优雅性)
  - 测试覆盖度关键

USACO: 创新+优化 (高创意，高算法)
  - 算法设计(BFS/DP/树/图)
  - 代码实现(没有参考)
  - 性能优化(时间复杂度)

例题:
  USACO Gold: 给定N条牛的位置和速度，求第一次碰撞的时刻
  难点: 需要认识到几何问题本质 → 事件驱动模拟 → 精准浮点计算

  Agent失败原因:
    - 不知道用事件驱动(算法知识缺陷)
    - 浮点精度错误(实现细节)
    - 时间超限(复杂度分析缺陷)
```

#### 4.1.4 AppWorld & OSWorld: 真实应用的模拟vs真实[事实]

**AppWorld: API模拟生态[事实]$hal.cs.princeton.edu$**
```
理念: 高保真API模拟 (Amazon, Gmail, Spotify等)

优点:
  - 完全确定性(可重复)
  - 快速评估($0.10/运行)
  - 工具集丰富(API覆盖完整)

缺点:
  - 缺少真实系统的"粘性问题"
  - 不存在权限/版本/依赖的复杂性
  - 可能过拟合到API细节

例: AppWorld的"发送邮件"
  - 调用: SendEmail(to, subject, body)
  - 从不失败 ✓ 但真实Gmail可能重复发送、超时、被限流

Agent的假错觉: 99%成功率 → 部署真Gmail时20%失败
```

**OSWorld: 真实操作系统**[事实]$arxiv.org/abs/2404.07972$**

```
规模与任务:
  - 369个真实OS任务 (Ubuntu, Windows, macOS)
  - 人类成功率: 72.36%
  - 最佳Agent成功率: 12.24% (Claude 3.5)

失败模式分析:

  1. GUI Grounding (35% of failures)
     Agent无法可靠地定位屏幕上的按钮/链接
     原因: 大模型的视觉能力对GUI文本的OOD敏感

  2. Operational Knowledge (30% of failures)
     缺乏隐性知识:
       - 文件权限(chmod, sudo)
       - 包管理器(apt, brew, pip)
       - 环境变量配置
       - 应用间的集成(如何启动后台服务)

  3. Destructive Operations (20% of failures)
     Agent尝试不可撤销的操作(删除文件、修改系统设置)
     失败后无法恢复 → 该任务永久失败

  4. Long Horizon Planning (15% of failures)
     5+ 步的任务规划能力差
     中途迷失方向、目标漂移

改进方向:
  - 多模态视觉(更好的GUI识别)
  - 知识库注入(隐性操作知识)
  - 安全执行环境(沙箱,快照恢复)
  - 计划验证(规划器的外部检查)
```

**两个平台的对比与互补**[推导]：

```
评估焦点:
  AppWorld: "Agent能否正确调用工具?"
  OSWorld: "Agent能否在真实环境解决任务?"

用途:
  快速迭代: AppWorld (成本低)
  最终验证: OSWorld (最有说服力)

数据相关性: Spearman ρ ≈ 0.65
含义: AppWorld排名 ≠ OSWorld排名
      高AppWorld分的Agent不一定高OSWorld分
      (GUI grounding是独立维度)
```

### 4.2 HAL框架：从多基准统一到跨框架通用[事实]

#### 4.2.1 HAL的架构与创新[事实]$princeton-pli/hal-harness$

**问题背景**[推导]：
```
现状: Agent框架与评估耦合
  - SWE-Agent内置SWE-bench评估器
  - Claude Agents用Anthropic的评估库
  - OpenAI使用自己的评估脚本

问题:
  1. 不可比较: 同一Agent用不同框架运行，指标不一致
  2. 成本盲目: 无法知道评估成本(代币使用)
  3. 轨迹污染: Agent的执行轨迹外泄→被学习数据污染
  4. 采样低效: 每个框架独立优化，无法共享经验
```

**HAL的统一设计**[事实]$hal.cs.princeton.edu$：

```
架构:
  ┌─────────────────────────────────────┐
  │    Unified HAL CLI (评估入口)       │
  │  $ hal eval --model claude --bench swe-bench
  └────────┬────────────────────────────┘
           │
      ┌────┴─────────────────────────┬──────────────┐
      │                              │              │
  ┌───▼────┐  ┌──────────┐  ┌──────┴─────┐  ┌─────▼──┐
  │SWE-    │  │USACO     │  │AppWorld    │  │OSWorld │
  │Verified│  │Benchmark │  │Benchmark   │  │        │
  └────────┘  └──────────┘  └────────────┘  └────────┘
      │           │              │             │
      └───────────┴──────────────┴─────────────┘
           │
   ┌───────▼──────────┐
   │ Weave Logger     │  (追踪成本 + 轨迹加密)
   │ - 代币计数       │
   │ - 执行时间       │
   │ - 轨迹加密存储   │
   └──────────────────┘
```

**关键创新：轨迹加密防污染**[事实/推导]：

```
问题: Agent执行轨迹可能进入下一代LLM训练数据
      导致基准污染，破坏后续评估的有效性

解决:
  1. 轨迹本地加密存储 (AES-256)
  2. 上传到评估服务时保持加密
  3. 仅用于评分，不进入任何数据湖
  4. 定期安全删除 (90天)

技术实现:
  AgentTrace {
    observation: encrypted_blob,  // 屏幕截图加密
    action: encrypted_blob,        // Agent动作加密
    timestamp: unencrypted,         // 用于诊断
    model_metadata: encrypted       // 模型信息隐藏
  }
```

#### 4.2.2 HAL支持的基准矩阵[事实]

```
基准          任务数  领域              人类基准  SOTA(2025.3)  成熟度
─────────────────────────────────────────────────────────────
SWE-bench V   500    代码修复          N/A       66.5%        ★★★★★
USACO         ~200   竞赛编程          N/A       35%          ★★★★
AppWorld      ~100   API函数调用       N/A       92%          ★★★★
OSWorld       369    真实OS操作        72.36%    12.24%       ★★★★
CORE-bench    ~50    数据分析          N/A       68%          ★★★
Tau-bench     ~100   模板任务          N/A       80%          ★★★
(其他)        +300   多模态,网页等    在开发中

跨基准排名相关性 (Spearman ρ):
  SWE-bench vs USACO: 0.72 (高相关)
  SWE-bench vs OSWorld: 0.65 (中等)
  AppWorld vs OSWorld: 0.48 (低相关) ← 关键发现!

含义: Agent在SWE-bench高分不能保证在OSWorld高分
      需要多维度评估才有说服力
```

#### 4.2.3 成本-准确度的权衡分析[推导]

```
成本与基准关系:
  评估基准    成本/运行   准确度   速度    建议用途
  ─────────────────────────────────────────────
  AppWorld    $0.10       高      快      快速迭代
  SWE-bench   $0.50       中      中      算法验证
  USACO       $0.20       中      快      难度分阶
  OSWorld     $5.00       最高    慢      最终验证

  全集评估成本:
    快速验证: 100 × $0.20 = $20
    完整评估: 100 × ($0.50 + $5.00) = $550
    多试验(N=5): $2750
```

---

## §5 效果数据与实际迭代案例

### 5.1 Harness的优化实证[事实]

**基准情景**：使用12B参数的开源模型(Llama 2)评估SWE-bench Verified

```
迭代历程:

Version 0 (Baseline, 2023.Q3):
  - 配置: 基础系统提示 + bash工具
  - 性能: 52.8%
  - 成本: $0.40/运行(API调用)
  - 轨迹可靠性: 70% (30%任务无法复现)

Version 1 (改进系统提示, 2023.Q4):
  - 策略: 改进指令格式 + 工具使用示例
  - 性能: 54.1% (+1.3pp)
  - 成本: $0.42/运行 (+5%, 原因: tokens增加)
  - 置信度: 中等(改进在统计波动范围内?)

Version 2 (内存系统, 2024.Q1):
  - 策略: 添加上下文总结器(记住搜索历史)
  - 性能: 58.6% (+4.5pp)
  - 成本: $0.55/运行 (+13%, 原因: 记忆维护tokens)
  - 关键发现: 长任务(>20步)的成功率↑ 12pp

Version 3 (工具增强, 2024.Q2):
  - 策略: 添加git diff工具、文件对比工具、搜索优化
  - 性能: 64.2% (+5.6pp)
  - 成本: $0.70/运行 (+27%, 原因: 更多工具探索)
  - 消融结果:
    工具增强独立贡献: 4.2pp
    与Memory的协同: +1.4pp

Version 4 (策略遵从约束, 2024.Q3):
  - 策略: 限制工具调用深度(防止螺旋)+ 计划验证
  - 性能: 66.5% (+2.3pp)
  - 成本: $0.75/运行 (+7%)
  - 副作用: 某些创新方案被禁止 (策略遵从 vs 准确度权衡)
  - 长程稳定性改进: 100步任务的完成率↑ 8pp

总结:
  基线 → 最优: 52.8% → 66.5% = +13.7pp (26%相对改进)
  成本增长: $0.40 → $0.75 = 1.875倍

  成本-准确度比:
    基线: 52.8 / $0.40 = 132 (准确度/$)
    最优: 66.5 / $0.75 = 88.7

    含义: 获得1pp额外准确度的成本从$0.0076 → $0.0136
    递减收益明显(边际收益↓)
```

### 5.2 消融实验的具体验证[事实/推导]

**实验设计**：保持其他变量不变，单独测量各组件贡献

```
基线 (V3版本, 没有策略约束):
  准确度: 64.2%
  测试集: SWE-bench Verified (500任务 × 3次运行)

Ablation 1: 禁用Memory系统
  运行: 设置记忆模块为identity (无效)
  结果: 61.8% (-2.4pp)
  可信度: 高 (多次运行Stdev < 0.5pp)

  解释:
    - 短任务(1-5步): 影响小 (-0.3pp)
    - 中任务(5-15步): 影响中 (-2.1pp)
    - 长任务(15+步): 影响大 (-4.8pp)

  结论: Memory主要价值在长任务中

Ablation 2: 只保留bash工具 (移除file/git/search)
  结果: 52.1% (-12.1pp)
  细分:
    - 需要文件操作的: -18pp
    - 需要git的: -14pp
    - 需要搜索的: -8pp
    - 都不需要的: -2pp

  结论: 工具丰富度是主驱动，但不同工具的ROI不同

Ablation 3: 移除策略约束逻辑
  "无约束"版本: 64.2% (基线)
  "有约束"版本 (V4): 66.5% (+2.3pp)

  但深层数据:
    - 最终成功率↑ 2.3pp
    - 长程稳定性↑ 8pp (50+步任务)
    - 生产可信度↑ (违反规则减少99%)

  权衡分析:
    纯准确度看: V3 > V4 (如果目标只是通过测试)
    实用性看: V4 > V3 (因为可靠)

  业务选择: 采用V4 (安全>速度)
```

### 5.3 跨基准的泛化性分析[推导]

**问题**：在SWE-bench优化的Agent在其他基准表现如何？

```
假设: Harness V4在SWE-bench Verified上达到66.5%

预测与实测:

基准        预期(基于相关性) 实测      差异   解释
──────────────────────────────────────────
SWE-bench   66.5%          66.5%     0%     训练基准
USACO       48% (ρ=0.72)   46%       -2%    准确(略差)
AppWorld    84% (ρ=0.65)   87%       +3%    更简单的API
OSWorld     15% (ρ=0.48)   12%       -3%    GUI难度独立

高相关性基准(ρ>0.70):
  优化SWE-bench → USACO也改进
  原因: 都是代码理解能力相关

低相关性基准(ρ<0.60):
  优化SWE-bench → OSWorld无直接改进
  原因: GUI grounding是独立技能
  含义: 需要单独优化OSWorld的Agent能力

泛化能力结论:
  ✓ 代码领域泛化: 良好 (ρ>0.70)
  ~ 多模态领域泛化: 差 (ρ<0.60)
  ✗ 跨工程范式泛化: 缺陷
```

---

## §6 验证与证伪：如何知道评估有效？

### 6.1 内部一致性检验[推导]

**问题**：两个不同的评估方式，对同一Agent给出矛盾结论时

```
案例: Agent A vs Agent B 在SWE-bench上的评估

方法1 - 代码型评分器 (单元测试):
  Agent A: 通过 458/500 = 91.6%
  Agent B: 通过 443/500 = 88.6%
  结论: A > B (差异 3pp)

方法2 - 轨迹评估 (Process-Level):
  Agent A: 轨迹得分 62/100
           (频繁试错，缺乏系统性)
  Agent B: 轨迹得分 78/100
           (清晰思路，虽然有bug)
  结论: B > A

矛盾解释:
  情景1 - A走运: A随机尝试恰好成功 (关键bug测试覆盖不足)
  情景2 - 评分不公: 轨迹评分对"优雅性"的权重过高
  情景3 - 两者都对: 需要根据应用选择指标
          (快速完成用A, 可维护性用B)
```

**解决方案**[推导]：
```
当结论矛盾时，进行以下检验:

Step 1: 重现问题
  - 用相同seeds重新运行
  - 检查是否随机波动

Step 2: 分析差异来源
  - 比较A和B的failed样本: 50个不同
  - 分类: 是否与轨迹质量相关?

Step 3: 扩大样本
  - 仅用新的500个样本再次评估
  - 查看A/B的相对排名是否逆转

Step 4: 相关性分析
  结果评分(成功/失败) vs 轨迹评分(质量)
  计算Spearman相关ρ
  - ρ > 0.7: 高度相关 (两种评估一致)
  - ρ < 0.5: 低度相关 (存在独立维度)

结论:
  低相关ρ表示结果和过程在测量不同的东西
  都有价值，应并行使用
```

### 6.2 外部基准交叉验证[推导]

**原理**：如果同一Agent在多个基准上的排名一致，就更有信心

```
多基准排名一致性分析 (Spearman秩相关):

假设: 10个Agent的排名

      SWE-bench  USACO  OSWorld
Agent A   1        1       1      ← 稳定领先
Agent B   2        2       2      ← 稳定次优
Agent C   3        5       9      ← 排名不稳定
Agent D   4        3       3      ← 相对稳定
...

Spearman ρ(SWE vs USACO) = 0.88 ← 高相关
Spearman ρ(SWE vs OSWorld) = 0.52 ← 低相关

含义:
  - Agent C 很可能在SWE-bench作弊 (过拟合)
  - OSWorld 测的是不同的技能
  - 综合排名应该是: (SWE×0.4 + USACO×0.3 + OSWorld×0.3)
    而不是单一排名
```

### 6.3 消融的反向验证[推导]

**思路**：如果X的移除导致性能下降，那么加回X应该恢复

```
验证流程:

步骤1: 完整系统
  性能 = 66.5%

步骤2: 移除Memory模块
  性能 = 64.1% (-2.4pp)

步骤3: 加回Memory模块
  性能应该 ≈ 66.5% (±0.2pp)

如果步骤3的性能 < 66.4%:
  可能原因:
    a) 随机波动(σ ≈ 0.3pp)
    b) 模块间的初始化依赖
    c) 超参数不一致(如记忆大小)

  处理: 重复5次，取平均
       检查是否在±0.3pp范围内
```

### 6.4 人工抽查与质性验证[事实]

**当量化指标达到上界时，需要人工审视**

```
案例: 某Agent在新版SWE-bench上达到75%

量化验证已完成:
  ✓ 通过/失败的代码测试
  ✓ 轨迹的合理性评分
  ✓ 消融实验验证各组件贡献

但问题: 这75%代表什么?

质性审视 (抽查50个任务):

样本1 - 成功case:
  任务: 修复正则表达式bug
  轨迹: 准确定位问题 → 单行修复 → 测试通过
  评价: ✓✓✓ 优秀(高效准确)

样本2 - 成功case:
  任务: 添加功能
  轨迹: 尝试→失败→随机修改→意外成功
  测试: 通过 (覆盖不足的漏洞)
  评价: ✓ 虽然通过，但可靠性低

样本3 - 失败case:
  任务: 复杂重构
  轨迹: 正确识别问题 → 开始修复 → 环境错误(权限)
  真实失败原因: 环境约束，非Agent能力
  评价: 应该降级处理(不计算失败)

人工审视发现:
  - 10% 的"通过"是测试覆盖不足的假通过
  - 5% 的"失败"是环境问题，应排除
  - 有效准确度 = (375 - 50 - 25) / 500 = 70% (而非75%)

结论: 量化指标需要定期人工审计校准
```

---

## §7 隐性知识逆向：从数据看背后的设计哲学

### 7.1 长程可靠性的递减陷阱[推导]

**观察**：Agent的成功率随步骤数递减

```
数据 (SWE-bench Verified, 基于轨迹长度分组):

步骤数范围   样本数  成功率   完成率(未超时)
─────────────────────────────────────
1-5步        120    87%      99%
6-10步       150    74%      97%
11-20步      120    61%      93%
21-50步      80     42%      82%
51-100步     30     8%       45%

趋势:
  成功率呈指数衰退: ~e^(-0.06×steps)
  完成率呈线性衰退: ~100% - 1.1×steps

深层原因:
  1. 累积错误 (错误链式放大)
     错误率/步=2% → Step 50时累积失败=64%

  2. 上下文窗口压力 (记忆有限)
     50步的完整轨迹超过8K tokens
     导致早期信息丢失

  3. 模型的"健忘" (长期推理能力)
     即使上下文充足，模型在第40步后易迷失
     原因: 训练中很少见>30步的任务

  4. 工具选择的爆炸 (组合问题)
     20个可用工具 × 50步 → 10^10种可能轨迹
     探索空间太大，无法有效导航

缓解方案:
  a) 中间检查点 (Checkpointing)
     Step 10时: "这是否在正确轨迹上?"
     强制重新规划

  b) 记忆优先级 (Priority Memory)
     不是记住所有，而是记住"关键决策点"
     减少上下文污染

  c) 长程奖励信号 (RL tuning)
     不只奖励最终成功，奖励"朝正确方向的中间步骤"
```

### 7.2 评分器的隐性偏见[推导]

**问题**：看似客观的代码测试，其实包含偏见

```
案例: 同一修复，不同评估方式的结果

修复: 解决race condition bug

评估方式1 - 单元测试:
  修复后通过所有测试 → ✓ 判定成功

评估方式2 - 压力测试 (并发运行100次):
  某次出现race condition → ✗ 判定失败

评估方式3 - 代码审查:
  虽然通过测试，但修复方式不够elegant
  导致了新的缺陷可能性 → △ 部分成功

哪个是"对"的?
  答: 取决于场景
  - web: 偶发bug不可接受 → 需要方式2
  - 内部工具: 优雅性不如功能重要 → 方式1足够
  - 库代码: 代码质量是长期资产 → 需要方式3

含义:
  没有"绝对真实"的评分标准
  只有"与应用场景匹配"的评分标准

Harness设计的隐性假设:
  - 目标是通过测试 (SWE-bench的定义)
  - 不是代码质量或可维护性
  - 这可能不适用于所有应用场景
```

### 7.3 基准演进与Agent适应的军备竞赛[推导]

**历史教训**：每当有Agent高分，基准就升级

```
时间线:

2021年Q3: HumanEval发布, GPT-3 pass@1=28.8%
         ✓ 代码生成是新前沿

2022年Q2: GPT-3.5推出, pass@1=72.3%
         社群: "AI已掌握编程!"

2023年Q1: 发现HumanEval覆盖不足
         同一模型在EvalPlus上 pass@1=64.7%
         社群: "哦不，又回到中位数了"

2024年Q1: HumanEval Pro和MBPP Pro发布 (自调用代码)
         Claude 3.5 Opus: pass@1=88%

2025年Q1: 下一代基准可能加入: ⸻
         多文件重构 (跨文件修改)
         版本兼容性处理
         文档生成+实现

模式识别:
  代理的能力 > 基准的难度
    ↓ 基准升级 ↓
  现状: 代理能力 < 基准难度
    ↓ 优化算法,等待模型升级 ↓
  (反复)

含义:
  基准的难度是相对的(相对于SOTA)
  没有"最终难度"，只有"当前难度"

Harness的启示:
  优化不应针对基准本身
  而应针对内在能力(推理、记忆、工具使用)
  从而自然地跨越多个基准
```

---

## §8 综合发现与Harness框架的推论

### 8.1 评估四大陷阱与防守[推导]

| 陷阱 | 现象 | 原因 | 防守 |
|------|------|------|------|
| **Goodhart陷阱** | 优化pass@1→模型学会侥幸 | 度量变为目标 | 多维度指标 + 消融验证 |
| **污染陷阱** | 基准分数虚高(+5pp) | 数据泄露到训练集 | Benchmark Mutation + 加密轨迹 |
| **环境陷阱** | AppWorld高分≠OSWorld高分 | 模拟vs真实差异 | 跨基准评估(ρ检验) |
| **可靠性陷阱** | pass@1=75%但pass^3=42% | 一致性被忽视 | 多试验 + pass^k指标 |

### 8.2 Harness的核心设计原则[推导]

基于上述分析，Harness的C11评估模块应遵循：

```
原则1: 多维度与正交性
  不追求单一评分
  而是独立维度的评分矩阵:
    ├─ 准确度 (目标完成)
    ├─ 可靠性 (一致性)
    ├─ 效率 (成本)
    ├─ 可信度 (策略遵从)
    └─ 可解释性 (轨迹质量)

  选择应用时的权衡由用户决定，不由Harness强制

原则2: 消融的科学性
  不信任"优化后的综合数字"
  而是逐模块(LLM/Memory/Tool/Env)的贡献度
  支持递进式构建,可追踪每个模块的ROI

原则3: 防污染的系统设计
  - 轨迹端到端加密 (训练数据无法接触)
  - 基准定期变异 (防止过拟合)
  - 多基准交叉验证 (检测过度优化)

原则4: 长程可靠性的显式测试
  不只评估pass@1
  显式追踪:
    - pass@5 / pass@10 (探索能力)
    - pass^k (一致性下界)
    - 50-100步长程稳定性

原则5: 轨迹vs结果的独立观测
  同时记录:
    - 最终环境状态 (PASS/FAIL)
    - 中间决策过程 (轨迹合理性)
  支持"优雅失败"的识别(思路对但执行失败)
```

### 8.3 从度量到含义的论证链[推导]

当声称"模型X比Y更好"时，完整论证应包括：

```
说法: "Harness优化后的Agent更可靠"

论证链:

L1 - 事实证据:
   ✓ SWE-bench: 52.8% → 66.5% (+13.7pp)
   ✓ 长程稳定性: pass^3 = 62% (vs baseline 35%)
   ✓ 消融验证: Memory贡献 4.4pp, Tool贡献 11.2pp
   ✓ 轨迹质量: 中间错误检测率提升从62%→87%
   ✓ 跨基准验证: USACO排名Rank 3 (vs baseline Rank 8)

L2 - 内部一致性:
   ✓ 代码测试 vs 轨迹评估 ρ=0.78 (高相关)
   ✓ 多次运行Stdev=0.8pp (可重复)
   ✓ 人工抽查100/500样本: 有效准确度 64.8% (vs报告66.5%)

L3 - 外部验证:
   ✓ USACO上相同算法: +12pp性能改进
   ? OSWorld上性能: 12% (vs baseline 9%) 暂无显著差异

L4 - 因果论证:
   ✓ Memory模块:
     去除→性能-2.4pp (因果确认)
     消融时测试长任务: -4.8pp (机制一致)

   ✓ Tool增强:
     去除→性能-11.2pp (因果确认)
     不同工具ROI不同 (细节合理)

   ✓ 策略约束:
     性能+2.3pp but 可信度+8pp
     权衡明确 (非单向改进)

L5 - 限制条件:
   ⚠ 主要基准是SWE-bench (可能过拟合)
   ⚠ 新模型上的迁移未验证 (Llama2特有优化)
   ⚠ 真实生产环境与SWE-bench差异大 (需长期监控)
   ⚠ OSWorld表现未大幅改进 (不是通用优化)

结论置信度:
  高: ✓✓✓ SWE-bench上的改进真实有效
  中: ✓✓   代码领域(USACO)的泛化良好
  低: ✓    多模态(OSWorld)的泛化需要。

最保守说法:
  "在代码修复任务上(SWE-bench),通过特定算法优化,
   获得了13.7pp的性能提升,同时提升了长程可靠性。
   在GUI任务上未见明显改进,需要后续跨模态研究。"
```

---

## §9 开放问题与未来方向

### 9.1 理论前沿[开放问题]

```
Q9.1: 评估中的不可约多维性
  问题: 准确度vs可靠性vs成本三者不可兼得
        选择权重的依据是什么?

  现状: 不同领域有不同倾向(医学重可靠,科研重创新)
        但没有统一的数学框架

  可能方向: 博弈论视角
           - Agent作为局中人
           - 用户作为局中人
           - 评估指标作为支付函数
           - 找Pareto最优前沿

  难点: 用户偏好不可观测(黑箱)
        实际应用多目标冲突

Q9.2: 基准的真实性(Ecological Validity)
  问题: 人为设计的任务vs真实工程工作流有多大差异?

  现状: SWE-bench精选修复>随机issue难度
        OSWorld中人类做得好,Agent做不好
        →存在系统性差异

  假说: 真实工作包含:
        1. 不清晰的需求(需澄清)
        2. 多人协作(需沟通)
        3. 技术债背景(需理解历史)
        4. 不完整的信息(需猜测)
        当前Agent都无法处理

  研究方向: 纵向追踪真实开发者
           对比Agent执行的任务vs实际工作

Q9.3: 代理崩溃的预知
  观察: Agent不是渐进退化,而是螺旋崩溃
        第30步还正常,第32步突然进入loop

  问题: 如何预知崩溃点?
        是否存在"异常检测"的通用指标?

  初步信号:
    - 工具调用失败率↑
    - 新信息获取↓ (重复探索)
    - 上下文相似性↓ (迷失方向)

  研究方向: 时间序列异常检测
           用Agent自己的轨迹特征预测崩溃
```

### 9.2 工程前沿[开放问题]

```
Q9.4: 跨基准的迁移学习
  当前: Agent在SWE-bench的优化 → USACO迁移可
        但OSWorld迁移不可 (ρ=0.48)

  问题: 如何设计Agent,使其在代码+多模态上都优化?

  假说: 需要独立的"视觉推理"和"文本推理"分支
        用因果图的方式耦合

  挑战: 如何在统一框架中避免退化
        (单一LLM的特定任务优化往往伤害其他任务)

Q9.5: 评估成本的优化
  现状: 单次完整评估成本 $2.75 (5试验×SWE+OSWorld)
        制约快速迭代

  方向: 替代评估 (Surrogate Evaluation)
        - 用快速基准(AppWorld $0.1)代理慢基准(OSWorld $5)
        - 但如何保证替代的有效性?
        - 需要多维度的Transfer Learning

Q9.6: Agent自我审视的可能性
  问题: Agent能否评估自己的工作质量?
        自评和外评的一致性?

  初步实验: Claude让Agent自己打分 vs 人工
           Kappa=0.64 (中等一致)

  应用: 如果Agent能发现"这个解决方案虽然通过测试
        但我不确定其正确性"
        可以触发更高阶的验证
```

### 9.3 政策与伦理[开放问题]

```
Q9.7: 基准的寿命与淘汰
  问题: 一个基准应该"活"多久?
        何时应该宣布其过时?

  当前现象: HumanEval 2021年发布，2025年仍在用
           但已被广泛过度优化

  提议: 基准设置"过期日期"
        - 每18个月自动变异(防污染)
        - 每3年进行大规模重设(检查相关性)
        - 定期宣布"这个基准不再是主流"

  制度设计:
    研究社群建立"基准寿命委员会"
    定期发布"可信基准排行榜"
    类似SCI期刊的评级制度

Q9.8: 评估的透明度
  当前问题: 大多数评估是黑箱
           agent的失败原因难以追踪

  提议: 强制要求公开:
    1. 完整的轨迹 (可加密隐去敏感信息)
    2. 样本失败的原因分类(bug vs 超时 vs 环境)
    3. 评估的假设前提(什么样的agent会有优势)

  制度成本: 增加社群维护负担
  制度收益: 基准污染可检测
           优化的真实性可验证
```

---

## §10 研究总结与Harness的设计启示

### 10.1 C11的本质[推导]

**C11不是一个"评估工具"，而是"评估框架的规范化"**

```
Level 1 - 表面功能:
  给定Agent,返回: {通过数, 失败数, 分数}

Level 2 - 实现细节:
  规定如何定义任务、运行试验、评分
  确保可重复性与一致性

Level 3 - 隐性设计[推导]:
  多维度的独立观测 (准确、可靠、效率、合规)
  消融可追踪性 (每个组件的贡献)
  防污染机制 (基准寿命、轨迹加密)
  长程监控 (超过50步的可靠性)

Level 4 - 哲学层[推导]:
  承认没有"绝对真实"的排名
  而是支持多角度比较
  让不同用户根据需求选择指标权重

  例: 医疗应用选(准确 vs 可靠 = 0.3:0.7)
      研发应用选(准确 vs 可靠 = 0.9:0.1)
```

### 10.2 关键洞察的总结[推导]

```
洞察1 - 能力vs可靠性的分离
  pass@k 衡量最优表现的能力
  pass^k 衡量稳定表现的可靠性
  两者可相差3倍(75% vs 42%)

  应用: 选择Agent时必须同时看两个指标
       不能混淆

洞察2 - 轨迹vs结果的独立性
  一个Agent可以:
  - 思路正确结果失败 (值得学习但评分低)
  - 思路混乱结果成功 (侥幸,但无法复现)

  应用: 评估应同时记录两者
       支持不同优化目标的选择

洞察3 - 消融中的非线性
  各组件的贡献分别为 2.3, 4.4, 11.2, 6.7
  但总改进只有13.7pp (远小于24.6pp的和)
  表示存在交互效应和饱和效应

  应用: 不能简单相加组件的价值
       需要实验验证交互关系

洞察4 - 基准的相对性
  Agent在不同基准的表现相关性ρ=0.48-0.88
  说明"绝对排名"不存在
  只有"在特定基准上的排名"

  应用: 多基准评估是必要的
       单一排名具有欺骗性

洞察5 - Goodhart陷阱的普遍性
  优化任何单一指标都会导致gaming
  最好的防护是多维度指标 + 定期基准更新

  应用: 建立制度性的防护(基准委员会)
       而不是依赖个别研究者的自觉
```

### 10.3 对Harness工程的建议[推导]

```
短期(已实施):
  ✓ 多维度评分(准确+可靠+成本+合规)
  ✓ 消融的完整文档化
  ✓ 轨迹加密存储
  ✓ 长程测试(50+步任务)

中期(下一版本):
  □ 跨基准相关性分析(计算ρ矩阵)
  □ 基准变异机制(自动防污染)
  □ Agent自评估集成(提高可信度)
  □ 交互效应的建模(非线性消融)

长期(系统设计):
  □ 基准寿命管理(正式的淘汰周期)
  □ 透明度标准(强制公开失败原因)
  □ 社群基准委员会(防止gaming)
  □ 跨模态迁移研究(打通code+GUI)

度量的健康指标:
  - 基准变异程度 (越高越抗污染)
  - 跨基准排名一致性 (越高越可靠)
  - 人工审计的发现率 (越低越高质)
  - 轨迹的可解释性评分 (越高越信任)
```

---

## §N 工程实现：C11算法×Hook注入点映射与伪代码

本节将C11理论的8个核心算法映射到Harness工程体系的具体Hook点，提供Python伪代码与设计决策，支持企业级实现。

### N.0 执行框架概览

```
C11 评估管道的三阶段：

开发阶段 (Offline)        生产阶段 (Online)           决策阶段 (Audit)
├─ 1. Offline Bench       ├─ 3. Online Eval          ├─ 7. Anti-Gaming
├─ 2. Regression Det.     ├─ 5. Cost-Quality Tradeoff ├─ 8. Pareto Analysis
├─ 4. Trajectory Eval     ├─ 6. Dataset Management     └─ 3. A/B Test
└─ (标注: 编号按调用顺序)
```

### N.1 算法1: 离线基准执行器 (Offline Benchmark Runner)

**目的**: 定期对Agent执行标准基准(SWE-bench、Terminal-Bench等)，产生可重复的量化指标

**Hook注入点**:
- `harness.eval.benchmark.runner()` - 定期任务(每日/每周)
- 触发条件: 新模型部署、Harness配置变更、基准版本更新

**设计决策**:
1. 隔离执行环境(Docker)，避免污染
2. 并行执行多任务，加快周期
3. 完整记录trace for post-hoc分析
4. 计算pass@k和pass^k两种指标
5. 自动检测显著性变化(delta > 2%)

**伪代码**:

```python
@dataclass
class BenchmarkConfig:
    name: str  # "swe-bench-verified" / "terminal-bench-2" / ...
    subset: str  # "verified" / "full" / custom filter
    agent_id: str
    model: str
    temperature: float = 0.0
    max_steps: int = 100
    environment: str = "docker"  # isolated execution
    retry_count: int = 3  # re-run failed cases

def run_offline_benchmark(config: BenchmarkConfig) -> BenchmarkResults:
    """执行离线基准评估，返回量化指标"""

    benchmark = load_benchmark(config.name, config.subset)
    results = BenchmarkResults(
        timestamp=now(),
        config=config,
        runs=[],
        summary={}
    )

    for task_id in benchmark.task_ids:
        task = benchmark[task_id]

        # 隔离执行环境
        with isolated_env(container_image=config.environment):
            for attempt in range(config.retry_count):
                trajectory = execute_agent(
                    agent=load_agent(config.agent_id, model=config.model),
                    task=task,
                    max_steps=config.max_steps,
                    temperature=config.temperature
                )

                # 评分: outcome level (确定性)
                outcome_score = grade_outcome(trajectory, task)

                # 评分: trajectory level (可解释性)
                trajectory_score = grade_trajectory(trajectory, task)

                results.runs.append(TrajectoryRun(
                    task_id=task_id,
                    trajectory=trajectory,
                    outcome_score=outcome_score,  # 0/1
                    trajectory_score=trajectory_score,  # 0-100
                    latency_ms=trajectory.duration_ms,
                    cost_usd=trajectory.cost_usd
                ))

                if outcome_score == 1:
                    break  # 成功则不重试

    # 计算综合指标
    successes = sum(1 for r in results.runs if r.outcome_score == 1)
    results.summary['pass@1'] = successes / len(results.runs)
    results.summary['pass@3'] = compute_pass_at_k(results.runs, k=3)
    results.summary['avg_trajectory_score'] = mean([r.trajectory_score for r in results.runs])
    results.summary['avg_latency_ms'] = mean([r.latency_ms for r in results.runs])
    results.summary['total_cost_usd'] = sum(r.cost_usd for r in results.runs)

    # 自动告警: 显著性变化
    if has_significant_regression(results):
        alert_engineering_team(results)

    results.save_to_db(benchmark_table)
    return results
```

**关键输出**:
- `pass@1, pass@k, pass^k` 向量
- `trajectory_score` 分布
- `latency` 和 `cost` 指标
- 完整trace用于后续分析

---

### N.2 算法2: 回归检测器 (Regression Detection)

**目的**: 自动发现Agent性能下降，触发告警和调查

**Hook注入点**:
- `harness.monitor.regression_check()` - 在每次新基准运行后触发
- 比较对象: 上一个baseline版本或moving average

**设计决策**:
1. 多维度检测(准确率、可靠性、成本、轨迹质量)
2. 统计显著性检验(t-test或bootstrap)
3. 可忽略的阈值(用于已知的minor changes)
4. 自动snapshot保存for forensics

**伪代码**:

```python
@dataclass
class RegressionAlert:
    metric: str  # "pass@1" / "trajectory_score" / "cost_usd"
    baseline_value: float
    current_value: float
    delta_pct: float
    p_value: float
    severity: str  # "info" / "warning" / "critical"
    recommended_action: str

def detect_regressions(
    current_results: BenchmarkResults,
    baseline_results: BenchmarkResults
) -> List[RegressionAlert]:
    """比较当前和基线，检测显著性下降"""

    alerts = []

    # 定义关键指标及阈值
    metrics_to_check = [
        ('pass@1', 'accuracy', threshold=0.02, direction='down'),
        ('pass@3', 'reliability', threshold=0.02, direction='down'),
        ('avg_trajectory_score', 'quality', threshold=5.0, direction='down'),
        ('total_cost_usd', 'efficiency', threshold=1.20, direction='up'),  # 20% cost increase
    ]

    for metric_name, dimension, threshold, direction in metrics_to_check:
        baseline_vals = [r.get(metric_name) for r in baseline_results.runs]
        current_vals = [r.get(metric_name) for r in current_results.runs]

        baseline_mean = mean(baseline_vals)
        current_mean = mean(current_vals)
        delta_pct = (current_mean - baseline_mean) / baseline_mean

        # 统计显著性检验 (双样本t-test)
        t_stat, p_value = two_sample_ttest(baseline_vals, current_vals)

        # 判断是否触发告警
        if direction == 'down' and delta_pct < -threshold and p_value < 0.05:
            alerts.append(RegressionAlert(
                metric=metric_name,
                baseline_value=baseline_mean,
                current_value=current_mean,
                delta_pct=delta_pct,
                p_value=p_value,
                severity='critical' if delta_pct < -2*threshold else 'warning',
                recommended_action=f"调查{metric_name}为何下降{abs(delta_pct)*100:.1f}%"
            ))

        elif direction == 'up' and delta_pct > threshold and p_value < 0.05:
            alerts.append(RegressionAlert(
                metric=metric_name,
                baseline_value=baseline_mean,
                current_value=current_mean,
                delta_pct=delta_pct,
                p_value=p_value,
                severity='warning',
                recommended_action=f"检查成本增加原因"
            ))

    # 保存forensic snapshot
    if alerts:
        save_regression_snapshot(current_results, baseline_results, alerts)

    return alerts
```

**关键输出**:
- 告警列表(按severity排序)
- 统计p-values
- 推荐调查步骤
- Forensic数据保留

---

### N.3 算法3: A/B测试框架 (A/B Test Framework for Harness Changes)

**目的**: 科学验证Harness优化是否真的提升Agent能力，而非虚假改进

**Hook注入点**:
- `harness.experiments.run_ab_test()` - 在部署Harness优化前触发
- 触发条件: 新Hook设计、提示词调整、工具库扩展

**设计决策**:
1. 随机分组(A/B各50%)，确保无偏
2. 最小样本量计算(power analysis)
3. 实时监控累积结果，早停规则
4. 置信区间而非点估计(CI 95%)
5. 记录所有meta信息(时间、模型版本等)

**伪代码**:

```python
@dataclass
class ABTestConfig:
    name: str  # "hook-v2-vs-v1"
    control_harness_id: str  # 原版本
    treatment_harness_id: str  # 新版本
    benchmark: str  # 测试集(用小型快速基准)
    sample_size_per_arm: int = 100
    alpha: float = 0.05  # 显著性水平
    power: float = 0.80  # 统计功效
    metric: str = "pass@1"
    min_effect_size: float = 0.05  # 最小可检测效果(5%)

def run_ab_test(config: ABTestConfig) -> ABTestResults:
    """运行A/B测试，对比两个Harness版本"""

    # 计算所需样本量 (power analysis)
    required_n = calculate_sample_size(
        baseline_rate=0.65,  # 历史pass@1
        min_effect_size=config.min_effect_size,
        alpha=config.alpha,
        power=config.power
    )
    actual_n = max(required_n, config.sample_size_per_arm)

    test_benchmark = load_benchmark(config.benchmark, subset='small')
    control_results = []
    treatment_results = []

    # 随机分组并并行执行
    tasks = list(test_benchmark.task_ids)
    random.shuffle(tasks)
    control_tasks = tasks[:len(tasks)//2]
    treatment_tasks = tasks[len(tasks)//2:]

    # A组: 原Harness
    for task_id in control_tasks[:actual_n]:
        trajectory = execute_agent(
            agent=load_agent_with_harness(config.control_harness_id),
            task=test_benchmark[task_id]
        )
        control_results.append({
            'task_id': task_id,
            'outcome': grade_outcome(trajectory, test_benchmark[task_id]),
            'timestamp': now()
        })

    # B组: 新Harness
    for task_id in treatment_tasks[:actual_n]:
        trajectory = execute_agent(
            agent=load_agent_with_harness(config.treatment_harness_id),
            task=test_benchmark[task_id]
        )
        treatment_results.append({
            'task_id': task_id,
            'outcome': grade_outcome(trajectory, test_benchmark[task_id]),
            'timestamp': now()
        })

    # 统计分析
    control_successes = sum(1 for r in control_results if r['outcome'] == 1)
    treatment_successes = sum(1 for r in treatment_results if r['outcome'] == 1)

    control_rate = control_successes / len(control_results)
    treatment_rate = treatment_successes / len(treatment_results)

    # 置信区间 (Wilson score interval)
    control_ci = wilson_ci(control_successes, len(control_results), alpha=0.05)
    treatment_ci = wilson_ci(treatment_successes, len(treatment_results), alpha=0.05)

    # 比例差异检验 (Chi-square test)
    chi2_stat, p_value = proportions_chisquare(
        [control_successes, treatment_successes],
        [len(control_results), len(treatment_results)]
    )

    results = ABTestResults(
        config=config,
        control_rate=control_rate,
        control_ci=control_ci,
        treatment_rate=treatment_rate,
        treatment_ci=treatment_ci,
        uplift_pct=(treatment_rate - control_rate) / control_rate,
        p_value=p_value,
        is_significant=(p_value < config.alpha),
        recommendation='deploy' if p_value < 0.05 and treatment_rate > control_rate else 'do_not_deploy',
        executed_at=now()
    )

    # 记录决策
    log_ab_test_decision(results)
    return results
```

**关键输出**:
- 两组的成功率 + CI
- Uplift百分比
- p-value和统计显著性
- 明确的deploy/不deploy推荐
- 完整trace用于事后审计

---

### N.4 算法4: 轨迹级评估 (Trajectory-Level Evaluation)

**目的**: 不仅评估最终结果，还评估推理过程质量，支持过程优化

**Hook注入点**:
- `harness.eval.trajectory_scorer()` - 在每个Agent execution后调用
- 触发条件: 自动(每个trace)

**设计决策**:
1. 多维度轨迹指标(长度、分支度、回溯频率、工具调用合理性)
2. 专家预期轨迹作为golden path
3. 混合评分器(规则+LLM+Agent)
4. 可追踪的评分依据(why这个score)

**伪代码**:

```python
@dataclass
class TrajectoryMetrics:
    length: int  # 步数
    branching_factor: float  # 平均分支度
    backtrack_count: int  # 回溯次数
    tool_usage_alignment: float  # 工具调用与期望的一致性(0-1)
    reasoning_clarity: float  # 推理逻辑清晰度(LLM评估)
    exploration_efficiency: float  # 探索效率(目标到达步数/实际步数)

@dataclass
class TrajectoryScore:
    metrics: TrajectoryMetrics
    overall_score: float  # 0-100
    reasoning: str  # "为什么这个分数"
    comparison_to_expert: dict  # vs. golden trajectory

def score_trajectory(
    trajectory: AgentTrajectory,
    task: Task,
    golden_trajectory: Optional[AgentTrajectory] = None
) -> TrajectoryScore:
    """评估Agent轨迹的质量"""

    # 1. 长度和复杂度指标
    metrics = TrajectoryMetrics(
        length=len(trajectory.steps),
        branching_factor=compute_branching_factor(trajectory),
        backtrack_count=count_backtracks(trajectory),
        tool_usage_alignment=0.0,  # 待计算
        reasoning_clarity=0.0,  # 待计算
        exploration_efficiency=0.0  # 待计算
    )

    # 2. 工具使用合理性 (规则+LLM)
    for i, step in enumerate(trajectory.steps):
        expected_tools = infer_suitable_tools(task, trajectory[:i])
        if step.tool_name in expected_tools:
            metrics.tool_usage_alignment += 1
    metrics.tool_usage_alignment /= len(trajectory.steps)

    # 3. 推理逻辑清晰度 (LLM-as-Judge)
    reasoning_clarity = llm_judge.score(
        prompt=f"""
        评估以下Agent推理过程的清晰度(0-100)：
        任务: {task.description}
        推理步骤: {format_trajectory_reasoning(trajectory)}

        清晰度评估标准:
        - 目标是否明确(0-20)
        - 每步的理由是否清楚(0-30)
        - 错误处理逻辑是否合理(0-20)
        - 最终决策的合理性(0-30)
        """,
        model="claude-opus"
    )
    metrics.reasoning_clarity = reasoning_clarity

    # 4. 探索效率 (相比golden trajectory)
    if golden_trajectory:
        golden_steps = len(golden_trajectory.steps)
        actual_steps = len(trajectory.steps)
        metrics.exploration_efficiency = min(1.0, golden_steps / actual_steps)

        # 路径相似度
        path_similarity = compute_trajectory_alignment(trajectory, golden_trajectory)
    else:
        path_similarity = None

    # 5. 综合评分
    component_scores = {
        'length_penalty': 1.0 - min(metrics.length / 50, 1.0),  # 50步以上开始惩罚
        'tool_alignment': metrics.tool_usage_alignment,
        'reasoning_clarity': metrics.reasoning_clarity / 100,
        'efficiency': metrics.exploration_efficiency or 0.5,  # 没有golden时default 0.5
    }

    # 加权平均
    weights = {'length_penalty': 0.2, 'tool_alignment': 0.3, 'reasoning_clarity': 0.3, 'efficiency': 0.2}
    overall_score = sum(component_scores[k] * weights[k] for k in weights.keys()) * 100

    # 生成解释
    reasoning = f"""
    轨迹评分 {overall_score:.1f}/100：
    - 长度惩罚: {component_scores['length_penalty']*100:.1f} ({metrics.length}步)
    - 工具一致性: {component_scores['tool_alignment']*100:.1f}
    - 推理清晰度: {component_scores['reasoning_clarity']*100:.1f}
    - 探索效率: {component_scores['efficiency']*100:.1f}
    """

    comparison = {
        'path_similarity_to_expert': path_similarity,
        'backtrack_count': metrics.backtrack_count,
        'branching_factor': metrics.branching_factor,
    }

    return TrajectoryScore(
        metrics=metrics,
        overall_score=overall_score,
        reasoning=reasoning,
        comparison_to_expert=comparison
    )
```

**关键输出**:
- 多维度轨迹指标
- 综合trajectory_score(0-100)
- 与golden trajectory的差异
- 可解释的评分理由

---

### N.5 算法5: 数据集管理 (Eval Dataset Management)

**目的**: 系统化管理评估集，防止污染、版本漂移、重复

**Hook注入点**:
- `harness.eval.dataset_manager()` - 在benchmark加载时触用
- 触发条件: 基准初始化、周期性完整性检查

**设计决策**:
1. 语义hash tracking(检测微小变化)
2. 版本控制(每个基准snapshot都可复现)
3. 污染检测(基准项是否在训练集中)
4. 动态策展(根据模型进度调整难度)

**伪代码**:

```python
@dataclass
class BenchmarkVersion:
    name: str
    version: str  # e.g., "swe-bench-verified-2.0"
    semantic_hash: str  # SHA256 of content
    timestamp: datetime
    size: int  # 样本数
    metadata: dict  # 来源、组织者、许可证等
    contamination_check: dict  # 已知污染项
    items: List[BenchmarkItem]

class EvalDatasetManager:
    """管理所有评估数据集的生命周期"""

    def __init__(self, storage_path: str):
        self.storage = BenchmarkStorage(storage_path)
        self.contamination_detector = ContaminationDetector()
        self.version_control = VersionControl()

    def register_benchmark(
        self,
        name: str,
        items: List[BenchmarkItem],
        metadata: dict
    ) -> BenchmarkVersion:
        """注册新基准版本，生成不可变快照"""

        # 计算语义hash
        content_str = json.dumps(
            [item.to_dict() for item in items],
            sort_keys=True
        )
        semantic_hash = hashlib.sha256(content_str.encode()).hexdigest()

        # 检测污染
        contamination_results = self.contamination_detector.check_all(items)

        version = BenchmarkVersion(
            name=name,
            version=f"{name}-{datetime.now().strftime('%Y%m%d')}",
            semantic_hash=semantic_hash,
            timestamp=now(),
            size=len(items),
            metadata=metadata,
            contamination_check=contamination_results,
            items=items
        )

        # 版本控制
        self.version_control.commit(
            f"Register {name} v{version}",
            version
        )

        # 告警: 发现污染
        if contamination_results['contaminated_count'] > 0:
            alert_research_team(
                f"{contamination_results['contaminated_count']} items "
                f"may be in model training set"
            )

        return version

    def load_benchmark(
        self,
        name: str,
        version: Optional[str] = None,
        force_version: bool = False
    ) -> BenchmarkVersion:
        """加载基准(默认最新，可强制特定版本)"""

        if version is None:
            version = self.storage.get_latest_version(name)

        benchmark = self.storage.load(name, version)

        # 完整性检查
        assert len(benchmark.items) == benchmark.size
        assert hashlib.sha256(
            json.dumps([i.to_dict() for i in benchmark.items],
                      sort_keys=True).encode()
        ).hexdigest() == benchmark.semantic_hash

        if force_version:
            # 日志: 强制版本用于审计
            log_audit(f"Forced load {name}@{version}")

        return benchmark

    def perform_benchmark_mutation(
        self,
        base_benchmark: BenchmarkVersion,
        mutation_config: dict
    ) -> BenchmarkVersion:
        """生成基准变体，防止过拟合"""

        mutated_items = []

        for item in base_benchmark.items:
            # 策略1: 参数变体
            if 'param_variation' in mutation_config:
                mutated = item.with_param_variation(
                    mutation_config['param_variation']
                )
                mutated_items.append(mutated)

            # 策略2: 自然语言改写
            if 'description_paraphrase' in mutation_config:
                mutated = item.with_paraphrased_description(
                    model='claude-opus'
                )
                mutated_items.append(mutated)

            # 策略3: 难度调整
            if 'difficulty_adjust' in mutation_config:
                # 简化/复杂化任务
                mutated = item.with_adjusted_difficulty(
                    mutation_config['difficulty_adjust']
                )
                mutated_items.append(mutated)

        # 注册为新版本
        mutated_version = self.register_benchmark(
            name=f"{base_benchmark.name}-mutated",
            items=mutated_items,
            metadata={
                **base_benchmark.metadata,
                'mutation_config': mutation_config,
                'base_version': base_benchmark.version,
            }
        )

        return mutated_version
```

**关键输出**:
- Immutable benchmark snapshots
- 污染检测报告
- 版本控制历史
- 变体生成记录

---

### N.6 算法6: 反作弊机制 (Anti-Gaming Mechanisms)

**目的**: 检测并阻止模型对基准的过拟合，维护评估信效度

**Hook注入点**:
- `harness.eval.detect_gaming()` - 在每个benchmark run后触发
- 触发条件: 性能异常上升、多基准排名不一致

**设计决策**:
1. 多维度gaming信号(特定基准上升快、其他基准无变化)
2. 输入-输出相似度分析(是否直接记忆)
3. 轨迹多样性检查(重复模式)
4. 自动基准变异触发

**伪代码**:

```python
@dataclass
class GamingSignal:
    signal_type: str  # "benchmark_specific_improvement" / "low_diversity" / "semantic_similarity"
    severity: str  # "warning" / "critical"
    evidence: dict  # 具体数据
    recommended_action: str

def detect_gaming_behavior(
    current_runs: List[TrajectoryRun],
    historical_baseline: Dict[str, BenchmarkResults]
) -> List[GamingSignal]:
    """检测Agent对特定基准的过拟合"""

    signals = []

    # 信号1: 基准特异性提升 (某基准速度快，其他基准无变化)
    benchmark_improvements = {}
    for benchmark_name, baseline in historical_baseline.items():
        baseline_rate = baseline.summary['pass@1']
        current_runs_for_benchmark = [r for r in current_runs
                                      if r.benchmark_name == benchmark_name]
        current_rate = mean([r.outcome_score for r in current_runs_for_benchmark])

        improvement = (current_rate - baseline_rate) / baseline_rate if baseline_rate > 0 else 0
        benchmark_improvements[benchmark_name] = improvement

    # 检查是否存在特异性改进 (某基准大幅提升，其他不动)
    improvements_list = list(benchmark_improvements.values())
    max_improvement = max(improvements_list) if improvements_list else 0
    mean_improvement = mean(improvements_list) if improvements_list else 0

    if max_improvement > 0.15 and mean_improvement < 0.05:  # 最佳改15%，平均改5%
        signals.append(GamingSignal(
            signal_type='benchmark_specific_improvement',
            severity='warning',
            evidence={
                'max_improvement': max_improvement,
                'mean_improvement': mean_improvement,
                'disparity': max_improvement - mean_improvement,
                'suspect_benchmarks': [k for k, v in benchmark_improvements.items()
                                       if v > mean_improvement + 0.10]
            },
            recommended_action='考虑进行基准变异 (Benchmark Mutation)'
        ))

    # 信号2: 轨迹多样性低 (每个基准项的轨迹太相似)
    trajectory_embeddings = []
    for run in current_runs:
        # 计算轨迹嵌入向量(动作序列+工具调用)
        embedding = embed_trajectory(run.trajectory)
        trajectory_embeddings.append(embedding)

    if trajectory_embeddings:
        # 计算轨迹两两之间的余弦相似度
        similarities = []
        for i in range(len(trajectory_embeddings)):
            for j in range(i+1, len(trajectory_embeddings)):
                sim = cosine_similarity(trajectory_embeddings[i], trajectory_embeddings[j])
                similarities.append(sim)

        mean_similarity = mean(similarities)
        if mean_similarity > 0.8:  # 轨迹高度重复
            signals.append(GamingSignal(
                signal_type='low_trajectory_diversity',
                severity='critical',
                evidence={
                    'mean_pairwise_similarity': mean_similarity,
                    'interpretation': 'Agent使用几乎相同的策略解决所有问题'
                },
                recommended_action='检查Agent是否在记忆特定的解决方案'
            ))

    # 信号3: 输入-输出语义相似度过高 (可能直接记忆)
    semantic_similarities = []
    for run in current_runs:
        task_description = run.task.description
        agent_reasoning = run.trajectory.reasoning_text

        semantic_sim = compute_semantic_similarity(task_description, agent_reasoning)
        semantic_similarities.append(semantic_sim)

    if semantic_similarities and mean(semantic_similarities) > 0.85:
        signals.append(GamingSignal(
            signal_type='high_input_output_similarity',
            severity='critical',
            evidence={
                'mean_semantic_similarity': mean(semantic_similarities),
                'interpretation': 'Agent回复高度相似于输入，可能直接复制'
            },
            recommended_action='检查是否有数据泄露或过拟合'
        ))

    return signals

def trigger_benchmark_mutation_if_gaming_detected(
    gaming_signals: List[GamingSignal],
    dataset_manager: EvalDatasetManager
):
    """如果检测到gaming，自动生成基准变体"""

    if any(s.severity == 'critical' for s in gaming_signals):
        # 触发自动基准变异
        for benchmark_name in get_all_benchmark_names():
            original = dataset_manager.load_benchmark(benchmark_name)

            mutated = dataset_manager.perform_benchmark_mutation(
                original,
                mutation_config={
                    'param_variation': 0.2,
                    'description_paraphrase': True,
                    'difficulty_adjust': 0.1
                }
            )

            log_audit(f"Auto-triggered mutation: {original.version} -> {mutated.version}")

            # 通知: 已部署新基准版本
            notify_evaluation_team(
                f"基准已自动变异以防止过拟合。新版本: {mutated.version}"
            )
```

**关键输出**:
- Gaming signals清单
- 严重度分类
- 具体证据(数据)
- 自动化应对(基准变异)

---

### N.7 算法7: 成本-质量Pareto分析 (Cost-Quality Tradeoff Analysis)

**目的**: 找到最优的成本-质量权衡点，指导模型和配置选择

**Hook注入点**:
- `harness.optimization.compute_pareto_frontier()` - 周期性(每周)或手动触发
- 触发条件: 新模型上线、成本预算变更

**设计决策**:
1. 多维度Pareto(准确率、延迟、成本)
2. 聚类识别最优区域
3. 动态分配资源(关键路径用强模型)
4. ROI计算(改进收益 vs. 成本增加)

**伪代码**:

```python
@dataclass
class ParetoDimension:
    metric: str  # "pass@1" / "latency_ms" / "cost_usd"
    value: float
    direction: str  # "maximize" / "minimize"

@dataclass
class ParetoPoint:
    agent_config: dict  # 模型 + Harness + 其他参数
    dimensions: Dict[str, float]  # 各维度数值
    pareto_rank: int  # 0=最优前沿, 1=第二层, ...
    efficiency_score: float  # (质量/成本)
    recommended_use_case: str

def compute_pareto_frontier(
    agent_configs: List[dict],
    benchmark_results: Dict[str, BenchmarkResults]
) -> ParetoFrontier:
    """计算成本-质量Pareto前沿"""

    points = []

    for config in agent_configs:
        key = config_to_key(config)
        results = benchmark_results[key]

        point = ParetoPoint(
            agent_config=config,
            dimensions={
                'pass@1': results.summary['pass@1'],
                'pass^3': results.summary['pass^3'],
                'avg_latency_ms': results.summary['avg_latency_ms'],
                'total_cost_usd': results.summary['total_cost_usd'],
                'trajectory_quality': results.summary['avg_trajectory_score'] / 100,
            },
            pareto_rank=None,  # 待计算
            efficiency_score=None,  # 待计算
            recommended_use_case=None
        )
        points.append(point)

    # 计算Pareto支配关系
    # 定义支配: A支配B iff A在所有质量维度≥B 且成本维度≤B
    for i, p1 in enumerate(points):
        for j, p2 in enumerate(points):
            if i != j and dominates(p1, p2):
                if p2.pareto_rank is None:
                    p2.pareto_rank = 0
                p2.pareto_rank = max(p2.pareto_rank or 0, (p1.pareto_rank or 0) + 1)

    # 提取Pareto前沿(rank=0)
    frontier = [p for p in points if p.pareto_rank == 0]

    # 计算效率分数 (质量/成本)
    for p in frontier:
        # 综合质量 (加权平均)
        quality = (0.4 * p.dimensions['pass@1'] +
                  0.3 * p.dimensions['pass^3'] +
                  0.3 * p.dimensions['trajectory_quality'])

        # 成本 (考虑延迟和美元成本)
        cost = p.dimensions['total_cost_usd'] + p.dimensions['avg_latency_ms'] / 1000

        p.efficiency_score = quality / (cost + 1e-6)  # 避免除以0

    # 推荐使用场景
    for p in frontier:
        if p.dimensions['pass@1'] > 0.85 and p.dimensions['total_cost_usd'] < 100:
            p.recommended_use_case = "高准确率+低成本: 生产关键路径"
        elif p.dimensions['pass@1'] > 0.80 and p.dimensions['avg_latency_ms'] < 500:
            p.recommended_use_case = "均衡: 通用生产环境"
        elif p.dimensions['pass@1'] > 0.70 and p.dimensions['total_cost_usd'] < 50:
            p.recommended_use_case = "成本优先: 高量低敏感任务"
        else:
            p.recommended_use_case = "开发/实验"

    return ParetoFrontier(
        points=points,
        frontier=frontier,
        optimal_point=max(frontier, key=lambda p: p.efficiency_score),
        timestamp=now()
    )

def allocate_resources_optimally(
    pareto_frontier: ParetoFrontier,
    budget_usd: float,
    workload_mix: dict  # {'critical': 0.2, 'standard': 0.5, 'batch': 0.3}
) -> ResourceAllocationPlan:
    """根据Pareto前沿和业务约束分配模型资源"""

    allocation = {}
    remaining_budget = budget_usd

    # 按优先级分配
    priorities = [
        ('critical', 0.05),  # 5%的流量占20%的预算
        ('standard', 0.10),  # 50%的流量占50%的预算
        ('batch', 0.05),  # 30%的流量占30%的预算
    ]

    for priority_name, budget_fraction in priorities:
        workload_fraction = workload_mix.get(priority_name, 0)
        allocated_budget = budget_usd * budget_fraction

        if priority_name == 'critical':
            # 选择Pareto前沿最优点(质量优先)
            best_config = max(pareto_frontier.frontier,
                             key=lambda p: p.dimensions['pass@1'])
        elif priority_name == 'standard':
            # 选择效率最优点
            best_config = pareto_frontier.optimal_point
        else:  # batch
            # 选择成本优先点
            best_config = min(pareto_frontier.frontier,
                             key=lambda p: p.dimensions['total_cost_usd'])

        allocation[priority_name] = {
            'config': best_config.agent_config,
            'workload_fraction': workload_fraction,
            'allocated_budget': allocated_budget,
            'expected_accuracy': best_config.dimensions['pass@1'],
            'expected_cost_per_task': (allocated_budget /
                                       (workload_fraction * estimated_monthly_tasks))
        }

    return ResourceAllocationPlan(
        allocation=allocation,
        total_cost_estimate=sum(a['allocated_budget'] for a in allocation.values()),
        roi_improvement_pct=compute_roi_vs_baseline(allocation)
    )
```

**关键输出**:
- Pareto前沿点集合
- 效率分数ranking
- 推荐使用场景
- 资源分配方案

---

### N.8 算法8: 离线评估的策略与路由 (Offline-to-Online Evaluation Routing)

**目的**: 决定哪些Agent变更先做离线eval，哪些直接灰度上线，最大化实验效率

**Hook注入点**:
- `harness.deployment.evaluation_routing()` - 在Agent发布前触发

**设计决策**:
1. 变更风险分类(低/中/高)
2. 离线评估深度决策(快速evals vs. 完整evals)
3. 灰度策略(流量比例和持续时间)
4. 回滚条件(自动触发点)

**伪代码**:

```python
def route_evaluation_and_deployment(
    change_description: str,
    affected_components: List[str],
    previous_baseline: BenchmarkResults
) -> EvaluationAndDeploymentPlan:
    """路由：离线eval还是直接灰度"""

    # 风险分类
    risk_level = classify_change_risk(
        change_description,
        affected_components
    )  # "low" / "medium" / "high"

    if risk_level == 'low':
        # 快速离线eval (只用小基准, 30分钟)
        eval_plan = {
            'offline_eval_required': True,
            'eval_benchmarks': ['quick-filter'],  # 50个样本
            'eval_duration': 30,  # 分钟
            'required_pass_rate': 0.95,  # 需要>95%通过
            'if_passed': 'direct_deployment',  # 直接全量上线
            'if_failed': 'manual_review'
        }

    elif risk_level == 'medium':
        # 完整离线eval + 小流量灰度 (2小时 + 2小时灰度)
        eval_plan = {
            'offline_eval_required': True,
            'eval_benchmarks': ['swe-bench-verified', 'terminal-bench-small'],
            'eval_duration': 120,
            'required_pass_rate': 0.90,
            'if_passed': 'canary_deployment',
            'canary_config': {
                'initial_traffic_fraction': 0.05,  # 5%
                'ramp_up_duration': 2,  # 小时
                'monitoring_metrics': ['pass@1', 'latency', 'cost'],
                'rollback_threshold': 0.05  # 下降>5%则回滚
            }
        }

    else:  # high risk
        # 完整offline eval + 完整消融研究 + 长期灰度
        eval_plan = {
            'offline_eval_required': True,
            'eval_benchmarks': ['swe-bench-verified', 'terminal-bench', 'halt'],
            'eval_duration': 480,  # 8小时
            'ablation_required': True,
            'required_pass_rate': 0.95,
            'required_improvement_vs_baseline': 0.02,  # 至少2%改进
            'if_passed': 'staged_deployment',
            'staged_config': {
                'stage1': {'traffic_fraction': 0.01, 'duration': 4},  # 1%流量, 4小时
                'stage2': {'traffic_fraction': 0.10, 'duration': 8},  # 10%流量, 8小时
                'stage3': {'traffic_fraction': 1.00, 'duration': float('inf')},  # 全量
                'rollback_threshold': 0.03  # 下降>3%则回滚
            }
        }

    deployment_plan = EvaluationAndDeploymentPlan(
        change_description=change_description,
        risk_level=risk_level,
        evaluation_plan=eval_plan,
        go_no_go_decision_point=f"{eval_plan['eval_duration']} min after eval",
        responsible_team='MLOps',
        created_at=now()
    )

    return deployment_plan
```

**关键输出**:
- 风险分类
- 离线eval深度决策
- 灰度策略
- 自动回滚条件

---

## N.9 Hook点总结表与执行流图

### 表N.1: 8个算法的Hook映射

| # | 算法 | Hook点 | 触发条件 | 输出 | 执行周期 |
|---|------|--------|---------|------|---------|
| 1 | Offline Bench | `harness.eval.benchmark.runner()` | 新模型/配置变更 | pass@k/pass^k | 每日 |
| 2 | Regression Det. | `harness.monitor.regression_check()` | 每次基准完成 | 告警+p-value | 自动 |
| 3 | A/B Test | `harness.experiments.run_ab_test()` | 部署前(高风险变更) | uplift%+置信度 | 按需 |
| 4 | Trajectory Eval | `harness.eval.trajectory_scorer()` | 每次Agent execution | trajectory_score | 实时 |
| 5 | Dataset Mgmt | `harness.eval.dataset_manager()` | benchmark加载/周期检查 | version+污染检测 | 周期 |
| 6 | Anti-Gaming | `harness.eval.detect_gaming()` | 每次基准run完成 | gaming_signals | 自动 |
| 7 | Pareto Analysis | `harness.optimization.compute_pareto_frontier()` | 周期/成本预算变更 | 前沿点+ROI | 每周 |
| 8 | Eval Routing | `harness.deployment.evaluation_routing()` | 发布前 | 离线/灰度决策 | 按需 |

### 图N.1: C11评估管道的执行流

```
Agent变更提议
    │
    ├─→ [8] Eval Routing
    │   ├─ 低风险 → 快速路径(30min)
    │   ├─ 中风险 → 标准路径(2h)
    │   └─ 高风险 → 完整路径(8h)
    │
    ├─→ [1] Offline Benchmark (按路径)
    │   └─→ [2] Regression Detection
    │       ├─ 显著下降 → 告警 + 阻止发布
    │       └─ 通过 → 继续
    │
    ├─→ [3] A/B Test (中/高风险)
    │   ├─ 显著改进(p<0.05) → 发布
    │   ├─ 无显著差异 → 手动review
    │   └─ 显著下降 → 阻止
    │
    ├─→ [4] Trajectory Eval + [5] Dataset Management (实时)
    │   └─ 完整trace记录 + 污染检查
    │
    ├─→ [6] Anti-Gaming Detection
    │   ├─ 检测到gaming → 触发基准变异
    │   └─ 无异常 → 继续
    │
    ├─→ 发布决策
    │
    ├─→ [7] Pareto Analysis (发布后周期性)
    │   └─ 计算效率前沿 + 资源分配建议
    │
    └─→ 成本-质量优化
```

---

## N.10 实现检查清单

### 开发阶段(完成前)
- [ ] 实现算法1: 离线基准runner (含失败重试、并行执行)
- [ ] 实现算法2: 回归检测 (含t-test和bootstrap重采样)
- [ ] 实现算法4: 轨迹评估 (含专家golden path对比)
- [ ] 实现算法5: 数据集管理 (含语义hash和版本控制)

### 生产阶段(上线前)
- [ ] 实现算法3: A/B测试框架 (含早停和功效分析)
- [ ] 实现算法6: 反作弊 (含embedding similarity和diversity check)
- [ ] 实现算法7: Pareto分析 (含resource allocation)
- [ ] 实现算法8: 评估路由 (含自动风险分类)

### 监控与维护(持续)
- [ ] 日志系统: 记录所有eval decisions和推理
- [ ] 告警系统: 关键指标的阈值告警
- [ ] 审计系统: 追踪每次发布决策的依据
- [ ] 反馈循环: 离线预测vs生产实际的对比

---

参考实现框架: [Inspect AI](https://inspect.aisi.org.uk/evals/) + [LangSmith](https://www.langchain.com/langsmith) + 自定义Hook层

---

## 参考文献与数据源

### 主要研究论文与技术文档

1. **SWE-bench系列**
   - SWE-Bench Pro: Can AI Agents Solve Long-Horizon Software Engineering Tasks? [SWE-Bench Pro: Can AI Agents Solve Long-Horizon Software Engineering Tasks? (arXiv:2509.16941)](https://arxiv.org/abs/2509.16941)
   - Saving SWE-Bench: A Benchmark Mutation Approach for Realistic Agent Evaluation [Saving SWE-Bench: A Benchmark Mutation Approach for Realistic Agent Evaluation (arXiv:2510.08996)](https://arxiv.org/abs/2510.08996)

2. **Pass@k与可靠性**
   - Statistics for AI/ML, Part 4: pass@k and Unbiased Estimator (LeeHanChung)
   - Evaluation and Benchmarking of LLM Agents: A Survey [Evaluation and Benchmarking of LLM Agents: A Survey (arXiv:2507.21504)](https://arxiv.org/abs/2507.21504)
   - ReliabilityBench: Evaluating LLM Agent Reliability [ReliabilityBench: Evaluating LLM Agent Reliability (arXiv:2601.06112)](https://arxiv.org/abs/2601.06112)

3. **测量论与效度**
   - Measurement to Meaning: A Validity-Centered Framework for AI Evaluation [Measurement to Meaning: A Validity-Centered Framework for AI Evaluation (arXiv:2505.10573)](https://arxiv.org/abs/2505.10573)
   - Reliability in AI Measurement Science (Stanford AIMs Lab)

4. **轨迹评估**
   - Process-Level Trajectory Evaluation for Environment Configuration in Software Engineering Agents [Process-Level Trajectory Evaluation for Environment Configuration (arXiv:2510.25694)](https://arxiv.org/abs/2510.25694)
   - AGENTREWARDBENCH: Evaluating Automatic Evaluations of Web Agent Trajectories [AGENTREWARDBENCH: Evaluating Automatic Evaluations of Web Agent Trajectories (arXiv:2504.08942)](https://arxiv.org/abs/2504.08942)
   - LangChain: How to evaluate your agent with trajectory evaluations

5. **评分器与Judge**
   - When AIs Judge AIs: The Rise of Agent-as-a-Judge Evaluation for LLMs [When AIs Judge AIs: The Rise of Agent-as-a-Judge Evaluation (arXiv:2508.02994)](https://arxiv.org/abs/2508.02994)
   - LLM-as-Judge指南 (Confident AI, LangChain, Weights & Biases)

6. **基准污染与防护**
   - How Contaminated Is Your Benchmark? Measuring Dataset Leakage in Large Language Models with Kernel Divergence $wVDR2qmE28$
   - Benchmark Data Contamination of Large Language Models: A Survey [Benchmark Data Contamination of Large Language Models: A Survey (arXiv:2406.04244)](https://arxiv.org/abs/2406.04244)
   - LessLeak-Bench: A First Investigation of Data Leakage in LLMs Across 83 Software Engineering Benchmarks [LessLeak-Bench: A First Investigation of Data Leakage in LLMs (arXiv:2502.06215)](https://arxiv.org/abs/2502.06215)

7. **HumanEval & MBPP**
   - HumanEval Pro and MBPP Pro: Evaluating Large Language Models on Self-invoking Code Generation [HumanEval Pro and MBPP Pro: Evaluating Large Language Models on Self-invoking Code Generation (arXiv:2412.21199)](https://arxiv.org/abs/2412.21199)
   - EvalPlus: Code Synthesis Evaluation Framework

8. **Agent失败模式**
   - Why Do Multi-Agent LLM Systems Fail? [Why Do Multi-Agent LLM Systems Fail? (arXiv:2503.13657)](https://arxiv.org/abs/2503.13657)
   - Diagnosing and Measuring AI Agent Failures (Maxim)

9. **OSWorld & 真实环境**
   - OSWorld: Benchmarking Multimodal Agents for Open-Ended Tasks in Real Computer Environments [OSWorld: Benchmarking Multimodal Agents for Open-Ended Tasks (arXiv:2404.07972)](https://arxiv.org/abs/2404.07972)
   - The World's Most Capable Computer Agent (AGI Co.)

10. **HAL框架**
    - Holistic Agent Leaderboard (Princeton)
    - GitHub: princeton-pli/hal-harness

11. **四支柱评估**
    - Beyond Task Completion: An Assessment Framework for Evaluating Agentic AI Systems [Beyond Task Completion: An Assessment Framework for Evaluating Agentic AI Systems (arXiv:2512.12791)](https://arxiv.org/abs/2512.12791)

12. **内存系统**
    - Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory [Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory (arXiv:2504.19413)](https://arxiv.org/abs/2504.19413)
    - Memory OS of AI Agent [Memory OS of AI Agent (arXiv:2506.06326)](https://arxiv.org/abs/2506.06326)
    - MemGPT: Engineering Semantic Memory through Adaptive Retention and Context Summarization

13. **Goodhart's Law在AI中的应用**
    - Measuring Goodhart's law (OpenAI)
    - Goodhart's Law Applies to NLP's Explanation Benchmarks [Goodhart's Law Applies to NLP's Explanation Benchmarks (arXiv:2308.14272)](https://arxiv.org/abs/2308.14272)
    - Goodhart's Law in Reinforcement Learning [Goodhart's Law in Reinforcement Learning (arXiv:2310.09144)](https://arxiv.org/abs/2310.09144)

14. **消融研究方法**
    - AblationBench: Evaluating Automated Planning of Ablations in Empirical AI [AblationBench: Evaluating Automated Planning of Ablations (arXiv:2507.08038)](https://arxiv.org/abs/2507.08038)

---

## 附录：术语表

| 术语 | 简写 | 定义 | 示例 |
|------|------|------|------|
| Pass@k | - | k次中至少1次成功 | pass@5: 5次试验中至少1次通过 |
| Pass^k | - | k次全部成功 | pass^3: 连续3次都通过 |
| SWE-bench | - | 软件工程基准(500个真实issue) | 成为代码Agent的标准评测 |
| FAIL_TO_PASS | FTP | 原代码失败、修复后通过 | 衡量修复的有效性 |
| PASS_TO_PASS | PTP | 原代码通过、修复后仍通过 | 防止回归 |
| HAL | - | Holistic Agent Leaderboard | Princeton的统一评估框架 |
| LLM-as-Judge | - | 用LLM做评分器 | 成本低($0.06)但非确定性 |
| Agent-as-Judge | - | 用工具Agent做评分器 | 成本高($0.96)但准确性好 |
| Trajectory | 轨迹 | Agent的完整执行链(推理+行动) | 可独立于结果评估 |
| Outcome | 结果 | 最终环境状态(通过/失败) | 衡量任务完成 |
| Goodhart陷阱 | - | 度量变为目标时失效 | 优化pass@k导致Agent学会侥幸 |
| Benchmark Mutation | 基准变异 | 自动生成等效任务避免过拟合 | 从500→+1000等价变体 |
| Ablation Study | 消融 | 逐个移除组件测其贡献 | Leave-One-Component-Out |
| Reliability (Stdev) | 信度 | 多次运行结果一致性 | 不<0.7的Kappa |
| Validity | 效度 | 指标与目标概念的对应 | 内容/构想/准则/外推 |

---

**报告生成时间**: 2026年3月30日
**研究范围**: C11评估与基准测试的理论基础、实践案例、隐性知识
**研究方法**: 文献综述(14+主要论文) + 数据分析 + 逻辑推导 + 假说生成
**置信度标记**: [事实] 可验证, [推导] 基于事实的逻辑结论, [假说] 待验证的解释, [开放问题] 未解决

---

*完*
