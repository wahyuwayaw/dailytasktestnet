from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ApplicationBuilder
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import asyncio
import sqlite3
import os

# === BOT TOKEN ===
BOT_TOKEN = os.getenv("BOT_TOKEN") or "8150499936:AAGddGk-KJ8ACY_ssptD7OCE54_EJdh6DEg"

# === Default testnet list ===
default_task_links = {
    "Fraction AI": "https://t.me/airdropfind/101646",
    "KiteAI": "https://t.me/airdropfind/102772",
    "03Layer": "https://t.me/airdropfind/103350",
    "0g Testnet (Danom Site - Node)": "https://t.me/crowid/163",
    "Yala": "https://t.me/airdropfind/104685",
    "Somnia": "https://quest.somnia.network/campaigns",
    "MegaETH": "https://t.me/airdropfind/105271",
    "T3RN": "https://bridge.t2rn.io/",
    "Union": "https://t.me/crowid/179",
    "Seismic": "https://t.me/airdropfind/106029",
    "T1": "https://airdrop.tokenomy.app/airdrops/detail/261",
    "Alpha Dyson": "https://t.me/airdropfind/105684",
    "Incentive Programs": "https://t.me/airdropfind/106102",
    "EuclidSwap": "https://t.me/airdropfind/106733",
    "SEAL (SUI)": "https://t.me/airdropfind/105938",
    "N1 (Solana)": "https://01.xyz/",
    "INCO": "https://t.me/airdropfind/107143",
    "OP Net": "https://t.me/c/2294721332/5069",
    "Aztec": "https://t.me/c/2294721332/5117",
    "SOUL PROTOCOL": "https://t.me/ZeroDropDAO/1041",
    "NEXUS MINING": "https://app.nexus.xyz/",
    "HELIOS": "https://t.me/crowid/191",
    "PHAROS": "https://t.me/airdropfind/108028"
}

# === Database setup ===
conn = sqlite3.connect('progress.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS progress (user_id INTEGER, task TEXT, status TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS delay_settings (user_id INTEGER, task TEXT, delay INTEGER)')
c.execute('CREATE TABLE IF NOT EXISTS task_links_custom (user_id INTEGER, task TEXT, link TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS notif (user_id INTEGER)')
conn.commit()

def get_all_tasks(user_id):
    c.execute("SELECT task, link FROM task_links_custom WHERE user_id=?", (user_id,))
    custom = dict(c.fetchall())
    all_tasks = default_task_links.copy()
    all_tasks.update(custom)
    return all_tasks

# === Commands ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    task_links = get_all_tasks(user_id)
    keyboard = [
        [InlineKeyboardButton(task, callback_data=f"view_{task}")]
        for task in task_links.keys()
    ]
    await update.message.reply_text("\ud83d\udccb Pilih task untuk lihat link & ubah status:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    task_links = get_all_tasks(user_id)

    if data.startswith("view_"):
        task = data.replace("view_", "")
        link = task_links.get(task, "Tidak ditemukan.")
        status_buttons = [
            [
                InlineKeyboardButton("\u2705 Selesai", callback_data=f"status_{task}_done"),
                InlineKeyboardButton("\u2699\ufe0f Progress", callback_data=f"status_{task}_progress"),
                InlineKeyboardButton("\u274c Belum", callback_data=f"status_{task}_none"),
            ]
        ]
        await query.edit_message_text(f"\ud83d\udd17 Link: {link}\n\n\ud83d\udccc Status task: {task}", reply_markup=InlineKeyboardMarkup(status_buttons))

    elif data.startswith("status_"):
        parts = data.split("_")
        task = "_".join(parts[1:-1])
        status = parts[-1]
        c.execute("REPLACE INTO progress (user_id, task, status) VALUES (?, ?, ?)", (user_id, task, status))
        conn.commit()
        await query.edit_message_text(f"\u2705 Status task *{task}* diset ke: {status.upper()}", parse_mode="Markdown")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    all_tasks = get_all_tasks(user_id)
    c.execute("SELECT task, status FROM progress WHERE user_id=?", (user_id,))
    rows = dict(c.fetchall())
    msg = "**\ud83d\udcca Status Task Kamu:**\n\n"
    for task in all_tasks:
        st = rows.get(task, "none")
        emoji = {"done": "\u2705", "progress": "\u2699\ufe0f", "none": "\u274c"}.get(st, "\u274c")
        msg += f"{emoji} {task}\n"
    await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)

async def tambah_testnet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    msg = update.message.text.replace("/tambahtestnet", "").strip()
    if "|" not in msg:
        await update.message.reply_text("Format salah!\nContoh: `/tambahtestnet MegaSwap | https://link.com`", parse_mode="Markdown")
        return
    name, link = [s.strip() for s in msg.split("|", 1)]
    c.execute("INSERT INTO task_links_custom (user_id, task, link) VALUES (?, ?, ?)", (user_id, name, link))
    conn.commit()
    await update.message.reply_text(f"\u2705 Testnet `{name}` berhasil ditambahkan!", parse_mode="Markdown")

async def setting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    args = update.message.text.replace("/setting", "").strip().split()
    if len(args) != 2 or not args[1].isdigit():
        await update.message.reply_text("Format salah!\nContoh: `/setting 03Layer 180`", parse_mode="Markdown")
        return
    task, delay = args[0], int(args[1])
    c.execute("REPLACE INTO delay_settings (user_id, task, delay) VALUES (?, ?, ?)", (user_id, task, delay))
    conn.commit()
    await update.message.reply_text(f"\u23f1\ufe0f Delay untuk `{task}` disetel ke {delay} detik.", parse_mode="Markdown")

async def notif_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cmd = update.message.text.strip().split()
    if len(cmd) < 2:
        await update.message.reply_text("Contoh: /notifikasi on atau /notifikasi off")
        return
    action = cmd[1].lower()
    if action == "on":
        c.execute("INSERT OR IGNORE INTO notif (user_id) VALUES (?)", (user_id,))
        conn.commit()
        await update.message.reply_text("\u2705 Notifikasi harian diaktifkan.")
    elif action == "off":
        c.execute("DELETE FROM notif WHERE user_id=?", (user_id,))
        conn.commit()
        await update.message.reply_text("\u274c Notifikasi harian dimatikan.")

async def kirim_notif():
    c.execute("SELECT user_id FROM notif")
    users = c.fetchall()
    for (user_id,) in users:
        all_tasks = get_all_tasks(user_id)
        c.execute("SELECT task, status FROM progress WHERE user_id=?", (user_id,))
        done = {task for task, status in c.fetchall() if status == "done"}
        pending = [t for t in all_tasks if t not in done]
        if pending:
            pesan = "\ud83d\udccc *Reminder Testnet Harian*\n\nTask belum selesai:\n" + "\n".join(f"\u274c {t}" for t in pending)
        else:
            pesan = "\ud83c\udf89 Semua testnet sudah kamu selesaikan hari ini, mantap!"
        try:
            await app.bot.send_message(chat_id=user_id, text=pesan, parse_mode="Markdown")
        except:
            pass

# === Scheduler untuk notifikasi ===
scheduler = BackgroundScheduler()
scheduler.add_job(lambda: asyncio.run(kirim_notif()), 'cron', hour=9, minute=0)
scheduler.start()

# === Jalankan bot ===
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("status", status))
app.add_handler(CommandHandler("tambahtestnet", tambah_testnet))
app.add_handler(CommandHandler("setting", setting))
app.add_handler(CommandHandler("notifikasi", notif_cmd))
app.add_handler(CallbackQueryHandler(button))
app.run_polling()
