# Testcase YAML Schema 定义

## 完整字段列表

| 字段 | 类型 | 必需 | 说明 |
|------|------|:----:|------|
| `id` | string | ✓ | Case 唯一编号 |
| `title` | string | ✓ | 场景标题 |
| `scenario` | string | ✓ | 一句话场景描述 |
| `algorithms` | list[string] | ✓ | 被验证的算法/能力列表 |
| `turns_target` | int | ✓ | 目标对话轮数 |
| `seed_data` | string | ✓ | 种子数据目录路径 |
| `seed_files` | dict | ✓ | 文件名→描述的映射 |
| `ground_truth_facts` | dict | ○ | 关键事实的 KV 对（辅助评分） |
| `system_prompt` | string | ✓ | Agent 的 system prompt |
| `turns` | list[Turn] | ✓ | 用户指令序列 |
| `probes` | list[Probe] | ✓ | Probe 评估问题 |
| `success_criteria` | list[string] | ✓ | 通过条件 |
| `metrics` | list[string] | ✓ | 观测指标 |

## Turn 对象

```yaml
- role: user           # 固定为 "user"
  content: "用户指令"   # 用户发送的消息
  expected_behavior: "Agent 预期行为描述"  # 用于人工评估
```

## Probe 对象

```yaml
- type: recall         # recall | artifact | plan | decision
  question: "评估问题"
  expected_answer: "预期答案，对应 ground truth"
```

## 验证脚本

```python
import yaml, os, sys

REQUIRED = ['id', 'title', 'scenario', 'algorithms', 'turns_target',
            'seed_data', 'seed_files', 'system_prompt', 'turns',
            'probes', 'success_criteria', 'metrics']

def validate_testcase(filepath):
    """验证单个 testcase YAML 文件"""
    errors = []
    data = yaml.safe_load(open(filepath, encoding='utf-8'))

    # 必需字段检查
    for key in REQUIRED:
        if key not in data:
            errors.append(f"missing required field: {key}")

    # turns 结构检查
    if 'turns' in data:
        for i, t in enumerate(data['turns']):
            if 'role' not in t:
                errors.append(f"turn[{i}] missing 'role'")
            if 'content' not in t:
                errors.append(f"turn[{i}] missing 'content'")

    # probes 结构检查
    if 'probes' in data:
        valid_types = {'recall', 'artifact', 'plan', 'decision'}
        for i, p in enumerate(data['probes']):
            if 'type' not in p:
                errors.append(f"probe[{i}] missing 'type'")
            elif p['type'] not in valid_types:
                errors.append(f"probe[{i}] invalid type: {p['type']}")
            if 'question' not in p:
                errors.append(f"probe[{i}] missing 'question'")

    return errors

def validate_all(directory):
    """验证目录下所有 YAML 文件"""
    total, passed, failed = 0, 0, 0
    for f in sorted(os.listdir(directory)):
        if not f.endswith('.yaml'):
            continue
        total += 1
        errors = validate_testcase(os.path.join(directory, f))
        if errors:
            failed += 1
            print(f"✗ {f}: {errors}")
        else:
            passed += 1
    print(f"\n{passed}/{total} passed, {failed} failed")
```
