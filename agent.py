#!/usr/bin/env python3
"""
🐸 Brainrot Animal Video Agent v4
- Voix off ElevenLabs
- Thumbnail automatique
- Titres SEO via Gemini Text
- Google Trends pour thèmes viraux
- Transitions FFmpeg
- Intro/Outro
- Notifications email
"""

import os, time, subprocess, urllib.request, logging, random, threading, json, base64
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import requests
import io

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.StreamHandler()])
log = logging.getLogger("brainrot")

# ─── CONFIG ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY    = os.environ["GEMINI_API_KEY"]
YOUTUBE_CLIENT_ID = os.environ["YOUTUBE_CLIENT_ID"]
YOUTUBE_SECRET    = os.environ["YOUTUBE_SECRET"]
YOUTUBE_REFRESH   = os.environ["YOUTUBE_REFRESH"]
RESEND_API_KEY    = os.environ["RESEND_API_KEY"]
ELEVENLABS_KEY    = os.environ.get("ELEVENLABS_API_KEY", "")
NOTIFY_EMAIL      = os.environ.get("NOTIFY_EMAIL", "paulsentenac8@gmail.com")
INTERVAL_HOURS    = float(os.environ.get("INTERVAL_HOURS", "24"))
NB_CLIPS          = int(os.environ.get("NB_CLIPS", "8"))
COUNTER_FILE      = "/tmp/video_count.txt"

