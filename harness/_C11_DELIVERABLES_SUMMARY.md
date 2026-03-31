# C11 评估与基准测试：三项交付物总结

**完成时间**：2026年3月30日
**版本**：Final v1.0

---

## 交付物1：增强研究笔记

**文件**：`/sessions/gifted-wonderful-dirac/mnt/harness/_research_c11_enhanced.md`

### 内容概览

完整的研究文献综述，覆盖：

| 主题 | 来源与关键内容 |
|------|--------------|
| **1. Anthropic评估策略** | Evaluation-driven开发、多基准组合、Claude Opus 4.5达80.9% SWE-bench Verified |
| **2. SWE-bench演进** | Verified版本、v2.0环保改进、~50% PR在code review被拒（Goodhart效应）|
| **3. Terminal-Bench 2.0** | 89个真实工作流任务、长轨迹评估(<65% frontier model pass率) |
| **4. Goodhart & Campbell Laws** | 度量变为目标时失效、Chatbot Arena崩坏案例、AI evaluation中的三层表现 |
| **5. Inspect AI (UK AISI)** | 开源框架、Task→Solver→Scorer、Anthropic/DeepMind/Grok采用 |
| **6. METR Task Standard** | ~200 task families、自动评分失效问题、~50% gap between test-pass和code-review合并 |
| **7. Braintrust与Langsmith** | 生产评估平台、离线+在线双通道、轨迹级评估 |
| **8. 轨迹级评估学术进展** | AGENTREWARDBENCH、TRAJECT-Bench、Agent-R1、trajectory complexity metrics |
| **9. 生产评估实践** | AWS Strands、A/B testing框架、离线→在线反馈循环 |
| **10. Anti-Gaming机制** | Benchmark Mutation、Ensemble Baselines、Out-of-Distribution保留 |
| **11. 成本-质量Pareto** | Opus vs Sonnet vs Haiku权衡、ROI计算、动态资源分配 |

### 关键发现

- **[事实]** Anthropic的evaluation-driven流程确保基准指导而非事后验证
- **[推导]** Goodhart在Agent评估三个层次出现：数据（过拟合）、流程（系统操纵）、目标（指标优化）
- **[假说]** 企业AI Agent评估需要：多基准+轨迹观测+反gaming+成本优化的整体系统
- **[开放问题]** 如何设计既能自动化又能捕捉人工审查质量的基准？

---

## 交付物2：工程实现与Hook映射

**位置**：`/sessions/gifted-wonderful-dirac/mnt/harness/012_SYSTEM_C11_EVALUATION.md` §N部分

### 8个核心算法的完整映射

#### 表2.1：Hook映射一览表

| # | 算法 | Hook点 | 触发条件 | 输出指标 | 伪代码行数 |
|---|------|--------|---------|---------|----------|
| 1 | **Offline Benchmark Runner** | `harness.eval.benchmark.runner()` | 新模型/配置变更 | pass@k, pass^k, trajectory_score | 45行 |
| 2 | **Regression Detection** | `harness.monitor.regression_check()` | 每次基准完成 | 告警 + p-value | 35行 |
| 3 | **A/B Test Framework** | `harness.experiments.run_ab_test()` | 部署前(高风险变更) | uplift%, CI, 推荐 | 50行 |
| 4 | **Trajectory-Level Evaluation** | `harness.eval.trajectory_scorer()` | 每次Agent execution | trajectory_score(0-100) | 60行 |
| 5 | **Dataset Management** | `harness.eval.dataset_manager()` | benchmark加载/周期检查 | 版本+污染检测 | 70行 |
| 6 | **Anti-Gaming Detection** | `harness.eval.detect_gaming()` | 每次基准run完成 | gaming_signals清单 | 55行 |
| 7 | **Pareto Analysis** | `harness.optimization.compute_pareto_frontier()` | 周期性/成本预算变更 | 前沿点+ROI | 45行 |
| 8 | **Eval Routing** | `harness.deployment.evaluation_routing()` | 发布前 | 离线/灰度决策 | 30行 |

**总计**：~390行高质量伪代码，每个包含：
- @dataclass结构定义
- 完整函数实现
- 内部逻辑注释
- 关键输出说明

#### 图2.1：C11评估管道执行流

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
    ├─→ [4] Trajectory Eval + [5] Dataset Mgmt (实时)
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

