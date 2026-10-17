import sqlite3
import os
from datetime import datetime
DB_PATH = os.path.join("data", "tracking.db")
def _conn():
    os.makedirs("data", exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con
def init_db():
    con = _conn()
    con.executescript("""
        CREATE TABLE IF NOT EXISTS snapshots (id INTEGER PRIMARY KEY AUTOINCREMENT, platform TEXT NOT NULL, username TEXT NOT NULL, nickname TEXT, followers INTEGER, following INTEGER, friends INTEGER, posts INTEGER, likes INTEGER, is_private INTEGER, is_verified INTEGER, bio TEXT, avatar TEXT, created_at TEXT, first_seen TEXT, last_seen TEXT, last_username_change TEXT, last_nickname_change TEXT, UNIQUE(platform, username));
        CREATE TABLE IF NOT EXISTS changes (id INTEGER PRIMARY KEY AUTOINCREMENT, platform TEXT NOT NULL, username TEXT NOT NULL, field TEXT NOT NULL, old_value TEXT, new_value TEXT, changed_at TEXT);
        CREATE INDEX IF NOT EXISTS idx_changes_lookup ON changes(platform, username);
    """)
    con.commit(); con.close()
def _get_or_none(con, platform, username): return con.execute("SELECT * FROM snapshots WHERE platform=? AND username=?", (platform, username)).fetchone()
def track_account(platform: str, data: dict):
    con = _conn(); now = datetime.utcnow().isoformat(); username = data.get("username")
    if not username: con.close(); return
    row = _get_or_none(con, platform, username)
    if row is None:
        con.execute("INSERT INTO snapshots (platform, username, nickname, followers, following, friends, posts, likes, is_private, is_verified, bio, avatar, created_at, first_seen, last_seen, last_username_change, last_nickname_change) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (platform, username, data.get("nickname"), data.get("followers"), data.get("following"), data.get("friends"), data.get("posts"), data.get("likes"), int(bool(data.get("is_private"))), int(bool(data.get("is_verified"))), data.get("bio"), data.get("avatar"), data.get("created_at"), now, now, None, None))
        data["last_username_change"] = None; data["last_nickname_change"] = None; data["first_seen"] = now
    else:
        fields = ["nickname", "followers", "following", "friends", "posts", "likes", "is_private", "bio"]
        for f in fields:
            old, new = row[f], data.get(f)
            if old != new and not (old is None and new is None):
                con.execute("INSERT INTO changes (platform, username, field, old_value, new_value, changed_at) VALUES (?,?,?,?,?,?)", (platform, username, f, str(old), str(new), now))
                if f == "nickname": con.execute("UPDATE snapshots SET last_nickname_change=? WHERE platform=? AND username=?", (now, platform, username)); data["last_nickname_change"] = now
                if f == "username": con.execute("UPDATE snapshots SET last_username_change=? WHERE platform=? AND username=?", (now, platform, username)); data["last_username_change"] = now
        con.execute("UPDATE snapshots SET nickname=?, followers=?, following=?, friends=?, posts=?, likes=?, is_private=?, is_verified=?, bio=?, avatar=?, last_seen=? WHERE platform=? AND username=?", (data.get("nickname"), data.get("followers"), data.get("following"), data.get("friends"), data.get("posts"), data.get("likes"), int(bool(data.get("is_private"))), int(bool(data.get("is_verified"))), data.get("bio"), data.get("avatar"), now, platform, username))
        data["last_username_change"] = data.get("last_username_change") or row["last_username_change"]; data["last_nickname_change"] = data.get("last_nickname_change") or row["last_nickname_change"]; data["first_seen"] = row["first_seen"]
    con.commit(); con.close()
def get_history(platform: str = None, username: str = None):
    con = _conn(); q = "SELECT * FROM changes WHERE 1=1"; args = []
    if platform: q += " AND platform=?"; args.append(platform)
    if username: q += " AND username=?"; args.append(username)
    q += " ORDER BY changed_at DESC LIMIT 200"
    rows = con.execute(q, args).fetchall(); con.close(); return [dict(r) for r in rows]
def get_tracked():
    con = _conn(); rows = con.execute("SELECT platform, username, nickname, followers, last_seen FROM snapshots ORDER BY last_seen DESC").fetchall(); con.close(); return [dict(r) for r in rows]
