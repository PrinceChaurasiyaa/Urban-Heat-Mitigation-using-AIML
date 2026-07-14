"""M1: Spectral index computation (NDVI, NDBI, NDWI) — feeds M3 driver analysis."""


def compute_ndvi(sr_image, nir_band="SR_B5", red_band="SR_B4"):
    return sr_image.normalizedDifference([nir_band, red_band]).rename("NDVI")


def compute_ndbi(sr_image, swir_band="SR_B6", nir_band="SR_B5"):
    return sr_image.normalizedDifference([swir_band, nir_band]).rename("NDBI")


def compute_ndwi(sr_image, green_band="SR_B3", nir_band="SR_B5"):
    return sr_image.normalizedDifference([green_band, nir_band]).rename("NDWI")
