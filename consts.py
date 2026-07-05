import os
import sys
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'D:\workspace\maj-soul\Tesseract-OCR\tesseract.exe'

DEBUG = '--debug' in sys.argv

NUM_ALARM = 81

TILE_REGION = (450, 885, 90, 140)
NUM_REGION = (365, 805, 125, 30)
CENTER = (960, 540)
TSUMO_BTN = (1200, 820)
SKIP_BTN = (500, 950)

CLICK_TIMES = 72
LOOP_SLEEP = 1.0
SLEEP_INTERVAL = 0.2
RETRY_LIMIT = 5

TARGET_DIR = r'D:\workspace\maj-soul\pics\targets'
DISTRACTOR_DIR = r'D:\workspace\maj-soul\pics\distractors'

THRESHOLD_DEFAULT = 20

PRECONDITION_TEMPLATE = r'D:\workspace\maj-soul\pics\precondition.png'
PRECONDITION_THRESHOLD = 0.8

TARGET_NAMES = {os.path.splitext(f)[0] for f in os.listdir(TARGET_DIR) if f.upper().endswith('.PNG')}

ALARM_TIMEOUT = 600

RELAUNCH_THRESHOLD = 0.9
RELAUNCH_INTERVAL = 15
RELAUNCH_DIR = r'D:\workspace\maj-soul\pics\relaunch'
RELAUNCH_BTN = (165, 80)
RELAUNCH_QYZZ_REGION = (1635, 720, 110, 100)
RELAUNCH_QYZZ_CLICK = (1695, 775)
RELAUNCH_CONTINUE_REGION = (795, 860, 330, 90)
RELAUNCH_CONTINUE_CLICK = (870, 900)
RELAUNCH_PRECOND_REGION = (475, 885, 35, 20)
