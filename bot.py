import discord
from discord.ext import commands, tasks
import json
from datetime import datetime
import os

TOKEN = "ISI_TOKEN_KAMU_DISINI"
REMINDER_CHANNEL_ID = 1471503842205106216
ROLE_ID = 1428267266222460948

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
            "deadline": deadline_str,
            "reminded": {
                "24h": False,
                "3h": False,
                "1h": False,
                "deadline": False
            }
        })

        save_tugas(data)

        await ctx.send(
            f"✅ **{nama}** berhasil ditambahkan!\n"
            f"🗓 Deadline: {deadline.strftime('%d %B %Y')}\n"
            f"⏰ Jam: {deadline.strftime('%H:%M')} WITA"
        )

    except:
        await ctx.send("❌ Format salah!\nGunakan: `!tambah RPL 2026-02-15 23:59`")


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
# REMINDER TUGAS
# =========================

@tasks.loop(minutes=1)
async def reminder_loop():
    channel = bot.get_channel(REMINDER_CHANNEL_ID)
    if not channel:
        return

    data = load_tugas()
    sekarang = datetime.now()

    for tugas in data:
        deadline = datetime.strptime(tugas["deadline"], "%Y-%m-%d %H:%M")
        sisa = deadline - sekarang
        mention_role = f"<@&{ROLE_ID}>"

        # H-24 JAM
        if sisa.total_seconds() <= 86400 and not tugas["reminded"]["24h"] and sisa.total_seconds() > 0:
            embed = discord.Embed(
                title="⏰ REMINDER H-1",
                description=f"📌 **{tugas['nama']}**",
                color=discord.Color.blue()
            )
            embed.add_field(name="Deadline", value=deadline.strftime("%A, %d %B %Y\n%H:%M WITA"))
            embed.set_footer(text="INFO PENTING BOT")
            embed.timestamp = deadline

            await channel.send(content=mention_role, embed=embed)
            tugas["reminded"]["24h"] = True

        # H-3 JAM
        if sisa.total_seconds() <= 10800 and not tugas["reminded"]["3h"] and sisa.total_seconds() > 0:
            embed = discord.Embed(
                title="⚠️ REMINDER 3 JAM LAGI",
                description=f"📌 **{tugas['nama']}**",
                color=discord.Color.orange()
            )
            embed.add_field(name="Deadline", value=deadline.strftime("%A, %d %B %Y\n%H:%M WITA"))
            embed.timestamp = deadline

            await channel.send(content=mention_role, embed=embed)
            tugas["reminded"]["3h"] = True

        # H-1 JAM
        if sisa.total_seconds() <= 3600 and not tugas["reminded"]["1h"] and sisa.total_seconds() > 0:
            embed = discord.Embed(
                title="🔥 REMINDER 1 JAM LAGI",
                description=f"📌 **{tugas['nama']}**",
                color=discord.Color.red()
            )
            embed.add_field(name="Deadline", value=deadline.strftime("%A, %d %B %Y\n%H:%M WITA"))
            embed.timestamp = deadline

            await channel.send(content=mention_role, embed=embed)
            tugas["reminded"]["1h"] = True

        # DEADLINE
        if sisa.total_seconds() <= 0 and not tugas["reminded"]["deadline"]:
            embed = discord.Embed(
                title="🚨 DEADLINE SEKARANG!",
                description=f"📌 **{tugas['nama']}**",
                color=discord.Color.dark_red()
            )
            embed.add_field(name="Waktu", value=deadline.strftime("%A, %d %B %Y\n%H:%M WITA"))
            embed.timestamp = sekarang

            await channel.send(content=mention_role, embed=embed)
            tugas["reminded"]["deadline"] = True

    save_tugas(data)

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

# =========================
@bot.event
async def on_ready():
    print(f"Bot aktif sebagai {bot.user}")
    check_deadlines.start()
    reminder_loop.start()

bot.run(TOKEN)
