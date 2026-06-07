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

# ─── GOOGLE TRENDS ─────────────────────────────────────────────────────────────
def get_trending_topic():
    try:
        import re
        r = requests.get(
            "https://trends.google.com/trends/trendingsearches/daily/rss?geo=FR",
            headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if r.status_code == 200:
            titles = re.findall(r'<title><!\[CDATA\[([^\]]+)\]\]></title>', r.text)
            topics = [t for t in titles if len(t) > 3 and "Google" not in t]
            if topics:
                topic = random.choice(topics[:5])
                log.info(f"Trending topic: {topic}")
                return topic
    except Exception as e:
        log.warning(f"Trends error: {e}")
    return None

def adapt_theme_to_trend(theme, trend_topic):
    if not trend_topic:
        return theme
    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}",
            json={"contents":[{"parts":[{"text": f"Trending topic France: '{trend_topic}'. Thème vidéo: '{theme['title']}'. Génère UN titre court qui mélange les deux pour enfants. Max 50 caractères, français, emojis. UNIQUEMENT le titre."}]}]},
            timeout=15)
        if r.status_code == 200:
            new_title = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            theme = dict(theme)
            theme["title"] = new_title
            log.info(f"Titre adapté trend: {new_title}")
            return theme
    except Exception as e:
        log.warning(f"Trend adapt error: {e}")
    return theme

# ─── MULTI-LANGUE ──────────────────────────────────────────────────────────────
def translate_to_english(french_title):
    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}",
            json={"contents":[{"parts":[{"text": f"Traduis en anglais ce titre YouTube, garde emojis et style accrocheur: '{french_title}'. UNIQUEMENT la traduction."}]}]},
            timeout=15)
        if r.status_code == 200:
            en = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            log.info(f"Titre EN: {en}")
            return en
    except Exception as e:
        log.warning(f"Translation error: {e}")
    return None

# ─── YOUTUBE ANALYTICS ─────────────────────────────────────────────────────────
def get_youtube_analytics():
    """Récupère les stats des 7 derniers jours et retourne le thème le plus performant"""
    try:
        token = get_youtube_token()
        end_date = datetime.utcnow().strftime("%Y-%m-%d")
        start_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")

        # Récupérer les stats globales de la chaîne
        r = requests.get(
            "https://youtubeanalytics.googleapis.com/v2/reports",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "ids": "channel==MINE",
                "startDate": start_date,
                "endDate": end_date,
                "metrics": "views,likes,comments,averageViewDuration,subscribersGained",
                "dimensions": "video",
                "sort": "-views",
                "maxResults": 10
            },
            timeout=15
        )

        if r.status_code != 200:
            log.warning(f"Analytics error: {r.status_code}")
            return None

        data = r.json()
        rows = data.get("rows", [])
        if not rows:
            log.info("Pas encore de données analytics (chaîne trop récente)")
            return None

        # Analyser les vidéos les plus vues
        total_views = sum(row[1] for row in rows)
        total_likes = sum(row[2] for row in rows)
        avg_duration = sum(row[4] for row in rows) / len(rows) if rows else 0

        log.info(f"📊 Analytics 7 jours: {total_views} vues, {total_likes} likes, {avg_duration:.0f}s durée moyenne")

        # Générer un rapport avec Gemini pour adapter la stratégie
        if total_views > 0:
            report_prompt = f"""Tu es un expert YouTube. Voici les stats de la chaîne Animal_Lab sur 7 jours:
- Vues totales: {total_views}
- Likes: {total_likes}
- Durée moyenne de visionnage: {avg_duration:.0f}s
- Nombre de vidéos: {len(rows)}

Donne 2-3 conseils très courts (1 ligne chacun) pour améliorer les prochaines vidéos. Sois direct et concret."""

            r2 = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}",
                json={"contents":[{"parts":[{"text": report_prompt}]}]},
                timeout=15
            )
            if r2.status_code == 200:
                advice = r2.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                log.info(f"💡 Conseils IA: {advice}")
                return {"views": total_views, "likes": total_likes, "avg_duration": avg_duration, "advice": advice}

        return {"views": total_views, "likes": total_likes, "avg_duration": avg_duration, "advice": None}

    except Exception as e:
        log.warning(f"Analytics exception: {e}")
        return None

