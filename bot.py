import discord
from discord.ext import commands, tasks
import json
from datetime import datetime
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "tugas.json"

# =========================
# LOAD & SAVE DATA
# =========================

def load_tugas():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_tugas(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# =========================
# TAMBAH TUGAS
# Format:
# !tambah NamaTugas 2026-02-15 23:59
# =========================

@bot.command()
async def tambah(ctx, nama: str, tanggal: str, jam: str):
    try:
        deadline_str = f"{tanggal} {jam}"
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M")

        data = load_tugas()

        data.append({
            "nama": nama,
            "deadline": deadline.strftime("%Y-%m-%d %H:%M")
        })

        save_tugas(data)

        await ctx.send(f"✅ Tugas **{nama}** ditambahkan!\n🕒 Deadline: {deadline_str}")

    except:
        await ctx.send("❌ Format salah!\nContoh: `!tambah Matematika 2026-02-15 23:59`")

# =========================
# LIST TUGAS
# =========================

@bot.command()
async def list(ctx):
    data = load_tugas()

    if not data:
        await ctx.send("📂 Tidak ada tugas.")
        return

    pesan = "📌 **Daftar Tugas:**\n"

    for tugas in data:
        deadline = datetime.strptime(tugas["deadline"], "%Y-%m-%d %H:%M")
        hari = deadline.strftime("%A")
        pesan += f"\n📝 {tugas['nama']}\n📅 {hari}, {deadline.strftime('%d %B %Y')}\n⏰ {deadline.strftime('%H:%M')}\n"

    await ctx.send(pesan)

# =========================
# AUTO HAPUS DEADLINE LEWAT
# =========================

@tasks.loop(minutes=1)
async def check_deadlines():
    data = load_tugas()
    sekarang = datetime.now()

    data_baru = []

    for tugas in data:
        deadline = datetime.strptime(tugas["deadline"], "%Y-%m-%d %H:%M")
        if deadline > sekarang:
            data_baru.append(tugas)

    save_tugas(data_baru)

@bot.event
async def on_ready():
    print(f"Bot aktif sebagai {bot.user}")
    check_deadlines.start()

bot.run(TOKEN)

