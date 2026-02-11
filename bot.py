import discord
from discord.ext import commands
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot aktif sebagai {bot.user}")

@bot.command()
async def halo(ctx):
    await ctx.send("DIH APASIH KONTOL")

bot.run(TOKEN)
