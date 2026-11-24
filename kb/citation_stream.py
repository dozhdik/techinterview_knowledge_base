"""Remove citation markers from a stream without exposing split markers."""
import re


class CitationFilter:
    def __init__(self):
        self.pending = ""

    def feed(self, text, final=False):
        self.pending += text
        visible = []
        while self.pending:
            at = self.pending.find("[")
            if at < 0:
                visible.append(self.pending)
                self.pending = ""
                break
            visible.append(self.pending[:at])
            self.pending = self.pending[at:]
            if len(self.pending) == 1:
                break
            double = self.pending.startswith("[[")
            end = self.pending.find("]]" if double else "]", 2 if double else 1)
            if end < 0:
                break
            length = end + (2 if double else 1)
            token = self.pending[:length]
            self.pending = self.pending[length:]
            if not double and not re.fullmatch(r"\[[A-Z]+-[A-Z]+-\d+\]", token):
                visible.append(token)
        if final:
            # Unclosed bracketed material is withheld; final validation decides validity.
            self.pending = ""
        return "".join(visible)
