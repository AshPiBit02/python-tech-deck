# NumPy Learning Deck

A structured, hands-on collection of NumPy notes, Jupyter notebooks, challenges, and applied data-science exercises.

This directory is designed to take learners from NumPy fundamentals through array manipulation, numerical computing, linear algebra, simulation, and performance-oriented workflows.

## Overview

The materials combine concise Markdown explanations with executable Jupyter notebooks. Each topic is organized around a core concept and, where useful, extends into challenges or real-world analysis.

### What you will learn

- How NumPy arrays differ from Python lists
- Array creation, shapes, dimensions, and data types
- Indexing, slicing, Boolean masks, and fancy indexing
- Element-wise operations and broadcasting
- Reshaping, flattening, joining, and splitting arrays
- Mathematical reductions, axis operations, clipping, percentiles, and dispersion
- Structured arrays and custom dtypes
- Linear algebra concepts and applied prediction exercises
- Random sampling, Monte Carlo estimation, and bootstrap confidence intervals
- Copy-versus-view behavior and memory implications
- Practical performance and optimization techniques
- NumPy workflows used in data science and image processing

## Learning Path

The recommended progression is:

1. **Start with the introduction** in [`numpy.md`](./numpy.md).
2. **Create and inspect arrays** using the Array Creation Techniques notebooks.
3. **Practice indexing and slicing** before moving to advanced indexing.
4. **Build fluency with element-wise operations and broadcasting.**
5. **Learn reshaping and array combination** patterns.
6. **Apply mathematical functions and axis-based reductions.**
7. **Explore structured data and linear algebra.**
8. **Finish with randomness, performance, and real-world analysis.**

## Topic Map

| Topic | Focus | Materials |
|---|---|---|
| **Introduction** | NumPy’s `ndarray`, installation, imports, and performance compared with Python lists | [`numpy.md`](./numpy.md) |
| **Array Creation Techniques** | `zeros`, `ones`, `empty`, `arange`, `linspace`, identity matrices, eye matrices, and random arrays | [`Array Creation Techniques/`](./Array%20Creation%20Techniques/) |
| **Array Operations** | Arithmetic, element-wise computation, basic broadcasting, row/column broadcasting, and practice challenges | [`Array Operations/`](./Array%20Operations/) |
| **Broadcasting Deep Dive** | Shape compatibility, broadcasting rules, and common broadcasting patterns | [`Broadcasting Deep Dive/`](./Broadcasting%20Deep%20Dive/) |
| **Indexing & Slicing** | One- and two-dimensional indexing, slicing, Boolean indexing, and fancy indexing | [`Indexing & Slicing/`](./Indexing%20%26%20Slicing/) |
| **Advanced Indexing & Tricks** | More expressive indexing patterns, Boolean logic, and sales-data exercises | [`Advanced Indexing & Tricks/`](./Advanced%20Indexing%20%26%20Tricks/) |
| **Reshaping & Manipulation** | Reshape, flatten, ravel, and combined manipulation workflows | [`Reshaping & Manipulation/`](./Reshaping%20%26%20Manipulation/) |
| **Joining & Splitting Arrays** | Combining arrays and dividing data into useful segments | [`Joining & Splitting Arrays/`](./Joining%20%26%20Splitting%20Arrays/) |
| **Mathematical Functions** | Aggregations, axis operations, clipping, `where`, percentiles, quantiles, variance, and standard deviation | [`Mathematical Functions/`](./Mathematical%20Functions/) |
| **Structured Arrays & Dtypes** | Record-like arrays, field definitions, and dtype-driven data organization | [`Structured Arrays & Dtypes/`](./Structured%20Arrays%20%26%20Dtypes/) |
| **Linear Algebra** | Core linear algebra operations and applied price-prediction notebooks | [`Linear Algebra/`](./Linear%20Algebra/) |
| **Random Module** | Random-number generation, Monte Carlo estimation, stock-rate analysis, and bootstrap intervals | [`Random Module/`](./Random%20Module/) |
| **Copy vs View** | Memory sharing, mutation behavior, and practical copy/view analysis | [`Copy vs View/`](./Copy%20vs%20View/) |
| **Performance & Optimization** | Core optimization concepts and image-processing analysis | [`Performance & Optimization/`](./Performance%20%26%20Optimization/) |
| **NumPy in Real Data Science** | Practical guidance for applying NumPy in data-science workflows | [`NumPy in Real Data Science/`](./NumPy%20in%20Real%20Data%20Science/) |

