#!/usr/bin/env python3
"""
🐸 Brainrot Animal Video Agent
Génère et publie automatiquement une vidéo brainrot animaux toutes les 2h sur YouTube
Railway 24/7 deployment
"""

import os, time, subprocess, urllib.request, logging, random, threading
from datetime import datetime, timedelta
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger("brainrot")

# ─── CONFIG (depuis variables d'environnement Railway) ─────────────────────────
GEMINI_API_KEY  = os.environ["GEMINI_API_KEY"]
YOUTUBE_CLIENT_ID = os.environ["YOUTUBE_CLIENT_ID"]
YOUTUBE_SECRET    = os.environ["YOUTUBE_SECRET"]
YOUTUBE_REFRESH   = os.environ["YOUTUBE_REFRESH"]
RESEND_API_KEY  = os.environ["RESEND_API_KEY"]
NOTIFY_EMAIL    = os.environ.get("NOTIFY_EMAIL", "paulsentenac8@gmail.com")
INTERVAL_HOURS  = float(os.environ.get("INTERVAL_HOURS", "2"))
NB_CLIPS        = int(os.environ.get("NB_CLIPS", "4"))   # 4 clips = ~32s, rapide

# ─── CLIPS ────────────────────────────────────────────────────────────────────
ALL_CLIPS = [
    ("Grenouille", "Ultra colorful brainrot short for kids. Cute cartoon frog in sunglasses skateboarding in supermarket. Fast cuts, neon colors, rainbow sparkles. Bold text: SIGMA FROG, NO CAP. 9:16 vertical TikTok style."),
    ("Canard",     "Kids brainrot. Cute cartoon duck with party hat flying in candy store, bumping giant lollipops. Neon explosions, fast zooms. Bold text: SKIBIDI DUCK, GYATT. 9:16."),
    ("Chat",       "Brainrot kids. Chubby cartoon cat in astronaut suit floating in space eating pizza. Cheese planets. Bold text: NPC MODE, FANUM TAX. 9:16."),
    ("Panda",      "Kids brainrot. Cartoon panda griddy dancing on giant birthday cake. Sprinkles, rainbow. Bold text: OHIO PANDA, RIZZ UNLOCKED. 9:16."),
    ("Renard",     "Silly kids. Cartoon fox in sunglasses driving watermelon race car through jungle. Bold text: SIGMA FOX. 9:16 TikTok."),
    ("Ours",       "Kids brainrot. Cartoon bear eating enormous pancake stack growing taller. Bold text: SLAY BESTIE. 9:16."),
    ("Pingouin",   "Brainrot short. Cute cartoon penguin breakdancing on giant ice cream sundae. Bold text: SKIBIDI PENGUIN. 9:16."),
    ("Licorne",    "Kids brainrot. Cartoon unicorn running through rainbow portal exploding in confetti. Bold text: UNICORN OHIO, W RIZZ. 9:16."),
    ("Hamster",    "Ultra silly kids. Cartoon hamster spinning in wheel that goes to the moon. Glitter explosions. Bold text: SIGMA HAMSTER. 9:16."),
    ("Lapin",      "Kids brainrot. Cartoon rabbit eating giant carrot that shoots rainbows everywhere. Bold text: OHIO BUNNY. 9:16."),
    ("Tigre",      "Brainrot kids. Cartoon tiger doing backflips in a candy factory. Neon colors. Bold text: SIGMA TIGER. 9:16."),
    ("Koala",      "Kids silly. Cartoon koala sleeping on cloud that starts flying super fast. Bold text: NPC KOALA. 9:16."),
]

BRAINROT_WORDS  = ["SIGMA","OHIO","SKIBIDI","NPC","GYATT","RIZZ","FANUM TAX","SLAY","NO CAP","W RIZZ","BASED","GLAZING"]
ANIMALS_EMOJI   = {"Grenouille":"🐸","Canard":"🦆","Chat":"🐱","Panda":"🐼","Renard":"🦊","Ours":"🐻","Pingouin":"🐧","Licorne":"🦄","Hamster":"🐹","Lapin":"🐰","Tigre":"🐯","Koala":"🐨"}

COUNTER_FILE    = "/tmp/video_count.txt"

# ─── VEO 3 ────────────────────────────────────────────────────────────────────
VEO_URL = "https://generativelanguage.googleapis.com/v1beta/models/veo-3.0-generate-001:predictLongRunning"

def veo_launch(prompt):
    r = requests.post(
        f"{VEO_URL}?key={GEMINI_API_KEY}",
        json={"instances":[{"prompt":prompt}],"parameters":{"aspectRatio":"9:16","durationSeconds":8,"resolution":"720p","negativePrompt":"violence, scary, dark, adult, boring"}},
        timeout=30
    )
    r.raise_for_status()
    return r.json().get("name","")