# ─── CHAPITRES YOUTUBE ─────────────────────────────────────────────────────────
def generate_chapters(nb_clips, clip_duration=8):
    chapters = "\n\n📚 CHAPITRES:\n00:00 Introduction\n"
    for i in range(nb_clips):
        ts = (i+1) * clip_duration
        chapters += f"{ts//60:02d}:{ts%60:02d} Partie {i+2}\n"
    return chapters

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

# ─── PRE-CHECKS ────────────────────────────────────────────────────────────────
def check_all_systems():
    """Vérifie que tout fonctionne AVANT de consommer le quota Veo 3"""
    log.info("🔍 Vérification des systèmes...")
    errors = []

    # 1. Vérifier FFmpeg
    r = subprocess.run(["ffmpeg", "-version"], capture_output=True)
    if r.returncode != 0:
        errors.append("❌ FFmpeg non disponible")
    else:
        log.info("  ✅ FFmpeg OK")

    # 2. Vérifier YouTube token
    try:
        token = get_youtube_token()
        if not token or len(token) < 10:
            errors.append("❌ YouTube token invalide")
        else:
            # Test rapide de l'API YouTube
            test_r = requests.get(
                "https://www.googleapis.com/youtube/v3/channels?part=id&mine=true",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10
            )
            if test_r.status_code == 200:
                log.info("  ✅ YouTube token OK")
            else:
                errors.append(f"❌ YouTube API erreur: {test_r.status_code}")
    except Exception as e:
        errors.append(f"❌ YouTube token erreur: {e}")

    # 3. Vérifier Gemini quota (test léger sans générer de vidéo)
    try:
        test_r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}",
            json={"contents":[{"parts":[{"text": "test"}]}]},
            timeout=10
        )
        if test_r.status_code == 200:
            log.info("  ✅ Gemini API OK")
        elif test_r.status_code == 429:
            errors.append("❌ Gemini quota épuisé — retry dans 1h")
        else:
            errors.append(f"❌ Gemini API erreur: {test_r.status_code}")
    except Exception as e:
        errors.append(f"❌ Gemini erreur: {e}")

    # 4. Vérifier espace disque
    disk = subprocess.run(["df", "-h", "/tmp"], capture_output=True, text=True)
    log.info(f"  💾 Disque: {disk.stdout.split()[-4] if disk.stdout else 'N/A'} disponible")

    if errors:
        for err in errors:
            log.error(f"  {err}")
        return False, errors

    log.info("✅ Tous les systèmes sont opérationnels !")
    return True, []

