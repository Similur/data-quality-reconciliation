# Automated data quality and reconciliation

I built this small Python portfolio project to show how I check data after an automated load. It compares the loaded data with a trusted reference dataset and reports missing records, extra records, and changed values.

The two sample CSV files contain made-up records. I built the demo independently, without using employer code or data.

## What it checks

- Compares record counts between the two datasets.
- Lists IDs that are missing from the loaded data or appear only there.
- Checks the category, amount, and update timestamp for each matching ID.
- Reports counts and amount totals by category so you can check differences within the overall total.
- Reports duplicate IDs, missing keys, invalid numbers, and timestamps that are invalid or lack a timezone.
- Allows small amount differences up to a tolerance of 0.01 by default.

The sample files differ on purpose, so the default run returns FAIL. The report lists the discrepancies. To see a passing result, use the same file for both inputs.

## Run it

You'll need Python 3.10 or newer. The project uses the standard library and needs no API keys.

On macOS or Linux:

```bash
PYTHONPATH=src python -m reconciliation.cli
PYTHONPATH=src python -m unittest discover -s tests -v
```

In Windows PowerShell:

```powershell
$env:PYTHONPATH = "src"
python -m reconciliation.cli
python -m unittest discover -s tests -v
```

Each run prints a short summary, saves the full results to `output/reconciliation.json`, and writes a Markdown summary to `output/reconciliation.md`.

Use the reference file as both inputs for a passing run:

```bash
PYTHONPATH=src python -m reconciliation.cli --reference sample_data/reference.csv --actual sample_data/reference.csv
```

To compare your own CSV files:

```bash
PYTHONPATH=src python -m reconciliation.cli --reference path/to/expected.csv --actual path/to/loaded.csv --output output/my_comparison.json
```

Both files need the columns `record_id`, `category`, `amount`, and `updated_at`.

## How it's organized

```text
data-quality-reconciliation/
├── src/reconciliation/
│   ├── __init__.py
│   ├── core.py             # File loading, comparisons, and category totals
│   └── cli.py              # Runs the checks and writes the report
├── sample_data/
│   ├── reference.csv
│   └── automated.csv
├── tests/
│   └── test_core.py
├── output/                  # Generated reports go here
├── .gitignore
└── README.md
```

## Where I'd take it next

This version holds the CSV data in memory, so it's meant for small files. For a larger production workflow, I'd consider comparing Spark DataFrames or database tables and saving results from each run. Configurable quality thresholds and a Power BI view of discrepancies would also be useful. None of those additions are implemented here.

## Project background

I've worked on checking automated data processing against existing reporting results. I wanted a public example of that approach, so I wrote this standalone demo using common data engineering techniques and made-up records. It contains no employer-owned code, internal schemas, credentials, student information, or private business rules.

The project is for testing and portfolio review. It isn't intended to be a production quality-control framework.