## Repository Structure

```text
numpy/
├── numpy.md
├── Advanced Indexing & Tricks/
├── Array Creation Techniques/
├── Array Operations/
├── Broadcasting Deep Dive/
├── Copy vs View/
├── Indexing & Slicing/
├── Joining & Splitting Arrays/
├── Linear Algebra/
├── Mathematical Functions/
├── NumPy in Real Data Science/
├── Performance & Optimization/
├── Random Module/
├── Reshaping & Manipulation/
└── Structured Arrays & Dtypes/
```

Most topic directories contain a combination of:

- Markdown notes for definitions, rules, and conceptual explanations
- Jupyter notebooks for executable examples and experiments
- Challenge notebooks for reinforcement and problem solving
- Applied notebooks using business, financial, or image-processing scenarios

## Requirements

- Python 3.9 or newer recommended
- NumPy
- Jupyter Notebook or JupyterLab

Optional tools such as Matplotlib or Pandas may be useful for extending the applied notebooks, depending on the notebook being explored.

## Installation

From the repository root, create and activate a virtual environment if desired:

```bash
python -m venv .venv
```

Activate it on macOS/Linux:

```bash
source .venv/bin/activate
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install the core dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install numpy jupyter
```

Launch Jupyter from the repository root:

```bash
jupyter lab
```

Then open any notebook under `numpy/` and execute the cells in order.

## Quick Start

```python
import numpy as np

# Create a two-dimensional array
sales = np.array([
    [120, 135, 128],
    [98,  110, 125],
])

# Inspect the array
print(sales.shape)  # (2, 3)
print(sales.ndim)   # 2
print(sales.dtype)  # integer dtype

# Vectorized computation
sales_with_bonus = sales * 1.10

# Aggregate by column
monthly_totals = sales.sum(axis=0)
print(monthly_totals)
```

## Working with the Notebooks

For the best learning experience:

1. Read the corresponding Markdown notes before opening the notebook.
2. Run each cell in sequence instead of jumping directly to the final output.
3. Change array shapes, values, and dtypes to test your understanding.
4. Use the challenge notebooks without referring to earlier solutions first.
5. Compare vectorized NumPy expressions with explicit Python loops when studying performance.
6. Restart the kernel and run all cells periodically to detect hidden state dependencies.

## Key Concepts Covered

### Vectorization

The notebooks emphasize expressing operations over complete arrays rather than writing Python-level loops. This leads to clearer code and often better performance for numerical workloads.

### Broadcasting

Broadcasting enables NumPy to perform operations between compatible shapes, including row-wise and column-wise transformations. The dedicated broadcasting material builds from basic examples to deeper shape reasoning.

### Axis-Aware Computation

Several exercises use `axis` to calculate totals, averages, dispersion, and other statistics across rows or columns. Understanding axis direction is essential for reliable multidimensional analysis.

### Views and Copies

The Copy vs View section highlights an important NumPy behavior: some operations return views that share memory with the original array, while others create independent copies. This distinction affects both correctness and memory usage.

### Applied Numerical Work

The collection moves beyond isolated syntax through examples involving sales data, car-price prediction, stock-rate analysis, Monte Carlo estimation, bootstrap confidence intervals, and image processing.

## Suggested Audience

This directory is useful for:

- Python developers building numerical-computing skills
- Data-science learners preparing for Pandas and machine learning
- Students reviewing array programming and linear algebra
- Practitioners looking for compact NumPy experiments and patterns

## Notes on Scope

These materials are educational implementations and experiments rather than a packaged Python library. Notebook outputs may depend on the execution environment, random seeds, available datasets, and installed optional dependencies.

For production work, validate assumptions around dtype, shape, missing values, numerical precision, memory sharing, and performance using the official NumPy documentation and project-specific tests.

## Related Repository Material

This NumPy section is part of [`python-tech-deck`](../), a broader collection of Python library implementations, experiments, and micro-tools. The repository also contains related learning material for Pandas and FastAPI.

## License

This directory is distributed under the repository’s [MIT License](../LICENSE).
