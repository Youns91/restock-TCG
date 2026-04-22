"""
🎴 TCG RESTOCK WATCHER + IA avec accès internet
Bot Telegram interactif - Répond en français
"""

import requests
import smtplib
import time
import json
import os
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ============================================================
#  ⚙️  CONFIGURATION
# ============================================================

TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "8681719781:AAF5BKRAiWBDxMPcH3HZ7AY-nynq7rE_79Y")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "1465767408")
OPENROUTER_KEY   = os.environ.get("OPENROUTER_KEY", "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")

EMAIL_EXPEDITEUR   = os.environ.get("EMAIL_EXPEDITEUR", "TON_EMAIL@hotmail.com")
MOT_DE_PASSE       = os.environ.get("MOT_DE_PASSE", "TON_MOT_DE_PASSE")
EMAIL_DESTINATAIRE = os.environ.get("EMAIL_DESTINATAIRE", "TON_EMAIL@hotmail.com")

INTERVALLE_SECONDES = 300

# ============================================================
#  🛒  PRODUITS
# ============================================================

TOUS_LES_PRODUITS = {
    "naruto": [
        {
            "nom": "Naruto Mythos - Starter Pack (DestockTCG)",
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
    ],
    "onepiece": [
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
    ],
    "pokemon": [
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
    ],
}

# ============================================================
#  🧠  ÉTAT DU BOT
# ============================================================

etat = {
    "actif": True,
    "intervalle": 300,
    "categories": ["naruto", "onepiece", "pokemon"],
    "last_update_id": 0,
}

historique_messages = []

def get_produits_actifs():
    produits = []
    for cat in etat["categories"]:
        produits.extend(TOUS_LES_PRODUITS.get(cat, []))
    return produits

# ============================================================
#  📱  TELEGRAM - ENVOI
# ============================================================

def envoyer_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }, timeout=10)
    except Exception as e:
        print(f"  ❌ Erreur Telegram : {e}")

# ============================================================
#  🌐  RECHERCHE INTERNET
# ============================================================

def chercher_internet(query):
    """Recherche Google via DuckDuckGo (gratuit, sans clé)"""
    try:
        url = "https://api.duckduckgo.com/"
        r = requests.get(url, params={
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1
        }, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        data = r.json()

        resultats = []

        # Résumé principal
        if data.get("AbstractText"):
            resultats.append(data["AbstractText"])

        # Résultats connexes
        for item in data.get("RelatedTopics", [])[:3]:
            if isinstance(item, dict) and item.get("Text"):
                resultats.append(item["Text"])

        if resultats:
            return "\n".join(resultats[:3])
        else:
            return "Aucun résultat trouvé sur internet."
    except Exception as e:
        return f"Erreur recherche internet : {e}"

# ============================================================
#  🤖  IA OPENROUTER
# ============================================================

def demander_ia(message_utilisateur):
    try:
        # Vérifie si la question nécessite internet
        mots_internet = ["prix", "stock", "restock", "dispo", "disponible", "combien", 
                        "actualité", "news", "nouveauté", "sortie", "date", "quand"]
        
        besoin_internet = any(mot in message_utilisateur.lower() for mot in mots_internet)
        
        contexte_internet = ""
        if besoin_internet:
            envoyer_telegram("🔍 Je recherche sur internet...")
            resultat = chercher_internet(message_utilisateur + " TCG France 2026")
            contexte_internet = f"\n\nInformations trouvées sur internet :\n{resultat}"

        # Contexte stock actuel
        produits = get_produits_actifs()
        cats = ", ".join(etat["categories"]).upper()
        minutes = etat["intervalle"] // 60

        system_prompt = f"""Tu es un assistant spécialisé en cartes TCG (Trading Card Game), 
particulièrement Naruto Mythos, One Piece TCG et Pokémon TCG.
Tu surveilles les restocks de 19 sites français pour l'utilisateur.
Tu réponds TOUJOURS en français, de manière concise et amicale.
Tu es intégré dans un bot Telegram.

Contexte actuel du bot :
- TCG surveillés : {cats}
- Vérification toutes les {minutes} minutes
- Nombre de sites surveillés : {len(produits)}

Commandes disponibles pour l'utilisateur :
naruto, onepiece, pokemon, tout, pause, reprend, status, sites, 5 min, 10 min, 30 min, 1h{contexte_internet}"""

        historique_messages.append({"role": "user", "content": message_utilisateur})
        
        # Garde seulement les 10 derniers messages
        messages_envoyes = historique_messages[-10:]

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "meta-llama/llama-3.1-8b-instruct:free",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    *messages_envoyes
                ],
                "max_tokens": 500,
            },
            timeout=30
        )

        data = response.json()
        reponse_ia = data["choices"][0]["message"]["content"]
        
        historique_messages.append({"role": "assistant", "content": reponse_ia})
        
        return reponse_ia

    except Exception as e:
        return f"❌ Erreur IA : {e}"

# ============================================================
#  📱  COMMANDES ET MESSAGES
# ============================================================

COMMANDES = ["naruto", "onepiece", "pokemon", "tout", "pause", "reprend", 
             "resume", "status", "sites", "aide", "help", "/start", "1h"]

