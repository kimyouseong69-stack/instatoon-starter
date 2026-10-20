#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""툰 → 릴스(9:16). 새로 그리지 않고 화면 효과(줌·흔들림·전환·글자 등장) + 효과음만 입힌다.

    python3 samples/엔진/reel/toon_reel.py <편 폴더> --plan     # reel.json(컷 길이·효과·소리 계획)만 만들고 끝
    python3 samples/엔진/reel/toon_reel.py <편 폴더>            # 영상 만들기 → 편 폴더/reel/reel.mp4
    (--profile 기본값 = 기본.  samples/엔진/reel/profiles/<이름>.json)

두 가지 입력 방식(프로필 "mode")
  cards   : 완성 카드 card1..N.png 를 그대로 쓴다. 글자 없는 판은 build.js 의
            slide('sN.png') → scenes/sN.png 로 자동 대응(카드 배경과 같은 그림). 표지 등 직접 짠 컷은 글자 없는 판 없음.
            컷 길이는 그 컷 글자 수로 자동 계산(읽는 속도 chars_per_sec).
  compose : 편 폴더 compose.py 의 s1()..sN() 로 그린다(고급). 글자 없는 판은 글자·말풍선 그리기를 끄고 다시 그림.
            reel.json 을 사람이 직접 쓴다(컷 길이·효과·효과음 시각).

reel.json(편 폴더) — 없으면 cards 모드에서 자동 생성. 컷 키:
  panel(번호) · dur · text_at · fx{punch, zoom, shake:[세기,초], bursts:[초..], flash} · sfx:[[이름, 초, 볼륨]] · reveal{n,start,step}
  최상위: bgm · bgm_vol · panel_y · tracker(체크리스트 띠, 기본 끔)

프로필(scripts/../profiles/<이름>.json): bg(solid|blur) · transition(swipe|fade) · idle_zoom · slow_zoom · text_bump · text_fade
  · asset_root(BGM 폴더) · sfx_root(효과음 폴더) · bgm · bgm_vol · 컷 길이 계산값
  폴더 경로는 저장소 맨 위 기준 상대경로. reel.json 의 효과음은 「파일 이름」만 적는다(내 컴퓨터 경로가 새지 않게).
  효과음 파일이 없으면 경고만 하고 그 소리는 건너뛴다.
