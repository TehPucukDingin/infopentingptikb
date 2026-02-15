import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
from datetime import datetime, timedelta
import os
import pytz

# =========================
TZ = pytz.timezone("Asia/Makassar")

TOKEN = os.getenv("TOKEN")
REMINDER_CHANNEL_ID = 1471544536072327300
ROLE_ID = 1428264636549169152

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "tugas.json"

# =========================
# LOAD & SAVE
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
# =========================

@bot.tree.command(name="tambah", description="Tambah tugas baru")
async def tambah(
    interaction: discord.Interaction,
    nama: str,
    tanggal: str,
    jam: str,
    notes: str = "Tidak ada catatan"
):
    try:
        deadline = TZ.localize(
            datetime.strptime(f"{tanggal} {jam}", "%Y-%m-%d %H:%M")
        )
    except:
        await interaction.response.send_message(
            "❌ Format salah! Gunakan YYYY-MM-DD dan HH:MM",
            ephemeral=True
        )
        return

    data = load_tugas()

    data.append({
        "nama": nama,
        "deadline": deadline.strftime("%Y-%m-%d %H:%M"),
        "notes": notes,
        "reminded": {
            "24h": False,
            "3h": False,
            "1h": False,
            "deadline": False
        }
    })

    save_tugas(data)

    embed = discord.Embed(
        title=f"📚 {nama}",
        description="✅ Tugas berhasil ditambahkan",
        color=discord.Color.green()
    )

    embed.add_field(name="📅 Deadline",
                    value=deadline.strftime("%A, %d %B %Y"),
                    inline=False)

    embed.add_field(name="⏰ Jam",
                    value=f"{deadline.strftime('%H:%M')} WITA",
                    inline=False)

    embed.add_field(name="📝 Notes",
                    value=notes,
                    inline=False)

    embed.set_footer(text="INFO PENTING BOT")
    embed.timestamp = deadline

    await interaction.response.send_message(embed=embed)

# =========================
# LIST TUGAS
# =========================

@bot.tree.command(name="list", description="Lihat semua tugas")
async def list_tugas(interaction: discord.Interaction):
    data = load_tugas()

    if not data:
        await interaction.response.send_message("📂 Tidak ada tugas.")
        return

    embeds = []

    for tugas in data:
        deadline = TZ.localize(
            datetime.strptime(tugas["deadline"], "%Y-%m-%d %H:%M")
        )

        notes = tugas.get("notes", "Tidak ada catatan")

        embed = discord.Embed(
            title=f"📚 {tugas['nama']}",
            color=discord.Color.blurple()
        )

        embed.add_field(name="📅 Deadline",
                        value=deadline.strftime("%A, %d %B %Y"),
                        inline=False)

        embed.add_field(name="⏰ Jam",
                        value=f"{deadline.strftime('%H:%M')} WITA",
                        inline=False)

        embed.add_field(name="📝 Notes",
                        value=notes,
                        inline=False)

        embed.set_footer(text="INFO PENTING BOT")
        embed.timestamp = deadline

        embeds.append(embed)

    await interaction.response.send_message(embeds=embeds)

# =========================
# REMINDER SYSTEM
# =========================

@tasks.loop(minutes=1)
async def reminder_loop():
    channel = bot.get_channel(REMINDER_CHANNEL_ID)

    if channel is None:
        channel = await bot.fetch_channel(REMINDER_CHANNEL_ID)

    data = load_tugas()
    sekarang = datetime.now(TZ)
    mention_role = f"<@&{ROLE_ID}>"
    updated = False

    for tugas in data:
        deadline = TZ.localize(
            datetime.strptime(tugas["deadline"], "%Y-%m-%d %H:%M")
        )

        sisa = deadline - sekarang
        notes = tugas.get("notes", "Tidak ada catatan")

        def build_embed(title, color):
            embed = discord.Embed(title=title, color=color)
            embed.add_field(name="📅 Deadline",
                            value=deadline.strftime("%A, %d %B %Y"),
                            inline=False)
            embed.add_field(name="⏰ Jam",
                            value=f"{deadline.strftime('%H:%M')} WITA",
                            inline=False)
            embed.add_field(name="📝 Notes",
                            value=notes,
                            inline=False)
            embed.set_footer(text="INFO PENTING BOT")
            embed.timestamp = deadline
            return embed

        if 0 < sisa.total_seconds() <= 86400 and not tugas["reminded"]["24h"]:
            await channel.send(content=mention_role,
                               embed=build_embed(f"🔔 H-24 JAM\n📚 {tugas['nama']}",
                                                 discord.Color.blue()))
            tugas["reminded"]["24h"] = True
            updated = True

        if 0 < sisa.total_seconds() <= 10800 and not tugas["reminded"]["3h"]:
            await channel.send(content=mention_role,
                               embed=build_embed(f"⚠️ H-3 JAM\n📚 {tugas['nama']}",
                                                 discord.Color.orange()))
            tugas["reminded"]["3h"] = True
            updated = True

        if 0 < sisa.total_seconds() <= 3600 and not tugas["reminded"]["1h"]:
            await channel.send(content=mention_role,
                               embed=build_embed(f"🔥 H-1 JAM\n📚 {tugas['nama']}",
                                                 discord.Color.red()))
            tugas["reminded"]["1h"] = True
            updated = True

        if sisa.total_seconds() <= 0 and not tugas["reminded"]["deadline"]:
            await channel.send(content=mention_role,
                               embed=build_embed(f"🚨 DEADLINE SEKARANG\n📚 {tugas['nama']}",
                                                 discord.Color.dark_red()))
            tugas["reminded"]["deadline"] = True
            updated = True

    if updated:
        save_tugas(data)

# =========================
# AUTO HAPUS DEADLINE LEWAT
# =========================

@tasks.loop(minutes=1)
async def check_deadlines():
    data = load_tugas()
    sekarang = datetime.now(TZ)

    data_baru = []

    for tugas in data:
        deadline = TZ.localize(
            datetime.strptime(tugas["deadline"], "%Y-%m-%d %H:%M")
        )

        if deadline > sekarang:
            data_baru.append(tugas)

    save_tugas(data_baru)

# =========================
# DELETE & CLEAR
# =========================

@bot.tree.command(name="hapus", description="Hapus tugas")
async def hapus(interaction: discord.Interaction, nama: str):
    data = load_tugas()
    data_baru = [t for t in data if t["nama"].lower() != nama.lower()]

    if len(data) == len(data_baru):
        await interaction.response.send_message("❌ Tugas tidak ditemukan.", ephemeral=True)
        return

    save_tugas(data_baru)
    await interaction.response.send_message(f"🗑 Tugas **{nama}** berhasil dihapus.")

@bot.tree.command(name="clear", description="Hapus semua tugas")
async def clear(interaction: discord.Interaction):
    save_tugas([])
    await interaction.response.send_message("🧹 Semua tugas berhasil dihapus.")

# =========================
# READY
# =========================

@bot.event
async def on_ready():
    print(f"Bot aktif sebagai {bot.user}")

    # 1️⃣ Hapus semua GLOBAL command lama
    bot.tree.clear_commands(guild=None)
    await bot.tree.sync()

    print("Global command dihapus")

    # 2️⃣ Sync ulang sebagai GLOBAL command versi baru
    synced = await bot.tree.sync()
    print(f"Global command tersinkron ulang: {len(synced)}")

    if not reminder_loop.is_running():
        reminder_loop.start()

    if not check_deadlines.is_running():
        check_deadlines.start()

bot.run(TOKEN)