def veo_poll(op, max_wait=300):
    url = f"https://generativelanguage.googleapis.com/v1beta/{op}?key={GEMINI_API_KEY}"
    deadline = time.time() + max_wait
    while time.time() < deadline:
        r = requests.get(url, timeout=20)
        data = r.json()
        if data.get("done"):
            videos = data.get("response",{}).get("videos",[])
            if videos:
                return videos[0].get("uri","")
        time.sleep(15)
    return ""

# ─── YOUTUBE ──────────────────────────────────────────────────────────────────
def youtube_upload(filepath, title, description, tags):
    """Upload via YouTube Data API v3 avec resumable upload"""
    size = os.path.getsize(filepath)
    # 1. Init resumable upload
    meta = {
        "snippet": {"title": title, "description": description, "tags": tags, "categoryId": "22"},
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": True}
    }
    init_r = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        headers={
            "Authorization": f"Bearer {YOUTUBE_TOKEN}",
            "Content-Type": "application/json",
            "X-Upload-Content-Type": "video/mp4",
            "X-Upload-Content-Length": str(size)
        },
        json=meta, timeout=30
    )
    if init_r.status_code not in (200, 201):
        raise Exception(f"YouTube init failed: {init_r.status_code} {init_r.text[:200]}")
    upload_url = init_r.headers.get("Location","")
    if not upload_url:
        raise Exception("No upload URL returned")
    # 2. Upload
    with open(filepath,"rb") as f:
        up_r = requests.put(
            upload_url,
            headers={"Content-Type":"video/mp4","Content-Length":str(size)},
            data=f, timeout=300
        )
    if up_r.status_code not in (200,201):
        raise Exception(f"YouTube upload failed: {up_r.status_code} {up_r.text[:200]}")
    vid_id = up_r.json().get("id","")
    return vid_id

# ─── RESEND EMAIL ─────────────────────────────────────────────────────────────
def send_email(subject, html):
    try:
        r = requests.post("https://api.resend.com/emails",
            headers={"Authorization":f"Bearer {RESEND_API_KEY}","Content-Type":"application/json"},
            json={"from":"Brainrot Agent <onboarding@resend.dev>","to":[NOTIFY_EMAIL],"subject":subject,"html":html},
            timeout=15)
        log.info(f"Email sent: {r.status_code}")
    except Exception as e:
        log.warning(f"Email error: {e}")

# ─── COUNTER ──────────────────────────────────────────────────────────────────
def get_counter():
    try:
        with open(COUNTER_FILE) as f: return int(f.read().strip())
    except: return 0

def inc_counter():
    n = get_counter() + 1
    with open(COUNTER_FILE,"w") as f: f.write(str(n))
    return n

