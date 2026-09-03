"""Pick a small, hands-on slice out of a large lazy HATS catalog.

Used at the top of nb_02-05 to give workshop participants something they can
`.compute()` and look at directly, without touching the whole HQ sample.
"""

VALID_MODES = ("partition", "cone_search")


def select_slice(cat, mode="partition", *, partition_index=0, ra=None, dec=None, radius_arcsec=None):
    """Return a small sub-catalog of `cat`, either one partition or a cone search.

    `mode="partition"` uses `partition_index` (fast, zero query cost, but an arbitrary
    HEALPix-tile boundary). `mode="cone_search"` uses `ra`/`dec`/`radius_arcsec` (an
    intuitive "pick a spot on the sky" pick, at the cost of a live query).
    """
    if mode == "partition":
        return cat.partitions[partition_index]
    if mode == "cone_search":
        if ra is None or dec is None or radius_arcsec is None:
            raise ValueError("mode='cone_search' needs ra, dec, and radius_arcsec")
        return cat.cone_search(ra=ra, dec=dec, radius_arcsec=radius_arcsec)
    raise ValueError(f"mode must be one of {VALID_MODES}, got {mode!r}")