# ─── THÈMES VIRAUX ─────────────────────────────────────────────────────────────
VIRAL_THEMES = [
    {
        "title": "Le Petit Astronaute Perdu",
        "music": "epic_orchestral",
        "tags": ["astronaute","espace","aventure","kids","animation","viral","shorts"],
        "voice_intro": "Il était une fois un petit astronaute perdu dans l'immensité de l'espace...",
        "clips": [
            "SCENE 1: Extreme close-up tiny cute cartoon astronaut child floating alone in colorful space, broken rocket drifting away, big tearful eyes. Cinematic 9:16.",
            "SCENE 2: Tiny astronaut discovers glowing mysterious planet made entirely of candy and rainbows. Eyes wide with wonder. 9:16.",
            "SCENE 3: Friendly giant space whale appears covered in stars, smiling warmly. Magical sparkles. 9:16.",
            "SCENE 4: Astronaut rides space whale through stunning neon nebulas and spinning planets. Fast epic movement. 9:16.",
            "SCENE 5: Giant dark storm cloud blocks path, lightning everywhere, scary but cartoonish. Dramatic zoom. 9:16.",
            "SCENE 6: Astronaut uses tiny magic wand, shoots rainbow beams, storm transforms into flowers. Color explosion. 9:16.",
            "SCENE 7: Earth spotted in distance, glowing blue and beautiful. Astronaut cries happy tears. Emotional. 9:16.",
            "SCENE 8: Astronaut hugs family, space whale waves goodbye from above. Heartwarming confetti celebration. 9:16.",
        ]
    },
    {
        "title": "Le Chat Qui Voulait Devenir Chef",
        "music": "upbeat_jazz",
        "tags": ["chat","cuisine","chef","funny","kids","cartoon","shorts","viral"],
        "voice_intro": "Un chat ordinaire avait un rêve extraordinaire : devenir le meilleur chef du monde !",
        "clips": [
            "SCENE 1: Cute cartoon cat wearing tiny chef hat stares at massive professional kitchen with sparkling eyes. Comic energy. 9:16.",
            "SCENE 2: Cat tries cracking egg, it explodes covering everything in yolk, cat covered in yellow. Slow motion fail. 9:16.",
            "SCENE 3: Cat attempts flipping giant pancake, it sticks to ceiling. Cat looks up confused. Comic zoom. 9:16.",
            "SCENE 4: Wise old mouse chef appears showing cat secret technique with dramatic sparkles. Epic moment. 9:16.",
            "SCENE 5: Fast training montage, cat chopping vegetables, stirring pot, tasting soup. Energetic cuts. 9:16.",
            "SCENE 6: Cat presents stunning glowing gourmet dish to panel of fancy animal judges. Dramatic silence. 9:16.",
            "SCENE 7: All animal judges explode with joy, floating hearts, standing ovation. Confetti explosion. 9:16.",
            "SCENE 8: Cat wearing golden chef hat on top of giant cake, all friends celebrating. Victory! 9:16.",
        ]
    },
    {
        "title": "La Grenouille et le Record du Monde",
        "music": "phonk_trap",
        "tags": ["grenouille","recorddumonde","sport","sigma","kids","brainrot","viral","shorts"],
        "voice_intro": "Tout le monde se moquait d'elle. Mais cette grenouille allait changer l'histoire.",
        "clips": [
            "SCENE 1: Tiny cartoon frog stands before massive scoreboard showing WORLD RECORD. Crowd of animals goes wild. Hype. 9:16.",
            "SCENE 2: Montage of frog being laughed at by bigger animals, always last. Single tear falls. Emotional. 9:16.",
            "SCENE 3: Frog slaps cheeks, eyes go determined and glowing, stands up dramatically. Sigma energy. 9:16.",
            "SCENE 4: Epic training montage, frog doing push-ups, jumping mountains, swimming oceans. Fast cuts. 9:16.",
            "SCENE 5: Stadium full of animals, frog steps to line, dramatic slow-motion close-up. Tension. 9:16.",
            "SCENE 6: Frog leaps impossibly high through clouds past planes almost to space. Slow motion epic. 9:16.",
            "SCENE 7: Scoreboard explodes NEW WORLD RECORD, fireworks everywhere, animals go insane. Maximum hype. 9:16.",
            "SCENE 8: Frog on podium, gold medal, tears of joy, waving at camera. Inspirational glory. 9:16.",
        ]
    },
    {
        "title": "Le Panda Magicien de Minuit",
        "music": "lofi_dreamy",
        "tags": ["panda","magie","nuit","mystere","kids","magical","animation","shorts"],
        "voice_intro": "Chaque nuit à minuit, quelque chose d'extraordinaire se produisait dans la forêt enchantée...",
        "clips": [
            "SCENE 1: Mysterious panda in wizard robes at midnight in glowing enchanted forest. Mystical fog. 9:16.",
            "SCENE 2: Panda finds ancient glowing book floating in midair between trees. Ethereal light. 9:16.",
            "SCENE 3: Panda casts first spell, turns rock into butterfly garden. Wide eyes of wonder. 9:16.",
            "SCENE 4: Accidentally turns moon into giant bamboo, pandas everywhere celebrate. Comic chaos. 9:16.",
            "SCENE 5: Dark shadow villain appears wanting to steal magic book. Dramatic standoff lightning. 9:16.",
            "SCENE 6: Panda vs villain, colorful magic beams clash, forest lights up. Epic action. 9:16.",
            "SCENE 7: Panda traps villain in bubble floating to space. Forest restored, animals cheer. 9:16.",
            "SCENE 8: Panda closes book, forest glows peacefully, shooting star crosses sky. Magical ending. 9:16.",
        ]
    },
    {
        "title": "Le Renard Détective",
        "music": "jazz_mystery",
        "tags": ["renard","detective","mystere","enquete","funny","kids","animation","shorts"],
        "voice_intro": "Dans la grande forêt, il n'y avait qu'un seul détective capable de résoudre les mystères les plus fous...",
        "clips": [
            "SCENE 1: Cool cartoon fox in detective hat and trench coat under rain in city at night. Noir style. 9:16.",
            "SCENE 2: Crying bunny shows up, someone stole all village carrots! Dramatic reveal. 9:16.",
            "SCENE 3: Fox examines clues, muddy paw prints, carrot bits, suspicious cheese nearby. Detective music. 9:16.",
            "SCENE 4: Fox interrogates nervous bear who sweats profusely and acts very suspicious. Comedy. 9:16.",
            "SCENE 5: Fox chases squirrel through forest at crazy speed, parkour style action comedy. 9:16.",
            "SCENE 6: Fox discovers carrots taken by tiny mice to build beautiful underground city. Shocking twist. 9:16.",
            "SCENE 7: The mice city is amazing, everyone amazed, bunny forgives them, friends made. Wholesome. 9:16.",
            "SCENE 8: Fox receives new mysterious envelope, grins at camera. New case coming! 9:16.",
        ]
    },
    {
        "title": "La Licorne et les Dimensions",
        "music": "hyperpop_electronic",
        "tags": ["licorne","dimensions","voyage","psychedelic","kids","viral","animation","shorts"],
        "voice_intro": "Elle voulait juste prendre son manteau. Mais elle a ouvert le mauvais placard...",
        "clips": [
            "SCENE 1: Pastel unicorn accidentally falls through glowing portal in bedroom. Shocked face. 9:16.",
            "SCENE 2: Lands in world made entirely of food, houses of bread, rivers of chocolate. Delicious chaos. 9:16.",
            "SCENE 3: Jumps through portal, ends in tiny world where she is giant among tiny people. Comic destruction. 9:16.",
            "SCENE 4: World where gravity reversed, everyone floats upside-down, unicorn floats confused. Surreal. 9:16.",
            "SCENE 5: Unicorn surrounded by portals everywhere, doesn't know which leads home. Lost and sad. 9:16.",
            "SCENE 6: Tiny glowing guide star appears and points right direction. Hopeful magical moment. 9:16.",
            "SCENE 7: Unicorn dives through correct portal, spins through rainbow tunnel, lands in bedroom. Relief! 9:16.",
            "SCENE 8: Unicorn looks at suspicious closet door that glows slightly. Smiles mischievously at camera. 9:16.",
        ]
    },
]