"""
import argparse, importlib.util, json, math, os, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
W, H, FPS, PH = 1080, 1920, 30, 1350   # PH = 컷 그림 높이(fill 모드면 1920 = 화면 꽉)

ap = argparse.ArgumentParser()
ap.add_argument("ep"); ap.add_argument("--profile", default="기본"); ap.add_argument("--plan", action="store_true")
ap.add_argument("--bgm", help="프로필 BGM 대신(asset_root 기준 경로)")
A = ap.parse_args()
EP = os.path.abspath(A.ep)
P = json.load(open(os.path.join(HERE, "profiles", A.profile + ".json"), encoding="utf-8"))
for k_ in ("asset_root", "sfx_root"):
    if P.get(k_) and not os.path.isabs(P[k_]): P[k_] = os.path.join(REPO, P[k_])
RJ = os.path.join(EP, "reel.json")
if P.get("sfxmap"):
    P["_sfxmap"] = json.load(open(os.path.join(HERE, "profiles", P["sfxmap"]), encoding="utf-8"))

# ---------------------------------------------------------------- 컷 그림 준비
def fit(im):
    return im.convert("RGB").resize((W, PH), Image.LANCZOS)   # PH 는 전역(fill 이면 1920)

def cards_inputs():
    """card1..N 과 글자 없는 판(scenes) 대응, 컷별 글자 수."""
    n = len([f for f in os.listdir(EP) if re.fullmatch(r"card\d+\.png", f)])
    js = open(os.path.join(EP, "build.js"), encoding="utf-8").read()
    blocks = re.split(r"(?:\n|;)\s*S\.push\(", js)[1:]          # 「`);S.push(」처럼 한 줄에 붙은 것도 나눈다
    out = []
    for k in range(1, n + 1):
        b = blocks[k - 1] if k - 1 < len(blocks) else ""
        m = re.match(r"\s*slide\('([^']+)'", b)
        bare = os.path.join(EP, "scenes", m.group(1)) if m else None
        # 글자 수 = 따옴표 문자열 중 CSS·파일명이 아닌 것의 한글 수(읽는 데 걸리는 시간 계산용)
        lits = re.findall(r"'([^'\n]*)'", b)
        words = [re.sub(r"<[^>]+>", "", s) for s in lits if not re.search(r"[:;]|\.png|px|^#", s)]
        chars = len(re.findall(r"[가-힣]", "".join(words)))
        body = b
        out.append({"card": os.path.join(EP, "card%d.png" % k),
                    "bare": bare if bare and os.path.exists(bare) else None, "chars": chars,
                    "sfx": re.findall(r"sfx\('([^']*)'", body),                       # 카드에 그려진 효과음 글자(순서대로)
                    "bubble": bool(re.search(r"\b(say|think)\(", body)), "text": " ".join(words),
                    "says": [re.sub(r"<[^>]+>", "", x) for x in re.findall(r"\bsay\('([^']*)'", body)]})
    return out

def plan_cards():
    global USED_ALSO
    USED_ALSO = set()
    items = cards_inputs(); cuts = []
    for i, it in enumerate(items):
        if i == 0:
            dur, ta = P["cover_dur"], 0.0
        elif it["chars"] == 0:
            dur, ta = P["notext_dur"], 0.0
        else:
            dur = min(P["max_dur"], max(P["min_dur"], P["base_sec"] + it["chars"] / P["chars_per_sec"]))
            ta = P["text_at"] if it["bare"] else 0.0
        fx = {"zoom": P.get("slow_zoom", 0)} if P.get("slow_zoom") else {}
        sfx, trans, words = [], "fade", []
        SM = P.get("_sfxmap")
        if SM:
            if i == 0:
                epk = os.path.basename(EP)[:4]                    # 표지 소리는 편마다(그림·제목의 상황) — 없으면 기본
                n_, v_, f_ = SM.get("cover_by_ep", {}).get(epk, SM["cover"]); sfx.append([n_, 0.05, v_])
                for k_, x_ in f_.items():
                    if k_ == "burst": fx.setdefault("bursts", []).append(0.1)
                    else: fx[k_] = x_
            for j, w in enumerate(it["sfx"]):
                hit = next((m for m in SM["map"] if m[0] in w), None)
                if not hit: continue
                at = round(ta + 0.35 * j, 2); words.append(w)
                sfx.append([hit[1], at, hit[2]])
                for k_, v_ in hit[3].items():
                    if k_ == "burst": fx.setdefault("bursts", []).append(at)
                    elif k_ == "pulse": fx.setdefault("bursts", []).extend([at, at + 0.55]); fx["pulse"] = True
                    elif k_ == "shake": fx["shake"] = [v_[0], at + v_[1]]
                    elif k_ in ("punch", "flash"): fx[k_] = max(fx.get(k_, 0), v_)
            for m in SM.get("also_map", []):            # 그림 효과음 글자가 있어도 같이 넣는 장면 소리(수화기 딸칵·경고음 등) — 편마다 한 번씩
                if m[0] in it["text"] and m[0] not in USED_ALSO:
                    USED_ALSO.add(m[0])
                    at = round(ta + m[4], 2) if len(m) > 4 else ta
                    sfx.append([m[1], at, m[2]])
                    for k_, v_ in m[3].items():
                        if k_ == "burst": fx.setdefault("bursts", []).append(at)
                        elif k_ in ("punch", "flash"): fx[k_] = max(fx.get(k_, 0), v_)
            voices = SM.get("babble", [])
            has_babble = any("babble" in x[0] for x in sfx)
            last = i == len(items) - 1
            for j, line in enumerate([] if (has_babble or last) else it["says"][:2]):   # 말풍선 대사 = 게임식 중얼중얼(톡 대신)
                if not voices: break
                senior = any(k in line for k in SM.get("senior_markers", []))
                panic = any(k in line for k in ("어…", "어...", "저…", "그…", "아, 저"))
                v = "babble_low" if senior else ("babble_fast" if panic else "babble")
                at = round(ta + 0.1 + 1.0 * j, 2)
                sfx.append([v, at, SM.get("babble_vol", 0.9)])
                words.append("(말:%s)" % line[:6])
            if not words and ta >= 0:
                hit = next((m for m in SM.get("text_map", []) if m[0] in it["text"]), None)
                if hit:
                    at = ta if ta > 0 else 0.3; words.append("(" + hit[0] + ")")
                    sfx.append([hit[1], at, hit[2]])
                    for k_, v_ in hit[3].items():
                        if k_ == "burst": fx.setdefault("bursts", []).append(at)
                        elif k_ == "pulse": fx.setdefault("bursts", []).extend([at, at + 0.55]); fx["pulse"] = True
                        elif k_ == "zoom": fx["zoom"] = v_
                        elif k_ in ("punch", "flash"): fx[k_] = max(fx.get(k_, 0), v_)
                elif it["bubble"] and ta > 0 and SM.get("bubble_pop"):   # 「띠링」 반복은 거슬림 → 기본은 소리 없음
                    n_, v_ = SM["bubble_pop"]; sfx.append([n_, ta, v_])
            # 전환: 소리 나는 사건 컷은 휙, 조용한 컷은 페이드, 충격 컷은 번쩍과 함께 곧바로
            snd = [x[0] for x in sfx]
            if fx.get("flash"): trans = "cut"                                   # 충격: 번쩍과 함께 바로
            elif any(not w.startswith("(") for w in words) or fx.get("punch"): trans = "swipe"   # 그림 효과음 글자 있는 사건 컷: 휙
            elif set(snd) & set(SM.get("dip_sounds", [])): trans = "dip"        # 가라앉는 컷: 까맣게 꺼졌다 켜짐
            elif set(snd) & set(SM.get("white_sounds", [])): trans = "white"    # 따뜻한 마무리: 하얗게
            elif fx.get("pulse") or fx.get("zoom", 0) >= 0.06: trans = "zoom"                   # 긴장: 확 다가가며 시작
            else: trans = "fade"
        cuts.append({"panel": i + 1, "dur": round(dur, 1), "text_at": ta, "chars": it["chars"],
                     "words": words, "trans": trans, "fx": fx, "sfx": sfx})
    # 다양성 보정: 같은 (전환, 소리) 조합이 3번 이어지면 전환을 돌린다(「다 똑같다」 방지)
    ROT_T = ["fade", "zoom", "swipe"]
    def combo(c): return (c["trans"], tuple(x[0] for x in c["sfx"]))
    for k in range(2, len(cuts)):
        if combo(cuts[k]) == combo(cuts[k - 1]) == combo(cuts[k - 2]):
            prev = cuts[k - 1]["trans"]
            cuts[k]["trans"] = next(t for t in ROT_T if t != prev and t != cuts[k]["trans"])
    cfg = {"profile": A.profile, "mood": P.get("default_mood", ""), "bgm_vol": P["bgm_vol"], "cuts": cuts}
    json.dump(cfg, open(RJ, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return cfg

if os.path.exists(RJ):
    cfg = json.load(open(RJ, encoding="utf-8"))
    if "bgm" not in cfg and P.get("bgm") is None: cfg["bgm"] = None
elif P["mode"] == "cards":
    cfg = plan_cards()
else:
    sys.exit("compose 모드는 reel.json 을 먼저 써야 합니다")
if A.plan:
    print("✓ reel.json", sum(c["dur"] for c in cfg["cuts"]), "초"); sys.exit()
if A.bgm: cfg["bgm"] = A.bgm
# 분위기로 고르기: reel.json 에 mood 만 있고 bgm 이 없으면 asset_root/library.json 에서 그 분위기의 「ok」 곡(없으면 첫 곡)
LIB = os.path.join(P["asset_root"], "library.json")
if cfg.get("mood") and not cfg.get("bgm") and os.path.exists(LIB):
    tr = [t for t in json.load(open(LIB, encoding="utf-8"))["tracks"] if cfg["mood"] in t["moods"]]
    if not tr: sys.exit("library.json 에 「%s」 곡이 없습니다 — 곡부터 추가" % cfg["mood"])
    cfg["bgm"] = next((t["file"] for t in tr if t.get("verdict", "").startswith("ok")), tr[0]["file"])
cuts = cfg["cuts"]; total = sum(c["dur"] for c in cuts)

FILL = P["mode"] == "cards" and P.get("fill")
if FILL:
    if not os.path.exists(os.path.join(EP, "_reel_fill", "card1.png")):
        subprocess.run([sys.executable, os.path.join(HERE, "fill_cards.py"), EP], check=True)
    PH = H
if P["mode"] == "cards":
    items = cards_inputs()
    if FILL:
        for it in items:
            it["card"] = os.path.join(EP, "_reel_fill", os.path.basename(it["card"]))
            if it["bare"]: it["bare"] = os.path.join(EP, "_reel_fill", "bare", os.path.basename(it["bare"]))
            if it["bare"] and not os.path.exists(it["bare"]): it["bare"] = None
        # 통째로 넣은 카드(reel_fill_fit.json)는 글자 없는 판이 잘린 그림이라 겹쳐 보인다 → 글자 등장 없이 카드만
        ff = os.path.join(EP, "reel_fill_fit.json")
        for k in (json.load(open(ff)) if os.path.exists(ff) else []):
            if 0 < k <= len(items): items[k - 1]["bare"] = None
    panels = []
    for c in cuts:
        it = items[c["panel"] - 1]; full = fit(Image.open(it["card"]))
        panels.append((fit(Image.open(it["bare"])) if it["bare"] else full, full))
    reveals = {}
else:
    spec = importlib.util.spec_from_file_location("compose", os.path.join(EP, "compose.py"))
    C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
    def render(n, text=True):
        fn = getattr(C, "s%d" % n)
        if text: return fn().convert("RGB")
        D = ImageDraw.ImageDraw; keep = {k: getattr(D, k) for k in ("text", "rounded_rectangle", "polygon", "line")}
        for k in keep: setattr(D, k, lambda *a, **k2: None)
        try: return fn().convert("RGB")
        finally:
            for k, v in keep.items(): setattr(D, k, v)
    panels = [(render(c["panel"], False), render(c["panel"], True)) for c in cuts]
    reveals = {}
    for i, c in enumerate(cuts):
        rv = c.get("reveal")
        if rv:
            imgs = []
            for k in range(rv["n"] + 1):
                C.JOBS_N = k; imgs.append(render(c["panel"], True))
            C.JOBS_N = None; imgs.append(panels[i][1]); reveals[i] = imgs

# 배경: solid = 그림 모서리 색 / blur = 그 컷 그림을 크게 흐려 어둡게
bgs = []
for nt, full in panels:
    if P["bg"] == "blur":
        b = full.resize((W, int(W * PH / W * H / PH * 1.0)), Image.BILINEAR).resize((W, H)).filter(ImageFilter.GaussianBlur(38))
        b = Image.blend(b, Image.new("RGB", (W, H), (20, 18, 22)), 0.35); bgs.append(b)
    else:
        bgs.append(Image.new("RGB", (W, H), full.getpixel((8, 8))))
PY = 0 if PH == H else cfg.get("panel_y", (H - PH) // 2)

def ease_out_back(x):
    c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2

def cut_at(t):
    acc = 0
    for i, c in enumerate(cuts):
        if t < acc + c["dur"] or i == len(cuts) - 1: return i, c, t - acc
        acc += c["dur"]

def panel_img(i, c, lt):
    ta = c.get("text_at", 0.4); tf = P.get("text_fade", 0.15)
    if i in reveals:
        rv = c["reveal"]; k = int((lt - rv["start"]) / rv["step"]) + 1 if lt >= rv["start"] else 0
        return reveals[i][min(k, len(reveals[i]) - 1)]
    if lt >= ta + tf: return panels[i][1]
    if lt >= ta: return Image.blend(panels[i][0], panels[i][1], (lt - ta) / tf)
    return panels[i][0]

def layer(i, c, lt, t):
    """컷 하나를 9:16 캔버스에 그린 결과."""
    fx = c.get("fx", {}); ta = c.get("text_at", 0.4)
    img = panel_img(i, c, lt)
    s = 1.0 + P.get("idle_zoom", 0) * math.sin(t * 2.4)
    if "punch" in fx: s *= 1 + fx["punch"] * max(0, 1 - lt / 0.25)
    if "zoom" in fx: s *= 1 + fx["zoom"] * min(1, lt / c["dur"])
    if P.get("text_bump") and 0 <= lt - ta < 0.22 and i not in reveals:
        s *= 1 + P["text_bump"] * math.sin(math.pi * (lt - ta) / 0.22)
    dx = dy = 0
    if "shake" in fx:
        a, until = fx["shake"]
        if lt < until: dx = int(a * math.sin(lt * 90)); dy = int(a * math.cos(lt * 70))
    if fx.get("pulse"):
        for bt in fx.get("bursts", []):
            if 0 <= lt - bt < 0.3: s *= 1 + 0.045 * math.sin(math.pi * (lt - bt) / 0.3)   # 두근
    for bt in ([] if fx.get("pulse") else fx.get("bursts", [])):
        if 0 <= lt - bt < 0.18:
            k = 1 - (lt - bt) / 0.18; dx += int(16 * k * math.sin(lt * 120)); dy += int(10 * k * math.cos(lt * 95))
    if c.get("trans", P["transition"]) == "swipe" and i > 0 and lt < 0.16:
        dx += int(W * (1 - ease_out_back(lt / 0.16)) * 0.9)
    pw, ph = int(W * s), int(PH * s)
    cv = bgs[i].copy()
    cv.paste(img.resize((pw, ph), Image.BILINEAR), ((W - pw) // 2 + dx, PY + (PH - ph) // 2 + dy))
    if "flash" in fx and lt < fx["flash"]:
        cv = Image.blend(cv, Image.new("RGB", (W, H), "white"), 1 - lt / fx["flash"])
    return cv

def frame(t):
    i, c, lt = cut_at(t)
    tr = c.get("trans", P["transition"])
    if tr == "zoom" and lt < 0.3:                      # 확 다가가며 시작: 1.12배에서 제자리로
        c = dict(c, fx=dict(c.get("fx", {}), punch=max(0.12, c.get("fx", {}).get("punch", 0))))
    cv = layer(i, c, lt, t)
    if tr in ("dip", "white") and i > 0 and lt < 0.5:  # 까맣게/하얗게 꺼졌다 켜짐
        col = Image.new("RGB", (W, H), (0, 0, 0) if tr == "dip" else (255, 252, 246))
        if lt < 0.25:
            pc = cuts[i - 1]; prev = layer(i - 1, pc, pc["dur"], t)
            return Image.blend(prev, col, lt / 0.25)
        return Image.blend(col, cv, (lt - 0.25) / 0.25)
    if c.get("trans", P["transition"]) == "fade" and i > 0 and lt < P.get("fade_sec", 0.35):
        pc = cuts[i - 1]; prev = layer(i - 1, pc, pc["dur"], t)
        cv = Image.blend(prev, cv, lt / P.get("fade_sec", 0.35))
    return cv

# ---------------------------------------------------------------- 영상 + 소리
out = os.path.join(EP, "reel"); os.makedirs(out, exist_ok=True)
silent = os.path.join(out, "_video.mp4")
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H),
                       "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", silent],
                      stdin=subprocess.PIPE)
for k in range(int(total * FPS)):
    ff.stdin.write(frame(k / FPS).tobytes())
ff.stdin.close(); ff.wait()

ROOT = P["asset_root"]; bgm_name = cfg.get("bgm", P.get("bgm"))
def sfx_file(name):
    """효과음 이름 → 실제 파일. 이름만 적힌 것은 sfx_root 에서 .mp3/.wav 를 찾는다."""
    if os.path.isabs(name): return name if os.path.exists(name) else None
    for d in (P.get("sfx_root"), ROOT):
        for ext in ("", ".mp3", ".wav"):
            if d and os.path.isfile(os.path.join(d, name + ext)): return os.path.join(d, name + ext)
    return None
# bgm 없음(앱에서 인스타 음악을 붙일 편) → 무음 바탕
bgm_in = ["-i", os.path.join(ROOT, bgm_name)] if bgm_name else ["-f", "lavfi", "-t", str(total), "-i", "anullsrc=r=48000:cl=stereo"]
ins, fl, labels, acc, n = ["-i", silent] + bgm_in, [], [], 0, 2
TS = P.get("text_sfx")          # [효과음 이름, 볼륨] — 글자가 떠오르는 순간마다
if TS:
    for c in cuts:
        if c.get("text_at", 0) > 0: c.setdefault("sfx", []).append([TS[0], c["text_at"], TS[1]])
for c in cuts:
    for e in c.get("sfx", []):
        name, at, vol = e[0], e[1], e[2]; keep = e[3] if len(e) > 3 else False   # keep=True 면 다음 컷까지 이어짐
        fp = sfx_file(name)
        if not fp:
            print("  ⚠️ 효과음 없음 — 건너뜀:", name); continue
        ins += ["-i", fp]
        ms = int((acc + at) * 1000); rem = max(0.2, c["dur"] - at)
        trim = "" if keep else "atrim=0:%.2f,afade=t=out:st=%.2f:d=0.12," % (rem, max(0, rem - 0.12))   # 컷이 끝나면 소리도 끝
        fl.append("[%d:a]%svolume=%s,adelay=%d|%d[s%d]" % (n, trim, vol, ms, ms, n)); labels.append("[s%d]" % n); n += 1
    acc += c["dur"]
fl.append("[1:a]atrim=0:%s,volume=%s,afade=t=in:d=0.8,afade=t=out:st=%s:d=1.5[b]" % (total, cfg.get("bgm_vol", P.get("bgm_vol", 0.5)) if bgm_name else 1, max(0, total - 1.5)))
mix = ("[b]%samix=inputs=%d:normalize=0," % ("".join(labels), len(labels) + 1)) if labels else "[b]"   # 효과음 없으면 amix 생략(입력 1개면 ffmpeg 오류)
fl.append(mix + ("loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]" if bgm_name else "alimiter=limit=0.7:level=false,aresample=48000[a]"))   # 효과음만이면 loudnorm(무음 키움) 대신 리미터만
final = os.path.join(out, "reel.mp4")
subprocess.run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "0:v", "-map", "[a]",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", str(total), final], check=True)
os.remove(silent)
print("✓", final, "%.1f초" % total)