#### 关键设计决策

**算法1-Offline Benchmark**：
- 隔离Docker环境防止污染
- 并行多任务加快周期
- 完整trace记录用于事后分析
- 自动检测>2%的显著性变化

**算法2-Regression Detection**：
- 多维度同时检测(accuracy/cost/quality/latency)
- 统计t-test确保显著性(p<0.05)
- 自动snapshot保存for forensics
- 可配置的忽略阈值(known changes)

**算法3-A/B Test**：
- 随机分组确保无偏
- Power analysis计算最小样本量
- Wilson score interval置信度
- 实时监控与早停规则

**算法4-Trajectory Eval**：
- 多维度指标：长度、分支度、回溯、工具一致性、推理清晰度
- 混合评分器：规则+LLM-as-judge+Agent-as-judge
- 与golden trajectory对比
- 可解释的评分理由

**算法5-Dataset Mgmt**：
- 语义hash tracking检测微小变化
- 版本控制每个snapshot
- 污染检测基于训练数据重叠
- 自动基准变异生成等价变体

**算法6-Anti-Gaming**：
- 基准特异性改进检测(某基准大升，其他不动)
- 轨迹多样性检查(余弦相似度>0.8警告)
- 输入-输出语义相似度(>0.85触发调查)
- 自动触发基准变异响应

**算法7-Pareto Analysis**：
- 多维支配关系计算
- 效率分数(质量/成本)
- 推荐使用场景自动化
- 动态资源分配计算

**算法8-Eval Routing**：
- 自动风险分类(低/中/高)
- 路径深度决策：快速30min / 标准2h / 完整8h
- 灰度策略与自动回滚条件
- Ablation requirement for high-risk changes

---

## 交付物3：参考文献更新与链接

**范围**：所有arXiv论文和技术文档已更新为clickable markdown links

### 更新统计

- **arXiv论文**：26篇论文ID → markdown链接
- **技术文档**：Anthropic、UK AISI、OpenAI、DeepMind等官方文档
- **GitHub仓库**：SWE-bench、Inspect AI、Harbor、Mem0等

### 核心引用列表

