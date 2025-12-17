import re


def chunk_msgs(msgs, chunk_size=220, overlap=50):

    n = len(msgs)
    if n == 0:
        return []

    chunks = []
    i = 0
    while i < n:
        end = min(i + chunk_size, n)
        chunks.append(msgs[i:end])
        i += (chunk_size - overlap)

    return chunks


def build_alias_map(msgs):

    alias_map = {}
    idx = 1

    for m in msgs:
        uid = m.get("user_id")
        nickname = m.get("sender_nickname") or str(uid)
        if uid not in alias_map:
            code = f"U{idx}"
            idx += 1
            alias_map[uid] = {"code": code, "nickname": nickname}

    return alias_map


def restore_nicknames(text: str, alias_map: dict) -> str:

    if not text or not alias_map:
        return text

    # 先把代号替换成昵称
    for info in alias_map.values():
        code = info["code"]
        nickname = info["nickname"]
        text = text.replace(code, nickname)

    # 再为昵称加上标记，避免重复包裹
    for info in alias_map.values():
        nickname = re.escape(info["nickname"])
        pattern = rf'(?<!「){nickname}(?!」)'
        text = re.sub(pattern, lambda m: f'「{m.group(0)}」', text)

    return text