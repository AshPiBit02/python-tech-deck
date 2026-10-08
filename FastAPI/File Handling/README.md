# File Handling in FastAPI

Up to this point, every request body in the auth system and the mini projects has been JSON — small, structured, text-based data parsed into Pydantic models. File handling introduces a fundamentally different kind of input and output: **binary data of arbitrary size** (images, PDFs, CSVs, videos) that cannot be parsed into a Pydantic model, may be too large to hold comfortably in memory, and carries its own metadata (filename, declared content type) that cannot be trusted at face value. This phase covers how FastAPI receives files from clients, how to store and validate them safely, and how to send files back out efficiently.

## Why Files Need Different Handling Than JSON

A JSON body is small, fully text-based, and can be read completely into memory and parsed in one step. Files differ in several ways that directly shape how they must be handled:

- **Size** — a JSON payload is typically kilobytes; a file can be megabytes or gigabytes. Reading an entire large file into memory at once can exhaust server memory, especially with many concurrent uploads.
- **Encoding** — files are raw bytes, not text, so they travel in a different request format (`multipart/form-data`) rather than `application/json`.
- **Untrusted metadata** — the filename and content type a client *claims* for an uploaded file are just strings the client chose; nothing guarantees a file named `photo.jpg` is actually an image, or that a file labeled `application/pdf` is really a PDF.
- **Persistence** — unlike a JSON body that is processed and discarded, uploaded files usually need to be stored somewhere (disk, object storage) and later retrieved, raising questions of naming, collisions, and access control.

## Required Dependency

FastAPI cannot parse `multipart/form-data` on its own. The `python-multipart` package must be installed, otherwise any route declaring a file parameter fails at startup:

```bash
pip install python-multipart
```

## Receiving a File — `UploadFile` vs `bytes`

FastAPI offers two ways to declare a file parameter, with a meaningful difference between them:

```python
from fastapi import FastAPI, File, UploadFile

app = FastAPI()

# Option 1: bytes — the ENTIRE file is read into memory immediately
@app.post("/upload-bytes")
async def upload_bytes(file: bytes = File(...)):
    return {"size": len(file)}

# Option 2: UploadFile — a file-like object, read on demand
@app.post("/upload")
async def upload(file: UploadFile):
    contents = await file.read()
    return {"filename": file.filename, "content_type": file.content_type, "size": len(contents)}
```

`bytes = File(...)` loads the whole file into memory before the route body even runs — acceptable only for small files. `UploadFile` is the preferred approach: it wraps a **spooled temporary file** — held in memory up to a size threshold, then automatically spilled to disk — and exposes methods to read it in controlled pieces. It also carries useful metadata: `file.filename`, `file.content_type`, and `file.size` (where available).

## `UploadFile` Methods Worth Knowing

```python
@app.post("/upload")
async def upload(file: UploadFile):
    first_chunk = await file.read(1024)   # read only the first 1 KB
    await file.seek(0)                      # rewind back to the beginning
    everything = await file.read()          # read the whole thing
    await file.close()                      # release resources when done
```

- `await file.read(size)` — reads up to `size` bytes (or everything, if omitted).
- `await file.seek(offset)` — moves the read position, so the same file can be re-read (important after inspecting its first bytes for validation, as covered below).
- `await file.close()` — releases the underlying temporary file; FastAPI also closes it automatically after the request in normal cases.

## Multiple Files and Form Fields Together

```python
from typing import Annotated
from fastapi import Form

@app.post("/upload-many")
async def upload_many(
    files: list[UploadFile],
    description: Annotated[str, Form()],
):
    return {"count": len(files), "description": description, "names": [f.filename for f in files]}
```

A route can accept a **list** of `UploadFile` for multiple files in one request, and can combine files with ordinary form fields (`Form()`). An important constraint: once a request uses `multipart/form-data` (which any file upload does), the body can no longer also be parsed as JSON — file fields and JSON body models cannot be mixed in the same route. Additional structured data must travel as individual `Form()` fields or as query parameters instead.

## Saving Files to Disk Safely

Writing an uploaded file to disk looks trivial, but the obvious version contains real vulnerabilities:

```python
# UNSAFE — never do this
@app.post("/upload")
async def upload(file: UploadFile):
    with open(f"uploads/{file.filename}", "wb") as f:   # trusts the client's filename
        f.write(await file.read())
```

Problems with this approach:

- **Path traversal** — a malicious client can send a filename like `../../etc/passwd` or `..\\..\\app\\main.py`, causing the write to escape the intended `uploads/` directory and overwrite arbitrary files on the server.
- **Collisions** — two users uploading `photo.jpg` overwrite each other's files.
- **Blocking I/O inside `async def`** — synchronous `open()`/`write()` on a large file blocks the event loop, exactly the anti-pattern covered in the Async & Performance phase.

A safer pattern generates the stored name server-side and never uses the client's filename for the filesystem path:

