#!/usr/bin/env python3
"""
验证完整的 benchmark 评测套件：种子数据 + testcase YAML
用法: python validate_suite.py <seeds_dir> <testcase_dir>
"""
import yaml, json, os, sys

def validate_seeds(seeds_dir):
    """验证种子数据目录"""
    errors, stats = [], {"cases": 0, "files": 0, "ground_truth": 0}
    if not os.path.isdir(seeds_dir):
        return [f"Seeds directory not found: {seeds_dir}"], stats

    for case_dir in sorted(os.listdir(seeds_dir)):
        case_path = os.path.join(seeds_dir, case_dir)
        if not os.path.isdir(case_path):
            continue
        stats["cases"] += 1
        file_count = 0
        has_gt = False

        for root, dirs, files in os.walk(case_path):
            for f in files:
                fp = os.path.join(root, f)
                file_count += 1
                # Check non-empty
                if os.path.getsize(fp) == 0:
                    errors.append(f"{case_dir}: empty file {f}")
                # Check YAML/JSON syntax
                try:
                    if f.endswith(('.yaml', '.yml')):
                        yaml.safe_load(open(fp, encoding='utf-8'))
                    elif f.endswith('.json'):
                        json.load(open(fp, encoding='utf-8'))
                except Exception as e:
                    errors.append(f"{case_dir}/{f}: parse error: {e}")
                # Check ground truth
                if f.startswith('_ground_truth') or f.startswith('_contradiction') or f.startswith('_conflict'):
                    has_gt = True

        stats["files"] += file_count
        if has_gt:
            stats["ground_truth"] += 1
        if file_count == 0:
            errors.append(f"{case_dir}: no files found")

    return errors, stats

def validate_testcases(testcase_dir):
    """验证 testcase YAML 文件"""
    REQUIRED = ['id', 'title', 'scenario', 'algorithms', 'turns_target',
                'seed_data', 'seed_files', 'system_prompt', 'turns',
                'probes', 'success_criteria', 'metrics']
    PROBE_TYPES = {'recall', 'artifact', 'plan', 'decision'}

    errors, stats = [], {"cases": 0, "turns": 0, "probes": 0}
    if not os.path.isdir(testcase_dir):
        return [f"Testcase directory not found: {testcase_dir}"], stats

    for f in sorted(os.listdir(testcase_dir)):
        if not f.endswith('.yaml'):
            continue
        stats["cases"] += 1
        fp = os.path.join(testcase_dir, f)
        try:
            data = yaml.safe_load(open(fp, encoding='utf-8'))
        except Exception as e:
            errors.append(f"{f}: YAML parse error: {e}")
            continue

        # Required fields
        for key in REQUIRED:
            if key not in data:
                errors.append(f"{f}: missing field '{key}'")

        # Turns validation
        if 'turns' in data:
            stats["turns"] += len(data['turns'])
            for i, t in enumerate(data['turns']):
                if 'role' not in t or 'content' not in t:
                    errors.append(f"{f}: turn[{i}] missing role/content")

        # Probes validation
        if 'probes' in data:
            stats["probes"] += len(data['probes'])
            for i, p in enumerate(data['probes']):
                if 'type' not in p:
                    errors.append(f"{f}: probe[{i}] missing 'type'")
                elif p['type'] not in PROBE_TYPES:
                    errors.append(f"{f}: probe[{i}] invalid type '{p['type']}'")
                if 'question' not in p:
                    errors.append(f"{f}: probe[{i}] missing 'question'")

    return errors, stats

def main():
    seeds_dir = sys.argv[1] if len(sys.argv) > 1 else "benchmark/seeds"
    testcase_dir = sys.argv[2] if len(sys.argv) > 2 else "testcase"

    print("=" * 60)
    print("Agent Benchmark Suite Validation")
    print("=" * 60)

    # Validate seeds
    print(f"\n📦 Seeds: {seeds_dir}")
    seed_errors, seed_stats = validate_seeds(seeds_dir)
    print(f"   Cases: {seed_stats['cases']}")
    print(f"   Files: {seed_stats['files']}")
    print(f"   Ground truth: {seed_stats['ground_truth']}/{seed_stats['cases']}")
    if seed_errors:
        for e in seed_errors:
            print(f"   ✗ {e}")
    else:
        print("   ✓ All seeds valid")

    # Validate testcases
    print(f"\n📋 Testcases: {testcase_dir}")
    tc_errors, tc_stats = validate_testcases(testcase_dir)
    print(f"   Cases: {tc_stats['cases']}")
    print(f"   Turns: {tc_stats['turns']}")
    print(f"   Probes: {tc_stats['probes']}")
    if tc_errors:
        for e in tc_errors:
            print(f"   ✗ {e}")
    else:
        print("   ✓ All testcases valid")

    # Summary
    total_errors = len(seed_errors) + len(tc_errors)
    print(f"\n{'=' * 60}")
    if total_errors == 0:
        print(f"✅ PASS — {seed_stats['cases']} seeds + {tc_stats['cases']} testcases")
    else:
        print(f"❌ FAIL — {total_errors} errors found")
    print("=" * 60)

    return 1 if total_errors else 0

if __name__ == "__main__":
    sys.exit(main())
```