**基准与评估框架**：
- [SWE-Bench Pro](https://arxiv.org/abs/2509.16941)
- [Terminal-Bench: Benchmarking Agents](https://arxiv.org/abs/2601.11868)
- [Evaluation and Benchmarking of LLM Agents: A Survey](https://arxiv.org/abs/2507.21504)

**测量论与效度**：
- [Measurement to Meaning: Validity-Centered Framework](https://arxiv.org/abs/2505.10573)
- [Goodhart's Law in RL](https://arxiv.org/abs/2310.09144)

**轨迹评估**：
- [Process-Level Trajectory Evaluation](https://arxiv.org/abs/2510.25694)
- [TRAJECT-Bench: Trajectory-Aware Benchmark](https://arxiv.org/abs/2510.04550)
- [AGENTREWARDBENCH: Evaluating Evaluations](https://arxiv.org/abs/2504.08942)

**Judge与评分**：
- [When AIs Judge AIs](https://arxiv.org/abs/2508.02994)
- [HumanEval Pro & MBPP Pro](https://arxiv.org/abs/2412.21199)

**多模态与真实环境**：
- [OSWorld: Benchmarking Agents](https://arxiv.org/abs/2404.07972)
- [Beyond Task Completion Framework](https://arxiv.org/abs/2512.12791)

**防污染与防作弊**：
- [Benchmark Data Contamination Survey](https://arxiv.org/abs/2406.04244)
- [LessLeak-Bench](https://arxiv.org/abs/2502.06215)
- [Saving SWE-Bench: Mutation Approach](https://arxiv.org/abs/2510.08996)

**开源工具**：
- [Inspect AI (UK AISI)](https://inspect.aisi.org.uk/evals/)
- [LangSmith Evaluations](https://www.langchain.com/langsmith/evaluation)
- [Braintrust AI Observability](https://www.braintrust.dev)

---

## 使用指南

### Step 1: 理解理论基础
1. 阅读 `_research_c11_enhanced.md` 的前两章了解评估理论
2. 关注"开放问题"标记的未解决议题
3. 理解Goodhart & Campbell Laws在企业评估中的表现

### Step 2: 规划工程实现
1. 在 `012_SYSTEM_C11_EVALUATION.md` §N中找到你的用例
2. 阅读对应算法的完整伪代码
3. 检查"关键设计决策"部分的trade-offs

### Step 3: 系统化部署
1. 按§N.10的"实现检查清单"分阶段部署
2. 开发阶段(1-2): Offline Bench + Regression Detection
3. 生产阶段(3,6,7,8): A/B Test + Anti-Gaming + Pareto + Routing
4. 持续监控(4,5): Trajectory Eval + Dataset Management

### Step 4: 评估有效性
- 比较"离线预测 vs 生产实际"的准确度
- 计算基准的"预测power"(能预测真实表现多少%)
- 定期审计gaming signals的假阳性率
- 追踪成本-质量Pareto前沿的稳定性

---

## 与Harness框架的关系

### C11的位置

```
Harness工程体系
├─ C1-C8: 优化与迭代层 (改进Agent能力)
├─ C9: 运行时监控层 (生产质量告警)
├─ C11: 离线评估层 (算法验证 + 发布把关) ← 本文档
├─ C12: 发布决策层 (cost-quality trade-off)
└─ C13-C15: 部署与反馈层
```

### C11的输入与输出

**输入**：
- Agent配置变更(新Harness hook、提示词、工具库)
- 基准集(SWE-bench、Terminal-Bench等)
- 生产数据(用于离线-在线对齐)

**输出**：
- 发布/不发布的go/no-go决策
- 成本-质量权衡建议
- 后续优化方向指引

### 与其他层的协作

- **↓ C1-C8提交变更** → C11进行离线评估 → **↑反馈优化方向**
- **← C9生产监控** → C11验证基准有效性 → **→校准告警阈值**
- **← C12发布决策** → C11提供量化依据 → **→降低发布风险**

---

## 关键指标与Health Checks

### 评估系统的健康指标

| 指标 | 目标 | 计算方法 | 告警阈值 |
|------|------|---------|---------|
| **基准变异程度** | 高(抗污染) | 每周新增变体数 | <10个/周 |
| **跨基准排名一致性** | 高(>0.8相关) | Kendall's tau | <0.7 |
| **人工审计发现率** | 低(<1%) | 发现错误/总样本 | >2% |
| **轨迹可解释性评分** | 高(>85) | LLM评估reasoning clarity | <75分 |
| **gaming signal假阳性** | 低(<5%) | 误报/总信号 | >10% |
| **离线-在线对齐** | 高(>0.85相关) | pass@1离线vs在线相关性 | <0.75 |
| **成本预估准确度** | 高(95% CI) | 预测vs实际成本范围 | >10% |
| **A/B test统计功效** | >80% | Power计算 | <75% |

### 定期审查计划

- **日**：监控回归检测告警
- **周**：计算Pareto分析，审视基准变异
- **月**：跨基准排名一致性分析，gaming signal review
- **季度**：完整的离线-在线对齐审计，评估系统有效性评分

---

## 前向兼容性与可扩展性

### 易于扩展的点

1. **新基准集成**：只需在`EvalDatasetManager`中注册新基准版本
2. **新评分器**：轨迹评估支持即插即用(规则/LLM/Agent组合)
3. **新维度**：Pareto分析支持任意维度的支配关系计算
4. **新路由策略**：`evaluation_routing()`支持自定义风险分类规则

### 未来研究方向

- **在线学习**: 从生产反馈动态更新评估权重
- **多目标优化**: 超越Pareto前沿，考虑用户满意度等隐性目标
- **自适应基准**: 根据模型进度智能调整基准难度分布
- **Cross-domain Transfer**: 从代码基准迁移到其他领域

---

## 使用许可与引用

**作者**：Harness工程体系 C11模块开发组
**日期**：2026年3月30日
**数据来源**：Anthropic、OpenAI、UK AISI、DeepMind、METR、arXiv等

**建议引用**：
```
@article{harness_c11_evaluation,
  title = {C11 评估与基准测试：工程实现与Hook映射},
  author = {Harness Engineering Team},
  year = {2026},
  month = {March},
  url = {/sessions/gifted-wonderful-dirac/mnt/harness/012_SYSTEM_C11_EVALUATION.md}
}
```

---

**完成时间**：2026年3月30日 16:55 UTC
**审核状态**：Ready for deployment
**下一步**：实现阶段按§N.10检查清单执行
