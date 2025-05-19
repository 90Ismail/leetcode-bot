from keep_alive import keep_alive
import os
os.system("pip install discord.py apscheduler")

import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.ui import Button, View
import datetime, json

TOKEN = os.environ['TOKEN']
CHANNEL_ID = 1261874667011182753  # your channel ID
STREAK_FILE = "streaks.json"

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
scheduler = AsyncIOScheduler()

# Load or initialize streaks
if os.path.exists(STREAK_FILE):
    with open(STREAK_FILE, "r") as f:
        streak_data = json.load(f)
else:
    streak_data = {}

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    if not os.path.exists(STREAK_FILE):
        with open(STREAK_FILE, "w") as f:
            json.dump({}, f)
    scheduler.add_job(send_daily_question, "cron", hour=5, minute=0)
    scheduler.start()

async def send_daily_question():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ Channel not found.")
        return

    today = str(datetime.date.today())
    button = Button(label="✅ I Did It", style=discord.ButtonStyle.success)

    async def button_callback(interaction):
        user_id = str(interaction.user.id)
        yesterday = str(datetime.date.today() - datetime.timedelta(days=1))

        previous = streak_data.get(user_id, {"streak": 0, "last": None})
        if previous["last"] == today:
            await interaction.response.send_message("Already checked in today!", ephemeral=True)
            return

        new_streak = previous["streak"] + 1 if previous["last"] == yesterday else 1
        streak_data[user_id] = {"streak": new_streak, "last": today}

        with open(STREAK_FILE, "w") as f:
            json.dump(streak_data, f)

        await interaction.response.send_message(f"🔥 You're at {new_streak} day(s)!", ephemeral=True)

    view = View()
    view.add_item(button)

    await channel.send(f"📅 **{today}**\nClick the button if you solved LeetCode today 👇", view=view)

@bot.command()
async def streak(ctx):
    user_id = str(ctx.author.id)
    user_data = streak_data.get(user_id, {"streak": 0})
    await ctx.send(f"🔥 {ctx.author.mention}, your current LeetCode streak is **{user_data['streak']}** day(s)!")

@bot.command()
async def leaderboard(ctx):
    leaderboard = [(int(uid), data["streak"]) for uid, data in streak_data.items() if uid.isdigit()]
    leaderboard.sort(key=lambda x: x[1], reverse=True)
    top_5 = leaderboard[:5]
    lines = ["🏆 **Top LeetCode Streaks**"]
    for i, (uid, streak) in enumerate(top_5, 1):
        user = await bot.fetch_user(uid)
        lines.append(f"{i}. {user.name} — {streak} day(s)")
    await ctx.send("\n".join(lines))

keep_alive()
bot.run(TOKEN)
