import json
import re
import sys
from pathlib import Path

EVENT_RE = re.compile(r"Event\s*(\d+)", re.IGNORECASE)


def parse_formula(formula: str) -> list[set[int]]:
    """
    'Event 6/Event 6+Event 41/Event 43/Event 48'
    -> [ {6}, {41,43,48} ]  # AND из OR-групп
    """
    formula = formula.strip()
    if not formula:
        return []

    and_terms = [t.strip() for t in formula.split("+") if t.strip()]
    groups: list[set[int]] = []

    for term in and_terms:
        or_parts = [p.strip() for p in term.split("/") if p.strip()]
        ids: set[int] = set()
        for part in or_parts:
            for m in EVENT_RE.finditer(part):
                ids.add(int(m.group(1)))
        if ids:
            groups.append(ids)

    return groups


def formula_is_satisfied(event_ids_present: set[int], formula: str) -> bool:
    groups = parse_formula(formula)
    if not groups:
        return False
    return all(any(eid in event_ids_present for eid in group) for group in groups)


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def dump_json(path: str, data: dict) -> None:
    tmp = Path(path).with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def collect_event_ids_from_card(card: dict) -> set[int]:
    """
    Берёт из card["events"]:
    - event_ids (list[int]) если есть
    - иначе id (int) если есть
    """
    out: set[int] = set()
    events = card.get("events") or []
    if not isinstance(events, list):
        return out

    for e in events:
        if not isinstance(e, dict):
            continue

        event_ids = e.get("event_ids")
        if isinstance(event_ids, list) and event_ids:
            for x in event_ids:
                try:
                    out.add(int(x))
                except (TypeError, ValueError):
                    pass
            continue

        # fallback: одиночный id
        eid = e.get("id")
        if eid is not None:
            try:
                out.add(int(eid))
            except (TypeError, ValueError):
                pass

    return out


def main(patients_path: str, diagnoses_path: str) -> None:
    patients = load_json(patients_path)
    diagnoses = load_json(diagnoses_path)

    dx_list = diagnoses.get("diagnoses", [])

    for patient in patients.get("patients", []):
        for card in patient.get("stac_cards", []):
            stac_card_id = card.get("id")
            if stac_card_id is None:
                continue

            # если events пустые — пропускаем
            if not card.get("events"):
                continue

            event_ids_present = collect_event_ids_from_card(card)
            if not event_ids_present:
                continue

            for dx in dx_list:
                formulas = dx.get("formulas") or []
                if not formulas:
                    continue

                ok = any(formula_is_satisfied(event_ids_present, f) for f in formulas)
                if ok:
                    ids = dx.setdefault("stac_card_ids", [])
                    if stac_card_id not in ids:
                        ids.append(stac_card_id)

    dump_json(diagnoses_path, diagnoses)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python assign_diagnoses.py patients_final.json diagnoses.json")
        raise SystemExit(2)

    main(sys.argv[1], sys.argv[2])
