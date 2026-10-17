import os, httpx, re, json
from datetime import datetime, timezone
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36", "Accept-Language": "en-US,en;q=0.9"}
async def _syndication_profile(username: str):
    url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{username}"
    async with httpx.AsyncClient(headers=HEADERS, timeout=20, follow_redirects=True) as c:
        r = await c.get(url)
        if r.status_code != 200: return None, r.status_code
        return r.text, 200
def _parse_syndication(html: str):
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m: return None
    try: return json.loads(m.group(1))
    except: return None
async def account(username: str):
    username = username.lstrip("@").strip()
    if not username: return {"error": "Username kosong"}
    bearer = os.getenv("X_BEARER")
    if bearer: return await _account_via_api(username, bearer)
    html, status = await _syndication_profile(username)
    if status != 200 or not html: return {"error": f"Gagal akses X (HTTP {status})."}
    data = _parse_syndication(html)
    if not data: return {"error": "Gagal parse data X"}
    props = data.get("props", {}).get("pageProps", {}) or {}; timeline = props.get("timeline", {}) or {}; entries = timeline.get("entries", []) or []
    user = None
    for e in entries:
        u = (e.get("content", {}) or {}).get("tweet", {}).get("user", {}) or {}
        if u.get("screen_name", "").lower() == username.lower(): user = u; break
    if not user: return {"error": "Akun tidak ditemukan atau private"}
    created_iso = user.get("created_at"); age_days = None
    if created_iso:
        try:
            dt = datetime.strptime(created_iso, "%a %b %d %H:%M:%S %z %Y"); age_days = (datetime.now(timezone.utc) - dt).days; created_iso = dt.isoformat()
        except: pass
    return {"username": user.get("screen_name"), "nickname": user.get("name"), "followers": user.get("followers_count"), "following": user.get("friends_count"), "friends": user.get("friends_count"), "posts": user.get("statuses_count"), "likes": user.get("favourites_count"), "is_private": bool(user.get("protected", False)), "is_verified": bool(user.get("verified", False)), "bio": user.get("description", ""), "avatar": user.get("profile_image_url_https"), "location": user.get("location"), "created_at": created_iso, "account_age_days": age_days, "account_age_human": _human_age(age_days) if age_days is not None else None, "last_username_change": None, "last_nickname_change": None}
async def _account_via_api(username: str, bearer: str):
    url = f"https://api.twitter.com/2/users/by/username/{username}?user.fields=created_at,description,profile_image_url,protected,public_metrics,verified"
    headers = {"Authorization": f"Bearer {bearer}"}
    try:
        async with httpx.AsyncClient(headers=headers, timeout=20) as c: r = await c.get(url)
    except Exception as e: return {"error": f"Request gagal: {e}"}
    if r.status_code != 200: return {"error": f"API X: HTTP {r.status_code} — {r.text[:200]}"}
    u = r.json().get("data", {}); m = u.get("public_metrics", {}); created = u.get("created_at"); age_days = None
    if created:
        try:
            dt = datetime.fromisoformat(created.replace("Z", "+00:00")); age_days = (datetime.now(timezone.utc) - dt).days
        except: pass
    return {"username": u.get("username"), "nickname": u.get("name"), "followers": m.get("followers_count"), "following": m.get("following_count"), "friends": m.get("following_count"), "posts": m.get("tweet_count"), "likes": m.get("like_count"), "is_private": bool(u.get("protected", False)), "is_verified": bool(u.get("verified", False)), "bio": u.get("description", ""), "avatar": u.get("profile_image_url"), "created_at": created, "account_age_days": age_days, "account_age_human": _human_age(age_days) if age_days is not None else None, "last_username_change": None, "last_nickname_change": None}
def _human_age(days: int) -> str:
    years = days // 365; months = (days % 365) // 30
    if years > 0: return f"{years} tahun {months} bulan"
    if months > 0: return f"{months} bulan"
    return f"{days} hari"
async def check_username(username: str):
    username = username.lstrip("@").strip().lower()
    if not re.fullmatch(r"[a-z0-9_]{1,15}", username): return {"username": username, "available": False, "reason": "Format tidak valid"}
    html, status = await _syndication_profile(username)
    if status == 200 and html:
        data = _parse_syndication(html)
        if data:
            entries = ((data.get("props", {}).get("pageProps", {}) or {}).get("timeline", {}) or {}).get("entries", []) or []
            for e in entries:
                u = (e.get("content", {}) or {}).get("tweet", {}).get("user", {}) or {}
                if u.get("screen_name", "").lower() == username: return {"username": username, "available": False, "status": "sudah dipakai"}
    return {"username": username, "available": True, "status": "kemungkinan tersedia"}
async def download(url: str):
    m = re.search(r"/status/(\d+)", url)
    if not m: return {"error": "URL tweet tidak valid"}
    tweet_id = m.group(1)
    api = f"https://cdn.syndication.twimg.com/tweet-result?id={tweet_id}&lang=en"
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=20) as c: r = await c.get(api)
    except Exception as e: return {"error": f"Request gagal: {e}"}
    if r.status_code != 200: return {"error": f"HTTP {r.status_code}"}
    try: data = r.json()
    except: return {"error": "Gagal parse JSON tweet"}
    media = data.get("mediaDetails", []) or []; videos, photos = [], []
    for med in media:
        if med.get("type") == "video" or med.get("type") == "animated_gif":
            variants = (med.get("video_info", {}) or {}).get("variants", []) or []; mp4s = [v for v in variants if v.get("content_type") == "video/mp4"]
            if mp4s: mp4s.sort(key=lambda x: x.get("bitrate", 0), reverse=True); videos.append(mp4s[0]["url"])
        else: photos.append(med.get("media_url_https"))
    return {"id": tweet_id, "text": data.get("text"), "author": (data.get("user", {}) or {}).get("screen_name"), "author_name": (data.get("user", {}) or {}).get("name"), "created_at": data.get("created_at"), "videos": videos, "photos": photos, "likes": data.get("favorite_count"), "replies": data.get("conversation_count")}
async def hashtag(tag: str):
    tag = tag.lstrip("#").strip()
    if not tag: return {"error": "Hashtag kosong"}
    return {"tag": tag, "note": "X membatasi akses hashtag publik tanpa login.", "url": f"https://x.com/hashtag/{tag}"}
