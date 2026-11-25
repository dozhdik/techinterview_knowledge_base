const CONTEXT_LIMIT = 6;
const STATES = new Set(["complete", "partial", "related_only", "absent", "clarification"]);

export function recentTurns(messages) {
  const turns = [];
  for (let i = messages.length - 1; i > 0 && turns.length < CONTEXT_LIMIT; i--) {
    const answer = messages[i];
    const question = messages[i - 1];
    if (answer?.role !== "assistant" || answer.status === "error" || question?.role !== "user") continue;
    if (answer.replyTo && answer.replyTo !== question.id) continue;
    if (typeof question.content !== "string" || !question.content.trim()) continue;
    const sources = Array.isArray(answer.sources) ? answer.sources : [];
    const sourceIds = sources.map(source => source?.id)
      .filter(id => typeof id === "string" && id.length >= 1 && id.length <= 48).slice(0, 8);
    turns.unshift({
      question: question.content.slice(0, 1000),
      source_ids: sourceIds,
      state: STATES.has(answer.searchState) ? answer.searchState : null,
    });
  }
  return turns;
}
