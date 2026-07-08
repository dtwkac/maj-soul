import cv2
import os
from consts import DEBUG, TARGET_DIR, DISTRACTOR_DIR, PRECONDITION_TEMPLATE

_ORB = cv2.ORB_create(nfeatures=200)
_BF = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

def _load_templates(folder, is_target):
    items = []
    for f in os.listdir(folder):
        if not f.upper().endswith('.PNG'):
            continue
        img = cv2.imread(os.path.join(folder, f), cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        _, des = _ORB.detectAndCompute(img, None)
        items.append((f, des, is_target))
    return items

templates = _load_templates(TARGET_DIR, True)
if os.path.isdir(DISTRACTOR_DIR):
    templates += _load_templates(DISTRACTOR_DIR, False)
if not templates:
    print("错误: 没有模板图片!"); exit(1)

if DEBUG:
    print(f"目标牌: {', '.join(sorted({os.path.splitext(f)[0] for f in os.listdir(TARGET_DIR) if f.upper().endswith('.PNG')}))}")

_precond = cv2.imread(PRECONDITION_TEMPLATE, cv2.IMREAD_GRAYSCALE) if os.path.isfile(PRECONDITION_TEMPLATE) else None

def check_precondition(bgra_region):
    if _precond is None:
        return 0.0
    gray = cv2.cvtColor(bgra_region, cv2.COLOR_BGRA2GRAY)
    result = cv2.matchTemplate(gray, _precond, cv2.TM_CCOEFF_NORMED)
    return float(cv2.minMaxLoc(result)[1])

def best_match(bgr):
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGRA2GRAY)
    _, des2 = _ORB.detectAndCompute(gray, None)
    if des2 is None:
        print("未检测到牌面特征点")
        return None, 0, False

    best_name, best_cnt, best_is_target = None, 0, False
    scores = []

    for name, des1, is_target in templates:
        if des1 is None:
            scores.append((name, 0))
            continue
        matches = _BF.match(des1, des2)
        good = sum(1 for m in matches if m.distance < 50)
        scores.append((name, good))
        if good > best_cnt:
            best_cnt = good
            best_name = name
            best_is_target = is_target
        if good > 50:
            break

    if DEBUG:
        scores.sort(key=lambda x: -x[1])
        dbg = '  '.join(f"{s[0].replace('.png', '')}={s[1]}" for s in scores[:6])
        label = best_name.replace('.png', '') if best_name else '无'
        print(f"[特征] {dbg} → 最佳:{label}({best_cnt})")

    return best_name, best_cnt, best_is_target
