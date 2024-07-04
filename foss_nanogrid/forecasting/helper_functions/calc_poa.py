import numpy as np

# Calculate the POA from the GHI
def calculate_poa_irradiance(solar_zenith, ghi, inclination, solar_azimuth, site_azimuth):
    elevation = 90 - solar_zenith

    sincident = ghi / np.sin(np.radians(elevation))

    if sincident < 0:
        sincident = 0

    poa = sincident * (np.cos(np.radians(elevation)) * np.sin(np.radians(inclination)) * np.cos(np.radians(site_azimuth - solar_azimuth)) + np.sin(np.radians(elevation)) * np.cos(np.radians(inclination)))

    if poa < 0:
        poa = 0
    
    return poa