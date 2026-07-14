"""M4: Model evaluation metrics. Implements FR-4.4."""

import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score


def regression_metrics(y_true, y_pred):
    return {
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
    }


def energy_balance_residual(rn, h, le, g):
    """
    Physical-consistency diagnostic: residual of the surface energy balance
    Rn = H + LE + G. Smaller residuals indicate a more physically plausible
    model (SRS Section 8.1).
    """
    return rn - (h + le + g)
