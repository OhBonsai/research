---
name: agent-bench-gen
description: >
  AI Agent Benchmark 生成器——从算法/能力规格文档自动生成完整的评测套件（种子数据+多轮对话testcase+评分标准）。
  当用户提到以下场景时触发此 skill：
  创建 benchmark、生成测试用例、评测 AI Agent、从规格文档生成 testcase、
  构建评估数据集、seed data 生成、多轮对话 prompt 设计、probe 问题设计、
  评测框架搭建、算法验证测试集。
  即使用户只说"帮我做个评测"或"把这个规格拆成测试"也应该触发。
---

# Agent Benchmark Generator

从算法/能力规格文档出发，自动化生成企业级 AI Agent 评测套件的完整工作流。

## 何时使用

当用户需要：
- 把一份算法规格或能力定义文档转化为可执行的测试集
- 为 AI Agent 生成多轮对话 benchmark
- 程序化生成带 ground truth 的种子数据
- 构建 probe-based 评估体系（recall / artifact / plan / decision）

## 核心理念

这套方法论来自实战经验：Context-Bench 的 SQL→虚构实体管线、Factory AI 的 probe-based evaluation、ACON 的 paired trajectory analysis。核心原则是：**种子数据必须程序化生成，确保虚构实体不与训练数据重叠，每个 probe 都有确定性 ground truth**。

---

## 工作流总览

```
输入：规格文档（算法/能力定义 + case 列表）
  │
  ├── Phase 1: 解析规格 ──→ 提取 case 定义（场景、轮次、算法、数据需求）
  │
  ├── Phase 2: 种子数据 ──→ 4 条程序化管线生成 seed data + ground truth
  │
  ├── Phase 3: Testcase  ──→ 多轮对话 YAML（system_prompt + turns + probes + criteria）
  │
  ├── Phase 4: 索引验证 ──→ README 索引 + YAML/JSON 语法校验 + 数据完整性
  │
  └── Phase 5: 提交归档 ──→ git commit（每阶段独立 commit）
```

---

## Phase 1：规格文档解析

### 输入要求

规格文档应包含结构化的 case 定义，每个 case 包含：

| 字段 | 必需 | 说明 |
|------|:----:|------|
| ID | ✓ | 唯一编号（如 SHORT-01, TASK-A） |
| 场景 | ✓ | 任务描述 |
| 测试目标 | ✓ | 验证什么算法/能力 |
| 种子数据 | ✓ | 需要哪些文件、数据规模 |
| 用户指令序列 | ✓ | 按轮次的用户输入 |
| Probe 问题 | ○ | 评估信息保留的问题（可后续补充） |
| 成功标准 | ○ | 可自动判定的通过条件 |

### 操作步骤

1. 读取规格文档，提取所有 case 的上述字段
2. 按 case 类型分组（短/中/长，或按用户定义的分类）
3. 对每个 case 判断种子数据生成策略（见 Phase 2 的管线选择）
4. 输出 case 清单表格，与用户确认后进入下一阶段

---

## Phase 2：种子数据生成

种子数据的核心要求：**虚构实体**（防止模型依赖训练数据）、**确定性答案**（每个 probe 有 ground truth）、**可控噪声**（干扰信息比例可配置）、**固定种子**（可复现）。

### 4 条程序化生成管线

根据 case 的数据特征选择管线：

#### 管线 A：SQLite + Faker（结构化数据）

**适用场景：** 需要大量结构化虚构数据的 case（人员档案、KPI、任务列表、检查项）

```python
# 模板
import sqlite3, yaml, csv
from faker import Faker
fake = Faker('zh_CN')
fake.seed_instance(SEED)  # 固定种子，可复现

# 1. 定义 schema
# 2. Faker 填充虚构中文数据
# 3. 导出为 YAML/CSV/Markdown
# 4. 程序化注入测试条件（如特定分布、已知异常）
```

**判断标准：** case 需要 >20 条结构化记录（人员、任务、KPI、控制项等）

#### 管线 B：规则注入 + 模板（文档类数据）

**适用场景：** 需要文档并注入已知错误/冲突的 case（翻译审校、合同审查、日程冲突）

```
1. 定义领域模板（合同/翻译文档/日历JSON）
2. 程序化注入已知错误/冲突（位置和数量可控）
3. 生成 _ground_truth_errors.yaml 作为评分答案
```

**判断标准：** case 的核心测试是"发现错误/冲突"，需要精确的 ground truth

#### 管线 C：矛盾对 / 冲突矩阵（螺旋检测类）

**适用场景：** 测试 Agent 识别矛盾/冲突的能力（需求反复变更、多方利益冲突）

```yaml
# _contradiction_pairs.yaml 模板
contradictions:
  - topic: "数据库选型"
    flip_sequence: ["MySQL", "PostgreSQL", "MySQL+读写分离"]
    trigger_turns: [2, 4]  # 在第2轮和第4轮触发翻转
    instruction_templates:
      forward: "把{component}从{A}换成{B}"
      backward: "还是用{A}，但加上{enhancement}"
```

**判断标准：** case 故意制造反复/冲突来测试检测能力

#### 管线 D：因果图 / 轨迹函数（分析推理类）

**适用场景：** 测试 Agent 的分析推理能力（Bug 根因分析、谈判策略、流程瓶颈）

```
1. 定义因果关系图或参数轨迹函数
2. 模板化生成文档（Bug报告/会议记录/流程图）
3. 注入红鲱鱼/瓶颈作为干扰
4. 生成 _ground_truth.yaml（正确答案 + 证据链）
```

**判断标准：** case 需要 Agent 从多个来源推理出根因/趋势/最优方案

### 管线选择决策树

