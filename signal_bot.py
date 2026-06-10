import os
import random
import logging
import requests
from flask import Flask, request

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "8785431437:AAHxOLTLHhLlwxzDRqzEYFxNBVJ8ClwfYYk"
CHANNEL = "@Inferiq"
VALID_ID = "1695385923"

waiting_for_id = {}
scores = {}


def api(method, data=None):
    try:
        r = requests.post(f"https://api.telegram.org/bot{TOKEN}/{method}", json=data or {}, timeout=10)
        return r.json()
    except Exception as e:
        logger.error(f"{method} error: {e}")
        return {}


def send(chat_id, text, markup=None):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if markup:
        data["reply_markup"] = markup
    api("sendMessage", data)


def typing(chat_id):
    api("sendChatAction", {"chat_id": chat_id, "action": "typing"})


def is_subscribed(user_id):
    try:
        r = requests.get(
            f"https://api.telegram.org/bot{TOKEN}/getChatMember",
            params={"chat_id": CHANNEL, "user_id": user_id}, timeout=10
        )
        d = r.json()
        if d.get("ok"):
            return d["result"]["status"] in ["member", "administrator", "creator"]
    except Exception:
        pass
    return False


def sub_msg(chat_id):
    send(chat_id,
        f"⚠️ <b>Botdan foydalanish uchun kanalga obuna bo'ling!</b>\n\n"
        f"📢 Kanal: {CHANNEL}\n\nObuna bo'lgach ✅ tugmasini bosing",
        markup={
            "inline_keyboard": [
                [{"text": "📢 Kanalga o'tish", "url": "https://t.me/Inferiq"}],
                [{"text": "✅ Obuna bo'ldim", "callback_data": "check_sub"}]
            ]
        }
    )


def main_menu():
    return {
        "keyboard": [
            [{"text": "🍎 O'yin Boshlash"}],
            [{"text": "🏆 Hisobim"}, {"text": "❓ Yordam"}]
        ],
        "resize_keyboard": True
    }


def back_menu():
    return {
        "keyboard": [[{"text": "⬅️ Orqaga"}]],
        "resize_keyboard": True
    }


def game_menu():
    return {
        "keyboard": [
            [{"text": "1️⃣"}, {"text": "2️⃣"}, {"text": "3️⃣"}, {"text": "4️⃣"}, {"text": "5️⃣"}],
            [{"text": "⬅️ Orqaga"}]
        ],
        "resize_keyboard": True
    }


