import os, re, json
from datetime import datetime, timezone
from curl_cffi.requests import AsyncSession

async def download(url: str):
    vid_match = re.search(r"/video/(\d+)", url) or re.search(r"(\d{15,25})", url)
    if not vid_match: return {"error": "URL TikTok tidak valid"}
    vid = vid_match.group(1)
    
    api = f"https://api16-normal-c-useast1a.tiktokv.com/aweme/v1/feed/?aweme_id={vid}"
    async with AsyncSession() as s:
        try:
            r = await s.get(api, impersonate="chrome110", timeout=20)
            data = r.json()
        except Exception as e:
            return {"error": f"Request gagal: {e}"}

        awemes = data.get("aweme_list") or []
        if not awemes: return {"error": "Video tidak ditemukan / dibatasi region"}
        aweme = awemes[0]
        video = aweme.get("video", {}) or {}
        music = aweme.get("music", {}) or {}
        author = aweme.get("author", {}) or {}
        
        play = (video.get("play_addr") or {}).get("url_list") or []
        dl = (video.get("download_addr") or {}).get("url_list") or []
        cover = (video.get("cover") or {}).get("url_list") or []
        audio = (music.get("play_url") or {}).get("url_list") or []
        stats = aweme.get("statistics", {}) or {}

        return {
            "id": vid, "title": aweme.get("desc"), "author": author.get("unique_id"), 
            "author_nickname": author.get("nickname"), "duration": video.get("duration"), 
            "no_watermark": play[0] if play else None, "watermark": dl[0] if dl else None, 
            "thumbnail": cover[0] if cover else None, "audio": audio[0] if audio else None, 
            "music_title": music.get("title"), 
            "stats": {"plays": stats.get("play_count"), "likes": stats.get("digg_count"), "comments": stats.get("comment_count"), "shares": stats.get("share_count")}
        }

async def account(username: str):
    username = username.lstrip("@").strip()
    if not username: return {"error": "Username kosong"}

    url = f"https://www.tiktok.com/@{username}?lang=en"
    async with AsyncSession() as s:
        try:
            r = await s.get(url, impersonate="chrome110", timeout=25)
        except Exception as e:
            return {"error": f"Request gagal: {e}"}

        if r.status_code == 404: return {"error": "Akun tidak ditemukan"}
        if r.status_code != 200: return {"error": f"TikTok Error HTTP {r.status_code}"}

        m = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', r.text, re.S)
        if not m:
            return {"error": "Gagal parsing data. IP lu benar-benar diblokir TikTok, coba nyalakan VPN (server US/SG)."}
        
        try:
            data = json.loads(m.group(1))
        except Exception as e:
            return {"error": f"Gagal parsing JSON: {e}"}
            
        scope = data.get("__DEFAULT_SCOPE__", {})
        info = (scope.get("webapp.user-detail", {}) or {}).get("userInfo", {}) or {}
        
        if not info:
            return {"error": "Data user tidak ditemukan (akun private/kosong)."}

        user = info.get("user", {}) or {}
        stats = info.get("stats", {}) or {}

        create_ts = user.get("createTime")
        age_days = None
        created_iso = None
        if create_ts:
            try:
                dt = datetime.fromtimestamp(int(create_ts), tz=timezone.utc)
                created_iso = dt.isoformat()
                age_days = (datetime.now(timezone.utc) - dt).days
            except: pass

        return {
            "username": user.get("uniqueId"), "nickname": user.get("nickname"),
            "followers": stats.get("followerCount", 0), "following": stats.get("followingCount", 0),
            "friends": stats.get("friendCount", 0), "posts": stats.get("videoCount", 0),
            "likes": stats.get("heartCount", 0), "is_private": bool(user.get("privateAccount", False)),
            "is_verified": bool(user.get("verified", False)), "bio": user.get("signature", ""),
            "avatar": user.get("avatarLarger") or user.get("avatarMedium"),
            "created_at": created_iso, "account_age_days": age_days,
            "account_age_human": _human_age(age_days) if age_days is not None else None,
            "region": user.get("region"), "last_username_change": None, "last_nickname_change": None,
        }

def _human_age(days: int) -> str:
    years = days // 365; months = (days % 365) // 30
    if years > 0: return f"{years} tahun {months} bulan"
    if months > 0: return f"{months} bulan"
    return f"{days} hari"

async def check_username(username: str):
    username = username.lstrip("@").strip().lower()
    if not re.fullmatch(r"[a-z0-9._]{2,24}", username): 
        return {"username": username, "available": False, "reason": "Format tidak valid"}
    
    url = f"https://www.tiktok.com/@{username}"
    async with AsyncSession() as s:
        try:
            r = await s.get(url, impersonate="chrome110", timeout=20, allow_redirects=False)
        except Exception as e: 
            return {"username": username, "error": str(e)}

        if r.status_code == 404: return {"username": username, "available": True, "status": "tidak dipakai"}
        if r.status_code in (200, 301, 302): return {"username": username, "available": False, "status": "sudah dipakai"}
        return {"username": username, "available": None, "status": f"HTTP {r.status_code}"}

async def hashtag(tag: str):
    tag = tag.lstrip("#").strip()
    if not tag: return {"error": "Hashtag kosong"}
    api = f"https://www.tiktok.com/api/challenge/detail/?challengeName={tag}&aid=1988&app_language=en"
    async with AsyncSession() as s:
        try:
            r = await s.get(api, impersonate="chrome110", timeout=20)
            if r.status_code != 200: return {"error": f"HTTP {r.status_code}"}
            data = r.json()
        except Exception as e: return {"error": f"Request gagal: {e}"}
        
        ch = data.get("challengeInfo", {}).get("challenge", {}) or {}
        stats = data.get("challengeInfo", {}).get("stats", {}) or {}
        return {"tag": tag, "title": ch.get("cha_name"), "description": ch.get("desc"), "video_count": stats.get("videoCount"), "view_count": stats.get("viewCount"), "profile_url": f"https://www.tiktok.com/tag/{tag}"}
