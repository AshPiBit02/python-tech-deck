# FastAPI Learning Lab

A structured collection of FastAPI examples, reference notes, experiments, and small application projects covering the core concepts required to design, implement, test, and reason about production-oriented Python APIs.

This directory is part of [`python-tech-deck`](https://github.com/AshPiBit02/python-tech-deck), a digital deck of Python library implementations, experiments, and micro-tools.

> **Status:** Educational and exploratory. Examples vary in scope and maturity; review configuration, validation, error handling, and security before using any sample in production.

## What you will find here

- HTTP fundamentals and REST-style endpoint design
- Pydantic models, validation, serialization, and type behavior
- Dependency injection patterns, caching, overrides, and resource cleanup
- Authentication and security workflows, including OAuth2, JWTs, password hashing, HTTPS, and CORS
- Database integration with layered application structures and migrations
- Asynchronous programming, concurrency, background tasks, and executor usage
- File uploads, downloads, streaming, image validation, and resume collection
- Middleware, routers, lifecycle events, request handling, and custom exception handlers
- Testing examples and small API-oriented projects
- Python refresher material supporting FastAPI development

## Directory map

### [`HTTP & API Foundations`](./HTTP%20%26%20API%20Foundations)

Introduces the building blocks of HTTP APIs:

- HTTP concepts and request/response behavior
- `GET`, `POST`, `PUT`, `PATCH`, and `DELETE` implementations
- Path parameters, response models, field validation, and `HTTPException`
- A calculator API
- A small library lending API project

### [`Pydantic`](./Pydantic)

Focused examples for modeling and validating API data with Pydantic, including:

- Field constraints and special validated types
- Field-level and model-level validators
- Nested and reference models
- Model configuration
- Model serialization with `model_dump`
- Union types and type-coercion behavior
- A small hotel booking API project

### [`Dependency Injection`](./Dependency%20Injection)

Demonstrates FastAPI's dependency system through progressively more advanced examples:

- Function-based, class-based, nested, global, and router-scoped dependencies
- Dependency caching and dependency overrides
- `yield` dependencies for database connections, file handles, and cleanup logic
- Request logging, header-based dependencies, sorting, rate-limiting-style counters, and unit conversion
- Wallet simulation and freelancer bidding board examples

### [`Authentication & Security`](./Authentication%20%26%20Security)

Explores common API security patterns:

- OAuth2 password flow and scopes
- JWT creation, decoding, and refresh-token patterns
- Secure password hashing
- HTTPS and CORS configuration concepts
- Small authentication projects, including a user-authentication system with routers, services, models, Alembic migrations, and tests

### [`DataBase Integration`](./DataBase%20Integration)

Provides database-oriented examples and application structures:

- Database setup and connection dependencies
- CRUD organization and service layers
- Models, schemas, routers, and configuration modules
- Alembic migration workflows
- Starter project for user persistence
- Enterprise-style department and employee API
- Mobile banking API with customer, account, card, transaction, and audit modules
- Notes on object-relational mapping depth

> The directory name is retained as `DataBase Integration` to match the repository structure.

### [`Async & Performance`](./Async%20%26%20Performance)

Covers asynchronous execution and performance considerations:

- `async def` versus `def` route behavior
- Async database and HTTP calls with HTTPX
- `asyncio.gather` and concurrent multi-source work
- Background tasks
- I/O-bound versus CPU-bound workloads
- Thread and process executors
- Shared clients, benchmarking, and concurrency demonstrations
- Mini-projects such as weather aggregation, health checking, dashboard aggregation, image batch processing, and background report generation

### [`File Handling`](./File%20Handling)

Contains practical file-processing examples:

- Single and multiple uploads
- Saving files to disk
- Streaming and downloading files
- CSV import
- Image validation
- Profile-picture upload handling
- A resume collector example with stored metadata and uploaded documents

### [`Middleware & Advanced Routing`](./Middleware%20%26%20Advanced%20Routing)

Explores application composition and request processing:

- Custom middleware, request logging, request IDs, security headers, maintenance gates, and rate-limiting-style behavior
- `APIRouter`, prefixes, tags, route classes, response configuration, and API versioning
- Nested routers and mounted applications
- Request/response lifecycle behavior
- Request object usage, request state, content negotiation, webhooks, and reverse-proxy URLs
- Custom exception handlers and domain-specific exception vocabularies
- Lifespan events and shared application resources
- Mini-projects including a modular blog API and an e-commerce API with domain exceptions

### [`Testing`](./Testing)

Testing notes and examples for validating FastAPI behavior and API contracts. The authentication mini-project also includes pytest configuration, fixtures, and endpoint-focused tests.

### [`starter`](./starter)

A minimal FastAPI application intended as a starting point for experimentation.

### [`refresher`](./refresher)

Supporting Python examples for concepts used throughout the collection:

- Type hints
- `dataclasses` and `TypedDict`
- Decorators
- Asynchronous waiting
- Concurrent grade processing

## Suggested learning path

For a guided progression, work through the material in this order:

1. **Starter** — run the smallest application and understand the basic project shape.
2. **HTTP & API Foundations** — learn routes, methods, parameters, responses, and errors.
3. **Pydantic** — add reliable input and output validation.
4. **Dependency Injection** — make shared services, configuration, and resources composable.
5. **Database Integration** — connect API layers to persistent storage and migrations.
6. **Authentication & Security** — protect routes and manage identity-related concerns.
7. **Middleware & Advanced Routing** — structure larger applications and control request flow.
8. **Async & Performance** — choose appropriate concurrency strategies for I/O and CPU work.
9. **File Handling** — build APIs that accept, validate, stream, and persist files.
10. **Testing** — verify behavior before extending the examples into larger projects.

## Prerequisites

- Python 3.10 or newer is recommended.
- Familiarity with Python functions, classes, type hints, virtual environments, and package installation is helpful.
- Some examples require additional services or packages, such as a database server, Alembic, HTTPX, image-processing libraries, or authentication libraries. Check the imports and local notes for each example before running it.

## Quick start

From the repository root:

```bash
cd FastAPI
python -m venv .venv
```

Activate the virtual environment:

```bash
# macOS/Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install FastAPI and an ASGI server for the starter example:

```bash
python -m pip install --upgrade pip
python -m pip install fastapi uvicorn
```

Run the starter application:

```bash
uvicorn starter.main:app --reload
```

Open the generated API documentation at:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`

The exact command for other examples depends on their location and module structure. For a script-based example, run it from its own directory or invoke it with Python as appropriate.

## Working with the examples

Because this collection contains independent demonstrations rather than one installable package:

1. Read the local `README.md`, `.md`, or comments before running an example.
2. Create a separate virtual environment when an example has conflicting dependencies.
3. Run commands from the example's directory when relative paths or local data files are used.
4. Inspect configuration modules and environment-variable requirements before starting database-backed or authentication examples.
5. Avoid committing secrets, tokens, local databases, uploaded files, or generated artifacts.
6. Treat committed `__pycache__` files and temporary files as repository artifacts rather than required source material.

## Testing

Where tests are provided, install the relevant test dependencies and run them from the project directory. For pytest-based examples, the typical command is:

```bash
python -m pytest
```

Some examples are demonstrations rather than fully packaged applications, so test commands and required setup may differ between subdirectories.

## Design themes

The examples repeatedly reinforce several practical API design principles:

- Keep request validation close to the API boundary.
- Separate routing, schemas, models, services, and persistence concerns as projects grow.
- Use dependency injection for reusable resources and test substitution.
- Prefer explicit domain exceptions and stable response contracts over catch-all error handling.
- Use async code for non-blocking I/O, not as a blanket replacement for synchronous code.
- Manage shared clients and resources through application lifespan events.
- Protect credentials and sensitive data with appropriate hashing, token handling, transport security, and configuration management.
- Test behavior at the route and service boundaries.

## Related resources

- [FastAPI documentation](https://fastapi.tiangolo.com/)
- [Pydantic documentation](https://docs.pydantic.dev/)
- [Starlette documentation](https://www.starlette.io/)
- [Uvicorn documentation](https://www.uvicorn.org/)
- [Alembic documentation](https://alembic.sqlalchemy.org/)

## Contributing

Improvements are welcome. When adding or updating an example:

- Keep the example focused on one concept or workflow.
- Include a short local README or explanatory comments for non-obvious setup.
- Prefer descriptive filenames and consistent formatting.
- Add or update tests when behavior changes.
- Do not include real credentials, personal data, or sensitive uploaded files.

## License

This directory is distributed as part of [`python-tech-deck`](https://github.com/AshPiBit02/python-tech-deck). See the repository [LICENSE](https://github.com/AshPiBit02/python-tech-deck/blob/main/LICENSE) for licensing information.