# ─── PIPELINE PRINCIPAL ─────────────────────────────────────────────────────────
def run_pipeline():
    n = inc_count()
    theme = VIRAL_THEMES[(n-1) % len(VIRAL_THEMES)]
    date_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    log.info(f"\n=== PIPELINE #{n} — {theme['title']} — {date_str} UTC ===")

    # 🔍 PRE-CHECKS — vérifier tout AVANT de consommer le quota Veo 3
    ok, errors = check_all_systems()
    if not ok:
        log.error(f"Pipeline annulé — systèmes non opérationnels: {errors}")
        # Si c'est un problème de quota Gemini, on réessaie dans 1h
        if any("quota" in e for e in errors):
            log.info("⏳ Retry dans 1h pour le quota...")
            time.sleep(3600)
            ok2, errors2 = check_all_systems()
            if not ok2:
                log.error("Toujours pas opérationnel après 1h, abandon jusqu'au prochain run")
                return None
        else:
            return None

    # Adapter au trending topic
    trend = get_trending_topic()
    if trend:
        theme = adapt_theme_to_trend(theme, trend)

    # 📊 Récupérer les analytics (chaque 7 jours)
    analytics = None
    if n % 7 == 0 or n == 1:  # Premier run + toutes les 7 vidéos
        analytics = get_youtube_analytics()
        if analytics and analytics.get("advice"):
            log.info(f"📊 Stats: {analytics['views']} vues | Conseil: {analytics['advice'][:100]}")

    os.makedirs("/tmp/clips", exist_ok=True)
    os.makedirs("/tmp/norm", exist_ok=True)

    # 1. Générer voix off intro (désactivé — plan gratuit insuffisant)
    has_voice = False
    voiceover_path = f"/tmp/voiceover_{n}.mp3"

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

    # 7. Titre SEO + traduction anglais
    title_fr = generate_seo_title(theme["title"], n)
    title_en = translate_to_english(title_fr)
    title = title_fr  # On utilise le français pour YouTube FR

    # 8. Chapitres automatiques
    chapters = generate_chapters(len(normed))

    # 9. Description complète avec chapitres
    trend_line = f"🔥 Trending aujourd'hui: {trend}\n" if trend else ""
    desc = f"""✨ {theme['title']} ✨

{trend_line}Une histoire complète en animation IA !
🎬 Nouvelle vidéo chaque jour — Abonne-toi pour ne rien rater !

📖 {theme['voice_intro']}
{chapters}
#shorts #animation #kids #viral #histoire #cartoon #youtube #trending #ia #animationIA #enfants"""

    # Version anglaise de la description
    if title_en:
        log.info(f"Titre EN disponible: {title_en}")

    tags = theme["tags"] + ["shorts","animation","viral","histoire","cartoon","kids","youtube","ia","enfants","trending"]

    # 10. YouTube upload FR
    yt_url = None
    try:
        token = get_youtube_token()
        vid_id = youtube_upload(final, title, desc, tags, token, thumb_path)
        yt_url = f"https://www.youtube.com/shorts/{vid_id}"
        log.info(f"YouTube FR ✅ {yt_url}")
    except Exception as e:
        log.error(f"YouTube: {e}")

    # 11. Email avec analytics
    trend_badge = f'<span style="background:#FF6B00;color:#fff;padding:3px 8px;border-radius:4px;font-size:12px">🔥 Trending: {trend}</span><br><br>' if trend else ""
    analytics_section = ""
    if analytics:
        analytics_section = f"""
        <div style='background:#e8f5e9;border-radius:8px;padding:12px;margin:12px 0'>
          <p><b>📊 Stats 7 derniers jours</b></p>
          <p>👁️ {analytics['views']} vues · ❤️ {analytics['likes']} likes · ⏱️ {analytics.get('avg_duration',0):.0f}s durée moy.</p>
          {f"<p>💡 <i>{analytics['advice']}</i></p>" if analytics.get('advice') else ""}
        </div>"""
    yt_btn = f'<a href="{yt_url}" style="display:inline-block;background:#FF0000;color:#fff;padding:14px 28px;border-radius:8px;text-decoration:none;font-weight:600">▶️ Voir sur YouTube</a>' if yt_url else "<p>❌ YouTube upload échoué</p>"
    send_email(
        f"🎬 Vidéo #{n} — {theme['title']} publiée !",
        f"""<div style='font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px'>
          <h2>🎬 {theme['title']} #{n}</h2>
          <div style='background:#f5f5f5;border-radius:10px;padding:16px;margin:16px 0'>
            {trend_badge}
            <p>📅 {date_str} UTC</p>
            <p>📝 FR: {title}</p>
            <p>📝 EN: {title_en or 'N/A'}</p>
            <p>⏱ {dur}s · 📦 {size_mb:.1f}MB · 📐 9:16</p>
            <p>🎙️ Voix off: {'✅' if has_voice else '❌'}</p>
            <p>🖼️ Thumbnail: ✅</p>
            <p>🔀 Transitions: ✅</p>
            <p>📚 Chapitres: ✅</p>
          </div>
          {yt_btn}
          {analytics_section}
          <p style='color:#999;font-size:12px;margin-top:16px'>1 vidéo/jour · Animal_Lab · Veo 3 + ElevenLabs + Google Trends</p>
        </div>"""
    )

    # Cleanup
    subprocess.run(["rm","-rf","/tmp/clips","/tmp/norm","/tmp/merged_transition.mp4","/tmp/merged.mp4"])
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
