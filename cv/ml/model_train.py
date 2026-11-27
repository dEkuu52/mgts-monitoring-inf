import random, shutil, zipfile
from pathlib import Path

ZIP_PATH = Path(r"C:\Users\friks\Desktop\Датасет-ДСС (3).zip")
OUT = Path(r"C:\Users\friks\Desktop\dss3_yolo_cls")
VAL_RATIO = 0.2
SEED = 42
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

CLASS_MAP = {
    "МП.РЩ": "mp_rsh",
    "Удовлетворительное состояние ТКШ": "ok_tksh",
}

random.seed(SEED)
if OUT.exists():
    shutil.rmtree(OUT)

by_class = {}
with zipfile.ZipFile(ZIP_PATH) as z:
    for name in z.namelist():
        if name.endswith("/"):
            continue
        p = Path(name)
        if p.suffix.lower() not in IMG_EXTS:
            continue
        parts = p.parts
        if len(parts) < 3:
            continue
        cls = CLASS_MAP.get(parts[1].strip())
        if not cls:
            continue
        by_class.setdefault(cls, []).append((p.name, z.read(name)))

for cls, items in by_class.items():
    random.shuffle(items)
    n_val = max(1, int(len(items) * VAL_RATIO)) if len(items) > 1 else 0
    if len(items) - n_val < 1:
        n_val = len(items) - 1
    for i, (fname, data) in enumerate(items):
        split = "val" if i < n_val else "train"
        dst = OUT / split / cls / fname
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)
    print(f"{cls}: total={len(items)}, train={len(items)-n_val}, val={n_val}")

print("Ready:", OUT)