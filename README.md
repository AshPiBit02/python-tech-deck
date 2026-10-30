# Python Tech Deck

`python-tech-deck` is a practical collection of Python learning materials, experiments, notebooks, and small projects. It is organized as a reference deck: each major topic has its own focused notes and README, while this page provides a concise overview of the repository.

## What's Included

- **[NumPy](./numpy/)** — Notes and exercises covering arrays, indexing, broadcasting, reshaping, mathematical operations, linear algebra, random sampling, and performance.
- **[Pandas](./pandas/)** — Jupyter notebooks for data structures, cleaning, file I/O, grouping, joins, reshaping, time-series analysis, optimization, and an e-commerce workflow.
- **[FastAPI](./FastAPI/)** — Examples and small projects covering HTTP APIs, Pydantic, dependency injection, authentication, databases, asynchronous programming, file handling, middleware, routing, and testing.
- **[Dummy Dataset Generators](./Dummy%20Datasets%20Generators/)** — Python utilities for creating sample addresses, products, and sales data.
- **[Data Files](./dataFiles/)** — Example CSV, JSON, and spreadsheet files used by the learning materials and data-processing exercises.

## Repository Layout

```text
python-tech-deck/
├── FastAPI/
├── Dummy Datasets Generators/
├── dataFiles/
├── numpy/
├── pandas/
└── LICENSE
```

## Getting Started

Clone the repository and explore the topic that matches your current goal:

```bash
git clone https://github.com/AshPiBit02/python-tech-deck.git
cd python-tech-deck
```

For notebook-based material, install Jupyter and the libraries required by the topic you want to explore:

```bash
python -m pip install numpy pandas jupyter openpyxl
jupyter notebook
```

FastAPI examples may require additional dependencies depending on the project. See [`FastAPI/README.md`](./FastAPI/README.md) for its detailed guidance.

## Intended Use

This repository is intended for learning, experimentation, and reference. Examples vary in scope and maturity, so review configuration, validation, error handling, and security before adapting any code for production use.

## License

See the [LICENSE](./LICENSE) file for licensing information.
