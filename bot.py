import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
from datetime import datetime
import os
import pytz
from datetime import datetime

from datetime import timedelta

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
@bot.tree.command(name="tambah", description="Tambah tugas baru")
async def tambah(interaction: discord.Interaction, nama: str, tanggal: str, jam: str):
    try:
        deadline = TZ.localize(
            datetime.strptime(f"{tanggal} {jam}", "%Y-%m-%d %H:%M")
        )

        data = load_tugas()

        data.append({
            "nama": nama,
            "deadline": deadline.strftime("%Y-%m-%d %H:%M"),
            "reminded": {
                "24h": False,
                "3h": False,
                "1h": False,
                "deadline": False
            }
        })

        save_tugas(data)

        await interaction.response.send_message(
            f"✅ **{nama}** berhasil ditambahkan!\n"
            f"🗓 {deadline.strftime('%A, %d %B %Y')}\n"
            f"⏰ {deadline.strftime('%H:%M')} WITA"
        )

    except:
        await interaction.response.send_message(
            "❌ Format salah! Gunakan YYYY-MM-DD dan HH:MM",
            ephemeral=True
        )


# =========================
# LIST TUGAS
# =========================

@bot.tree.command(name="list", description="Lihat semua tugas")
async def list_tugas(interaction: discord.Interaction):
    data = load_tugas()

    if not data:
        await interaction.response.send_message("📂 Tidak ada tugas.")
        return

    pesan = "📌 **Daftar Tugas:**\n"

    for tugas in data:
        deadline = TZ.localize(
            datetime.strptime(tugas["deadline"], "%Y-%m-%d %H:%M")
        )

        pesan += (
            f"\n📝 {tugas['nama']}"
            f"\n📅 {deadline.strftime('%A, %d %B %Y')}"
            f"\n⏰ {deadline.strftime('%H:%M')} WITA\n"
        )

    await interaction.response.send_message(pesan)

# =========================
# REMINDER TUGAS
# =========================

@tasks.loop(minutes=1)
async def reminder_loop():
    channel = bot.get_channel(REMINDER_CHANNEL_ID)

    if channel is None:
        channel = await bot.fetch_channel(REMINDER_CHANNEL_ID)

    data = load_tugas()
    sekarang = datetime.now(TZ)

    for tugas in data:
        deadline_naive = datetime.strptime(tugas["deadline"], "%Y-%m-%d %H:%M")
        deadline = TZ.localize(deadline_naive)
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
    sekarang = datetime.now(TZ)

    data_baru = []

    for tugas in data:
        deadline_naive = datetime.strptime(tugas["deadline"], "%Y-%m-%d %H:%M")
        deadline = TZ.localize(deadline_naive)

        if deadline > sekarang:
            data_baru.append(tugas)

    save_tugas(data_baru)

# =========================
# HAPUS TUGAS
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

# =========================
# EDIT DEADLINE
# =========================
@bot.tree.command(name="edit", description="Edit deadline tugas")
async def edit(interaction: discord.Interaction, nama: str, tanggal: str, jam: str):
    data = load_tugas()
    ditemukan = False

    for tugas in data:
        if tugas["nama"].lower() == nama.lower():
            deadline = TZ.localize(
                datetime.strptime(f"{tanggal} {jam}", "%Y-%m-%d %H:%M")
            )

            tugas["deadline"] = deadline.strftime("%Y-%m-%d %H:%M")
            tugas["reminded"] = {
                "24h": False,
                "3h": False,
                "1h": False,
                "deadline": False
            }

            ditemukan = True
            break

    if not ditemukan:
        await interaction.response.send_message("❌ Tugas tidak ditemukan.", ephemeral=True)
        return

    save_tugas(data)
    await interaction.response.send_message(f"✏️ Deadline **{nama}** berhasil diperbarui.")

# =========================
# CLEAR SEMUA TUGAS
# =========================
@bot.tree.command(name="clear", description="Hapus semua tugas")
async def clear(interaction: discord.Interaction):
    save_tugas([])
    await interaction.response.send_message("🧹 Semua tugas berhasil dihapus.")

# =========================
# LIHAT TUGAS BESOK
# =========================
@bot.tree.command(name="besok", description="Lihat tugas deadline besok")
async def besok(interaction: discord.Interaction):
    data = load_tugas()
    sekarang = datetime.now(TZ)
    besok_tanggal = (sekarang + timedelta(days=1)).date()

    pesan = "📅 **Tugas Deadline Besok:**\n"
    ada = False

    for tugas in data:
        deadline = TZ.localize(
            datetime.strptime(tugas["deadline"], "%Y-%m-%d %H:%M")
        )

        if deadline.date() == besok_tanggal:
            pesan += f"\n📝 {tugas['nama']}\n⏰ {deadline.strftime('%H:%M')} WITA\n"
            ada = True

    if not ada:
        await interaction.response.send_message("🎉 Tidak ada tugas deadline besok.")
        return

    await interaction.response.send_message(pesan)

# =========================
# HELP MENU
# =========================
@bot.command()
async def helpbot(ctx):
    embed = discord.Embed(
        title="📌 INFO PENTING BOT - Command List",
        color=discord.Color.green()
    )

    embed.add_field(name="!tambah", value="Tambah tugas", inline=False)
    embed.add_field(name="!list", value="Lihat semua tugas", inline=False)
    embed.add_field(name="!hapus", value="Hapus tugas", inline=False)
    embed.add_field(name="!edit", value="Edit deadline tugas", inline=False)
    embed.add_field(name="!besok", value="Lihat tugas deadline besok", inline=False)
    embed.add_field(name="!clear", value="Hapus semua tugas", inline=False)

    await ctx.send(embed=embed)

# =========================
@bot.event
async def on_ready():
    print(f"Bot aktif sebagai {bot.user}")

    try:
        synced = await bot.tree.sync()
        print(f"Slash command tersinkron: {len(synced)}")
    except Exception as e:
        print(e)

    if not reminder_loop.is_running():
        reminder_loop.start()

    if not check_deadlines.is_running():
        check_deadlines.start()

bot.run(TOKEN)


