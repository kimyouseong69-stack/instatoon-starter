#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""인스타그램 업로드 — 캐러셀(이미지 여러 장) · 릴스(mp4). Instagram API with Instagram Login.

    python3 samples/엔진/upload/ig_publish.py whoami                                   # 토큰이 어느 계정 건지 확인
    python3 samples/엔진/upload/ig_publish.py carousel <편 폴더> --caption <편 폴더>/캡션.md            # 미리보기만
    python3 samples/엔진/upload/ig_publish.py carousel <편 폴더> --caption <편 폴더>/캡션.md --check    # 인스타가 파일을 가져가는지만 시험(게시 안 함)
    python3 samples/엔진/upload/ig_publish.py carousel <편 폴더> --caption <편 폴더>/캡션.md --publish  # 실제 게시
    python3 samples/엔진/upload/ig_publish.py reel <편 폴더>/reel/reel.mp4 --caption <편 폴더>/캡션.md --publish

안전장치
  · 토큰은 .env 의 IG_ACCESS_TOKEN 에서만 읽고, 화면·로그에 절대 찍지 않는다.
  · --publish 를 붙이지 않으면 게시하지 않는다. 붙여도 「@계정 에 올립니다」 확인을 한 번 더 받는다(--yes 로 생략).

인스타는 「인터넷 주소(URL)」에 있는 파일만 가져간다(내 컴퓨터 파일을 직접 못 보냄). 그래서 잠깐 공개 주소를 만든다:
  --host tunnel (기본) : cloudflared 임시 터널. 계정·결제 없이 바로. 끝나면 주소가 사라진다.
  --host r2            : 내 Cloudflare R2 버킷(.env 의 R2_*). 가장 안정적. pip install boto3 필요.
  --host url --base-url https://… : 이미 파일을 올려 둔 주소가 있을 때.
