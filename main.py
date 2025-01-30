import discord, os
from discord.ext import commands
from dotenv import load_dotenv

bot = commands.Bot(command_prefix="!s", intents=discord.Intents.all())

async def initalize():
    for fileName in os.listdir(f"{os.getcwd()}/cogs"):
        if fileName.endswith(".py"):
            await bot.load_extension(f"cogs.{fileName[:-3]}")

@bot.event
async def on_ready():
    print("Logged into bot successfully!")
    await initalize()

if __name__ == "__main__":
    load_dotenv()
    TOKEN = os.getenv("TOKEN")
    bot.run(token=TOKEN)
