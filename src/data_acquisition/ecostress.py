"""M1: ECOSTRESS LST connector. Implements FR-1.2 (LST fusion with Landsat)."""

def fetch_ecostress_lst(cfg):
    """
    Pull ECOSTRESS LST scenes for the configured AOI/date range via
    NASA AppEEARS API or the GEE community ECOSTRESS catalog, and
    reconcile spatial/temporal resolution with Landsat 8 (FR-1.2).
    TODO: implement AppEEARS request + polling, or GEE ECOSTRESS asset ingestion.
    """
    raise NotImplementedError
