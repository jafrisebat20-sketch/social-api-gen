import os, re, json
from curl_cffi.requests import AsyncSession

async def _web_profile(username: str):
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    headers = {
        "X-IG-App-ID": "936619743392459",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
    }
    sessionid = os.getenv("IG_SESSIONID")
    if sessionid:
        headers["Cookie"] = f"sessionid={sessionid}"
        
    async with AsyncSession() as s:
        r = await s.get(url, headers=headers, impersonate="chrome110", timeout=20)
        if r.status_code != 200:
            return None, r.status_code
        try: return r.json(), 200
        except: return None, r.status_code

async def account(username: str):
    username = username.lstrip("@").strip()
    if not username: return {"error": "Username kosong"}

    data, status = await _web_profile(username)
    if status == 404: return {"error": "Akun tidak ditemukan"}
    if not data or "data" not in data or not data["data"].get("user"): 
        return {"error": f"Gagal mengambil data (HTTP {status}). Akun private/kosong, atau IP diblokir IG."}

    u = data["data"]["user"]
    return {
        "username": u.get("username"), "nickname": u.get("full_name"),
        "followers": u.get("edge_followed_by", {}).get("count", 0), 
        "following": u.get("edge_follow", {}).get("count", 0),
        "friends": None, 
        "posts": u.get("edge_owner_to_timeline_media", {}).get("count", 0), 
        "likes": None,
        "is_private": bool(u.get("is_private", False)), 
        "is_verified": bool(u.get("is_verified", False)),
        "is_business": bool(u.get("is_business_account", False)), 
        "bio": u.get("biography", ""),
        "avatar": u.get("profile_pic_url_hd") or u.get("profile_pic_url"),
        "external_url": u.get("external_url"), "category": u.get("category_name"),
        "created_at": None, "account_age_days": None, "account_age_human": None,
        "last_username_change": None, "last_nickname_change": None,
    }

async def check_username(username: str):
    username = username.lstrip("@").strip().lower()
    if not re.fullmatch(r"[a-z0-9._]{1,30}", username): 
        return {"username": username, "available": False, "reason": "Format tidak valid"}
    
    data, status = await _web_profile(username)
    if status == 404 or (data and not data.get("data", {}).get("user")): 
        return {"username": username, "available": True, "status": "tidak dipakai"}
    if status == 200 and data and data.get("data", {}).get("user"): 
        return {"username": username, "available": False, "status": "sudah dipakai"}
    return {"username": username, "available": None, "status": f"HTTP {status}"}

async def download(url: str):
    m = re.search(r"/(p|reel|reels|tv)/([A-Za-z0-9_-]+)", url)
    if not m: return {"error": "URL Instagram tidak valid"}
    shortcode = m.group(2)

    # Tembak langsung ke halaman utama (bukan /embed/)
    target_url = f"https://www.instagram.com/reel/{shortcode}/"
    async with AsyncSession() as s:
        try:
            r = await s.get(target_url, impersonate="chrome110", timeout=20)
        except Exception as e:
            return {"error": f"Request gagal: {e}"}

        if r.status_code != 200:
            return {"error": f"IG Error HTTP {r.status_code}. Coba ganti VPN."}

        html = r.text
        # Ambil URL dari tag meta Open Graph
        video = re.search(r'<meta property="og:video" content="([^"]+)"', html)
        image = re.search(r'<meta property="og:image" content="([^"]+)"', html)
        caption = re.search(r'<meta property="og:title" content="([^"]+)"', html)

        def clean(u):
            if not u: return None
            return u.replace("&amp;", "&").replace("\\u0026", "&")

        return {
            "shortcode": shortcode,
            "type": "video" if video else ("image" if image else "unknown"),
            "video_url": clean(video.group(1)) if video else None,
            "image_url": clean(image.group(1)) if image else None,
            "caption": clean(caption.group(1)) if caption else None,
        }

async def hashtag(tag: str):
    tag = tag.lstrip("#").strip().lower()
    if not tag: return {"error": "Hashtag kosong"}
    
    # IG sangat ketat untuk hashtag tanpa login
    return {
        "tag": tag, 
        "note": "IG membatasi akses hashtag publik tanpa login. Fitur ini butuh IG_SESSIONID di file .env.", 
        "profile_url": f"https://www.instagram.com/explore/tags/{tag}/"
    }