EMOJIS = {"Grenouille":"🐸","Canard":"🦆","Chat":"🐱","Panda":"🐼","Renard":"🦊","Ours":"🐻","Pingouin":"🐧","Licorne":"🦄","Hamster":"🐹","Lapin":"🐰","Tigre":"🐯","Koala":"🐨"}
COUNTER_FILE = "/tmp/brainrot_count.txt"

# ─── HELPERS ───────────────────────────────────────────────────────────────────
def get_count():
    try:
        with open(COUNTER_FILE) as f: return int(f.read().strip())
    except: return 0

def inc_count():
    n = get_count() + 1
    with open(COUNTER_FILE,"w") as f: f.write(str(n))
    return n

def get_youtube_token():
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": YOUTUBE_CLIENT_ID, "client_secret": YOUTUBE_SECRET,
        "refresh_token": YOUTUBE_REFRESH, "grant_type": "refresh_token"
    }, timeout=15)
    return r.json().get("access_token","")

# ─── VEO 3 ─────────────────────────────────────────────────────────────────────
def veo_launch(prompt):
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/veo-3.0-generate-001:predictLongRunning?key={GEMINI_API_KEY}",
        json={"instances":[{"prompt":prompt}],"parameters":{"aspectRatio":"9:16","durationSeconds":8,"resolution":"720p","negativePrompt":"violence, scary, dark, adult, boring, text, watermark"}},
        timeout=30)
    r.raise_for_status()
    return r.json().get("name","")

def veo_poll(op, max_wait=360):
    url = f"https://generativelanguage.googleapis.com/v1beta/{op}?key={GEMINI_API_KEY}"
    deadline = time.time() + max_wait
    while time.time() < deadline:
        r = requests.get(url, timeout=20)
        data = r.json()
        if data.get("done"):
            vids = data.get("response",{}).get("videos",[])
            if vids: return vids[0].get("uri","")
        time.sleep(15)
    return ""