"""
import argparse, json, os, re, shutil, socket, subprocess, sys, tempfile, threading, time, uuid
import http.server, functools
from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
API = "https://graph.instagram.com/v25.0"


# ------------------------------------------------------------------ 토큰
def env(name):
    v = os.environ.get(name)
    if v: return v.strip()
    f = ROOT / ".env"
    if f.exists():
        for ln in f.read_text(encoding="utf-8").splitlines():
            if ln.startswith(name + "="):
                return ln.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def token():
    t = env("IG_ACCESS_TOKEN")
    if not t: sys.exit("❌ .env 에 IG_ACCESS_TOKEN 이 비어 있습니다 — docs/02_인스타_API_연결.md 참고")
    if not t.startswith("IG"): print("⚠️ 토큰 모양이 Instagram Login 토큰(IG…)이 아닙니다. 페이스북 로그인 토큰이면 이 스크립트로는 안 됩니다.")
    return t


def call(method, path, **params):
    params["access_token"] = token()
    r = requests.request(method, API + path, params=params if method == "GET" else None,
                         data=params if method != "GET" else None, timeout=120)
    try: j = r.json()
    except ValueError: j = {}
    if r.status_code != 200 or "error" in j:
        e = j.get("error", {})
        msg = e.get("error_user_msg") or e.get("message") or r.text[:300]
        code = f"{e.get('code', r.status_code)}/{e.get('error_subcode', '-')}"
        hint = HINTS.get(str(e.get("error_subcode"))) or HINTS.get(str(e.get("code")), "")
        sys.exit(f"❌ 인스타 API 오류 {code}: {msg}\n   {hint}")
    return j


HINTS = {
    "2207052": "인스타가 파일 주소를 못 열었습니다 → 다른 --host 로 다시(예: r2), 파일 주소를 브라우저로 열어 보세요.",
    "9004": "인스타가 파일 주소를 못 열었습니다 → 다른 --host 로 다시(예: r2).",
    "2207009": "이미지 비율이 4:5 ~ 1.91:1 밖입니다.",
    "2207004": "이미지가 8MB 를 넘습니다.",
    "2207026": "영상 형식 문제 → H.264/AAC mp4 로.",
    "2207050": "계정이 제한 상태입니다 → 인스타 앱에 로그인해서 요구하는 확인(생일·전화 인증 등)을 끝내세요.",
    "2207051": "짧은 시간에 너무 많이 올려 스팸 의심 → 잠시 뒤에.",
    "190": "토큰이 만료됐거나 잘못됐습니다 → 앱 대시보드에서 다시 발급(60일짜리).",
    "10": "권한이 없습니다 → 토큰 만들 때 instagram_business_content_publish 권한이 켜져 있어야 합니다.",
}


def whoami():
    me = call("GET", "/me", fields="user_id,username,account_type")
    return me


# ------------------------------------------------------------------ 파일 준비(영문 이름·JPEG)
def prepare(files, work, kind):
    out = []
    for i, f in enumerate(files, 1):
        f = Path(f)
        if kind == "image":
            dst = work / f"card{i:02d}.jpg"
            im = Image.open(f).convert("RGB")
            w, h = im.size
            if not (0.8 - 1e-3 <= w / h <= 1.91): sys.exit(f"❌ {f.name}: 비율 {w}x{h} — 인스타 캐러셀은 4:5 ~ 1.91:1")
            im.save(dst, "JPEG", quality=92)               # 인스타는 JPEG 만 받는다
        else:
            dst = work / "reel.mp4"; shutil.copy(f, dst)
        out.append(dst)
    return out


# ------------------------------------------------------------------ 공개 주소 만들기
class Tunnel:
    """내 컴퓨터 폴더를 잠깐 인터넷 주소로 — 파이썬 웹서버 + cloudflared 임시 터널."""
    def __init__(self, folder):
        if not shutil.which("cloudflared"): sys.exit("❌ cloudflared 가 없습니다 → brew install cloudflared")
        s = socket.socket(); s.bind(("127.0.0.1", 0)); self.port = s.getsockname()[1]; s.close()
        h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(folder))
        http.server.SimpleHTTPRequestHandler.log_message = lambda *a: None
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", self.port), h)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.p = subprocess.Popen(["cloudflared", "tunnel", "--no-autoupdate", "--url", f"http://127.0.0.1:{self.port}"],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        self.base = None; t0 = time.time()
        while time.time() - t0 < 40:
            ln = self.p.stderr.readline()
            m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", ln or "")
            if m: self.base = m.group(0); break
        if not self.base: self.close(); sys.exit("❌ 임시 터널 주소를 못 받았습니다. 인터넷 연결 확인 후 다시, 또는 --host r2")
        print("  임시 주소:", self.base, "(끝나면 사라집니다)")

    def url(self, f): return f"{self.base}/{f.name}"

    def wait_ready(self, f):
        # 새 주소가 인터넷에 퍼지는 데 몇 초 걸린다. 내 컴퓨터에서만 안 열리는 경우(IPv6·DNS 캐시)도 있어
        # 여기서 실패해도 멈추지 않는다 — 진짜 시험은 인스타가 가져가는지(--check)다.
        for _ in range(8):
            try:
                if requests.head(self.url(f), timeout=8).status_code == 200: return
            except requests.RequestException: pass
            time.sleep(2)
        print("  ⚠️ 내 컴퓨터에서는 임시 주소가 아직 안 열립니다(흔함). 인스타 쪽에서 가져가는지로 확인합니다.")
        time.sleep(5)

    def close(self):
        try: self.p.terminate()
        except Exception: pass
        self.httpd.shutdown()


class R2:
    """내 Cloudflare R2 버킷에 올리고 1시간짜리 서명 주소를 만든다. 끝나면 지운다."""
    def __init__(self, folder):
        try: import boto3
        except ImportError: sys.exit("❌ pip install boto3 가 필요합니다")
        need = ["R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET"]
        miss = [k for k in need if not env(k)]
        if miss: sys.exit("❌ .env 에 비어 있음: " + ", ".join(miss))
        self.b = env("R2_BUCKET"); self.pre = f"ig-tmp/{uuid.uuid4().hex[:10]}/"
        self.s3 = boto3.client("s3", endpoint_url=f"https://{env('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
                               aws_access_key_id=env("R2_ACCESS_KEY_ID"), aws_secret_access_key=env("R2_SECRET_ACCESS_KEY"),
                               region_name="auto")
        self.keys = []

    def put(self, f):
        k = self.pre + f.name
        ct = "image/jpeg" if f.suffix == ".jpg" else "video/mp4"
        self.s3.upload_file(str(f), self.b, k, ExtraArgs={"ContentType": ct}); self.keys.append(k)

    def url(self, f):
        return self.s3.generate_presigned_url("get_object", Params={"Bucket": self.b, "Key": self.pre + f.name}, ExpiresIn=3600)

    def wait_ready(self, f): pass

    def close(self):
        for k in self.keys:
            try: self.s3.delete_object(Bucket=self.b, Key=k)
            except Exception: pass


class Given:
    def __init__(self, base): self.base = base.rstrip("/")
    def url(self, f): return f"{self.base}/{f.name}"
    def wait_ready(self, f): pass
    def close(self): pass


# ------------------------------------------------------------------ 게시
def wait_finished(cid, label):
    for k in range(40):                                           # 최대 약 10분
        st = call("GET", f"/{cid}", fields="status_code,status").get("status_code")
        if st == "FINISHED": return
        if st in ("ERROR", "EXPIRED"):
            sys.exit(f"❌ {label} 처리 실패({st}) — 영상이면 H.264/AAC mp4·3초 이상·300MB 이하인지 확인")
        print(f"  … {label} 처리 중({st})"); time.sleep(15)
    sys.exit(f"❌ {label} 처리가 너무 오래 걸립니다. 잠시 뒤 다시.")


def main():
    ap = argparse.ArgumentParser(description="인스타 업로드(캐러셀·릴스)")
    ap.add_argument("kind", choices=["whoami", "carousel", "reel", "limit"])
    ap.add_argument("target", nargs="?", help="carousel=편 폴더(card*.png) 또는 이미지들이 든 폴더 / reel=mp4 파일")
    ap.add_argument("--caption", help="캡션 파일(.md/.txt)")
    ap.add_argument("--host", choices=["tunnel", "r2", "url"], default="tunnel")
    ap.add_argument("--base-url")
    ap.add_argument("--check", action="store_true", help="인스타가 파일을 가져가는지만 시험(게시 안 함)")
    ap.add_argument("--publish", action="store_true", help="실제 게시")
    ap.add_argument("--yes", action="store_true", help="게시 전 확인 질문 생략")
    a = ap.parse_args()

    me = whoami()
    print(f"계정: @{me.get('username')} ({me.get('account_type', '?')})")
    if a.kind == "whoami": return
    ig = me.get("user_id") or me.get("id")
    if a.kind == "limit":
        print(json.dumps(call("GET", f"/{ig}/content_publishing_limit", fields="quota_usage,config"), ensure_ascii=False, indent=1)); return
    if not a.target: sys.exit("❌ 올릴 대상(편 폴더 또는 mp4)을 적어 주세요")

    t = Path(a.target)
    if a.kind == "carousel":
        files = sorted(t.glob("card*.png"), key=lambda p: int(re.sub(r"\D", "", p.stem) or 0)) if t.is_dir() else []
        if not files and t.is_dir(): files = sorted([p for p in t.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg")])
        if not 2 <= len(files) <= 10:
            sys.exit(f"❌ 캐러셀은 2~10장입니다(지금 {len(files)}장). 인스타 API 한도가 10장이라 더 많으면 나눠서 올리세요.")
    else:
        files = [t]
        if t.suffix.lower() != ".mp4" or not t.exists(): sys.exit("❌ 릴스는 mp4 파일 경로를 주세요")
    caption = Path(a.caption).read_text(encoding="utf-8").strip() if a.caption else ""
    if len(caption) > 2200: sys.exit("❌ 캡션은 2,200자 이내")

    print(f"올릴 것: {a.kind} · {len(files)}개 파일 · 캡션 {len(caption)}자")
    for f in files: print("  -", f)
    if not (a.check or a.publish):
        print("\n(미리보기만 했습니다. 인스타가 가져가는지 시험 = --check, 실제 게시 = --publish)"); return
    if a.publish and not a.yes:
        if input(f"\n@{me.get('username')} 계정에 실제로 올립니다. 계속할까요? (y/N) ").strip().lower() != "y":
            print("취소했습니다."); return

    work = Path(tempfile.mkdtemp(prefix="igpub_"))
    host = None
    try:
        prepped = prepare(files, work, "image" if a.kind == "carousel" else "video")
        host = Tunnel(work) if a.host == "tunnel" else R2(work) if a.host == "r2" else Given(a.base_url or sys.exit("--base-url 필요"))
        if isinstance(host, R2):
            for f in prepped: host.put(f)
        for f in prepped: host.wait_ready(f)

        if a.kind == "carousel":
            kids = []
            for i, f in enumerate(prepped, 1):
                c = call("POST", f"/{ig}/media", image_url=host.url(f), is_carousel_item="true")
                kids.append(c["id"]); print(f"  ✓ {i}/{len(prepped)} 장 받아 감")
            if a.check: print("\n✅ 시험 통과 — 인스타가 파일을 전부 가져갔습니다(게시는 안 함)."); return
            for k in kids: wait_finished(k, "이미지")
            parent = call("POST", f"/{ig}/media", media_type="CAROUSEL", children=",".join(kids), caption=caption)["id"]
            wait_finished(parent, "캐러셀")
        else:
            parent = call("POST", f"/{ig}/media", media_type="REELS", video_url=host.url(prepped[0]), caption=caption, share_to_feed="true")["id"]
            print("  ✓ 영상 받아 가는 중")
            wait_finished(parent, "릴스")
            if a.check: print("\n✅ 시험 통과 — 인스타가 영상을 가져가 처리까지 끝냈습니다(게시는 안 함)."); return
        pub = call("POST", f"/{ig}/media_publish", creation_id=parent)
        link = call("GET", f"/{pub['id']}", fields="permalink").get("permalink", "")
        print(f"\n🎉 게시 완료: {link}")
    finally:
        if host: host.close()
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
