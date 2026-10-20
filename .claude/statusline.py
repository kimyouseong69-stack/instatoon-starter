#!/usr/bin/env python3
"""Claude Code 상태줄 — 현재 세션 컨텍스트 토큰 사용량 실시간 표시.

Claude Code가 stdin으로 넘겨주는 세션 정보(JSON)에서 transcript 경로를 받아,
마지막 API 호출의 usage로 현재 컨텍스트 크기를 계산한다.
🟢 <50% | 🟡 50~75% | 🔴 ≥75% (+ /clear 권장 경고)
"""
import sys, json, os

def fmt(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.2f}M"
    return f"{n/1000:.0f}k"

try:
    data = json.load(sys.stdin)
except Exception:
    print("…")
    sys.exit(0)

model = (data.get("model") or {})
model_name = model.get("display_name", "")
model_id = (model.get("id") or "").lower()
# 1M 컨텍스트 모델 여부
limit = 1_000_000 if "1m" in model_id else 200_000

ctx = 0
tp = data.get("transcript_path") or ""
try:
    size = os.path.getsize(tp)
    with open(tp, "rb") as f:
        f.seek(max(0, size - 300_000))  # 끝 300KB만 읽어 최신 usage 탐색
        chunk = f.read().decode("utf-8", "ignore")
    for line in reversed(chunk.splitlines()):
        try:
            d = json.loads(line)
        except Exception:
            continue
        u = (d.get("message") or {}).get("usage")
        if u:
            ctx = (u.get("input_tokens", 0)
                   + u.get("cache_read_input_tokens", 0)
                   + u.get("cache_creation_input_tokens", 0))
            break
except Exception:
    pass

pct = ctx * 100 // limit if limit else 0
if pct >= 75:
    icon, color = "🔴", "\033[31m"
elif pct >= 50:
    icon, color = "🟡", "\033[33m"
else:
    icon, color = "🟢", "\033[32m"

parts = [f"{icon} {color}컨텍스트 {fmt(ctx)}/{fmt(limit)} ({pct}%)\033[0m"]
if model_name:
    parts.append(model_name)
cost = (data.get("cost") or {}).get("total_cost_usd")
if cost:
    parts.append(f"${cost:.2f}")
if pct >= 75:
    parts.append("⚠️ 비대해짐 — /compact 또는 /clear 권장")

print("  |  ".join(parts))
