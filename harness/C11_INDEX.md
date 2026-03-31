# C11 评估与基准测试 - 完整文档索引

**更新时间**：2026年3月30日
**版本**：1.0 FINAL
**状态**：✓ 已提交 (Git commit 4faf00c)

---

## 核心文档导航

### 主研究文档
**`012_SYSTEM_C11_EVALUATION.md`** - 2918行，128KB
- 完整的C11评估体系研究报告
- 包含理论基础、实践案例、工程实现
- **新增**：§N工程实现与Hook映射（1181行）

```
结构：
├─ 前言：C11在Harness中的定位
├─ §0-§8：理论与案例研究
├─ §N：工程实现（本次更新）
│  ├─ N.0：执行框架概览
│  ├─ N.1-N.8：8个核心算法
│  ├─ N.9：Hook点总结表
│  ├─ N.10：实现检查清单
│  └─ 执行流图
├─ §10：综合发现与建议
└─ 附录：术语表
```

**快速导航到特定部分**：
- 算法1（离线基准）：行1811-1855
- 算法2（回归检测）：行1857-1891
- 算法3（A/B测试）：行1893-1943
- 算法4（轨迹评估）：行1945-2004
- 算法5（数据集管理）：行2006-2075
- 算法6（反作弊）：行2077-2131
- 算法7（Pareto）：行2133-2181
- 算法8（评估路由）：行2183-2213

---

### 增强研究笔记
**`_research_c11_enhanced.md`** - 297行，16KB

完整的文献综述，覆盖2025-2026最新研究：

1. **Anthropic评估策略** (10段)
   - Claude Opus 4.5的内部基准
   - Evaluation-driven开发流程
   - 多基准组合策略

2. **SWE-bench演进** (12段)
   - Verified版本设计
   - v2.0环境改进
   - 实际PR拒率问题分析

3. **Terminal-Bench 2.0** (8段)
   - 89个真实工作流任务
   - 轨迹复杂度的评估
   - Frontier模型的区分度

4. **Goodhart & Campbell Laws** (10段)
   - 经典理论回顾
   - AI评估中的三层表现
   - Chatbot Arena案例分析

5. **Inspect AI框架** (7段)
   - UK AISI的开源框架
   - 核心抽象与采用情况
   - 与其他框架的对比

6. **METR Task Standard** (8段)
   - 标准化任务定义
   - 自动评分的局限
   - METR的critical findings

7. **Braintrust & LangSmith** (8段)
   - 生产评估平台对比
   - 轨迹级评估能力
   - 集成方案对比

8. **轨迹级评估学术进展** (10段)
   - 最新arXiv研究（2024-2025）
   - 核心指标与方法论
   - Trajectory Reward Learning前景

9. **生产环境评估实践** (10段)
   - 离线vs在线评估
   - A/B测试严谨性
   - 实时anti-Goodhart机制

10. **Anti-Gaming机制** (6段)
    - Benchmark Mutation
    - Ensemble Baselines
    - Out-of-Distribution保留

11. **成本-质量Pareto** (6段)
    - 模型成本分析
    - 企业权衡策略
    - 动态资源分配

---

### 综合总结文档
**`_C11_DELIVERABLES_SUMMARY.md`** - 30KB

面向实施团队的完整指南：

**章节**：
1. 三项交付物总结表
2. 8个算法的设计决策深度解析
3. Hook映射执行流图
4. 实现检查清单（开发/生产/监控三阶段）
5. 与Harness框架的关系定位
6. 评估系统的健康指标与审查计划
7. 扩展性与未来研究方向
8. 快速启动步骤

**关键部分**：
- §N.7：Hook点总结表（所有8个算法一览）
- §N.8：执行流图（完整管道可视化）
- §N.10：实现检查清单（按阶段的具体任务）

---

## 查找指南

### 我想要…

**理解评估理论？**
→ `_research_c11_enhanced.md` §4（Goodhart's Law）

**查看伪代码？**
→ `012_SYSTEM_C11_EVALUATION.md` §N.1-N.8（每个算法45-70行）

**了解Hook点？**
→ `012_SYSTEM_C11_EVALUATION.md` §N.9（表N.1）

**开始实现？**
→ `_C11_DELIVERABLES_SUMMARY.md`（检查清单 + 快速启动）

**看执行流程？**
→ `012_SYSTEM_C11_EVALUATION.md` §N.8 或 `_C11_DELIVERABLES_SUMMARY.md` §2.1

**查找arXiv论文链接？**
→ `012_SYSTEM_C11_EVALUATION.md`（所有引用已markdown化）

**了解Goodhart防护？**
→ `_research_c11_enhanced.md` §8 + `012_SYSTEM_C11_EVALUATION.md` §N.6

**成本优化建议？**
→ `_research_c11_enhanced.md` §11 + `012_SYSTEM_C11_EVALUATION.md` §N.7

---

## 关键统计

