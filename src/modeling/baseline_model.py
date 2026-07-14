"""M4: Baseline data-driven model (Random Forest / XGBoost). Implements FR-4.1."""

import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor


def train_baseline_xgboost(X_train, y_train, params=None):
    default_params = dict(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="reg:squarederror",
    )
    if params:
        default_params.update(params)
    model = xgb.XGBRegressor(**default_params)
    model.fit(X_train, y_train)
    return model


def train_baseline_random_forest(X_train, y_train, params=None):
    default_params = dict(n_estimators=500, max_depth=None, n_jobs=-1)
    if params:
        default_params.update(params)
    model = RandomForestRegressor(**default_params)
    model.fit(X_train, y_train)
    return model
