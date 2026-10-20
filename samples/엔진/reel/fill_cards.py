#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""카드 조립 HTML(4:5)을 릴스 화면(9:16)을 꽉 채우는 판으로 다시 렌더한다 — 캐러셀 원본은 건드리지 않음.

    python3 samples/엔진/reel/fill_cards.py <편 폴더>   → <편>/_reel_fill/card1..N.png (1080x1920) + bare/sN.png(글자 없는 판)

방법: 4:5 카드를 세로 1920에 맞춰 키우면(×1.42) 좌우가 약 15%씩 잘린다.
  - 그래서 글자 상자(나레이션·말풍선)의 left/right 를 안쪽(SAFE_X=255, 4:5 기준)으로 당긴다
  - 릴스 화면의 아래쪽(캡션·버튼)·위쪽에 가리지 않게 top 은 +TOP_ADD, bottom 은 +BOT_ADD 만큼 안으로
  - 렌더 후 가운데 9:16 만 잘라 1080x1920 으로
"""
import json, os, re, shutil, subprocess, sys
from PIL import Image
EP = os.path.abspath(sys.argv[1]); OUT = os.path.join(EP, "_reel_fill")
# 2026-10-14 「디바이스마다 글자가 잘린다·위 여백이 없다·좌우 빠듯」 → 기종마다 9:16 을 더 잘라 보여 주므로 안전 여백을 넓힘
#   SAFE_X 170→255(릴스 화면 좌우 여백 ≈135px, 19.5:9 폰이 좌우를 ~97px씩 더 자름) · 위 TOP_MIN·아래 BOT_MIN(4:5 기준)은 렌더 직전 실측으로 강제
SAFE_X, TOP_ADD, BOT_ADD = 255, 110, 250
CLAMP_X = 170                        # HTML 단계 left/right 하한은 예전 값 유지(넓이를 줄이면 줄바꿈이 새로 생겨 「(지주막하출혈)/로」처럼 끊김) → 남는 넘침은 JS가 통째로 축소
TOP_MIN, BOT_MIN = 190, 330          # 릴스 화면 기준 위 ≈270px · 아래 ≈470px(상단 바·하단 캡션/버튼 + 기종별 잘림)
RENDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "render.js")

def fix_style(m):
    st = m.group(1)
    def clamp(k, minv):
        nonlocal st
        st = re.sub(r"(?<![-\w])%s:\s*(-?\d+)px" % k, lambda x: "%s:%dpx" % (k, max(minv, int(x.group(1)))), st)
    # 말풍선 꼬리·생각풍선 점처럼 부모에 붙은 장식(음수 위치)은 건드리지 않는다 — 옮기면 풍선에서 떨어져 화면에 「v」「°」로 떠 있음(10/12 발견, 전 편)
    attached = re.search(r"(?<![-\w])(top|bottom|left|right):\s*-\d+px", st)
    if "position:absolute" in st.replace(" ", "") and "inset:0" not in st.replace(" ", "") and not attached:
        clamp("left", CLAMP_X); clamp("right", CLAMP_X)
        st = re.sub(r"(?<![-\w])top:\s*(-?\d+)px", lambda x: "top:%dpx" % (int(x.group(1)) + TOP_ADD) if int(x.group(1)) < 700 else x.group(0), st)
        st = re.sub(r"(?<![-\w])bottom:\s*(-?\d+)px", lambda x: "bottom:%dpx" % (int(x.group(1)) + BOT_ADD) if int(x.group(1)) < 500 else x.group(0), st)
    return 'style="%s"' % st

def main():
    src = open(os.path.join(EP, "instagram_cards.html"), encoding="utf-8").read()
    os.makedirs(OUT, exist_ok=True)
    fx_ = os.path.join(EP, "reel_fill_fix.json")      # 편별 손보정: [[원래 문자열, 바꿀 문자열], …] (릴스판에만 적용, 캐러셀 원본은 그대로)
    if os.path.exists(fx_):
        for a_, b_ in json.load(open(fx_, encoding="utf-8")):
            assert a_ in src, a_
            src = src.replace(a_, b_)
    html = re.sub(r'style="([^"]*)"', fix_style, src)
    html = html.replace("<head>", '<head><base href="file://%s/">' % EP, 1)
    # 렌더 직전 실제 위치를 재서 9:16 안전 영역(가로 SAFE_X~1080-SAFE_X) 밖으로 나간 글자 상자를 안쪽으로 민다(회전·말풍선 포함)
    fixjs = """<script>window.addEventListener('load',()=>{const S=%d,R=1080-%d;
      document.querySelectorAll('.slide').forEach(sl=>{const b=sl.getBoundingClientRect();
        sl.querySelectorAll('div').forEach(el=>{const st=el.getAttribute('style')||'';
          if(!/position:\\s*absolute/.test(st)||/inset:\\s*0/.test(st)||!el.textContent.trim())return;
          if(el.parentElement!==sl)return;
          // 배경 없는 껍데기 상자(left:0;right:0 가운데 정렬 등)는 상자 말고 안의 내용 범위를 잰다
          const ext=()=>{const bg=getComputedStyle(el).backgroundColor;
            if(bg&&bg!=='rgba(0, 0, 0, 0)'&&bg!=='transparent')return el.getBoundingClientRect();
            const g=document.createRange();g.selectNodeContents(el);return g.getBoundingClientRect();};
          let r=ext();
          // 폭이 넘치면 줄바꿈은 그대로 두고 상자를 통째로 줄인다(scale — 회전 transform 과 따로 적용됨, 10/14)
          if(r.width>R-S){el.style.scale=String((R-S)/r.width);r=ext();}
          const L=r.left-b.left,Rr=r.right-b.left;let dx=0;
          if(L<S)dx=S-L;else if(Rr>R)dx=R-Rr;
          const T=r.top-b.top,B=r.bottom-b.top;let dy=0;
          if(T<%d)dy=%d-T;else if(B>1350-%d)dy=1350-%d-B;
          if(dx||dy)el.style.translate=dx+'px '+dy+'px';});});});</script>""" % (SAFE_X - 10, SAFE_X - 10, TOP_MIN, TOP_MIN, BOT_MIN, BOT_MIN)
    html = html.replace("</body>", fixjs + "</body>", 1)
    open(os.path.join(OUT, "instagram_cards.html"), "w", encoding="utf-8").write(html)
    # 크롬이 닫히다 멈추는 일이 있음(10/14, 카드는 다 찍힌 뒤) → 시간 제한 후 「✅ 완료」 없이도 카드 수가 맞으면 진행
    pr = subprocess.Popen(["node", RENDER, OUT, "1080", "1350"], stdout=subprocess.DEVNULL)
    try:
        assert pr.wait(timeout=480) == 0, "render 실패"
    except subprocess.TimeoutExpired:
        pr.kill(); want = src.count('class="slide"')
        got = len([f for f in os.listdir(OUT) if re.fullmatch(r"card\d+\.png", f)])
        assert got >= want, "render 멈춤: 카드 %d/%d" % (got, want)
    def crop916(im):
        w, h = im.size; cw = int(h * 9 / 16); x = (w - cw) // 2
        return im.crop((x, 0, x + cw, h)).resize((1080, 1920), Image.LANCZOS)
    n = 0
    for f in sorted(os.listdir(OUT)):
        if re.fullmatch(r"card\d+\.png", f):
            crop916(Image.open(os.path.join(OUT, f)).convert("RGB")).save(os.path.join(OUT, f)); n += 1
    # 표지(1장)는 큰 제목이 좌우로 넘친다 → 4:5 원본을 폭에 맞추고 위·아래를 맨 끝 줄 색으로 늘려 9:16 (배경이 단색에 가까운 표지 전제)
    # 위·아래 두 칸으로 나뉜 컷처럼 잘리면 안 되는 카드는 편 폴더 reel_fill_fit.json 에 번호를 적는다
    fit = [1]
    ff = os.path.join(EP, "reel_fill_fit.json")
    if os.path.exists(ff): fit += [k for k in json.load(open(ff)) if k != 1]
    for k in fit:
        cov = Image.open(os.path.join(EP, "card%d.png" % k)).convert("RGB").resize((1080, 1350), Image.LANCZOS)
        pad = (1920 - 1350) // 2
        import numpy as np
        a_ = np.asarray(cov).astype(float)
        if a_[0].std(0).max() < 12 and a_[-1].std(0).max() < 12:      # 끝 줄이 단색(표지) → 그 줄을 늘린다
            top = cov.crop((0, 0, 1080, 1)).resize((1080, pad)); bot = cov.crop((0, 1349, 1080, 1350)).resize((1080, 1920 - 1350 - pad))
            c = Image.new("RGB", (1080, 1920)); c.paste(top, (0, 0)); c.paste(cov, (0, pad)); c.paste(bot, (0, pad + 1350))
        else:                                                       # 끝 줄에 그림이 걸쳐 있으면 늘리면 세로 줄무늬 → 배경 단색 + 이음새 부드럽게
            bg = tuple(int(v) for v in np.median(np.concatenate([a_[0], a_[:, 0], a_[:, -1]]), 0))
            c = Image.new("RGB", (1080, 1920), bg); c.paste(cov, (0, pad))
            F = 60
            for y0, rng in ((pad, range(F)), (pad + 1350 - F, range(F))):
                for i in rng:
                    yy = y0 + i; t = (1 - i / F) if y0 == pad else (i / F)
                    row = np.asarray(c.crop((0, yy, 1080, yy + 1))).astype(float)
                    c.paste(Image.fromarray((row * (1 - t) + np.array(bg) * t).astype("uint8")), (0, yy))
        # 통째로 넣은 카드도 좌우 끝 글자(표지 라벨·두 칸 컷 말풍선)가 기종에 따라 잘림(10/14) → 88%로 줄여 가운데,
        # 남는 둘레는 가장자리 픽셀을 늘린 뒤 흐리게(통째 흐림은 그림이 번져 보여 탈락)
        from PIL import ImageFilter
        K = 0.88; w2, h2 = int(1080 * K), int(1920 * K); x0, y0_ = (1080 - w2) // 2, (1920 - h2) // 2
        small = c.resize((w2, h2), Image.LANCZOS)
        sa = np.asarray(small)
        padded = np.pad(sa, ((y0_, 1920 - h2 - y0_), (x0, 1080 - w2 - x0), (0, 0)), mode="edge")
        base = Image.fromarray(padded).filter(ImageFilter.GaussianBlur(18))
        m = Image.new("L", (w2, h2), 255); mp = m.load(); F2 = 14
        for xx in list(range(F2)) + list(range(w2 - F2, w2)):
            for yy in range(h2): mp[xx, yy] = min(mp[xx, yy], int(255 * min(xx, w2 - 1 - xx) / F2))
        for yy in list(range(F2)) + list(range(h2 - F2, h2)):
            for xx in range(w2): mp[xx, yy] = min(mp[xx, yy], int(255 * min(yy, h2 - 1 - yy) / F2))
        base.paste(small, (x0, y0_), m)
        base.save(os.path.join(OUT, "card%d.png" % k))
    os.makedirs(os.path.join(OUT, "bare"), exist_ok=True)
    sd = os.path.join(EP, "scenes")
    for f in os.listdir(sd) if os.path.isdir(sd) else []:
        if f.endswith(".png"):
            im = Image.open(os.path.join(sd, f)).convert("RGB")
            w, h = im.size; s = max(1080 / w * 1.0, 1350 / h)   # 4:5 상자에 cover 로 맞춘 뒤
            im = im.resize((int(w * 2160 / w), int(h * 2160 / w)), Image.LANCZOS)
            if im.height < 2700: im = im.resize((int(im.width * 2700 / im.height), 2700), Image.LANCZOS)
            x = (im.width - 2160) // 2; y = (im.height - 2700) // 2
            crop916(im.crop((x, y, x + 2160, y + 2700))).save(os.path.join(OUT, "bare", f))
    print("✓ 릴스 꽉 채움 판", n, "장 →", OUT)

if __name__ == "__main__":
    main()
