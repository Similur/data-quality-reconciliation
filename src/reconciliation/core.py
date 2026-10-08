"""Compare a loaded dataset with reference data and report the differences."""

import csv
from collections import Counter
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from pathlib import Path

REQUIRED = ('record_id', 'category', 'amount', 'updated_at')


@dataclass(frozen=True)
class Record:
    record_id: str
    category: str
    amount: Decimal
    updated_at: str


def load_records(path: Path) -> tuple[dict[str, Record], list[str]]:
    """Read valid CSV records and collect errors for rows that cannot be loaded."""
    records = {}
    problems = []
    with path.open(newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not set(REQUIRED).issubset(reader.fieldnames):
            raise ValueError(f'{path.name} must have columns: {", ".join(REQUIRED)}')
        for line, row in enumerate(reader, start=2):
            key = (row.get('record_id') or '').strip()
            if not key:
                problems.append(f'{path.name}:{line}: missing record_id')
                continue
            try:
                amount = Decimal((row.get('amount') or '').strip())
                if not amount.is_finite():
                    raise InvalidOperation
            except InvalidOperation:
                problems.append(f'{path.name}:{line}: invalid amount for {key}')
                continue
            if key in records:
                problems.append(f'{path.name}:{line}: duplicate record_id {key}')
                continue
            raw_timestamp = (row.get('updated_at') or '').strip()
            try:
                parsed = datetime.fromisoformat(raw_timestamp.replace('Z', '+00:00'))
                if parsed.tzinfo is None or parsed.utcoffset() is None:
                    raise ValueError('timestamp has no timezone')
                timestamp = parsed.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
            except ValueError:
                problems.append(f'{path.name}:{line}: invalid timezone-aware timestamp for {key}')
                continue
            records[key] = Record(key, (row.get('category') or '').strip(), amount, timestamp)
    return records, problems


def compare(reference: dict[str, Record], actual: dict[str, Record], tolerance: Decimal = Decimal('0.01')) -> dict:
    """Return summary counts, amount totals, and differences for individual records."""
    reference_ids, actual_ids = set(reference), set(actual)
    missing = sorted(reference_ids - actual_ids)
    unexpected = sorted(actual_ids - reference_ids)
    changed = []
    for key in sorted(reference_ids & actual_ids):
        before, after = reference[key], actual[key]
        issues = []
        if before.category != after.category:
            issues.append('category')
        if abs(before.amount - after.amount) > tolerance:
            issues.append('amount')
        if before.updated_at != after.updated_at:
            issues.append('updated_at')
        if issues:
            changed.append({'record_id': key, 'fields': issues, 'reference': _serialize(before), 'actual': _serialize(after)})
    ref_total = sum((record.amount for record in reference.values()), Decimal('0'))
    actual_total = sum((record.amount for record in actual.values()), Decimal('0'))
    return {
        'summary': {
            'reference_count': len(reference), 'actual_count': len(actual),
            'count_difference': len(actual) - len(reference),
            'reference_total': str(ref_total), 'actual_total': str(actual_total),
            'total_difference': str(actual_total - ref_total),
            'missing_count': len(missing), 'unexpected_count': len(unexpected), 'changed_count': len(changed),
            'passed': not (missing or unexpected or changed),
        },
        'missing_ids': missing, 'unexpected_ids': unexpected, 'changed_records': changed,
    }


def category_totals(records: dict[str, Record]) -> dict[str, dict]:
    """Return the record count and amount total for each category."""
    counts = Counter(record.category for record in records.values())
    totals = {}
    for record in records.values():
        totals[record.category] = totals.get(record.category, Decimal('0')) + record.amount
    return {category: {'count': counts[category], 'total': str(totals[category])} for category in sorted(counts)}


def _serialize(record: Record) -> dict:
    data = asdict(record)
    data['amount'] = str(record.amount)
    return data