def traiter_commandes():
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
            r = requests.get(url, params={
                "offset": etat["last_update_id"] + 1, 
                "timeout": 30
            }, timeout=35)
            data = r.json()

            for update in data.get("result", []):
                etat["last_update_id"] = update["update_id"]
                msg = update.get("message", {})
                texte = msg.get("text", "").strip()
                texte_lower = texte.lower()
                chat_id = str(msg.get("chat", {}).get("id", ""))

                if chat_id != TELEGRAM_CHAT_ID:
                    continue

                print(f"  📩 Message reçu : {texte}")

                # ── COMMANDES RESTOCK ─────────────────────
                if texte_lower in ["/start", "aide", "help"]:
                    envoyer_telegram(
                        "🎴 *TCG Restock Bot + IA*\n\n"
                        "💬 *Parle-moi librement !*\nPose-moi n'importe quelle question sur les TCG, les prix, les cartes...\n\n"
                        "🔧 *Commandes restock :*\n"
                        "`naruto` `onepiece` `pokemon` `tout`\n"
                        "`pause` `reprend` `status` `sites`\n"
                        "`5 min` `10 min` `30 min` `1h`"
                    )

                elif texte_lower == "naruto":
                    etat["categories"] = ["naruto"]
                    envoyer_telegram("✅ Je surveille uniquement *Naruto TCG* !")

                elif texte_lower == "onepiece":
                    etat["categories"] = ["onepiece"]
                    envoyer_telegram("✅ Je surveille uniquement *One Piece TCG* !")

                elif texte_lower == "pokemon":
                    etat["categories"] = ["pokemon"]
                    envoyer_telegram("✅ Je surveille uniquement *Pokémon TCG* !")

                elif texte_lower == "tout":
                    etat["categories"] = ["naruto", "onepiece", "pokemon"]
                    envoyer_telegram("✅ Je surveille les *3 TCG* !")

                elif "min" in texte_lower:
                    try:
                        minutes = int(''.join(filter(str.isdigit, texte_lower)))
                        etat["intervalle"] = minutes * 60
                        envoyer_telegram(f"✅ Vérification toutes les *{minutes} minutes* !")
                    except:
                        reponse = demander_ia(texte)
                        envoyer_telegram(reponse)

                elif texte_lower == "1h":
                    etat["intervalle"] = 3600
                    envoyer_telegram("✅ Vérification toutes les *1 heure* !")

                elif texte_lower == "pause":
                    etat["actif"] = False
                    envoyer_telegram("⏸ Surveillance *mise en pause*.")

                elif texte_lower in ["reprend", "reprendre", "resume"]:
                    etat["actif"] = True
                    envoyer_telegram("▶️ Surveillance *relancée* !")

                elif texte_lower == "status":
                    cats = ", ".join(etat["categories"]).upper()
                    minutes = etat["intervalle"] // 60
                    actif = "✅ Active" if etat["actif"] else "⏸ En pause"
                    nb = len(get_produits_actifs())
                    envoyer_telegram(
                        f"📊 *Status :*\n\n"
                        f"• État : {actif}\n"
                        f"• TCG : {cats}\n"
                        f"• Intervalle : {minutes} min\n"
                        f"• Sites surveillés : {nb}"
                    )

                elif texte_lower == "sites":
                    produits = get_produits_actifs()
                    liste = "\n".join([f"• {p['nom']}" for p in produits])
                    envoyer_telegram(f"🌐 *Sites surveillés :*\n\n{liste}")

                # ── IA POUR TOUT LE RESTE ─────────────────
                else:
                    envoyer_telegram("🤖 Je cherche une réponse...")
                    reponse = demander_ia(texte)
                    envoyer_telegram(reponse)

        except Exception as e:
            print(f"  ❌ Erreur commandes : {e}")
            time.sleep(5)

# ============================================================
#  🔍  VÉRIFICATION STOCK
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

etats_stock = {}

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
    except:
        return "ERREUR"

def envoyer_alerte(produit_nom, produit_url):
    heure = datetime.now().strftime("%d/%m/%Y à %H:%M:%S")
    envoyer_telegram(
        f"🚨 *RESTOCK DÉTECTÉ !*\n\n"
        f"🎴 *{produit_nom}*\n\n"
        f"🕐 {heure}\n\n"
        f"👉 [VOIR LE PRODUIT]({produit_url})"
    )

# ============================================================
#  🔄  BOUCLE PRINCIPALE
# ============================================================

def main():
    print("=" * 60)
    print("🎴  TCG RESTOCK WATCHER + IA — Démarrage")
    print(f"📱  Telegram : {TELEGRAM_CHAT_ID}")
    print("=" * 60)

    envoyer_telegram(
        "✅ *Bot TCG + IA démarré !*\n\n"
        "🎴 Je surveille *19 sites* pour les restocks\n"
        "🤖 Tu peux aussi me parler librement !\n"
        "🌐 J'ai accès à internet pour répondre\n\n"
        "Envoie `aide` pour voir les commandes disponibles."
    )

    thread = threading.Thread(target=traiter_commandes, daemon=True)
    thread.start()

    while True:
        if etat["actif"]:
            heure = datetime.now().strftime("%H:%M:%S")
            print(f"\n🔍 Vérification à {heure}...")
            produits = get_produits_actifs()

            for produit in produits:
                nom = produit["nom"]
                etat_produit = verifier_stock(produit)
                ancien = etats_stock.get(nom, "INCONNU")

                symbole = "✅" if etat_produit == "EN_STOCK" else "❌" if etat_produit == "RUPTURE" else "⚠️"
                print(f"  {symbole} {nom[:50]:<50} → {etat_produit}")

                if etat_produit == "EN_STOCK" and ancien != "EN_STOCK":
                    print(f"  🚨 RESTOCK ! Alerte envoyée.")
                    envoyer_alerte(nom, produit["url"])

                etats_stock[nom] = etat_produit

            minutes = etat["intervalle"] // 60
            print(f"\n⏳ Prochaine vérification dans {minutes} minutes...")

        time.sleep(etat["intervalle"])

if __name__ == "__main__":
    main()
