import assert from "node:assert/strict";
import test from "node:test";
import {readFile} from "node:fs/promises";

const source = await readFile(new URL("../../web/static/js/conversation.js", import.meta.url), "utf8");
const {recentTurns} = await import("data:text/javascript;base64," + Buffer.from(source).toString("base64"));

test("only confirmed question-answer pairs with bounded data are transmitted", () => {
  const turns = Array.from({length:8}, (_, i) => [
    {role:"user", id:"q"+i, content:"Вопрос "+i},
    {role:"assistant", replyTo:"q"+i, content:"Служебный ответ", searchState:"partial",
      sources:[{id:"CS-CONCEPT-016", title:"Поиск"}]},
  ]).flat();
  turns.push({role:"user", id:"orphan", content:"Прерванный запрос"});
  const found = recentTurns(turns);
  assert.equal(found.length,6);
  assert.deepEqual(found[0],{question:"Вопрос 2",source_ids:["CS-CONCEPT-016"],state:"partial"});
  assert.ok(found.every(item => !Object.hasOwn(item,"answer")));
});

test("legacy messages restore context and unrelated or rejected replies are skipped", () => {
  const state = [{role:"user",id:"a",content:"Что такое BFS?"}, {role:"assistant",content:"описание"},
    {role:"user",id:"b",content:"А память?"},{role:"assistant",replyTo:"another",content:"несовпадение"},
    {role:"user",id:"c",content:"Отправка не удалась"},{role:"assistant",status:"error"}];
  assert.deepEqual(recentTurns(state),[{question:"Что такое BFS?",source_ids:[],state:null}]);
  assert.deepEqual(recentTurns([]),[]);
});
