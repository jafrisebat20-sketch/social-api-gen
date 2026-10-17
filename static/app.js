let CONFIG = { app_name: "Ryuu Social API", developer_name: "Ryuu", developer_handle: "ryuuwaguri", base_url: "https://api.ryuuwaguri.com", contact_email: "jafrisebat20@gmail.com", developer_tiktok: "https://tiktok.com/@ryuu.ndivision", version: "1.0.0" };
const REQUEST_ORIGIN = window.location.origin;
const APIS = {
    tiktok: [
        { name: "Downloader", desc: "Ambil video, audio, thumbnail dari URL TikTok.", endpoint: "/api/tiktok/downloader", param: "url", paramLabel: "URL TikTok" },
        { name: "Detail Akun", desc: "Followers, following, friends, video, likes, status private, umur akun.", endpoint: "/api/tiktok/account", param: "username", paramLabel: "Username (tanpa @)" },
        { name: "Cek Username", desc: "Cek ketersediaan username TikTok.", endpoint: "/api/tiktok/check", param: "username", paramLabel: "Username" },
        { name: "Statistik Hashtag", desc: "Total views dan jumlah video hashtag TikTok.", endpoint: "/api/tiktok/hashtag", param: "tag", paramLabel: "Nama hashtag" }
    ],
    instagram: [
        { name: "Downloader", desc: "Ambil media foto/video/reel dari URL Instagram.", endpoint: "/api/instagram/downloader", param: "url", paramLabel: "URL Instagram" },
        { name: "Detail Akun", desc: "Followers, following, posts, status private, bio.", endpoint: "/api/instagram/account", param: "username", paramLabel: "Username" },
        { name: "Cek Username", desc: "Cek ketersediaan username Instagram.", endpoint: "/api/instagram/check", param: "username", paramLabel: "Username" },
        { name: "Statistik Hashtag", desc: "Jumlah post dan info hashtag Instagram.", endpoint: "/api/instagram/hashtag", param: "tag", paramLabel: "Nama hashtag" }
    ],
    x: [
        { name: "Downloader", desc: "Ambil media (video/foto) dari URL tweet.", endpoint: "/api/x/downloader", param: "url", paramLabel: "URL Tweet" },
        { name: "Detail Akun", desc: "Followers, following, tweets, likes, umur akun.", endpoint: "/api/x/account", param: "username", paramLabel: "Username" },
        { name: "Cek Username", desc: "Cek ketersediaan username X.", endpoint: "/api/x/check", param: "username", paramLabel: "Username" },
        { name: "Statistik Hashtag", desc: "Info hashtag X.", endpoint: "/api/x/hashtag", param: "tag", paramLabel: "Nama hashtag" }
    ],
    tracking: [
        { name: "Riwayat Perubahan", desc: "Riwayat perubahan field akun yang pernah dilacak.", endpoint: "/api/tracking/history", param: null },
        { name: "Daftar Akun Dilacak", desc: "Daftar semua akun yang pernah dilacak.", endpoint: "/api/tracking/list", param: null }
    ]
};
let currentPlatform = "tiktok";
let currentAPI = null;
async function loadConfig() {
    try { const r = await fetch("/api/config"); if (r.ok) { const data = await r.json(); CONFIG = { ...CONFIG, ...data }; } } catch (e) { console.warn("Config fetch gagal:", e); }
    applyConfig();
}
function applyConfig() {
    document.title = CONFIG.app_name;
    const el = (id) => document.getElementById(id);
    if (el("appName")) el("appName").textContent = CONFIG.app_name;
    if (el("devName")) el("devName").textContent = CONFIG.developer_name;
    if (el("devHandle")) el("devHandle").textContent = "@" + CONFIG.developer_handle;
    if (el("baseUrl")) el("baseUrl").textContent = CONFIG.base_url;
    const tiktokEl = el("devTiktok");
    if (tiktokEl && CONFIG.developer_tiktok) { tiktokEl.href = CONFIG.developer_tiktok; tiktokEl.title = "TikTok developer: " + CONFIG.developer_tiktok; }
    if (el("footerText")) el("footerText").textContent = "© " + CONFIG.app_name;
    if (el("footerContact")) { el("footerContact").textContent = CONFIG.contact_email; el("footerContact").href = "mailto:" + CONFIG.contact_email; }
    if (el("footerTiktok") && CONFIG.developer_tiktok) { el("footerTiktok").href = CONFIG.developer_tiktok; el("footerTiktok").textContent = "@" + CONFIG.developer_tiktok.split("/").pop(); }
}
function renderCards() {
    const content = document.getElementById("content");
    const apis = APIS[currentPlatform];
    content.innerHTML = "";
    apis.forEach((api) => {
        const card = document.createElement("div");
        card.className = "card";
        const displayUrl = CONFIG.base_url + api.endpoint + (api.param ? `?${api.param}=...` : "");
        card.innerHTML = `<span class="card-method">GET</span><div class="card-title">${api.name}</div><div class="card-desc">${api.desc}</div><div class="card-endpoint">${displayUrl}</div>`;
        card.addEventListener("click", () => openModal(api));
        content.appendChild(card);
    });
}
function openModal(api) {
    currentAPI = api;
    document.getElementById("modalTitle").textContent = api.name;
    document.getElementById("result").textContent = "";
    const requestLine = document.getElementById("requestLine");
    const displayUrl = CONFIG.base_url + api.endpoint + (api.param ? `?${api.param}=...` : "");
    requestLine.innerHTML = `<span class="method">GET</span>${displayUrl}`;
    requestLine.classList.add("show");
    const input = document.getElementById("paramInput");
    const label = document.getElementById("paramLabel");
    if (api.param) { label.style.display = "block"; input.style.display = "block"; input.value = ""; label.textContent = api.paramLabel; input.focus(); }
    else { label.style.display = "none"; input.style.display = "none"; }
    document.getElementById("modal").classList.add("active");
}
document.getElementById("modalClose").addEventListener("click", () => document.getElementById("modal").classList.remove("active"));
document.getElementById("modal").addEventListener("click", (e) => { if (e.target.id === "modal") document.getElementById("modal").classList.remove("active"); });
document.getElementById("runBtn").addEventListener("click", async () => {
    if (!currentAPI) return;
    const btn = document.getElementById("runBtn"), result = document.getElementById("result"), input = document.getElementById("paramInput");
    let url = REQUEST_ORIGIN + currentAPI.endpoint;
    if (currentAPI.param) {
        const val = input.value.trim();
        if (!val) { result.textContent = "Parameter wajib diisi."; return; }
        url += `?${currentAPI.param}=${encodeURIComponent(val)}`;
    }
    btn.disabled = true; btn.textContent = "Loading..."; result.textContent = "Mengambil data...";
    try {
        const r = await fetch(url); const data = await r.json();
        result.textContent = JSON.stringify(data, null, 2);
    } catch (e) { result.textContent = "Error: " + e.message; }
    finally { btn.disabled = false; btn.textContent = "Jalankan"; }
});
document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
        document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
        tab.classList.add("active"); currentPlatform = tab.dataset.platform; renderCards();
    });
});
(async () => { await loadConfig(); renderCards(); })();
