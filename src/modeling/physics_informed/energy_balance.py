"""M4: Surface energy balance formulation used as a physics constraint.
Implements FR-4.2. Reference: SRS Section 8.1, Rn = H + LE + G.
"""


def net_radiation(shortwave_in, albedo, longwave_in, longwave_out):
    """Rn = (1 - albedo) * SW_in + LW_in - LW_out"""
    return (1 - albedo) * shortwave_in + longwave_in - longwave_out


def sensible_heat_flux(surface_temp, air_temp, aerodynamic_resistance, air_density=1.2, specific_heat=1005):
    """H = rho * cp * (Ts - Ta) / ra"""
    return air_density * specific_heat * (surface_temp - air_temp) / aerodynamic_resistance


def latent_heat_flux(evapotranspiration, latent_heat_vaporization=2.45e6):
    """LE = ET * lambda (evapotranspiration-driven cooling)"""
    return evapotranspiration * latent_heat_vaporization


def ground_heat_flux(net_radiation_value, fraction=0.1):
    """Simple empirical fraction-of-Rn approximation for G; refine per literature as needed."""
    return fraction * net_radiation_value
