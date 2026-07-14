"""M3: Driver attribution via SHAP. Implements FR-3.4, FR-3.5."""

import shap


def compute_shap_values(model, X, feature_names=None):
    """
    Compute SHAP values for a trained tree-based model (XGBoost/RF/GW-XGBoost).
    Returns per-sample, per-feature attribution used to build driver ranking
    and spatial attribution maps.
    """
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    return shap_values


def driver_ranking(shap_values, feature_names):
    """Aggregate mean |SHAP| per feature into a global driver importance ranking."""
    import numpy as np
    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    ranking = sorted(zip(feature_names, mean_abs_shap), key=lambda x: -x[1])
    return ranking