@app.route("/webhook", methods=["POST"])
def webhook():
    u = request.json
    if not u:
        return "ok"

    # Callback
    if "callback_query" in u:
        cb = u["callback_query"]
        chat_id = cb["message"]["chat"]["id"]
        user_id = cb["from"]["id"]
        requests.post(f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery",
                      json={"callback_query_id": cb["id"]}, timeout=5)
        if cb["data"] == "check_sub":
            if is_subscribed(user_id):
                send(chat_id, "✅ Obuna tasdiqlandi! Botdan foydalanishingiz mumkin.", markup=main_menu())
            else:
                send(chat_id, f"❌ Hali obuna bo'lmadingiz!\n{CHANNEL} kanaliga obuna bo'lib qayta bosing.",
                     markup={"inline_keyboard": [
                         [{"text": "📢 Kanalga o'tish", "url": "https://t.me/Inferiq"}],
                         [{"text": "✅ Obuna bo'ldim", "callback_data": "check_sub"}]
                     ]})
        return "ok"

    msg = u.get("message")
    if not msg:
        return "ok"

    chat_id = msg["chat"]["id"]
    user_id = msg["from"]["id"]
    text = msg.get("text", "").strip()

    if not text:
        return "ok"

    # Obuna tekshirish
    if not is_subscribed(user_id):
        sub_msg(chat_id)
        return "ok"

    # Scores initsializatsiya
    if chat_id not in scores:
        scores[chat_id] = {"wins": 0, "total": 0}

    # /start
    if text == "/start":
        waiting_for_id[chat_id] = False
        send(chat_id,
            "🍎 <b>Apple of Fortune</b>\n\n"
            "Salom! Bu qiziqarli mini o'yin!\n\n"
            "🎮 Qanday o'ynash:\n"
            "• O'yin boshlash tugmasini bosing\n"
            "• ID kiriting\n"
            "• 1-5 orasidan raqam tanlang\n"
            "• To'g'ri topgan bo'lsangiz 🏆 yutasiz!\n\n"
            "<i>Inferiq jamoasi</i>",
            markup=main_menu()
        )
        return "ok"

    # O'yin boshlash
    if text == "🍎 O'yin Boshlash":
        waiting_for_id[chat_id] = True
        send(chat_id,
            "🔐 <b>ID ni kiriting:</b>\n\n"
            "Hisob raqamingizni yozing\n"
            "<i>Misol: 1695385923</i>",
            markup=back_menu()
        )
        return "ok"

    # Orqaga
    if text == "⬅️ Orqaga":
        waiting_for_id[chat_id] = False
        scores[chat_id]["game_number"] = None
        send(chat_id, "🏠 Bosh menyu", markup=main_menu())
        return "ok"

    # Hisobim
    if text == "🏆 Hisobim":
        w = scores[chat_id]["wins"]
        t = scores[chat_id]["total"]
        pct = int(w / t * 100) if t > 0 else 0
        send(chat_id,
            f"🏆 <b>Sizning hisobingiz:</b>\n\n"
            f"🎮 Jami o'yinlar: {t}\n"
            f"✅ Yutishlar: {w}\n"
            f"❌ Yutqizishlar: {t - w}\n"
            f"📊 Foiz: {pct}%",
            markup=main_menu()
        )
        return "ok"

    # Yordam
    if text in ["❓ Yordam", "/help"]:
        send(chat_id,
            "📖 <b>Yordam</b>\n\n"
            "1️⃣ 🍎 O'yin Boshlash tugmasini bosing\n"
            "2️⃣ ID ni kiriting\n"
            "3️⃣ 1-5 orasidan raqam tanlang\n"
            "4️⃣ To'g'ri topgan bo'lsangiz yutasiz!\n\n"
            f"📢 Kanal: {CHANNEL}\n"
            "<i>Inferiq jamoasi</i>",
            markup=main_menu()
        )
        return "ok"

    # ID tekshirish
    if waiting_for_id.get(chat_id):
        entered = text.strip()

        if not entered.isdigit() or len(entered) != 10:
            send(chat_id,
                "❌ <b>Noto'g'ri format!</b>\n\n"
                "ID 10 ta raqamdan iborat bo'lishi kerak.\n"
                "Qayta kiriting:",
                markup=back_menu()
            )
            return "ok"

        if entered != VALID_ID:
            send(chat_id,
                "❌ <b>Xato ID!</b>\n\n"
                "Bu ID topilmadi.\n"
                "ID ni tekshirib qayta kiriting:",
                markup=back_menu()
            )
            return "ok"

        # To'g'ri ID — o'yinni boshlash
        waiting_for_id[chat_id] = False
        secret = random.randint(1, 5)
        scores[chat_id]["secret"] = secret
        scores[chat_id]["guessing"] = True

        send(chat_id,
            "✅ <b>ID tasdiqlandi!</b>\n\n"
            "🎮 <b>O'yin boshlanadi!</b>\n\n"
            "1️⃣ 2️⃣ 3️⃣ 4️⃣ 5️⃣\n\n"
            "Qaysi katak ostida 🍎 yashiringan?\n"
            "Raqamni tanlang 👇",
            markup=game_menu()
        )
        return "ok"

    # O'yin jarayonida raqam tanlash
    if scores[chat_id].get("guessing") and text in ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]:
        num_map = {"1️⃣": 1, "2️⃣": 2, "3️⃣": 3, "4️⃣": 4, "5️⃣": 5}
        guess = num_map[text]
        secret = scores[chat_id].get("secret", random.randint(1, 5))
        emojis = {1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣", 5: "5️⃣"}

        scores[chat_id]["total"] += 1
        scores[chat_id]["guessing"] = False

        typing(chat_id)

        if guess == secret:
            scores[chat_id]["wins"] += 1
            send(chat_id,
                f"🎉 <b>To'g'ri topdingiz!</b>\n\n"
                f"Siz {emojis[guess]} ni tanladingiz\n"
                f"🍎 Olma {emojis[secret]} da edi!\n\n"
                f"✅ <b>YUTDINGIZ!</b> 🏆\n\n"
                f"Jami yutishlar: {scores[chat_id]['wins']} / {scores[chat_id]['total']}",
                markup=main_menu()
            )
        else:
            send(chat_id,
                f"😔 <b>Noto'g'ri!</b>\n\n"
                f"Siz {emojis[guess]} ni tanladingiz\n"
                f"🍎 Olma {emojis[secret]} da edi!\n\n"
                f"❌ <b>Yutqazdingiz!</b>\n\n"
                f"Jami yutishlar: {scores[chat_id]['wins']} / {scores[chat_id]['total']}",
                markup=main_menu()
            )
        return "ok"

    # Boshqa
    send(chat_id, "👇 Tugmani bosing:", markup=main_menu())
    return "ok"


@app.route("/")
def index():
    return "Apple of Fortune Bot ✅"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