```python
import uuid
from pathlib import Path

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.post("/upload")
async def upload(file: UploadFile):
    suffix = Path(file.filename).suffix          # keep only the extension, if needed
    stored_name = f"{uuid.uuid4()}{suffix}"       # server-generated, collision-proof
    destination = UPLOAD_DIR / stored_name

    contents = await file.read()
    destination.write_bytes(contents)

    return {"stored_as": stored_name, "original_name": file.filename}
```

The original filename can still be stored as *metadata* (in a database column, for display purposes) — it just must never be used to construct the actual filesystem path.

## Validating Uploads — Never Trust the Client's Claims

Two separate things need validation, and neither can be taken from the client's word:

### 1. File size limits

FastAPI does not enforce an upload size limit by default. Without one, a client can upload an arbitrarily large file and consume disk space or memory. A size limit must be enforced explicitly:

```python
MAX_SIZE = 5 * 1024 * 1024   # 5 MB

@app.post("/upload")
async def upload(file: UploadFile):
    contents = await file.read(MAX_SIZE + 1)   # read one byte past the limit
    if len(contents) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 5 MB)")
    ...
```

Reading `MAX_SIZE + 1` bytes is a deliberate technique: it detects an oversized file without ever loading the entire (potentially huge) file into memory. A production deployment typically *also* enforces a maximum request body size at the reverse-proxy level (e.g. Nginx's `client_max_body_size`), since by the time application code runs, the upload has already been received.

### 2. File type

`file.content_type` is simply whatever header the client sent. A malicious or careless client can label an executable as `image/png`. Real validation inspects the file's actual **magic bytes** — the first few bytes that identify the true format:

```python
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SIGNATURE = b"\xff\xd8\xff"

@app.post("/upload-image")
async def upload_image(file: UploadFile):
    header = await file.read(8)
    await file.seek(0)   # rewind so the full file can still be read afterwards

    if not (header.startswith(PNG_SIGNATURE) or header.startswith(JPEG_SIGNATURE)):
        raise HTTPException(status_code=415, detail="Only PNG and JPEG images are allowed")
    ...
```

Note the `await file.seek(0)` — reading the header advances the file position, so without rewinding, a later `file.read()` would return the file *minus* its first bytes. Checking the declared `content_type` as a first, cheap filter is reasonable, but the magic-byte check is what actually enforces the rule. (Libraries such as `python-magic` or `filetype` can do this detection more thoroughly than hand-written signature checks.)

## Sending Files Back — `FileResponse`

```python
from fastapi.responses import FileResponse

@app.get("/files/{filename}")
async def download(filename: str):
    path = UPLOAD_DIR / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, filename=filename)
```

`FileResponse` streams a file from disk to the client efficiently, sets appropriate headers (`Content-Length`, `Content-Type` guessed from the extension), and `filename=` adds a `Content-Disposition` header so browsers download it under that name. The same path-traversal concern applies in reverse here: a `filename` path parameter like `../../secret.txt` must be prevented from escaping the intended directory — resolving the final path and confirming it still sits inside `UPLOAD_DIR` is the standard safeguard.

## Streaming — `StreamingResponse` for Large or Generated Content

When content is very large, or is generated on the fly rather than sitting in a file, loading it all into memory before responding is wasteful. `StreamingResponse` sends data in chunks as it is produced:

```python
from fastapi.responses import StreamingResponse

def generate_rows():
    for i in range(1_000_000):
        yield f"row {i}\n"

@app.get("/export")
def export():
    return StreamingResponse(generate_rows(), media_type="text/plain")
```

Memory usage stays flat regardless of total size, since only one chunk exists in memory at a time. This is the right tool for large CSV exports, log downloads, and similar bulk output.

## Connecting to the Earlier Phases

- **Async & Performance** — saving a large upload with plain synchronous `write_bytes` inside an `async def` route blocks the event loop; parsing a large CSV with pandas is CPU-bound work that belongs in a thread pool via `run_in_executor`. File handling is where the I/O-bound vs CPU-bound distinction becomes concrete.
- **Middleware** — a request-size-limiting middleware can reject oversized uploads early, before the route reads anything, mirroring the early-rejection principle from the lifecycle discussion.
- **Exception handlers** — domain exceptions such as `FileTooLargeError` or `UnsupportedFileTypeError` fit the custom-exception-handler pattern cleanly, keeping validation logic HTTP-agnostic.

## Key Points to Retain

- File uploads require `python-multipart` and use `multipart/form-data`, which cannot be combined with a JSON body in the same route.
- Prefer `UploadFile` over `bytes = File(...)` — it avoids loading the entire file into memory up front and exposes `read`, `seek`, and metadata.
- Never use a client-supplied filename to build a filesystem path; generate the stored name server-side to prevent path traversal and collisions.
- FastAPI enforces no upload size limit by default — enforce one explicitly, ideally also at the reverse-proxy level.
- A declared `content_type` is a client claim, not a fact; real type validation inspects the file's magic bytes, remembering to `seek(0)` afterwards.
- `FileResponse` serves files from disk; `StreamingResponse` serves large or generated content in chunks without holding it all in memory.