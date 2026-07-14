"""M5: Optional high-fidelity SOLWEIG coupling. Implements FR-5.4."""


def run_solweig(met_forcing, dsm, dem, land_cover, output_dir):
    """
    TODO: invoke SOLWEIG (via UMEP Python API or QGIS plugin subprocess call)
    on shortlisted scenarios to estimate mean radiant temperature / pedestrian-
    level thermal comfort (UTCI), for comparison against the LST-based prediction.
    See: Wang et al. finding that albedo increases can raise UTCI even while
    lowering LST — flag this trade-off explicitly in the scenario report.
    """
    raise NotImplementedError
