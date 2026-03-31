# 种子数据生成管线模板

## 管线 A：SQLite + Faker（结构化数据）

### 适用场景
- 人员档案（绩效评估、团队管理）
- 任务列表（项目排期、WBS）
- 检查项（ISO 控制项、上线清单）
- 财务数据（KPI、预算）

### 完整模板

```python
#!/usr/bin/env python3
"""管线 A 模板：SQLite + Faker 生成结构化种子数据"""
import sqlite3, yaml, csv, os, random
from faker import Faker

# === 配置 ===
SEED = 42  # 固定种子，可复现
CASE_ID = "case-id"
OUTPUT_DIR = f"benchmark/seeds/{CASE_ID}"
os.makedirs(OUTPUT_DIR, exist_ok=True)

fake = Faker('zh_CN')
fake.seed_instance(SEED)
random.seed(SEED)

# === 1. 定义数据结构 ===
# 根据 case 需求定义，示例：团队花名册
team = []
skills_pool = ["Python", "Java", "React", "K8s", "数据库", "安全", "测试", "产品"]
for i in range(15):
    member = {
        "id": f"T{i+1:03d}",
        "name": fake.name(),
        "department": random.choice(["研发", "测试", "产品", "运维"]),
        "role": random.choice(["工程师", "高级工程师", "架构师", "经理"]),
        "skills": random.sample(skills_pool, k=random.randint(2, 4)),
        "availability": round(random.uniform(0.6, 1.0), 2),
        "daily_rate": random.choice([800, 1000, 1200, 1500, 2000])
    }
    team.append(member)

# === 2. 导出为目标格式 ===
# CSV 导出
with open(f"{OUTPUT_DIR}/team_roster.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=team[0].keys())
    writer.writeheader()
    writer.writerows(team)

# YAML 导出
with open(f"{OUTPUT_DIR}/config.yaml", "w", encoding="utf-8") as f:
    yaml.dump({"team": team}, f, allow_unicode=True, default_flow_style=False)

# === 3. 程序化注入测试条件 ===
# 示例：注入已知的资源冲突
# team[3]["availability"] = 0.3  # 制造过载
# team[7]["skills"] = ["Python"]  # 制造技能瓶颈

# === 4. 生成 ground truth ===
ground_truth = {
    "total_members": len(team),
    "departments": {d: sum(1 for m in team if m["department"] == d)
                    for d in set(m["department"] for m in team)},
    "overloaded_members": [m["name"] for m in team if m["availability"] < 0.5],
}
with open(f"{OUTPUT_DIR}/_ground_truth.yaml", "w", encoding="utf-8") as f:
    yaml.dump(ground_truth, f, allow_unicode=True, default_flow_style=False)

print(f"✓ {CASE_ID}: {len(team)} records generated")
```

### 关键技巧
- `Faker('zh_CN')` 生成中文虚构数据
- 固定 seed 确保可复现
- 注入特定异常值作为测试探针
- ground truth 由生成脚本自动计算，非人工编写

---

## 管线 B：规则注入 + 模板（文档类数据）

### 适用场景
- 翻译审校（注入已知翻译错误）
- 合同审查（注入条款风险）
- 日程管理（注入时间冲突）
- 数据清洗（注入已知数据质量问题）

### 完整模板

```python
#!/usr/bin/env python3
"""管线 B 模板：规则注入生成带已知缺陷的文档"""
import json, yaml, random

SEED = 50
random.seed(SEED)

# === 1. 定义正确的基础数据 ===
events = []
for day_offset in range(5):  # 周一到周五
    for hour in [9, 10, 11, 14, 15, 16]:
        if random.random() < 0.5:  # 50% 的时段有事件
            events.append({
                "id": f"EVT-{len(events)+1:03d}",
                "day": day_offset,
                "start_hour": hour,
                "duration": random.choice([1, 1.5, 2]),
                "title": random.choice(["客户会议", "内部周会", "技术评审", "1:1沟通", "培训"]),
                "priority": random.choice(["high", "medium", "low"])
            })

# === 2. 程序化注入冲突 ===
conflicts = []
# 冲突1：完全重叠
evt_a, evt_b = events[2], events[3]
evt_b["day"] = evt_a["day"]
evt_b["start_hour"] = evt_a["start_hour"]
conflicts.append({"type": "full_overlap", "events": [evt_a["id"], evt_b["id"]]})

# 冲突2：部分重叠
evt_c, evt_d = events[5], events[6]
evt_d["day"] = evt_c["day"]
evt_d["start_hour"] = evt_c["start_hour"] + 0.5
conflicts.append({"type": "partial_overlap", "events": [evt_c["id"], evt_d["id"]]})

# === 3. 导出 ===
output = {
    "week_of": "2026-04-06",
    "events": events,
    "_ground_truth_conflicts": conflicts  # ground truth 嵌入数据文件
}
with open("calendar_week.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
```

