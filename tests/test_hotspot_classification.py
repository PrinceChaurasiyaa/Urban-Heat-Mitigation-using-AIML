"""Unit tests for src/hotspot_mapping/classify.py"""

import numpy as np
from src.hotspot_mapping.classify import classify_heat_stress


def test_classify_heat_stress_basic():
    lst = np.array([25, 30, 35, 40, 45, 50])
    thresholds = {"low_max": 0.2, "moderate_max": 0.5, "high_max": 0.8}
    result = classify_heat_stress(lst, thresholds, method="percentile")
    assert result.shape == lst.shape
    assert set(np.unique(result)).issubset({0, 1, 2, 3})
