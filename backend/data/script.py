import json
from pathlib import Path

TRIGGER_MAP = {
    "ТРИГГЕР K+": [36],
    "ТРИГГЕР ТРОМБОЦИТЫ": [33],
    "ТРИГГЕР ГЕМОГЛОБИН": [26],
    "ТРИГГЕР КРЕАТИНИН": [34],

    "ТРИГГЕР ПОВТ ХИРУРГ ВМЕШ": [25],
    "ТРИГГЕР ГЕМАТОМА ПРИ УЗИ МТ": [56],

    "ТРИГГЕР ЛИХОРАДКА": [1, 2, 3, 4, 5, 6, 7, 8],
    "ТРИГГЕР ТГВ ПРИ УЗАС ВЕН": [29, 30],

    "ТРИГГЕР ТРОПОНИН I": [39]
}

def dump_json(path: str, data: dict) -> None:
    tmp = Path(path).with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(path)

with open("patients_final.json", "r", encoding="utf-8") as f:
    payload = json.load(f)

unknown_triggers = set()

for patient in payload.get("patients", []):
    for card in patient.get("stac_cards", []):
        events = card.get("events") or []
        if not isinstance(events, list) or not events:
            continue

        for e in events:
            if not isinstance(e, dict):
                continue

            trig = e.get("trigger")
            if not trig:
                continue

            ids = TRIGGER_MAP.get(trig)
            if not ids:
                unknown_triggers.add(trig)
                continue

            ids_sorted = sorted(set(int(x) for x in ids))

            # Для UI
            e["id"] = ids_sorted[0]
            # Для логики диагнозов
            e["event_ids"] = ids_sorted

if unknown_triggers:
    print("Неизвестные triggers (нет в TRIGGER_MAP):")
    for t in sorted(unknown_triggers):
        print(" -", t)

dump_json("patients_final.json", payload)
print("Готово: обновил patients_final.json")
