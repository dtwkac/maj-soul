import numpy as np
import mss

_SCT = mss.MSS()
_COMBINED = {"left": 365, "top": 805, "width": 175, "height": 223}

def grab_combined():
    return np.asarray(_SCT.grab(_COMBINED))
