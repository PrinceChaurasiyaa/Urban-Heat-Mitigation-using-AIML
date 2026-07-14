"""M3: Geographically Weighted Regression cross-check against SHAP driver ranking.
Implements FR-3.4.
"""


def fit_gwr(coords, y, X, bandwidth=None):
    """
    TODO: fit a Geographically Weighted Regression (mgwr library) as a
    statistical cross-check on SHAP-derived driver importance, per the
    Wang et al. GW-XGBoost + SHAP-GAM methodology referenced in the SRS.
    """
    raise NotImplementedError
