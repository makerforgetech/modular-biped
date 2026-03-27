import math

def degrees_to_radians(deg):
    return math.radians(deg)

def radians_to_degrees(rad):
    return math.degrees(rad)

def degrees_to_raw(deg, min_deg, max_deg, min_raw, max_raw):
    # Linear mapping from degrees to raw units
    return int((deg - min_deg) * (max_raw - min_raw) / (max_deg - min_deg) + min_raw)

def raw_to_degrees(raw, min_deg, max_deg, min_raw, max_raw):
    # Linear mapping from raw units to degrees
    return (raw - min_raw) * (max_deg - min_deg) / (max_raw - min_raw) + min_deg

def radians_to_raw(rad, min_rad, max_rad, min_raw, max_raw):
    # Linear mapping from radians to raw units
    return int((rad - min_rad) * (max_raw - min_raw) / (max_rad - min_rad) + min_raw)

def raw_to_radians(raw, min_rad, max_rad, min_raw, max_raw):
    # Linear mapping from raw units to radians
    return (raw - min_raw) * (max_rad - min_rad) / (max_raw - min_raw) + min_rad
