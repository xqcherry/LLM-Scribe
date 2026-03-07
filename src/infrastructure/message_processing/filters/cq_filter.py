import re
import html
from typing import Dict, Callable

# 预编译正则
RE_CQ_CODE = re.compile(r"\[CQ:(?P<type>[a-z0-9_-]+)(?P<params>(?:,[^]]*)?)]", re.I)
RE_WHITESPACE = re.compile(r"\s+")
RE_PROMPT_IN_JSON = re.compile(r"\"prompt\"\s*:\s*\"([^\"]+)\"")


class CQHandlers:
    """存放所有 CQ 类型的渲染逻辑"""

    @staticmethod
    def at(p: Dict) -> str:
        qq = p.get("qq", "?")
        return "[@all]" if qq.lower() == "all" else f"[@{qq}]"

    @staticmethod
    def face(p: Dict) -> str:
        return f"[表情:id={p['id']}]" if "id" in p else "[表情]"

    @staticmethod
    def reply(p: Dict) -> str:
        rid = p.get("id") or p.get("seq")
        return f"[回复:id={rid}]" if rid else "[回复]"

    @staticmethod
    def image(p: Dict) -> str:
        res = p.get("file") or p.get("md5") or ("url..." if "url" in p else None)
        return f"[图片:file={res}]" if res else "[图片]"

    @staticmethod
    def video(p: Dict) -> str:
        res = p.get("file") or p.get("md5") or ("url..." if "url" in p else None)
        return f"[视频:file={res}]" if res else "[视频]"

    @staticmethod
    def json(p: Dict) -> str:
        data = p.get("data")
        if data:
            # 优先尝试正则匹配 prompt
            m = RE_PROMPT_IN_JSON.search(data)
            if m and (prompt := m.group(1).strip()):
                return f"[卡片: {prompt}]"
        return "[卡片]"

    @staticmethod
    def file(p: Dict) -> str:
        name, fid = p.get("name"), p.get("file")
        if name and fid: return f"[文件:name={name} file={fid}]"
        return f"[文件:file={fid}]" if fid else "[文件]"

    @staticmethod
    def share(p: Dict) -> str:
        return f"[分享:title={p['title']}]" if "title" in p else "[分享]"


# 建立映射表
HANDLER_MAP: Dict[str, Callable[[Dict], str]] = {
    "at": CQHandlers.at,
    "face": CQHandlers.face,
    "reply": CQHandlers.reply,
    "image": CQHandlers.image,
    "video": CQHandlers.video,
    "record": lambda p: f"[语音:file={p.get('file')}]" if "file" in p else "[语音]",
    "json": CQHandlers.json,
    "file": CQHandlers.file,
    "share": CQHandlers.share,
    "forward": lambda p: f"[转发消息:id={p.get('id')}]" if "id" in p else "[转发消息]",
    "location": lambda p: f"[位置:lat={p.get('lat')} lon={p.get('lon')}]" if "lat" in p else "[位置]",
}


def _parse_params_to_dict(raw: str) -> Dict[str, str]:
    """将参数串解析为字典，处理更方便"""
    if not raw: return {}
    d = {}
    for part in raw.split(","):
        if "=" in (p := part.strip()):
            k, v = p.split("=", 1)
            d[k.strip()] = html.unescape(v.strip())
        elif p:
            d[p] = None
    return d


def cq_filter(text: str) -> str:
    """智能过滤/标准化 CQ 码（优化版）"""
    if not text: return ""

    def _replace(match: re.Match) -> str:
        ctype = match.group("type").lower()
        params = _parse_params_to_dict(str(match.group("params").lstrip(",")))

        handler = HANDLER_MAP.get(ctype)
        if handler:
            token = handler(params)
        else:
            # 未知类型降级处理
            p_str = " ".join(f"{k}={v}" for k, v in params.items() if v is not None)
            token = f"[CQ:{ctype}{' ' + p_str if p_str else ''}]"

        return f" {token} "

    # 1. 先用 re.sub 处理所有 CQ 码，并利用回调函数渲染
    # 2. 对整体结果做一次 unescape 处理普通文本
    # 3. 压缩空白符
    processed = RE_CQ_CODE.sub(_replace, text)
    final = html.unescape(processed)
    return RE_WHITESPACE.sub(" ", final).strip()
