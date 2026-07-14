"""M2: Heat stress classification. Implements FR-2.3."""

import numpy as np


def classify_heat_stress(lst_array, thresholds, method="percentile"):
    """
    Classify an LST raster (as a numpy array) into Low/Moderate/High/Severe
    categories, per SRS Section 6.2 / Appendix A.

    method="percentile": thresholds are percentile cutoffs (0-1) of the AOI's LST distribution.
    method="stddev": thresholds are expressed in standard deviations from the mean.
    """
    if method == "percentile":
        p = np.nanpercentile(lst_array, [
            thresholds["low_max"] * 100,
            thresholds["moderate_max"] * 100,
            thresholds["high_max"] * 100,
        ])
        low_cut, mod_cut, high_cut = p
    else:
        mean, std = np.nanmean(lst_array), np.nanstd(lst_array)
        low_cut = mean - 0.5 * std
        mod_cut = mean + 0.5 * std
        high_cut = mean + 1.5 * std

    classified = np.select(
        [lst_array < low_cut, lst_array < mod_cut, lst_array < high_cut],
        [0, 1, 2],           # Low, Moderate, High
        default=3,            # Severe
    )
    return classified  # 0=Low, 1=Moderate, 2=High, 3=Severe
