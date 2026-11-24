"""Cancellable asynchronous client for the local Ollama NDJSON API."""
import asyncio
import json
import re
import ssl
from urllib.parse import urlparse

from .rag import RagError, SYSTEM_PROMPT


async def stream_chat(config, question, context, allowed_ids=None):
    parsed = urlparse(config.base_url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise RagError("Некорректный адрес Ollama")
    base = parsed.path.rstrip("/")
    if base.endswith("/v1"):
        base = base[:-3]
    path = (base or "") + "/api/chat"
    options = {"temperature": config.temperature, "num_ctx": config.num_ctx,
               "num_predict": config.num_predict}
    allowed = sorted({item for item in (allowed_ids or []) if re.fullmatch(r"[A-Z]+-[A-Z]+-\d+", item)})
    instruction = SYSTEM_PROMPT
    if allowed:
        instruction += " Допустимые ID источников: " + ", ".join(allowed) + "."
    body = {"model": config.model, "stream": True, "keep_alive": config.keep_alive,
            "options": options,
            "messages": [{"role": "system", "content": instruction},
                         {"role": "user", "content": f"Вопрос: {question}\n\nКонтекст БЗ:\n{context}"}]}
    if config.think is not None:
        body["think"] = config.think
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = [f"POST {path} HTTP/1.1", f"Host: {parsed.netloc}",
               "Content-Type: application/json", f"Content-Length: {len(payload)}", "Connection: close"]
    if config.api_key:
        headers.append(f"Authorization: Bearer {config.api_key}")
    writer = None
    try:
        async with asyncio.timeout(config.timeout_seconds):
            reader, writer = await asyncio.open_connection(
                parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80),
                ssl=ssl.create_default_context() if parsed.scheme == "https" else None)
            writer.write(("\r\n".join(headers) + "\r\n\r\n").encode("ascii") + payload)
            await writer.drain()
            status = (await reader.readline()).decode("iso-8859-1").split()
            if len(status) < 2 or status[1] != "200":
                raise RagError("Ollama вернул ошибку HTTP " + (status[1] if len(status) > 1 else ""))
            response_headers = {}
            while True:
                line = await reader.readline()
                if line in (b"\r\n", b"\n", b""):
                    break
                key, _, value = line.decode("iso-8859-1").partition(":")
                response_headers[key.lower()] = value.strip().lower()
            pending = b""
            chunked = "chunked" in response_headers.get("transfer-encoding", "")
            while True:
                if chunked:
                    line = await reader.readline()
                    if not line:
                        raise RagError("Соединение с Ollama прервано")
                    size = int(line.split(b";", 1)[0].strip(), 16)
                    if not size:
                        break
                    part = await reader.readexactly(size)
                    if await reader.readexactly(2) != b"\r\n":
                        raise RagError("Некорректный поток Ollama")
                else:
                    part = await reader.read(4096)
                    if not part:
                        break
                pending += part
                while b"\n" in pending:
                    line, pending = pending.split(b"\n", 1)
                    if line.strip():
                        item = json.loads(line)
                        if not isinstance(item, dict):
                            raise RagError("Ollama вернул некорректное сообщение")
                        yield item
            if pending.strip():
                item = json.loads(pending)
                if not isinstance(item, dict):
                    raise RagError("Ollama вернул некорректное сообщение")
                yield item
    except (OSError, TimeoutError, ValueError, json.JSONDecodeError, asyncio.IncompleteReadError) as exc:
        raise RagError("Поток Ollama недоступен или повреждён") from exc
    finally:
        if writer is not None:
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass
