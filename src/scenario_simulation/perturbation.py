"""M5: Scenario perturbation engine. Implements FR-5.1, FR-5.2, FR-5.3."""


INTERVENTION_DEFAULTS = {
    "tree_canopy_expansion": {"ndvi_delta": 0.3},
    "cool_roof": {"albedo_delta": 0.35},
    "high_albedo_pavement": {"albedo_delta": 0.25},
    "green_roof": {"ndvi_delta": 0.2, "albedo_delta": 0.05},
    "water_body": {"ndwi_delta": 0.4},
}


def apply_intervention(feature_stack, intervention_type, zone_mask, params=None):
    """
    TODO: given a raster feature stack, an intervention type, and a spatial
    zone mask (which cells the intervention applies to), perturb the
    relevant input feature layer(s) (e.g., NDVI for greening, albedo for
    cool roofs) within the zone, leaving everything outside it untouched.
    """
    raise NotImplementedError


def run_scenario(trained_model, perturbed_feature_stack):
    """Re-run the trained model on the perturbed stack and return predicted LST."""
    raise NotImplementedError