| 类别 | 数值 |
|------|------|
| **总文档行数** | 3243行 |
| **总文档大小** | ~174KB |
| **核心伪代码** | 390+行 |
| **@dataclass结构** | 9个 |
| **函数实现** | 9个 |
| **arXiv论文链接** | 39条 |
| **设计决策记录** | 8个算法×6个决策 |
| **执行检查项** | 16项 |

---

## 推荐阅读路线

### 路线A：5分钟快速了解
1. 本索引页面
2. `_C11_DELIVERABLES_SUMMARY.md` 执行总结
3. `012_SYSTEM_C11_EVALUATION.md` §N.8 执行流图

### 路线B：30分钟理论入门
1. `_research_c11_enhanced.md` §1-4
2. `012_SYSTEM_C11_EVALUATION.md` §N.0 框架概览
3. `_C11_DELIVERABLES_SUMMARY.md` 表2.1算法概览

### 路线C：2小时深入理解
1. `_research_c11_enhanced.md` 完整阅读
2. `012_SYSTEM_C11_EVALUATION.md` §N.1-N.8 逐算法学习
3. `_C11_DELIVERABLES_SUMMARY.md` 设计决策和健康指标

### 路线D：4小时实施准备
1. 路线C的全部内容
2. `_C11_DELIVERABLES_SUMMARY.md` §N.10 检查清单
3. 在你的框架中映射Hook点
4. 设计初始实施计划

---

## 文件快速参考

```
harness/
├── 012_SYSTEM_C11_EVALUATION.md ........... 主研究文档 (2918行)
├── _research_c11_enhanced.md ............ 增强研究笔记 (297行)
├── _C11_DELIVERABLES_SUMMARY.md ........ 综合总结 (参考本文档)
├── C11_INDEX.md ......................... 本索引文件
│
└── 相关文档：
    ├── 012_SYSTEM_C1.md ................. Harness优化层
    ├── 012_SYSTEM_C9_OBSERVABILITY.md .. 运行时监控
    ├── 012_SYSTEM_C12.md ............... 发布决策 (待)
    └── _research_c*.md ................. 其他层的研究笔记
```

---

## Git历史

**提交信息**：
```
commit 4faf00c
Author: Claude Opus 4.6
Date:   2026-03-30 16:55 UTC

docs(C11): Add engineering implementation with 8 algorithms + Hook pseudocode

- Section §N: Complete C11 engineering implementation
- 8 core algorithms with 390+ LOC pseudocode
- Hook mapping and execution flow diagram
- Implementation checklist with 3 phases
- Enhanced research notes covering 9 major areas
- Updated all 39 arXiv references with markdown links
```

---

## 常见问题（FAQ）

**Q: 这三项交付物的优先级是什么？**
A:
1. 先阅读`_research_c11_enhanced.md`理解背景
2. 再看`012_SYSTEM_C11_EVALUATION.md`§N的伪代码
3. 最后参考`_C11_DELIVERABLES_SUMMARY.md`规划实施

**Q: 如果我只有1小时，应该读什么？**
A: `_C11_DELIVERABLES_SUMMARY.md`的执行总结 + §N.9的表 + §N.8的流图

**Q: 伪代码可以直接运行吗？**
A: 不行。这是概念伪代码（@dataclass + 主要逻辑），需要：
- 实现依赖库（isolation env、statistical test、LLM API调用）
- 适配你的Agent框架和基准格式
- 添加错误处理和日志系统

**Q: Goodhart's Law的三层表现指什么？**
A: 参考`_research_c11_enhanced.md`§4：
1. 数据层：模型对基准分布的过拟合
2. 流程层：评估系统本身的操纵（如Chatbot Arena）
3. 目标层：优化指标而非真实目标

**Q: Anti-gaming检测包括哪些信号？**
A: 参考`012_SYSTEM_C11_EVALUATION.md`§N.6：
1. 基准特异性改进（某基准快升，其他不动）
2. 轨迹多样性低（所有任务用相同策略）
3. 输入-输出语义相似度高（可能直接记忆）

**Q: 如何选择离线vs灰度路径？**
A: 参考`012_SYSTEM_C11_EVALUATION.md`§N.8：
- 低风险：快速路径(30min离线)
- 中风险：标准路径(2h离线 + 小流量灰度)
- 高风险：完整路径(8h离线 + 长期灰度)

---

## 联系与反馈

**文档维护**：Harness工程体系评估小组
**最后更新**：2026-03-30
**反馈方式**：向研究组提交issue或pull request
**预期下一个版本**：Q3 2026（生产实现反馈）

---

## 许可与引用

本文档系列采用CC-BY-4.0许可。如使用，请引用：

```bibtex
@misc{harness_c11_2026,
  title = {C11 评估与基准测试：工程实现与Hook映射},
  author = {Harness Engineering Team},
  year = {2026},
  month = {March},
  note = {Git commit 4faf00c},
  url = {/sessions/gifted-wonderful-dirac/mnt/harness/012_SYSTEM_C11_EVALUATION.md}
}
```

---

**最后更新**：2026年3月30日
**版本**：1.0
**准备好开始了吗？** → 选择上述推荐阅读路线之一开始！
