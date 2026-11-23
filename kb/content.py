import re

from .parser import KnowledgeUnit


def has_material(unit: KnowledgeUnit) -> bool:
    body = re.sub(r"<!--.*?-->", "", unit.content, flags=re.DOTALL)
    body = re.sub(r"```.*?```", "", body, flags=re.DOTALL)
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "|")):
            continue
        line = re.sub(r"^(?:[-*+]\s*|\d+[.)]\s*)", "", line).strip()
        if re.fullmatch(r"\*\*[^*]+\*\*:\s*(?:O\(\?\))?", line):
            continue
        if re.search(r"[A-Za-zА-Яа-яЁё]{3,}", line):
            return True
    return False