# ─── PIPELINE ─────────────────────────────────────────────────────────────────
def run_pipeline():
    date_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    n = inc_counter()
    log.info(f"=== PIPELINE #{n} — {date_str} UTC ===")

    # Sélectionner clips aléatoirement
    clips = random.sample(ALL_CLIPS, min(NB_CLIPS, len(ALL_CLIPS)))
    os.makedirs("/tmp/clips", exist_ok=True)
    os.makedirs("/tmp/norm",  exist_ok=True)

    # 1. Lancer générations en parallèle
    ops = []
    for i,(name,prompt) in enumerate(clips):
        try:
            op = veo_launch(prompt)
            ops.append((i+1, name, op))
            log.info(f"  Clip {i+1} ({name}) lancé")
            time.sleep(1)
        except Exception as e:
            log.error(f"  Clip {i+1} launch error: {e}")

    # 2. Polling
    downloaded = []
    for idx,name,op in ops:
        log.info(f"  Polling {name}...")
        uri = veo_poll(op)
        if not uri:
            log.warning(f"  {name} timeout, skip")
            continue
        raw = f"/tmp/clips/clip{idx}.mp4"
        try:
            r = requests.get(uri, headers={"Authorization":f"Bearer {GEMINI_API_KEY}"}, timeout=60)
            with open(raw,"wb") as f: f.write(r.content)
            log.info(f"  {name} ✅ ({os.path.getsize(raw)/1024/1024:.1f}MB)")
            downloaded.append((name, raw))
        except Exception as e:
            log.error(f"  Download {name}: {e}")

    if len(downloaded) < 2:
        log.error("Pas assez de clips, abandon")
        return

    # 3. Normaliser
    normed = []
    for i,(name,path) in enumerate(downloaded):
        out = f"/tmp/norm/clip{i+1}.mp4"
        r = subprocess.run([
            "ffmpeg","-y","-i",path,
            "-vf","scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1",
            "-r","30","-c:v","libx264","-preset","fast","-crf","22","-c:a","aac",out
        ], capture_output=True, timeout=60)
        if r.returncode == 0: normed.append(out)

    # 4. Fusionner + compresser
    with open("/tmp/concat.txt","w") as f:
        f.writelines([f"file '{p}'\n" for p in normed])
    merged   = "/tmp/merged.mp4"
    final    = "/tmp/final.mp4"
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i","/tmp/concat.txt","-c","copy",merged], capture_output=True, timeout=60)
    subprocess.run(["ffmpeg","-y","-i",merged,"-vf","scale=720:1280","-c:v","libx264","-crf","30","-preset","ultrafast","-c:a","aac","-b:a","96k","-movflags","+faststart",final], capture_output=True, timeout=90)

    size_mb = os.path.getsize(final)/1024/1024
    dur     = len(normed)*8
    log.info(f"Vidéo: {size_mb:.1f}MB, {dur}s")

    # 5. Titre / description
    animals_used = [name for name,_ in downloaded]
    a1  = animals_used[0]
    a2  = animals_used[1] if len(animals_used)>1 else animals_used[0]
    b1  = random.choice(BRAINROT_WORDS)
    b2  = random.choice(BRAINROT_WORDS)
    title_templates = [
        f"🐾 {ANIMALS_EMOJI.get(a1,'🐾')}{a1} {b1} mode 💀 Brainrot Animaux #{n}",
        f"POV: {ANIMALS_EMOJI.get(a1,'🐾')}{a1} découvre le {b1} 😭 #{n}",
        f"SIGMA {ANIMALS_EMOJI.get(a1,'🐾')}{a1} vs OHIO {ANIMALS_EMOJI.get(a2,'🐾')}{a2} 🔥 #{n}",
        f"{ANIMALS_EMOJI.get(a1,'🐾')}{a1} {b1} {b2} 💀 Kids Brainrot #{n}",
        f"🚨 {ANIMALS_EMOJI.get(a1,'🐾')}{a1} en mode {b1} 😂 Brainrot #{n}",
    ]
    title = random.choice(title_templates)
    emoji_line = " | ".join([f"{ANIMALS_EMOJI.get(a,'🐾')} {a}" for a in animals_used])
    description = f"""🔥 BRAINROT ANIMAUX #{n} 🔥

{emoji_line}

✨ Nouvelle vidéo toutes les 2h — Abonne-toi !

#brainrot #animaux #sigma #ohio #skibidi #shorts #viral #kids #foryou #NPC #gyatt #rizz #slay #npcmode #brainrotfr"""
    tags = ["brainrot","animaux","sigma","ohio","skibidi","kids","shorts","viral","foryou","NPC","gyatt","rizz","slay"] + [a.lower() for a in animals_used]

    # 6. Upload YouTube
    try:
        vid_id = youtube_upload(final, title, description, tags)
        yt_url = f"https://www.youtube.com/shorts/{vid_id}"
        log.info(f"YouTube ✅ {yt_url}")
    except Exception as e:
        log.error(f"YouTube upload error: {e}")
        yt_url = None

    # 7. Email
    yt_btn = f'<a href="{yt_url}" style="display:inline-block;background:#FF0000;color:#fff;padding:14px 28px;border-radius:8px;text-decoration:none;font-weight:600">▶️ Voir sur YouTube</a>' if yt_url else "<p>❌ Upload YouTube échoué</p>"
    send_email(
        f"🐸 Brainrot #{n} publié sur YouTube !",
        f"""<div style='font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px'>
          <h2>🎬 Vidéo Brainrot #{n}</h2>
          <div style='background:#f5f5f5;border-radius:8px;padding:16px;margin:16px 0'>
            <p>📅 <b>{date_str} UTC</b></p>
            <p>🐾 <b>Animaux:</b> {emoji_line}</p>
            <p>⏱ <b>{dur}s</b> &nbsp;·&nbsp; 📦 <b>{size_mb:.1f}MB</b> &nbsp;·&nbsp; 📐 <b>9:16</b></p>
            <p>📝 <b>{title}</b></p>
          </div>
          {yt_btn}
          <p style='color:#999;font-size:12px;margin-top:20px'>Publié sur Animal_Lab · Agent Brainrot · Toutes les 2h</p>
        </div>"""
    )

    # Cleanup
    subprocess.run(["rm","-rf","/tmp/clips","/tmp/norm",merged,final])
    log.info(f"=== Pipeline #{n} terminé ===\n")

# ─── MAIN LOOP ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    log.info(f"🤖 Brainrot Agent démarré")
    log.info(f"⏰ Intervalle: {INTERVAL_HOURS}h | Clips: {NB_CLIPS} | Email: {NOTIFY_EMAIL}")

    # Premier run immédiat au démarrage
    run_pipeline()

    # Boucle infinie
    while True:
        log.info(f"💤 Pause {INTERVAL_HOURS}h avant prochain run...")
        time.sleep(INTERVAL_HOURS * 3600)
        run_pipeline()