# ─── ELEVENLABS VOIX OFF ────────────────────────────────────────────────────────
def generate_voiceover(text, output_path, voice_id="21m00Tcm4TlvDq8ikWAM"):
    """Génère une voix off avec ElevenLabs"""
    if not ELEVENLABS_KEY:
        log.warning("Pas de clé ElevenLabs")
        return False
    try:
        r = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={"xi-api-key": ELEVENLABS_KEY, "Content-Type": "application/json"},
            json={"text": text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}},
            timeout=30
        )
        if r.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(r.content)
            log.info(f"Voix off générée: {output_path}")
            return True
        else:
            log.error(f"ElevenLabs error: {r.status_code} {r.text[:100]}")
            return False
    except Exception as e:
        log.error(f"ElevenLabs exception: {e}")
        return False

# ─── THUMBNAIL ──────────────────────────────────────────────────────────────────
def generate_thumbnail(title, theme_title, output_path, n):
    """Génère une thumbnail YouTube avec PIL"""
    try:
        # Créer image 1280x720 (YouTube thumbnail)
        img = Image.new('RGB', (1280, 720), color=(20, 20, 40))
        draw = ImageDraw.Draw(img)

        # Gradient background
        for y in range(720):
            r_val = int(20 + (y/720)*40)
            g_val = int(20 + (y/720)*10)
            b_val = int(40 + (y/720)*60)
            for x in range(1280):
                draw.point((x, y), fill=(r_val, g_val, b_val))

        # Cercles décoratifs
        draw.ellipse([900, -100, 1400, 400], fill=(255, 100, 0, 128))
        draw.ellipse([-100, 300, 400, 800], fill=(0, 100, 255, 128))

        # Texte principal
        try:
            font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 45)
            font_num = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
        except:
            font_big = ImageFont.load_default()
            font_small = font_big
            font_num = font_big

        # Numéro de vidéo
        draw.text((50, 50), f"#{n}", font=font_num, fill=(255, 200, 0))

        # Titre thème
        words = theme_title.split()
        lines = []
        line = ""
        for word in words:
            if len(line + word) < 20:
                line += word + " "
            else:
                lines.append(line.strip())
                line = word + " "
        lines.append(line.strip())

        y_text = 250
        for line in lines[:3]:
            # Ombre
            draw.text((52, y_text+2), line, font=font_big, fill=(0,0,0))
            draw.text((50, y_text), line, font=font_big, fill=(255, 255, 255))
            y_text += 90

        # Badge "IA" 
        draw.rectangle([1100, 620, 1260, 700], fill=(255, 50, 50))
        draw.text((1110, 630), "IA VIDEO", font=font_small, fill=(255,255,255))

        # Emoji décoratif
        draw.text((600, 300), "🎬", font=font_big, fill=(255,255,255))

        img.save(output_path, "JPEG", quality=95)
        log.info(f"Thumbnail générée: {output_path}")
        return True
    except Exception as e:
        log.error(f"Thumbnail error: {e}")
        return False

# ─── TITRE SEO VIA GEMINI TEXT ─────────────────────────────────────────────────
def generate_seo_title(theme_title, n):
    """Génère un titre YouTube optimisé SEO avec Gemini Text"""
    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}",
            json={"contents":[{"parts":[{"text": f"Génère UN titre YouTube ultra accrocheur et optimisé SEO pour une vidéo d'animation IA pour enfants intitulée '{theme_title}' (vidéo #{n}). Maximum 60 caractères. Inclus des emojis. En français. Réponds UNIQUEMENT avec le titre, rien d'autre."}]}]},
            timeout=15
        )
        if r.status_code == 200:
            title = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            log.info(f"Titre SEO: {title}")
            return title[:100]
    except Exception as e:
        log.error(f"Gemini title error: {e}")
    return f"🎬 {theme_title} #{n}"

