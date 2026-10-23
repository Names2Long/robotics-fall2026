GAIN = 0.08
SPEED = 0.16
ROI_TOP = 0.60
ROI_BOTTOM = 0.95
HUE_LOW = 140
HUE_HIGH = 169
MIN_FRACTION = 0.002

def angular_velocity(error, gain):
    return -gain * error