"""Minimal GEDCOM relationship reader. Not a complete GEDCOM validator."""
from __future__ import annotations
from dataclasses import dataclass, field
import hashlib
from pathlib import Path
import re

TOP = re.compile(r"^0\s+@([^@\s]+)@\s+(INDI|FAM)\s*$")
FIELD = re.compile(r"^(\d+)\s+(\S+)(?:\s+(.*))?$")
REF = re.compile(r"^@([^@]+)@$", re.I)

@dataclass
class Individual:
    uid: str
    name: str = ""
    parent_families: list[str] = field(default_factory=list)
    birth_date: str | None = None

@dataclass
class Family:
    uid: str
    husband: str | None = None
    wife: str | None = None
    children: list[str] = field(default_factory=list)

def _xref(s: str | None) -> str | None:
    m = REF.fullmatch((s or "").strip())
    return m.group(1) if m else None

def parse(text: str) -> tuple[dict[str, Individual], dict[str, Family]]:
    people: dict[str, Individual] = {}
    families: dict[str, Family] = {}
    section: tuple[str, str] | None = None
    subevent: str | None = None
    for lineno, raw in enumerate(text.splitlines(), 1):
        if raw.startswith("0 "):
            m = TOP.match(raw)
            section = (m.group(1), m.group(2)) if m else None
            subevent = None
            if m:
                uid, kind = section
                if kind == "INDI":
                    if uid in people: raise ValueError(f"duplicate INDI id at line {lineno}")
                    people[uid] = Individual(uid)
                else:
                    if uid in families: raise ValueError(f"duplicate FAM id at line {lineno}")
                    families[uid] = Family(uid)
            continue
        if not section:
            continue
        m = FIELD.match(raw)
        if not m: continue
        lvl, tag, value = int(m.group(1)), m.group(2), (m.group(3) or "")
        uid, kind = section
        if lvl == 1:
            subevent = tag
            if kind == "INDI":
                p = people[uid]
                if tag == "NAME" and not p.name: p.name = value
                if tag == "FAMC":
                    r = _xref(value)
                    if r: p.parent_families.append(r)
            else:
                fam = families[uid]
                if tag == "HUSB": fam.husband = _xref(value)
                if tag == "WIFE": fam.wife = _xref(value)
                if tag == "CHIL":
                    r = _xref(value)
                    if r: fam.children.append(r)
        if kind == "INDI" and lvl == 2 and tag == "DATE" and subevent == "BIRT":
            people[uid].birth_date = value
    return people, families

def read_gedcom(path: str | Path):
    data = Path(path).read_bytes()
    people, families = parse(data.decode("utf-8-sig", errors="replace"))
    return people, families, hashlib.sha256(data).hexdigest()

def paternal_line(people, families, *, root_id=None, root_name=None, max_generations=15):
    if (root_id is None) == (root_name is None):
        raise ValueError("give exactly one of root_id or root_name")
    if root_name is not None:
        matches = [p.uid for p in people.values() if p.name.casefold() == root_name.casefold()]
        if len(matches) != 1:
            raise ValueError(f"root name matched {len(matches)} records; use unique root-id")
        root_id = matches[0]
    if root_id not in people:
        raise ValueError("unknown root id")
    nodes, alerts, visited = [], [], set()
    current = root_id
    for _ in range(max_generations):
        if current in visited:
            alerts.append({"code": "ANCESTRY_CYCLE", "record_id": current});break
        visited.add(current)
        p = people[current]
        nodes.append({"record_id": p.uid, "name": p.name, "birth_date": p.birth_date,
                      "claim_state": "GEDCOM_REPORTED"})
        options = list(dict.fromkeys(p.parent_families))
        if not options: break
        if len(options) > 1:
            alerts.append({"code": "MULTIPLE_PARENT_FAMILIES", "record_id": current,
                           "family_refs": options}); break
        fam = families.get(options[0])
        if not fam:
            alerts.append({"code": "MISSING_FAMILY", "family_ref": options[0]}); break
        if not fam.husband:
            alerts.append({"code": "NO_PATERNAL_LINK", "family_ref": fam.uid}); break
        if current not in fam.children:
            alerts.append({"code": "INCONSISTENT_FAMILY_EDGE", "family_ref": fam.uid,
                           "record_id": current}); break
        if fam.husband not in people:
            alerts.append({"code": "MISSING_FATHER_RECORD", "family_ref": fam.uid}); break
        current = fam.husband
    return {"line": nodes, "alerts": alerts, "authority_effect": "NONE",
            "independently_verified": False, "external_search_authorized": False}
