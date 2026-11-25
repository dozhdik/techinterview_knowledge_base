"""Replay the frozen dialogue benchmark against a running local FastAPI server."""
import argparse
import json
from pathlib import Path
import sys
from time import perf_counter
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "evaluation" / "dialogues.json"


def replay(dialogues, url, strategy):
    rows = []
    for dialogue in dialogues:
        history = []
        for number, turn in enumerate(dialogue["turns"], start=1):
            question = turn["question"]
            payload = {"question": question}
            if history and strategy == "naive":
                previous = history[-1]["question"].rstrip(" .!?")
                payload["question"] = f"{previous}. {question}"
                if len(payload["question"]) > 1000:
                    raise ValueError("The combined baseline question exceeds the API limit")
            if history and strategy == "structured":
                payload["context"] = history[-6:]

            request = Request(f"{url.rstrip('/')}/api/ask", data=json.dumps(payload).encode(),
                              headers={"Content-Type": "application/json"})
            started = perf_counter()
            with urlopen(request, timeout=90) as response:
                answer = json.load(response)
            elapsed_ms = (perf_counter() - started) * 1000
            if answer["is_rag_enabled"] or answer["search_notice"] or answer["status"] == "error":
                raise RuntimeError(f"Extractive search was unavailable for {dialogue['id']}:{number}")
            sources = [item["id"] for item in answer["sources"]]
            if any(item["url"] != f"/cards/{item['id']}" for item in answer["sources"]):
                raise ValueError(f"Unexpected source URL for {dialogue['id']}:{number}")
            history.append({"question": question, "source_ids": sources[:8], "state": answer["search_state"]})
            rows.append({"dialogue": dialogue["id"], "turn": number, "split": dialogue["split"],
                         "sent": payload, "ms": elapsed_ms, "answer": answer})
    return rows



def attach_diagnostics(rows):
    """Obtain ranks locally after timing HTTP. Confirm that the source IDs match."""
    sys.path.insert(0, str(ROOT))
    from kb.conversation import Conversation, ConversationTurn, DialogueState
    from kb.extractive import direct_search
    from kb.retrieval import get_engine
    from web.server import load_units

    units = load_units()
    dialogue = Conversation(units)
    engine = get_engine(ROOT)
    engine.warm_up()
    for row in rows:
        sent = row["sent"]
        question = sent["question"]
        context = [ConversationTurn.model_validate(item) for item in sent.get("context", [])]
        prior = dialogue.restore(context) if context else DialogueState()
        resolution = dialogue.resolve(question, prior)
        if direct := direct_search(question, units):
            result, debug = direct
        elif context and resolution.clarification:
            result, debug = None, {"ranked_cards": []}
        else:
            result, debug = engine.ask(resolution.search_query if context else question, units,
                                       context_ids=resolution.required_cards if context else ())
        sources = [unit.id for unit in result.units] if result else []
        if sources != [item["id"] for item in row["answer"]["sources"]]:
            raise ValueError(f"Local and HTTP sources differ for {row['dialogue']}:{row['turn']}")
        row["diagnostics"] = {
            "ranked_cards": debug["ranked_cards"],
            "kind": resolution.kind if context else "standalone",
            "active": resolution.updated.active if context else resolution.explicit,
            "explicit": resolution.explicit,
            "inherited": resolution.inherited if context else (),
            "search_query": resolution.search_query if context else question,
        }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--strategy", required=True, choices=("baseline", "naive", "structured"))
    parser.add_argument("--split", choices=("dev", "holdout", "all"), default="holdout")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--diagnose", action="store_true",
                        help="Attach local ranks from the default MiniLM index; serve with KB_ENTITY_MODE=off")
    args = parser.parse_args()
    dialogues = json.loads(args.cases.read_text(encoding="utf-8"))
    selected = [item for item in dialogues if args.split in ("all", item["split"])]
    rows = replay(selected, args.url, args.strategy)
    if args.diagnose:
        attach_diagnostics(rows)
    args.output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{args.strategy}, {args.split}: {len(selected)} dialogues, {len(rows)} HTTP responses")


if __name__ == "__main__":
    main()