```
case 的核心数据是什么？
├── 大量结构化记录 → 管线 A（SQLite + Faker）
├── 文档 + 已知缺陷 → 管线 B（规则注入）
├── 反复变更 / 多方冲突 → 管线 C（矛盾对）
└── 多源推理 / 因果链 → 管线 D（因果图）
```

多数 case 使用单一管线；复杂 case 可组合（如管线 A 生成基础数据 + 管线 B 注入缺陷）。

### 输出规范

每个 case 的种子数据存放在 `benchmark/seeds/{case-id}/` 目录下：

- 业务文件：.md / .yaml / .csv / .json（按 case 需求）
- Ground truth：`_ground_truth.yaml` 或 `_ground_truth_errors.yaml` 或 `_contradiction_pairs.yaml` 或 `_conflict_matrix.yaml`
- 所有虚构实体名称不与真实数据重叠
- 固定随机种子，注释中注明 seed 值

### 生成后验证

每批种子数据生成后，运行验证：

```python
# 验证清单
# 1. 文件数量与 case 定义一致
# 2. 所有文件非空
# 3. YAML/JSON 语法正确
# 4. ground truth 文件存在
# 5. 数据规模与 case 定义匹配（如"60个任务"确实有60条）
```

---

## Phase 3：Testcase YAML 生成

从 case 定义生成可执行的多轮对话脚本。

### YAML 结构模板

```yaml
id: "CASE-ID"
title: "场景标题"
scenario: "一句话描述"
algorithms: ["被测试的算法/能力列表"]
turns_target: 30          # 目标对话轮数
seed_data: "benchmark/seeds/case-id/"
seed_files:               # 种子文件清单及描述
  "file.yaml": "文件内容说明"

system_prompt: |
  你是一个{角色}AI助手，擅长{能力}。
  请{任务要求}。

turns:                    # 完整的用户指令序列
  - role: user
    content: "用户指令"
    expected_behavior: "Agent 预期行为描述"

probes:                   # Probe 评估问题
  - type: recall          # recall / artifact / plan / decision
    question: "评估问题"
    expected_answer: "预期答案（对应 ground truth）"

success_criteria:         # 可自动判定的通过条件
  - "条件1"
  - "条件2"

metrics:                  # 需记录的观测指标
  - "指标1"
```

### Probe 设计原则

4 种 Probe 类型，每个 case 至少覆盖 2 种：

| 类型 | 测试什么 | 示例 |
|------|---------|------|
| **recall** | 事实性保留 | "第3次会议讨论了什么？" |
| **artifact** | 工件追踪 | "生成了哪些文件？" |
| **plan** | 任务规划 | "下一步应该做什么？" |
| **decision** | 推理链保留 | "为什么选了方案A？" |

Probe 的 `expected_answer` 必须可从 ground truth 文件验证。

### Turn 设计原则

- **SHORT case（5-10 轮）：** 每轮都写出来，覆盖完整用户旅程
- **MID case（20-50 轮）：** 关键轮次详写，中间常规轮次可用 `"（继续类似操作）"` 占位
- **LONG case（100+ 轮）：** 按阶段分组，每阶段写 3-5 个代表性轮次，注明阶段边界

### System Prompt 设计

system_prompt 应包含：
1. Agent 角色定义（"你是一个{领域}AI助手"）
2. 核心能力声明（"擅长{能力}"）
3. 关键约束（如"保护机密信息不泄露"）

不要在 system_prompt 中透露测试意图或评分标准。

---

## Phase 4：索引与验证

### README 生成

在输出目录下生成 README.md，包含：

1. **数据集清单表**：目录 / 来源 / 大小 / 覆盖 case
2. **Case 全景表**：ID / 场景 / 轮数 / 测试算法 / 数据来源 / 状态
3. **种子文件清单**：每个 case 的文件详细列表
4. **目录结构树**
5. **生成方法说明**：4 条管线的简要描述
6. **统计汇总**：总 case 数、覆盖率、总文件数

### 全量验证

```bash
# 验证所有 YAML testcase
python3 -c "
import yaml, os
required = ['id','title','scenario','algorithms','turns_target',
            'seed_data','seed_files','system_prompt','turns',
            'probes','success_criteria','metrics']
for f in sorted(os.listdir('testcase/')):
    if not f.endswith('.yaml'): continue
    data = yaml.safe_load(open(f'testcase/{f}'))
    missing = [k for k in required if k not in data]
    assert not missing, f'{f}: missing {missing}'
    for t in data['turns']:
        assert 'role' in t and 'content' in t
    for p in data['probes']:
        assert 'type' in p and 'question' in p
print('All YAML valid')
"
```

---

## Phase 5：提交归档

遵循分阶段提交原则：

| 阶段 | Commit message 前缀 | 内容 |
|------|---------------------|------|
| 种子数据 | `data(benchmark):` | seeds/ 目录下的新增文件 |
| Testcase | `feat(testcase):` | testcase/*.yaml 文件 |
| README | `docs(benchmark):` | README.md 更新 |

每个 commit message 包含变更总结（文件数、case 数、覆盖率变化）。

---

## 快速开始检查清单

1. [ ] 规格文档已读取，case 清单已确认
2. [ ] 每个 case 的管线已选定（A/B/C/D）
3. [ ] 种子数据已生成并通过验证
4. [ ] Testcase YAML 已生成并通过语法检查
5. [ ] README 索引已更新
6. [ ] 所有变更已 git commit

---

## 参考资料

详细的管线实现模板和示例脚本见 `references/` 目录：
- `references/pipeline_templates.md` — 4 条管线的完整 Python 模板
- `references/yaml_schema.md` — Testcase YAML 的完整字段定义
- `references/probe_design.md` — Probe 问题设计指南和示例库
