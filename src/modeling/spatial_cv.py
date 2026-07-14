"""M4: Spatial train/validation/test splitting to avoid leakage. Implements FR-4.3."""


def spatial_train_test_split(gdf, test_fraction=0.2, block_size_m=1000, random_seed=42):
    """
    TODO: implement spatial blocking (e.g., checkerboard or spatial k-fold)
    so nearby, autocorrelated points don't leak between train and test sets.
    """
    raise NotImplementedError