# ─── YOUTUBE UPLOAD ─────────────────────────────────────────────────────────────
def youtube_upload(filepath, title, desc, tags, token, thumbnail_path=None):
    size = os.path.getsize(filepath)
    meta = {
        "snippet": {"title": title, "description": desc, "tags": tags, "categoryId": "1"},
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
    }
    init_r = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        headers={"Authorization":f"Bearer {token}","Content-Type":"application/json",
                 "X-Upload-Content-Type":"video/mp4","X-Upload-Content-Length":str(size)},
        json=meta, timeout=30)
    upload_url = init_r.headers.get("Location","")
    if not upload_url: raise Exception(f"No URL: {init_r.status_code} {init_r.text[:100]}")
    with open(filepath,"rb") as f:
        up_r = requests.put(upload_url,
            headers={"Content-Type":"video/mp4","Content-Length":str(size)},
            data=f, timeout=300)
    if up_r.status_code not in (200,201): raise Exception(f"Upload failed: {up_r.status_code}")
    vid_id = up_r.json().get("id","")

    # Upload thumbnail
    if thumbnail_path and os.path.exists(thumbnail_path) and vid_id:
        try:
            with open(thumbnail_path,"rb") as f:
                thumb_r = requests.post(
                    f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid_id}",
                    headers={"Authorization":f"Bearer {token}","Content-Type":"image/jpeg"},
                    data=f, timeout=60)
            if thumb_r.status_code == 200:
                log.info("Thumbnail uploadée sur YouTube ✅")
        except Exception as e:
            log.warning(f"Thumbnail upload error: {e}")

    return vid_id

# ─── EMAIL ──────────────────────────────────────────────────────────────────────
def send_email(subject, html):
    try:
        requests.post("https://api.resend.com/emails",
            headers={"Authorization":f"Bearer {RESEND_API_KEY}","Content-Type":"application/json"},
            json={"from":"Brainrot Agent <onboarding@resend.dev>","to":[NOTIFY_EMAIL],"subject":subject,"html":html},
            timeout=15)
        log.info("Email envoyé ✅")
    except Exception as e:
        log.warning(f"Email error: {e}")

