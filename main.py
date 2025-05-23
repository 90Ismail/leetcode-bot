import os
import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.ui import View, Button
import datetime, json
from keep_alive import keep_alive
from pytz import timezone

TOKEN = os.environ["TOKEN"]
CHANNEL_ID = 1261874667011182753
STREAK_FILE = "streaks.json"

# Use your local timezone (adjust as needed)
LOCAL_TZ = timezone("America/Chicago")  # or use "UTC" if unsure

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
scheduler = AsyncIOScheduler(timezone=LOCAL_TZ)

# Load or initialize streaks
if os.path.exists(STREAK_FILE):
    with open(STREAK_FILE, "r") as f:
        streak_data = json.load(f)
else:
    streak_data = {}

# Button view
class DailyButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✅ I Did It", style=discord.ButtonStyle.success)
    async def did_it_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        today = str(datetime.date.today())

        if streak_data.get("today") != today:
            await interaction.response.send_message("This button is no longer active.", ephemeral=True)
            return

        if user_id in streak_data["responses"]:
            await interaction.response.send_message("You've already responded today ✅", ephemeral=True)
            return

        previous = streak_data.get(user_id, {"streak": 0, "last": None})
        yesterday = str(datetime.date.today() - datetime.timedelta(days=1))

        if previous["last"] == yesterday:
            new_streak = previous["streak"] + 1
        else:
            new_streak = 1

        streak_data[user_id] = {
            "streak": new_streak,
            "last": today
        }
        streak_data["responses"][user_id] = "yes"

        with open(STREAK_FILE, "w") as f:
            json.dump(streak_data, f)

        await interaction.response.send_message(f"🔥 Streak recorded! You're at {new_streak} days.", ephemeral=True)

async def send_daily_question():
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        today = str(datetime.date.today())
        streak_data["today"] = today
        streak_data["responses"] = {}

        with open(STREAK_FILE, "w") as f:
            json.dump(streak_data, f)

        await channel.send(
            f"📅 {today}\nClick the button if you solved LeetCode today 👇",
            view=DailyButtonView()
        )

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    bot.add_view(DailyButtonView())

    if not os.path.exists(STREAK_FILE):
        with open(STREAK_FILE, "w") as f:
            json.dump({}, f)

    # Run immediately on boot
    await send_daily_question()

    # Schedule every day at 12:00 AM local time
    scheduler.add_job(send_daily_question, "cron", hour=0, minute=0)
    scheduler.start()

@bot.command()
async def streak(ctx):
    user_id = str(ctx.author.id)
    user_data = streak_data.get(user_id, {"streak": 0})
    await ctx.send(
        f"🔥 {ctx.author.mention}, your current LeetCode streak is **{user_data['streak']}** day(s)!"
    )

@bot.command()
async def leaderboard(ctx):
    leaderboard = []
    for user_id, data in streak_data.items():
        if user_id.isdigit() and "streak" in data:
            leaderboard.append((int(user_id), data["streak"]))

    leaderboard.sort(key=lambda x: x[1], reverse=True)
    top_5 = leaderboard[:5]

    if not top_5:
        await ctx.send("No one has a streak yet!")
        return

    message_lines = ["🏆 **Top LeetCode Streaks**"]
    for i, (user_id, streak) in enumerate(top_5, 1):
        try:
            user = await bot.fetch_user(user_id)
            username = user.name
        except:
            username = f"User {user_id}"
        message_lines.append(f"{i}. {username} – {streak} day(s)")

    await ctx.send("\n".join(message_lines))

keep_alive()
bot.run(TOKEN)
