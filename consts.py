import os
import sys
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'D:\workspace\maj-soul\Tesseract-OCR\tesseract.exe'

DEBUG = '--debug' in sys.argv

NUM_ALARM = 105

TILE_REGION = (450, 885, 90, 140)
NUM_REGION = (365, 805, 125, 30)
CENTER = (960, 540)
TSUMO_BTN = (1200, 820)
SKIP_BTN = (500, 950)

CLICK_TIMES = 72
LOOP_SLEEP = 1.2
SLEEP_INTERVAL = 0.2
RETRY_LIMIT = 5

TARGET_DIR = r'D:\workspace\maj-soul\pics\targets'
DISTRACTOR_DIR = r'D:\workspace\maj-soul\pics\distractors'

THRESHOLD_DEFAULT = 20

TARGET_NAMES = {os.path.splitext(f)[0] for f in os.listdir(TARGET_DIR) if f.upper().endswith('.PNG')}
