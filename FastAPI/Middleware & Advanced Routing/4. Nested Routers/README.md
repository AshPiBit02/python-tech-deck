# Nested Routers — Advanced Usage

Briefly, as groundwork: a router isn't limited to being included only into the main `FastAPI` app — a router can call `include_router()` on *another* router, forming a tree rather than a flat list. This document goes past that basic mechanic into how nesting is actually structured and reasoned about in a real, growing application.

## Why Nesting Becomes Necessary, Not Just Possible

A flat structure — every router included directly on `app` — works fine while an application has a handful of route groups. It starts to strain once a natural hierarchy exists in the domain itself: an "admin" area that itself contains several distinct sub-areas (`users`, `reports`, `billing`), or an API that's versioned (`v1`, `v2`) with each version internally split into the same sub-areas again. Nesting exists to let the *code structure* mirror that *domain structure*, rather than forcing every leaf-level router to individually know about and repeat shared context (a common prefix, a shared tag, a shared dependency) that logically belongs to the group as a whole.

## The Tree, Not Just the Path

It's easy to think of nested routers purely in terms of the resulting URL (as covered in the prefix composition section of the previous topic), but the more important mental model is that `include_router` builds an actual **tree of ownership** among router objects, independent of URLs entirely. A router included into another router becomes a child of it in the codebase's structure — meaning shared configuration attached at a parent level (a prefix, a tag, a dependency) genuinely belongs to and describes the whole subtree beneath it, not merely a coincidence of matching path segments.

This distinction matters once dependencies enter the picture (covered next): a dependency attached at a parent router applies to every route in every child router beneath it, however many levels deep — the tree structure is what makes that inheritance meaningful, not just the URL prefix stacking.

## Depth and When to Stop Nesting

Nesting can technically go arbitrarily deep — a router inside a router inside a router — but in practice, real applications rarely benefit from going more than two or three levels deep (e.g. `app` → `admin_router` → `admin_users_router`). Beyond that, the organizational benefit tends to invert: instead of making the codebase easier to navigate, excessive nesting makes it harder to trace which file a given route actually lives in, since a request handler for `/api/v2/admin/reports/quarterly` might require opening four or five files to find where it's actually defined. A reasonable practical guideline: nest only as deep as there's a genuine, stable domain grouping that justifies its own file — nesting for the sake of matching a URL's segment count is not, by itself, a good reason.

## Shared Context Flowing Down the Tree

The practical value of nesting is that configuration set at a parent level in the tree — not just the prefix, but tags and dependencies too — is inherited by every router and route beneath it, without each leaf-level file needing to redeclare it. This means a parent router representing "everything under `/admin`" can, in one place, guarantee that *no* route anywhere beneath it in the tree can accidentally ship without whatever the parent enforces (a shared prefix, a shared "Admin" tag, or — most significantly — a shared authentication/authorization dependency, covered in the router-level dependencies topic). The child routers focus purely on their own specific routes, trusting that the tree they're nested inside already handles what's common to the whole group.

## Reasoning About a Request's Path Through a Nested Tree

Once routers are nested, it's worth being able to mentally trace a single incoming request through the structure: a request arrives at the application, gets matched against the combined set of all routes (flattened at runtime, regardless of how deeply they were nested in the source code), and only then does FastAPI resolve which specific route function — and which specific chain of dependencies accumulated from every level of the tree it passed through — actually handles it. The nesting is a *source-code-time* organizational structure; by the time a request is actually being routed, FastAPI has already flattened the tree into one combined routing table. This is worth internalizing precisely because it explains why nesting has zero runtime performance cost and zero effect on how clients perceive the API — the tree exists for the people reading and maintaining the code, not for the request-handling machinery itself.

## Key Points to Retain

- Nested routers form a genuine ownership tree in the codebase, not merely a coincidence of matching URL path segments — shared prefix, tags, and dependencies at a parent level describe the entire subtree beneath it.
- Nesting should mirror a real, stable domain grouping; nesting purely to match a URL's segment structure, without an underlying organizational reason, tends to make a codebase harder to navigate rather than easier.
- Configuration inherited from a parent router in the tree — especially dependencies — is what makes nesting valuable beyond simple path composition, since it can structurally guarantee that nothing beneath a given point in the tree ships without whatever the parent enforces.
- By request-handling time, the entire nested tree has already been flattened into one routing table — nesting is purely a source-code organizational tool with no runtime cost or effect on API behavior as seen by a client.