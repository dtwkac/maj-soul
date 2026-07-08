import numpy as np
import mss
from consts import TILE_REGION, NUM_REGION

_SCT = mss.MSS()
left = NUM_REGION[0]
top = NUM_REGION[1]
width = TILE_REGION[0] + TILE_REGION[2] - left
height = TILE_REGION[1] + TILE_REGION[3] - top
_COMBINED = {"left": left, "top": top, "width": width, "height": height}

def grab_combined():
    return np.asarray(_SCT.grab(_COMBINED))
