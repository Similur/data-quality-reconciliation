"""Run the reconciliation checks from the command line and save the reports."""
import argparse
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from .core import category_totals, compare, load_records


def make_markdown(report: dict) -> str:
    """Summarize the results and input errors in Markdown."""
    summary = report['summary']
    lines = [
        '# Reconciliation Results', '',
        f"**Status:** {'PASS' if summary['passed'] else 'FAIL'}", '',
        '| Check | Result |', '|---|---:|',
        f"| Reference records | {summary['reference_count']} |",
        f"| Automated records | {summary['actual_count']} |",
        f"| Missing IDs | {summary['missing_count']} |",
        f"| Unexpected IDs | {summary['unexpected_count']} |",
        f"| Changed records | {summary['changed_count']} |",
        f"| Amount difference | {summary['total_difference']} |",
        f"| Invalid input rows | {len(report['validation_errors'])} |", '',
    ]
    for title, values in [('Missing IDs', report['missing_ids']), ('Unexpected IDs', report['unexpected_ids'])]:
        lines.extend([f'## {title}', '', ', '.join(values) if values else 'None', ''])
    lines.extend(['## Changed Records', ''])
    if report['changed_records']:
        lines.extend(f"- **{record['record_id']}**: {', '.join(record['fields'])}" for record in report['changed_records'])
    else:
        lines.append('None')
    lines.extend(['', '## Input Errors', ''])
    lines.extend(f'- {issue}' for issue in report['validation_errors'])
    if not report['validation_errors']:
        lines.append('None')
    return '\n'.join(lines) + '\n'


def main() -> int:
    parser = argparse.ArgumentParser(description='Compare an automated load against reference data.')
    parser.add_argument('--reference', type=Path, default=Path('sample_data/reference.csv'))
    parser.add_argument('--actual', type=Path, default=Path('sample_data/automated.csv'))
    parser.add_argument('--output', type=Path, default=Path('output/reconciliation.json'))
    parser.add_argument('--tolerance', type=Decimal, default=Decimal('0.01'))
    args = parser.parse_args()
    if not args.tolerance.is_finite() or args.tolerance < 0:
        parser.error('--tolerance must be a nonnegative finite decimal')
    try:
        reference, ref_problems = load_records(args.reference)
        actual, actual_problems = load_records(args.actual)
    except (OSError, ValueError) as exc:
        parser.exit(2, f'Input error: {exc}\n')
    report = compare(reference, actual, args.tolerance)
    problems = ref_problems + actual_problems
    report['validation_errors'] = problems
    report['reference_by_category'] = category_totals(reference)
    report['actual_by_category'] = category_totals(actual)
    report['generated_at_utc'] = datetime.now(timezone.utc).isoformat()
    report['summary']['passed'] = report['summary']['passed'] and not problems
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    args.output.with_suffix('.md').write_text(make_markdown(report), encoding='utf-8')
    print(f"Reference: {len(reference)} | Automated: {len(actual)}")
    print(f"Missing: {len(report['missing_ids'])} | Unexpected: {len(report['unexpected_ids'])} | Changed: {len(report['changed_records'])} | Input errors: {len(problems)}")
    print(f"Result: {'PASS' if report['summary']['passed'] else 'FAIL'} | Report: {args.output}")
    return 0 if report['summary']['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
