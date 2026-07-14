"""Unit tests for src/modeling/evaluation.py"""

from src.modeling.evaluation import regression_metrics, energy_balance_residual


def test_regression_metrics():
    y_true = [30.0, 32.0, 35.0]
    y_pred = [30.5, 31.0, 36.0]
    metrics = regression_metrics(y_true, y_pred)
    assert "rmse" in metrics and "mae" in metrics and "r2" in metrics
    assert metrics["rmse"] >= 0


def test_energy_balance_residual_zero_when_balanced():
    residual = energy_balance_residual(rn=500, h=200, le=250, g=50)
    assert residual == 0
