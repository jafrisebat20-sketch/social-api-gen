import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from scrapers import tiktok, instagram, x as xscraper
from database import init_db, track_account, get_history, get_tracked
from config import load_config
app = FastAPI(title="Ryuu Social API", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
init_db()
@app.get("/api/config")
async def get_config():
    cfg = load_config()
    return {"app_name": cfg["app_name"], "developer_name": cfg["developer_name"], "developer_handle": cfg["developer_handle"], "base_url": cfg["base_url"].rstrip("/"), "contact_email": cfg.get("contact_email"), "developer_tiktok": cfg.get("developer_tiktok"), "version": "1.0.0"}
@app.get("/api/tiktok/downloader")
async def tiktok_downloader(url: str): return await tiktok.download(url)
@app.get("/api/tiktok/account")
async def tiktok_account(username: str):
    data = await tiktok.account(username)
    if "error" in data: raise HTTPException(status_code=404, detail=data["error"])
    track_account("tiktok", data); return data
@app.get("/api/tiktok/check")
async def tiktok_check(username: str): return await tiktok.check_username(username)
@app.get("/api/tiktok/hashtag")
async def tiktok_hashtag(tag: str): return await tiktok.hashtag(tag)
@app.get("/api/instagram/downloader")
async def instagram_downloader(url: str): return await instagram.download(url)
@app.get("/api/instagram/account")
async def instagram_account(username: str):
    data = await instagram.account(username)
    if "error" in data: raise HTTPException(status_code=404, detail=data["error"])
    track_account("instagram", data); return data
@app.get("/api/instagram/check")
async def instagram_check(username: str): return await instagram.check_username(username)
@app.get("/api/instagram/hashtag")
async def instagram_hashtag(tag: str): return await instagram.hashtag(tag)
@app.get("/api/x/downloader")
async def x_downloader(url: str): return await xscraper.download(url)
@app.get("/api/x/account")
async def x_account(username: str):
    data = await xscraper.account(username)
    if "error" in data: raise HTTPException(status_code=404, detail=data["error"])
    track_account("x", data); return data
@app.get("/api/x/check")
async def x_check(username: str): return await xscraper.check_username(username)
@app.get("/api/x/hashtag")
async def x_hashtag(tag: str): return await xscraper.hashtag(tag)
@app.get("/api/tracking/history")
async def tracking_history(platform: str = None, username: str = None): return get_history(platform, username)
@app.get("/api/tracking/list")
async def tracking_list(): return get_tracked()
app.mount("/", StaticFiles(directory="static", html=True), name="static")
if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0"); port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
