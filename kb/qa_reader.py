"""Optional local span reader. The public answer is assembled from source blocks."""
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    margin: float


class LocalReader:
    def __init__(self, directory):
        import torch
        from transformers import AutoModelForQuestionAnswering, AutoTokenizer

        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(directory, local_files_only=True, use_fast=True)
        if not self.tokenizer.is_fast:
            raise ValueError("Для QA требуется токенизатор с символьными смещениями.")
        self.model = AutoModelForQuestionAnswering.from_pretrained(
            directory, local_files_only=True, use_safetensors=True,
        ).eval()

    def score(self, question, contexts):
        if not contexts:
            return []
        tok = self.tokenizer
        question_offsets = tok(question, add_special_tokens=False, truncation=True,
                               max_length=96, return_offsets_mapping=True)["offset_mapping"]
        question = question[:question_offsets[-1][1]] if question_offsets else question
        inputs = tok([question] * len(contexts), contexts, padding=True, truncation="only_second",
                     max_length=288, return_offsets_mapping=True, return_tensors="pt")
        sequences = [inputs.sequence_ids(i) for i in range(len(contexts))]
        offsets = inputs.pop("offset_mapping")
        torch = self.torch
        with torch.inference_mode():
            out = self.model(**inputs)
        results = []
        for i, seq in enumerate(sequences):
            positions = [j for j, sid in enumerate(seq) if sid == 1 and int(offsets[i, j, 1]) > int(offsets[i, j, 0])]
            if not positions:
                results.append(None)
                continue
            start, end = out.start_logits[i], out.end_logits[i]
            positions = torch.tensor(positions)
            widths = positions[None, :] - positions[:, None]
            joint = start[positions, None] + end[None, positions]
            joint.masked_fill_((widths < 0) | (widths >= 32), float("-inf"))
            a, b = divmod(int(joint.argmax()), len(positions))
            lo = int(offsets[i, positions[a], 0])
            hi = int(offsets[i, positions[b], 1])
            margin = float(joint[a, b] - (start[0] + end[0]))
            results.append(Span(lo, hi, margin))
        return results


@lru_cache(maxsize=1)
def load_reader(directory):
    path = Path(directory).resolve()
    if not (path / "model.safetensors").is_file():
        raise ValueError("Укажите локальный каталог QA с model.safetensors.")
    return LocalReader(str(path))


def apply_reader(reader, mode, scorer, candidates):
    """Adjust evidence only when a span has structural support."""
    if reader is None or mode == "off" or not candidates:
        return candidates, {}
    eligible = [c for c in candidates if c.blocks and c.reason != "unsupported_specific_detail"]
    if not eligible:
        return candidates, {}
    accepted = [c for c in eligible if c.admitted]
    if mode == "selective" and accepted and accepted[0].score >= .98:
        if len(accepted) == 1 or accepted[0].score - accepted[1].score > .12:
            return candidates, {}
    pairs = [(c, c.blocks[0]) for c in eligible[:3]]
    if len(pairs) < 3 and len(eligible[0].blocks) > 1:
        pairs.append((eligible[0], eligible[0].blocks[1]))
    # Read contiguous source blocks so the offsets and displayed Markdown refer to the same text.
    found = reader.score(scorer.query.normalized, [b.text for _, b in pairs])
    supported = {}
    diagnostics = {}
    for (c, b), span in zip(pairs, found):
        if span is None or not 0 <= span.start < span.end <= len(b.text):
            continue
        diagnostics[b.index] = {"card": c.card, "margin": round(span.margin, 4),
                                "span": [span.start, span.end]}
        if span.margin >= 1.5 and scorer.cover(b.matched) >= .12:
            prev = supported.get(c.card)
            if prev is None or span.margin > prev[0]:
                supported[c.card] = (span.margin, b)
    adjusted = []
    for c in candidates:
        if c.card not in supported:
            adjusted.append(c)
            continue
        margin, block = supported[c.card]
        # A span can supplement weak evidence, subject to lexical support. It
        # cannot override rejection of a specific missing detail.
        admits = c.admitted or (margin >= 4.0 and c.score >= .65 and scorer.cover(block.matched) >= .26)
        blocks = (block, *(b for b in c.blocks if b.index != block.index))
        adjusted.append(replace(c, score=c.score + .11, admitted=admits, blocks=blocks,
                                reason="qa_supported" if admits else c.reason))
    return sorted(adjusted, key=scorer.priority, reverse=True), diagnostics
