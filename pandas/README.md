# Pandas Learning Deck

A practical, notebook-driven collection of Pandas examples covering data structures, data wrangling, file I/O, aggregation, reshaping, time-series analysis, optimization, and an end-to-end e-commerce workflow.

This directory is part of the [`python-tech-deck`](https://github.com/AshPiBit02/python-tech-deck) repository, a digital deck of Python library implementations, experiments, and micro-tools.

## Overview

The notebooks progress from Pandas fundamentals to more realistic data-processing tasks. Examples use small, self-contained datasets as well as CSV files and an e-commerce workflow so that individual techniques can be studied in isolation and then combined into a practical pipeline.

### Topics covered

- Pandas `Series` and `DataFrame` fundamentals
- Indexing, selection, filtering, and descriptive statistics
- Column creation, renaming, sorting, ranking, and transformation
- Missing-value detection and cleanup
- Duplicate-row removal and data-quality checks
- Reading and writing CSV, Excel, and JSON files
- Chunked processing for larger CSV files
- `groupby`, aggregation, transformation, filtering, and custom aggregations
- Merging, joining, concatenating, and combining DataFrames
- Pivot tables, crosstabs, MultiIndex operations, stacking, unstacking, melting, and exploding list-valued columns
- Datetime conversion, date-based indexing, resampling, and custom time intervals
- Vectorized calculations, numeric downcasting, categorical data, and query-based filtering
- A complete e-commerce cleaning, transformation, and analysis workflow

## Directory Structure

```text
pandas/
├── intro.ipynb
├── series_init.ipynb
├── dataFrame_impl.ipynb
├── indexingAndSelection.ipynb
├── dataCleaning.ipynb
├── Working_with_files.ipynb
├── GroupingAggregation.ipynb
├── advancedGrouping.ipynb
├── MergingJoiningDF.ipynb
├── advancedDataManipulation_imple.ipynb
├── Timeseries.ipynb
├── PerformaceOptimization.ipynb
└── Real-World Implementation/
    └── Ecommerce workflow/
        ├── ecommerce_data.csv
        ├── cleaned_ecommerce_data.csv
        └── processor.ipynb
```

## Notebook Guide

| Notebook | Focus |
| --- | --- |
| [`intro.ipynb`](./intro.ipynb) | Introduction to Pandas, its core structures, common use cases, and the role of `Series` and `DataFrame`. |
| [`series_init.ipynb`](./series_init.ipynb) | Creating and working with `Series`, including labels, attributes, selection, filtering, statistics, missing values, mapping, rolling operations, and alignment. |
| [`dataFrame_impl.ipynb`](./dataFrame_impl.ipynb) | Constructing DataFrames from dictionaries, lists, and NumPy arrays; inspecting structure; transforming columns; selecting data; and combining tables. |
| [`indexingAndSelection.ipynb`](./indexingAndSelection.ipynb) | Column and row selection, `.loc`, `.iloc`, boolean filtering, index usage, and targeted value access. |
| [`dataCleaning.ipynb`](./dataCleaning.ipynb) | Detecting, removing, and replacing missing values, with examples based on employee-style tabular data. |
| [`Working_with_files.ipynb`](./Working_with_files.ipynb) | Importing and exporting CSV, Excel, and JSON data; index handling; concatenation; and chunked processing for large files. |
| [`GroupingAggregation.ipynb`](./GroupingAggregation.ipynb) | Grouping sales records by category, region, and product using sums, means, counts, and multiple aggregations. |
| [`advancedGrouping.ipynb`](./advancedGrouping.ipynb) | Group-level `transform`, `filter`, `apply`, custom aggregations, top-N selection, ordering, and `size` versus `count`. |
| [`MergingJoiningDF.ipynb`](./MergingJoiningDF.ipynb) | Inner, left, and right merges; vertical and horizontal concatenation; and index-based joins. |
| [`advancedDataManipulation_imple.ipynb`](./advancedDataManipulation_imple.ipynb) | Pivot tables, crosstabs, normalized frequencies, MultiIndex, stack/unstack, melt, pivoting, and exploding list-valued columns. |
| [`Timeseries.ipynb`](./Timeseries.ipynb) | Datetime conversion, date components, date slicing, time-based indexing, weekly/monthly resampling, custom intervals, and aggregation comparisons. |
| [`PerformaceOptimization.ipynb`](./PerformaceOptimization.ipynb) | Vectorized calculations, memory inspection, numeric downcasting, categorical encoding, and efficient filtering on a 10,000-row sales dataset. |

## Real-World Implementation: E-commerce Workflow

The [`Real-World Implementation/Ecommerce workflow`](./Real-World%20Implementation/Ecommerce%20workflow/) example combines the techniques from the learning notebooks into a compact data-processing pipeline.

### Workflow stages

1. **Load** raw order data from `ecommerce_data.csv`.
2. **Inspect** shape, schema, summary statistics, and sample records.
3. **Clean** missing values and remove duplicate orders.
4. **Transform** order dates into datetime values and calculate per-order revenue with `price × quantity`.
5. **Analyze** total revenue and identify the most frequently sold products.
6. **Group** revenue by product category and sales by city.
7. **Export** the cleaned dataset to `cleaned_ecommerce_data.csv`.

The sample data models orders containing customer, location, product, category, price, quantity, order date, and payment-method fields. It is suitable for demonstrating an approachable ETL-style workflow without requiring an external database or API.

## Getting Started

### Requirements

- Python 3.10 or newer
- Jupyter Notebook or JupyterLab
- Pandas
- NumPy
- An Excel engine such as `openpyxl` if running the Excel examples

Install the core dependencies with:

```bash
python -m pip install pandas numpy jupyter openpyxl
```

### Run the notebooks

From the repository root:

```bash
jupyter notebook
```

Then open any notebook under `pandas/`. To run the e-commerce workflow, open:

```text
pandas/Real-World Implementation/Ecommerce workflow/processor.ipynb
```

The file-based notebooks expect their example input files in a `dataFiles/` directory relative to the notebook's working directory. If a notebook is opened from a different location, update the paths or start Jupyter from the appropriate directory.

## Representative Examples

### Create and transform a DataFrame

```python
import pandas as pd

sales = pd.DataFrame(
    {
        "product": ["Laptop", "Phone", "Tablet"],
        "price": [1200, 800, 300],
        "quantity": [2, 5, 3],
    }
)

sales["revenue"] = sales["price"] * sales["quantity"]
print(sales)
```

### Aggregate by a category

```python
revenue_by_product = (
    sales.groupby("product", as_index=True)["revenue"]
    .sum()
    .sort_values(ascending=False)
)
```

### Resample time-indexed data

```python
daily = pd.DataFrame(
    {
        "date": pd.date_range("2026-04-01", periods=10, freq="D"),
        "sales": [200, 220, 250, 270, 300, 280, 260, 310, 330, 350],
    }
).set_index("date")

weekly_sales = daily.resample("W")["sales"].sum()
```

## Recommended Learning Path

1. Start with `intro.ipynb`, `series_init.ipynb`, and `dataFrame_impl.ipynb`.
2. Practice selection and cleanup with `indexingAndSelection.ipynb` and `dataCleaning.ipynb`.
3. Learn file-based workflows with `Working_with_files.ipynb`.
4. Continue with `GroupingAggregation.ipynb`, `advancedGrouping.ipynb`, and `MergingJoiningDF.ipynb`.
5. Study reshaping and hierarchical data in `advancedDataManipulation_imple.ipynb`.
6. Explore time-indexed data in `Timeseries.ipynb`.
7. Finish with `PerformaceOptimization.ipynb` and the e-commerce workflow.

## Notes

- These notebooks are educational examples rather than a packaged Pandas library or production ETL framework.
- Several examples intentionally use small, constructed datasets to make individual operations easy to inspect.
- Notebook outputs may reflect the environment and Pandas version used when the notebook was last executed.
- Some filenames and example variable names retain their original learning-oriented spelling, including `PerformaceOptimization.ipynb`.

## Related Resources

- [Pandas documentation](https://pandas.pydata.org/docs/)
- [Pandas user guide](https://pandas.pydata.org/docs/user_guide/index.html)
- [NumPy documentation](https://numpy.org/doc/)
- [Parent repository](https://github.com/AshPiBit02/python-tech-deck)