### 错误注入类型参考
| 错误类型 | 注入方法 | ground truth 记录 |
|---------|---------|-----------------|
| 术语不一致 | 替换术语表中的翻译 | 位置+正确译文 |
| 遗漏 | 删除原文中的句子 | 被删句子+位置 |
| 意义反转 | 加/去否定词 | 原文+错误译文+正确译文 |
| 时间冲突 | 重叠事件时间 | 冲突事件对 |
| 数据质量 | 格式错误/重复/空值 | 问题行号+类型 |

---

## 管线 C：矛盾对 / 冲突矩阵（螺旋检测类）

### 适用场景
- 迭代式文档撰写（需求反复变更）
- 多方利益冲突（部门间矛盾需求）
- 技术选型反复

### 矛盾对模板

```yaml
# _contradiction_pairs.yaml
contradictions:
  - topic: "数据库选型"
    options: ["MySQL", "PostgreSQL"]
    flip_sequence:
      - turn: 2
        direction: "forward"
        instruction: "把数据库从 MySQL 换成 PostgreSQL"
      - turn: 4
        direction: "backward"
        instruction: "还是用 MySQL，但加一个读写分离"
    final_choice: "MySQL + 读写分离"

  - topic: "缓存方案"
    options: ["Redis", "Memcached"]
    flip_sequence:
      - turn: 6
        direction: "forward"
        instruction: "缓存从 Redis 换成 Memcached"
      - turn: 8
        direction: "backward"
        instruction: "还是 Redis，但换成集群模式"
    final_choice: "Redis 集群"

spiral_detection:
  expected_trigger_turn: "10-15"
  expected_behavior: "Agent 应主动提出先确认最终选型"
```

### 冲突矩阵模板

```yaml
# _conflict_matrix.yaml
stakeholders:
  - name: "财务部"
    core_demand: "更多审批层级，风险控制"
    non_negotiable: "不允许自动审批"
  - name: "运营部"
    core_demand: "减少审批，提高效率"
    non_negotiable: "端到端≤5天"
  - name: "合规部"
    core_demand: "100%审核覆盖"
    non_negotiable: "所有采购必须经法务审核"

conflicts:
  - topic: "审批层级"
    finance: "要三级"
    operations: "要一级"
    resolution_hint: "分级审批（金额阈值）"
  - topic: "自动化程度"
    finance: "禁止自动审批"
    operations: "小额自动通过"
    resolution_hint: "仅小额（<5000）自动+人工复核抽检"
```

---

## 管线 D：因果图 / 轨迹函数（分析推理类）

### 适用场景
- Bug 根因分析（因果图 + 红鲱鱼）
- 商务谈判分析（参数轨迹函数）
- 流程瓶颈识别（SLA 违规注入）

### 因果图模板（Bug 分析）

```python
# 2 个根因 → 12 个 Bug + 3 个红鲱鱼
root_causes = {
    "A": {"name": "连接池泄漏", "bugs": [101,103,105,107,109,111],
           "symptom_pattern": "超时/OOM/服务不可用"},
    "B": {"name": "缓存TTL错误", "bugs": [102,104,106,108,110,112],
           "symptom_pattern": "数据不一致/状态过期"}
}
red_herrings = ["Nginx超时调整", "JDK版本升级", "K8s内存限制变更"]
```

### 参数轨迹函数模板（谈判分析）

```python
import math

def price_trajectory(meeting_num, side):
    """价格谈判轨迹：双方逐渐趋同"""
    if side == "our":
        return 45 - 12 * (1 - math.exp(-0.3 * meeting_num))  # 45→33
    else:
        return 20 + 12 * (1 - math.exp(-0.3 * meeting_num))  # 20→32

# 生成12次会议记录
for i in range(1, 13):
    our_price = round(price_trajectory(i, "our"), 1)
    their_price = round(price_trajectory(i, "their"), 1)
    # 用模板生成 meeting_{i:02d}.md
```

### SLA 瓶颈注入模板（流程优化）

```python
process_steps = [
    {"name": "需求确认", "sla_days": 3, "actual_avg": 2.5},
    {"name": "方案设计", "sla_days": 5, "actual_avg": 4.0},
    {"name": "系统配置", "sla_days": 15, "actual_avg": 22.0},  # 瓶颈！47%超标
    {"name": "数据迁移", "sla_days": 5, "actual_avg": 4.5},
]
# ground truth: 系统配置是最大瓶颈（actual/sla = 1.47）
```
