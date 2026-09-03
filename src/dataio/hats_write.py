"""write_catalog wrapper that recovers from a stale, schema-inconsistent partial write."""

from __future__ import annotations

import shutil
from pathlib import Path


def write_catalog_resumable(cat, path, **kwargs):
    """`cat.write_catalog(path, **kwargs)`, auto-recovering from a stale partial write.

    `resume=True` only checks whether a pixel's output file already exists at `path`, not
    whether it has the same columns the *current* mapped function would produce. If an
    earlier, interrupted `write_catalog(path, resume=True, ...)` call used an older version
    of that function, resuming re-executes only the still-missing pixels with today's
    (different) schema — HATS then fails while assembling `path`'s combined metadata,
    loudly: `RuntimeError: ... AppendRowGroups requires equal schemas. This schema has N
    columns, other has M`. That failure leaves `path` in a half-written, inconsistent state.

    Recovers by deleting `path` and writing to it fresh, once, so a schema mismatch costs a
    full redo of this pass instead of blocking with a cryptic pyarrow error.
    """
    try:
        cat.write_catalog(path, **kwargs)
    except RuntimeError as exc:
        if "AppendRowGroups requires equal schemas" not in str(exc):
            raise
        print(
            f"{path} has a schema mismatch across partitions (a stale partial write from "
            "before the mapped function changed) — deleting it and rewriting from scratch."
        )
        shutil.rmtree(Path(path), ignore_errors=True)
        cat.write_catalog(path, **kwargs)
