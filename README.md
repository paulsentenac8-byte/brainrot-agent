# 🐸 Brainrot Animal Video Agent

Génère et publie automatiquement une vidéo brainrot animaux toutes les 2h sur YouTube.

## Déploiement Railway (5 minutes)

### Étape 1 — Créer un compte Railway
→ https://railway.app (gratuit, 500h/mois)

### Étape 2 — Nouveau projet depuis GitHub
1. Va sur https://railway.app/new
2. Clique **"Deploy from GitHub repo"**
3. Connecte ton GitHub et push ce dossier
   ```
   git init
   git add .
   git commit -m "brainrot agent"
   git remote add origin <ton-repo>
   git push -u origin main
   ```
4. Railway détecte le Dockerfile automatiquement ✅

### Étape 3 — Variables d'environnement (obligatoires)

Dans Railway → ton projet → **Variables** :

| Variable | Valeur | Comment l'obtenir |
|----------|--------|-------------------|
| `GEMINI_API_KEY` | `AIza...` | https://aistudio.google.com → API Keys |
| `YOUTUBE_ACCESS_TOKEN` | `ya29...` | Voir ci-dessous |
| `RESEND_API_KEY` | `re_...` | https://resend.com → API Keys |
| `NOTIFY_EMAIL` | `paulsentenac8@gmail.com` | Ton email |
| `INTERVAL_HOURS` | `2` | Fréquence en heures |
| `NB_CLIPS` | `4` | Clips par vidéo (4 = 32s rapide) |

### Obtenir le YouTube Access Token

1. Va sur https://developers.google.com/oauthplayground
2. En haut à droite → ⚙️ → coche "Use your own OAuth credentials"
3. Entre ton Client ID + Secret (depuis https://console.cloud.google.com)
4. Dans "Step 1" sélectionne : `https://www.googleapis.com/auth/youtube.upload`
5. Clique "Authorize APIs" → connecte ton compte YouTube (Animal_Lab)
6. Clique "Exchange authorization code for tokens"
7. Copie le `access_token` (commence par `ya29...`)

> ⚠️ Le token expire toutes les 1h. Pour un token permanent, utilise un refresh_token.
> Voir REFRESH_TOKEN.md pour la procédure complète.

### Étape 4 — Deploy !
Railway build automatiquement le Docker container et lance l'agent.
Le premier run démarre immédiatement, puis toutes les 2h.

## Ce que fait l'agent

```
⏰ Toutes les 2h
  ↓
🎬 4-8 clips Google Veo 3 générés (animaux aléatoires)
  ↓
🔧 FFmpeg — normalise 1080×1920 + fusionne
  ↓
📺 Upload sur YouTube "Animal_Lab" (public, titre + description + tags auto)
  ↓
📧 Email de notification avec lien YouTube
```

## Variables optionnelles

| Variable | Défaut | Description |
|----------|--------|-------------|
| `INTERVAL_HOURS` | `2` | Heures entre chaque vidéo |
| `NB_CLIPS` | `4` | Clips par vidéo (4=32s, 8=64s) |
| `NOTIFY_EMAIL` | `paulsentenac8@gmail.com` | Email de notification |

## Logs

Dans Railway → ton projet → **Logs** pour voir le pipeline en temps réel.
