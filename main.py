import os, json, tempfile
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import google.generativeai as genai
from groq import Groq

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

PROMPT = """Kamu Auditor TikTok 2026. Cek vs aturan: Klaim Medis, Fear, Graphic, Redirect, Tanpa #TikTokShop. Input: {video_text} | {caption}. Balas HANYA JSON: {"skor":int,"status":"str","pelanggaran":[str],"caption_aman":str}"""

async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    await u.message.reply_text("Halo 👋 Kirim 1 video + caption. Gratis 5x/hari.")

async def audit(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not u.message.video: return await u.message.reply_text("Kirim video + caption.")
    msg = await u.message.reply_text("⏳ Audit 20 detik...")
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        await (await u.message.video.get_file()).download_to_drive(tmp.name)
        txt = genai.GenerativeModel('gemini-1.5-flash').generate_content(["Jelaskan video ini.", genai.upload_file(tmp.name)]).text
    res = json.loads(groq_client.chat.completions.create(messages=[{"role":"user","content":PROMPT.format(video_text=txt,caption=u.message.caption or "")}],model="llama-3.1-8b-instant",response_format={"type":"json_object"}).choices[0].message.content)
    await msg.edit_text(f"**Skor: {res['skor']}/100 | {res['status']}**\n\n**Pelanggaran:**\n- "+"- ".join(res['pelanggaran'])+f"\n\n**Caption Aman:**\n{res['caption_aman']}", parse_mode='Markdown')
    os.remove(tmp.name)

ApplicationBuilder().token(TELEGRAM_TOKEN).build().add_handler(CommandHandler("start", start)).add_handler(MessageHandler(filters.VIDEO & filters.CAPTION, audit)).run_polling()