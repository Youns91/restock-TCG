"""
🎴 SURVEILLANCE RESTOCK TCG - Pokémon / One Piece / Naruto Mythos
Alertes Telegram instantanées + Email Outlook
"""

import requests
from bs4 import BeautifulSoup
import smtplib
import time
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ============================================================
#  ⚙️  CONFIGURATION
# ============================================================

# -- Telegram --
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "8681719781:AAHHkjpMv7jRBTZ4gFnZknYc_CNOGqM_9H8")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "8681719781")

# -- Email Outlook (optionnel en plus du Telegram) --
EMAIL_EXPEDITEUR   = os.environ.get("EMAIL_EXPEDITEUR", "TON_EMAIL@hotmail.com")
MOT_DE_PASSE       = os.environ.get("MOT_DE_PASSE", "TON_MOT_DE_PASSE")
EMAIL_DESTINATAIRE = os.environ.get("EMAIL_DESTINATAIRE", "TON_EMAIL@hotmail.com")

INTERVALLE_SECONDES = 300  # Vérification toutes les 5 minutes

# ============================================================
#  🛒  PRODUITS À SURVEILLER
# ============================================================

PRODUITS = [
    # ── NARUTO MYTHOS TCG ──────────────────────────────────
    {
        "nom": "Naruto Mythos - Starter Pack Konoha Shido (DestockTCG)",
        "url": "https://www.destocktcg.fr/jeux-de-cartes-a-collectionner/naruto-mythos-tcg/",
        "mot_rupture": "rupture",
        "mot_stock": "ajouter au panier"
    },
    {
        "nom": "Naruto Mythos - Starter Pack (Shop-TCG)",
        "url": "https://shop-tcg.fr/product-category/naruto-tcg/",
        "mot_rupture": "rupture de stock",
        "mot_stock": "ajouter au panier"
    },
    {
        "nom": "Naruto Kayou - NarutokFR",
        "url": "https://narutok.fr/",
        "mot_rupture": "rupture",
        "mot_stock": "ajouter au panier"
    },
    {
        "nom": "Naruto Kayou - HamaCards",
        "url": "https://www.hamacards.com/",
        "mot_rupture": "rupture",
        "mot_stock": "ajouter au panier"
    },
    {
        "nom": "Naruto TCG - Cultura",
        "url": "https://www.cultura.com/search/?q=naruto+mythos+starter",
        "mot_rupture": "rupture de stock",
        "mot_stock": "ajouter au panier"
    },

    # ── ONE PIECE TCG ──────────────────────────────────────
    {
        "nom": "One Piece TCG - CarteOnePiece.fr",
        "url": "https://carteonepiece.fr/",
        "mot_rupture": "rupture",
        "mot_stock": "ajouter au panier"
    },
    {
        "nom": "One Piece TCG - NipponTCG",
        "url": "https://www.nippontcg.fr/",
        "mot_rupture": "épuisé",
        "mot_stock": "ajouter au panier"
    },
    {
        "nom": "One Piece TCG - DestockTCG",
        "url": "https://www.destocktcg.fr/jeux-de-cartes-a-collectionner/one-piece-card-game/",
        "mot_rupture": "rupture",
        "mot_stock": "ajouter au panier"
    },
    {
        "nom": "One Piece TCG - LeCoinDesBarons",
        "url": "https://lecoindesbarons.com/les-tcg/cartes-onepiece/",
        "mot_rupture": "rupture",
        "mot_stock": "ajouter au panier"
    },
    {
        "nom": "One Piece TCG - Fuji Store",
        "url": "https://fuji-store.fr/nos-produits/franchise-one-piece/",
        "mot_rupture": "rupture",
        "mot_stock": "ajouter au panier"
    },
    {
        "nom": "One Piece TCG - Ludisphere",
        "url": "https://ludisphere.fr/collections/one-piece",
        "mot_rupture": "épuisé",
        "mot_stock": "ajouter au panier"
    },
    {
        "nom": "One Piece TCG - Fnac",
        "url": "https://www.fnac.com/SearchResult/ResultList.aspx?Search=one+piece+carte&sft=1",
        "mot_rupture": "épuisé",
        "mot_stock": "ajouter au panier"
    },
    {
        "nom": "One Piece TCG - Cultura",
        "url": "https://www.cultura.com/search/?q=one+piece+carte+tcg",
        "mot_rupture": "rupture de stock",
        "mot_stock": "ajouter au panier"
    },

    # ── POKÉMON TCG ────────────────────────────────────────
    {
        "nom": "Pokémon TCG - Fuji Store",
        "url": "https://fuji-store.fr/nos-produits/franchise-pokemon/",
        "mot_rupture": "rupture",
        "mot_stock": "ajouter au panier"
    },
    {
        "nom": "Pokémon TCG - Ludisphere",
        "url": "https://ludisphere.fr/collections/pokemon",
        "mot_rupture": "épuisé",
        "mot_stock": "ajouter au panier"
    },
    {
        "nom": "Pokémon TCG - Philibert",
        "url": "https://www.philibertnet.com/fr/pokemon.html",
        "mot_rupture": "rupture",
        "mot_stock": "ajouter au panier"
    },
    {
        "nom": "Pokémon TCG - Magic Bazar",
        "url": "https://www.magicbazar.fr/boutique/pokemon-jcc.html",
        "mot_rupture": "rupture",
        "mot_stock": "ajouter au panier"
    },
    {
        "nom": "Pokémon TCG - Fnac",
        "url": "https://www.fnac.com/SearchResult/ResultList.aspx?Search=pokemon+carte&sft=1",
        "mot_rupture": "épuisé",
        "mot_stock": "ajouter au panier"
    },
    {
        "nom": "Pokémon TCG - Cultura",
        "url": "https://www.cultura.com/search/?q=pokemon+carte+tcg",
        "mot_rupture": "rupture de stock",
        "mot_stock": "ajouter au panier"
    },
]

