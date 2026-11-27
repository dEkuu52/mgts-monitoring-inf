"""Логика разбора результатов детекции для CV-воркера.

Здесь нет ни БД, ни YOLO — только чистые функции, поэтому их можно проверить
без модели и базы (см. backend/tests/test_cv_logic.py).

ГЛАВНОЕ, ЧТО НУЖНО НАСТРОИТЬ — CLASS_RULES. Это таблица «класс модели -> что он значит».
Текущие веса (1-version.pt) знают один класс `odn_pole` (столб): модель находит объект,
но не оценивает его состояние. Когда появятся классы дефектов, просто добавьте их сюда.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

RAW_PREFIX = "/uploads/raw/"

# Статусы из таблицы statuses (создаются в seed.py).
STATUS_OK = "ok"
STATUS_CHECK = "check_required"
STATUS_REPAIR = "repair_required"
STATUS_UNRECOGNIZED = "unrecognized"
REQUIRED_STATUSES = (STATUS_OK, STATUS_CHECK, STATUS_REPAIR, STATUS_UNRECOGNIZED)


@dataclass(frozen=True)
class ClassRule:
    """Что означает класс, который вернула модель.

    kind="object" — модель нашла объект инфраструктуры (столб, колодец, шкаф).
                    Это НЕ дефект: объект просто опознан.
    kind="defect" — модель нашла признак неудовлетворительного состояния.
    """

    kind: str
    object_type: str | None = None  # значение для infrastructure_objects.type
    severity: str | None = None  # для дефектов: "medium" | "high"
    action: str | None = None  # для дефектов: "check" | "repair"


CLASS_RULES: dict[str, ClassRule] = {
    # --- Колодцы (кабельные колодцы / люки): у модели есть оценка состояния ---
    "Good":      ClassRule(kind="object", object_type="cable_manhole"),  # исправная крышка
    "Broken":    ClassRule("defect", "cable_manhole", severity="high",   action="repair"),  # сломана крышка
    "Uncovered": ClassRule("defect", "cable_manhole", severity="high",   action="repair"),  # колодец открыт
    "Lose":      ClassRule("defect", "cable_manhole", severity="medium", action="check"),   # неплотно лежит/сдвинута

    # --- Опоры и оборудование: модель только опознаёт объект, состояние не оценивает ---
    "wood pole":          ClassRule(kind="object", object_type="support"),
    "concrete pole":      ClassRule(kind="object", object_type="support"),
    "steel pole":         ClassRule(kind="object", object_type="support"),
    "single crossarm":    ClassRule(kind="object", object_type="support"),
    "double crossarm":    ClassRule(kind="object", object_type="support"),
    "insulator":          ClassRule(kind="object", object_type="support"),
    "lightning arrester": ClassRule(kind="object", object_type="support"),
    "cutout":             ClassRule(kind="object", object_type="support"),
    "transformer":        ClassRule(kind="object", object_type="support"),
    "splice case":        ClassRule(kind="object", object_type="support"),
    "street light":       ClassRule(kind="object", object_type="support"),
}

# Класс, которого нет в CLASS_RULES, трактуем осторожно: как дефект, требующий проверки.
UNKNOWN_CLASS_RULE = ClassRule(kind="defect", severity="medium", action="check")


@dataclass(frozen=True)
class Detection:
    class_name: str
    confidence: float
    bbox: tuple[float, float, float, float]  # x1, y1, x2, y2, нормированные 0..1


@dataclass(frozen=True)
class DefectRecord:
    defect_type: str
    confidence: float
    severity: str
    action: str
    bbox: tuple[float, float, float, float]


@dataclass
class Outcome:
    object_type: str | None = None
    defects: list[DefectRecord] = field(default_factory=list)
    status: str | None = None  # None — статус объекта не меняем
    summary: str = ""


def rule_for(class_name: str) -> ClassRule:
    return CLASS_RULES.get(class_name, UNKNOWN_CLASS_RULE)


def condition_is_assessed(rules: dict[str, ClassRule] | None = None) -> bool:
    """Умеет ли модель вообще оценивать состояние (есть ли у неё классы-дефекты)."""
    rules = CLASS_RULES if rules is None else rules
    return any(rule.kind == "defect" for rule in rules.values())


def assessed_object_types(rules: dict[str, ClassRule] | None = None) -> set[str]:
    """Типы объектов, для которых у модели есть классы-дефекты (состояние можно оценить).

    Для остальных типов (например, опор) модель только опознаёт объект, поэтому
    утверждать «состояние в норме» нельзя.
    """
    rules = CLASS_RULES if rules is None else rules
    return {r.object_type for r in rules.values() if r.kind == "defect" and r.object_type}


def build_outcome(
    detections: list[Detection],
    *,
    high_confidence: float,
    rules: dict[str, ClassRule] | None = None,
) -> Outcome:
    """Превращает детекции в дефекты и целевой статус объекта.

    * Уверенность модели НЕ определяет серьёзность дефекта — её задаёт класс (ClassRule).
      Уверенность лишь решает, можно ли сразу рекомендовать ремонт: при низкой
      уверенности рекомендация понижается до «проверить».
    * Нашли дефекты  -> repair_required, если есть хоть один «ремонт», иначе check_required.
    * Нашли объект, состояние которого модель умеет оценивать (у его типа есть классы-дефекты,
      например колодец с классом Good), и дефектов нет -> ok.
    * Нашли только объекты, состояние которых модель не оценивает (опора, изолятор...) ->
      check_required: нельзя утверждать «всё хорошо», когда состояние не проверялось.
    * Ничего не нашли -> unrecognized («Не распознано»): фото обработано, но модель
      не дала результата, поэтому объект нельзя считать проверенным.
    """
    rules = CLASS_RULES if rules is None else rules
    assessed_types = assessed_object_types(rules)

    defects: list[DefectRecord] = []
    object_found = False
    assessed_object_found = False
    best_type: tuple[float, str] | None = None

    for det in detections:
        rule = rules.get(det.class_name, UNKNOWN_CLASS_RULE)

        if rule.object_type and (best_type is None or det.confidence > best_type[0]):
            best_type = (det.confidence, rule.object_type)

        if rule.kind == "object":
            object_found = True
            if rule.object_type in assessed_types:
                assessed_object_found = True
            continue

        object_found = True
        action = rule.action if det.confidence >= high_confidence else "check"
        defects.append(
            DefectRecord(
                defect_type=det.class_name,
                confidence=det.confidence,
                severity=rule.severity or "medium",
                action=action or "check",
                bbox=det.bbox,
            )
        )

    if defects:
        status = STATUS_REPAIR if any(d.action == "repair" for d in defects) else STATUS_CHECK
    elif object_found:
        status = STATUS_OK if assessed_object_found else STATUS_CHECK
    else:
        status = STATUS_UNRECOGNIZED

    summary = (
        f"детекций={len(detections)}, дефектов={len(defects)}, "
        f"статус={status or 'без изменений'}"
    )
    return Outcome(
        object_type=best_type[1] if best_type else None,
        defects=defects,
        status=status,
        summary=summary,
    )


def resolve_image_path(img_url: str | None, uploads_dir: Path) -> Path:
    """Путь вида `/uploads/raw/<файл>` -> реальный файл внутри uploads_dir.

    Принимаются только загруженные через /upload файлы. Любые другие значения
    (http-ссылки, абсолютные пути, `..`) отклоняются: img_url задаёт пользователь,
    и воркер не должен читать/скачивать произвольное.
    """
    if not isinstance(img_url, str) or not img_url.startswith(RAW_PREFIX):
        raise ValueError(f"Недопустимый img_url (ожидается {RAW_PREFIX}*): {img_url!r}")

    raw_dir = (uploads_dir / "raw").resolve()
    path = (uploads_dir / img_url[len("/uploads/"):]).resolve()
    if not path.is_relative_to(raw_dir):
        raise ValueError(f"img_url выходит за пределы {raw_dir}: {img_url!r}")
    if not path.is_file():
        raise FileNotFoundError(f"Файл не найден: {path}")
    return path


def _dms_to_degrees(value, ref) -> float | None:
    try:
        deg, minutes, seconds = (float(x) for x in value)
    except (TypeError, ValueError):
        return None
    result = deg + minutes / 60 + seconds / 3600
    if str(ref).strip().upper() in {"S", "W"}:
        result = -result
    return result


def gps_from_image(path: Path) -> tuple[float, float] | None:
    """Координаты (lat, lon) из EXIF фото, если они там есть."""
    try:
        from PIL import Image

        with Image.open(path) as img:
            gps = img.getexif().get_ifd(0x8825)  # GPSInfo
    except Exception:
        return None

    if not gps:
        return None

    lat = _dms_to_degrees(gps.get(2), gps.get(1))
    lon = _dms_to_degrees(gps.get(4), gps.get(3))
    if lat is None or lon is None:
        return None
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    if lat == 0 and lon == 0:  # «нулевой остров» — типичный мусор от камер без GPS-фикса
        return None
    return round(lat, 6), round(lon, 6)