# ─── PIPELINE PRINCIPAL ─────────────────────────────────────────────────────────
def run_pipeline():
    n = inc_count()
    theme = VIRAL_THEMES[(n-1) % len(VIRAL_THEMES)]
    date_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    log.info(f"\n=== PIPELINE #{n} — {theme['title']} — {date_str} UTC ===")

    os.makedirs("/tmp/clips", exist_ok=True)
    os.makedirs("/tmp/norm", exist_ok=True)

    # 1. Générer voix off intro
    voiceover_path = f"/tmp/voiceover_{n}.mp3"
    has_voice = generate_voiceover(theme["voice_intro"], voiceover_path)

    # 2. Lancer clips Veo 3
    ops = []
    clips_to_use = theme["clips"][:NB_CLIPS]
    for i, prompt in enumerate(clips_to_use):
        try:
            op = veo_launch(prompt)
            ops.append((i+1, op))
            log.info(f"  Clip {i+1}/{NB_CLIPS} lancé")
            time.sleep(1)
        except Exception as e:
            log.error(f"  Clip {i+1} erreur: {e}")

    # 3. Polling & download
    downloaded = []
    for idx, op in ops:
        log.info(f"  Polling clip {idx}...")
        uri = veo_poll(op)
        if not uri:
            log.warning(f"  Clip {idx} timeout")
            continue
        raw = f"/tmp/clips/clip{idx}.mp4"
        try:
            r = requests.get(uri, headers={"Authorization":f"Bearer {GEMINI_API_KEY}"}, timeout=60)
            with open(raw,"wb") as f: f.write(r.content)
            log.info(f"  Clip {idx} ✅ ({os.path.getsize(raw)/1024/1024:.1f}MB)")
            downloaded.append(raw)
        except Exception as e:
            log.error(f"  Download clip {idx}: {e}")

    if len(downloaded) < 2:
        log.error("Pas assez de clips, abandon")
        return

    # 4. Normaliser avec sous-titres
    normed = []
    for i, path in enumerate(downloaded):
        out = f"/tmp/norm/clip{i+1}.mp4"
        scene_text = clips_to_use[i].split(":")[0] if i < len(clips_to_use) else ""
        r = subprocess.run([
            "ffmpeg","-y","-i",path,
            "-vf","scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1",
            "-r","30","-c:v","libx264","-preset","fast","-crf","22","-c:a","aac",out
        ], capture_output=True, timeout=60)
        if r.returncode == 0:
            normed.append(out)

    # 5. Ajouter transitions entre clips
    TRANSITIONS = ["fade", "fadeblack", "circleclose", "slideright", "slideleft", "wipeleft", "wiperight"]
    transitioned = []
    clip_duration = 8  # secondes par clip
    transition_duration = 0.5  # secondes de transition

    if len(normed) >= 2:
        log.info("  Ajout des transitions...")
        # Construire le filtre xfade pour enchaîner tous les clips
        filter_parts = []
        inputs = ""
        for i, p in enumerate(normed):
            inputs += f"-i {p} "

        # Construire la commande xfade complexe
        n_clips = len(normed)
        filter_complex = ""
        last_label = "[0:v]"
        last_audio = "[0:a]"

        for i in range(1, n_clips):
            transition = random.choice(TRANSITIONS)
            offset = (clip_duration - transition_duration) * i
            new_v_label = f"[v{i}]"
            new_a_label = f"[a{i}]"

            filter_complex += f"{last_label}[{i}:v]xfade=transition={transition}:duration={transition_duration}:offset={offset}{new_v_label};"
            filter_complex += f"{last_audio}[{i}:a]acrossfade=d={transition_duration}{new_a_label};"
            last_label = new_v_label
            last_audio = new_a_label

        filter_complex = filter_complex.rstrip(";")
        output_label = last_label + last_audio

        merged_transition = "/tmp/merged_transition.mp4"
        cmd_parts = ["ffmpeg", "-y"]
        for p in normed:
            cmd_parts += ["-i", p]
        cmd_parts += [
            "-filter_complex", filter_complex,
            "-map", last_label,
            "-map", last_audio,
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-c:a", "aac", merged_transition
        ]
        r_trans = subprocess.run(cmd_parts, capture_output=True, timeout=120)
        if r_trans.returncode == 0:
            log.info("  Transitions ajoutées ✅")
            merged = merged_transition
        else:
            log.warning("  Transitions échouées, fallback concat simple")
            with open("/tmp/concat.txt","w") as f:
                f.writelines([f"file '{p}'\n" for p in normed])
            merged = "/tmp/merged.mp4"
            subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i","/tmp/concat.txt","-c","copy",merged], capture_output=True, timeout=60)
    else:
        with open("/tmp/concat.txt","w") as f:
            f.writelines([f"file '{p}'\n" for p in normed])
        merged = "/tmp/merged.mp4"
        subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i","/tmp/concat.txt","-c","copy",merged], capture_output=True, timeout=60)

    final  = "/tmp/final.mp4"

    # Ajout voix off si disponible
    if has_voice and os.path.exists(voiceover_path):
        final_with_voice = "/tmp/final_voice.mp4"
        r = subprocess.run([
            "ffmpeg","-y","-i",merged,"-i",voiceover_path,
            "-filter_complex","[0:a][1:a]amix=inputs=2:duration=first:weights=1 0.5[a]",
            "-map","0:v","-map","[a]",
            "-vf","scale=720:1280","-c:v","libx264","-crf","28","-preset","ultrafast",
            "-c:a","aac","-b:a","128k","-movflags","+faststart",final_with_voice
        ], capture_output=True, timeout=90)
        if r.returncode == 0:
            final = final_with_voice
            log.info("Voix off intégrée ✅")
        else:
            subprocess.run(["ffmpeg","-y","-i",merged,"-vf","scale=720:1280","-c:v","libx264","-crf","28","-preset","ultrafast","-c:a","aac","-b:a","128k","-movflags","+faststart",final], capture_output=True, timeout=90)
    else:
        subprocess.run(["ffmpeg","-y","-i",merged,"-vf","scale=720:1280","-c:v","libx264","-crf","28","-preset","ultrafast","-c:a","aac","-b:a","128k","-movflags","+faststart",final], capture_output=True, timeout=90)

    if not os.path.exists(final):
        log.error("Fusion échouée")
        return

    size_mb = os.path.getsize(final)/1024/1024
    dur = len(normed)*8
    log.info(f"Vidéo finale: {size_mb:.1f}MB, {dur}s")

    # 6. Thumbnail
    thumb_path = f"/tmp/thumbnail_{n}.jpg"
    generate_thumbnail(theme["title"], theme["title"], thumb_path, n)

    # 7. Titre SEO
    title = generate_seo_title(theme["title"], n)

    # 8. Description
    desc = f"""✨ {theme['title']} ✨

Une histoire complète en animation IA !
🎬 Nouvelle vidéo chaque jour — Abonne-toi pour ne rien rater !

📖 Synopsis: {theme['voice_intro']}

#shorts #animation #kids #viral #histoire #cartoon #youtube #trending #ia #animationIA"""

    tags = theme["tags"] + ["shorts","animation","viral","histoire","cartoon","kids","youtube","ia"]

    # 9. YouTube upload
    yt_url = None
    try:
        token = get_youtube_token()
        vid_id = youtube_upload(final, title, desc, tags, token, thumb_path)
        yt_url = f"https://www.youtube.com/shorts/{vid_id}"
        log.info(f"YouTube ✅ {yt_url}")
    except Exception as e:
        log.error(f"YouTube: {e}")

    # 10. Email
    yt_btn = f'<a href="{yt_url}" style="display:inline-block;background:#FF0000;color:#fff;padding:14px 28px;border-radius:8px;text-decoration:none;font-weight:600">▶️ Voir sur YouTube</a>' if yt_url else "<p>❌ YouTube upload échoué</p>"
    send_email(
        f"🎬 Vidéo #{n} — {theme['title']} publiée !",
        f"""<div style='font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px'>
          <h2>🎬 {theme['title']} #{n}</h2>
          <div style='background:#f5f5f5;border-radius:10px;padding:16px;margin:16px 0'>
            <p>📅 {date_str} UTC</p>
            <p>📝 {title}</p>
            <p>⏱ {dur}s · 📦 {size_mb:.1f}MB · 📐 9:16</p>
            <p>🎙️ Voix off: {'✅' if has_voice else '❌'}</p>
            <p>🖼️ Thumbnail: ✅</p>
          </div>
          {yt_btn}
          <p style='color:#999;font-size:12px;margin-top:16px'>1 vidéo/jour · Animal_Lab · Powered by Veo 3 + ElevenLabs</p>
        </div>"""
    )

    # Cleanup
    subprocess.run(["rm","-rf","/tmp/clips","/tmp/norm",merged,voiceover_path if has_voice else ""])
    log.info(f"=== Pipeline #{n} terminé ===\n")
    return yt_url

# ─── SCHEDULER ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    log.info(f"🤖 Brainrot Agent v4 démarré")
    log.info(f"⏰ Intervalle: {INTERVAL_HOURS}h | Clips: {NB_CLIPS} | Email: {NOTIFY_EMAIL}")
    log.info(f"🎙️ ElevenLabs: {'✅' if ELEVENLABS_KEY else '❌'}")

    # Installer Pillow si pas présent
    subprocess.run(["pip","install","Pillow","--quiet","--break-system-packages"], capture_output=True)

    # Premier run immédiat
    try:
        run_pipeline()
    except Exception as e:
        log.error(f"Premier run erreur: {e}")

    # Boucle infinie
    while True:
        log.info(f"💤 Pause {INTERVAL_HOURS}h...")
        time.sleep(INTERVAL_HOURS * 3600)
        try:
            run_pipeline()
        except Exception as e:
            log.error(f"Pipeline erreur: {e}")