# ============================================================
#  📱  FONCTION TELEGRAM
# ============================================================

def envoyer_telegram(produit_nom, produit_url):
    try:
        heure = datetime.now().strftime("%d/%m/%Y à %H:%M:%S")
        message = (
            f"🚨 *RESTOCK DÉTECTÉ !*\n\n"
            f"🎴 *{produit_nom}*\n\n"
            f"🕐 {heure}\n\n"
            f"👉 [VOIR LE PRODUIT]({produit_url})"
        )
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        r = requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }, timeout=10)
        if r.status_code == 200:
            print(f"  ✅ Telegram envoyé pour : {produit_nom}")
        else:
            print(f"  ❌ Erreur Telegram : {r.text}")
    except Exception as e:
        print(f"  ❌ Erreur Telegram : {e}")

# ============================================================
#  📧  FONCTION EMAIL
# ============================================================

def envoyer_email(produit_nom, produit_url):
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🚨 RESTOCK DÉTECTÉ — {produit_nom}"
        msg["From"]    = EMAIL_EXPEDITEUR
        msg["To"]      = EMAIL_DESTINATAIRE
        heure = datetime.now().strftime("%d/%m/%Y à %H:%M:%S")
        corps_html = f"""
        <html><body style="font-family:Arial,sans-serif;background:#f5f5f5;padding:20px;">
          <div style="background:white;border-radius:10px;padding:30px;max-width:600px;margin:auto;">
            <h2 style="color:#e74c3c;">🚨 RESTOCK DÉTECTÉ !</h2>
            <p><strong style="font-size:18px;">{produit_nom}</strong></p>
            <p>🕐 <strong>Détecté le :</strong> {heure}</p>
            <a href="{produit_url}"
               style="display:inline-block;background:#e74c3c;color:white;padding:12px 25px;
                      border-radius:5px;text-decoration:none;font-weight:bold;">
              👉 VOIR LE PRODUIT
            </a>
          </div>
        </body></html>
        """
        msg.attach(MIMEText(corps_html, "html"))
        with smtplib.SMTP("smtp-mail.outlook.com", 587) as serveur:
            serveur.starttls()
            serveur.login(EMAIL_EXPEDITEUR, MOT_DE_PASSE)
            serveur.sendmail(EMAIL_EXPEDITEUR, EMAIL_DESTINATAIRE, msg.as_string())
        print(f"  ✅ Email envoyé pour : {produit_nom}")
    except Exception as e:
        print(f"  ❌ Erreur email : {e}")

# ============================================================
#  🔍  FONCTION VÉRIFICATION STOCK
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

FICHIER_ETATS = "etats_stock.json"

def charger_etats():
    if os.path.exists(FICHIER_ETATS):
        with open(FICHIER_ETATS, "r") as f:
            return json.load(f)
    return {}

def sauvegarder_etats(etats):
    with open(FICHIER_ETATS, "w") as f:
        json.dump(etats, f, indent=2)

def verifier_stock(produit):
    try:
        r = requests.get(produit["url"], headers=HEADERS, timeout=15)
        texte = r.text.lower()
        en_stock   = produit["mot_stock"].lower() in texte
        en_rupture = produit["mot_rupture"].lower() in texte
        if en_stock and not en_rupture:
            return "EN_STOCK"
        elif en_rupture:
            return "RUPTURE"
        else:
            return "INCONNU"
    except Exception as e:
        return f"ERREUR: {e}"

# ============================================================
#  🔄  BOUCLE PRINCIPALE
# ============================================================

def main():
    print("=" * 60)
    print("🎴  TCG RESTOCK WATCHER — Démarrage")
    print(f"📱  Telegram actif")
    print(f"⏱️   Vérification toutes les {INTERVALLE_SECONDES // 60} minutes")
    print(f"🛒  {len(PRODUITS)} produits surveillés")
    print("=" * 60)

    # Message de confirmation au démarrage
    envoyer_telegram("✅ Script TCG démarré ! Je surveille 19 sites pour toi 🎴", "https://railway.app")

    etats = charger_etats()

    while True:
        heure = datetime.now().strftime("%H:%M:%S")
        print(f"\n🔍 Vérification à {heure}...")

        for produit in PRODUITS:
            nom = produit["nom"]
            etat = verifier_stock(produit)
            ancien_etat = etats.get(nom, "INCONNU")

            symbole = "✅" if etat == "EN_STOCK" else "❌" if etat == "RUPTURE" else "⚠️"
            print(f"  {symbole} {nom[:50]:<50} → {etat}")

            if etat == "EN_STOCK" and ancien_etat != "EN_STOCK":
                print(f"  🚨 RESTOCK DÉTECTÉ ! Envoi alertes...")
                envoyer_telegram(nom, produit["url"])
                envoyer_email(nom, produit["url"])

            etats[nom] = etat

        sauvegarder_etats(etats)
        print(f"\n⏳ Prochaine vérification dans {INTERVALLE_SECONDES // 60} minutes...")
        time.sleep(INTERVALLE_SECONDES)

if __name__ == "__main__":
    main()
