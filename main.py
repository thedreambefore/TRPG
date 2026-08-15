import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import os
import asyncio
import card_manager

# === 1. Flask 網頁伺服器設定 ===
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# === 2. Discord 機器人設定 ===
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=".", intents=intents, case_insensitive=True)
bot.remove_command('help')

@bot.event
async def on_ready():
    card_manager.load_data() # 開機時自動載入角色卡
    print(f"機器人已上線: {bot.user}")

@bot.event
async def on_message(message):
    # 如果是機器人自己發的訊息，不予理會
    if message.author == bot.user:
        return
    # 🔴 核心關鍵：這行會強制把收到的訊息「推下去」給 cogs/card_commands.py 處理！
    await bot.process_commands(message)


# === 3. 自動載入 cogs 資料夾底下的所有擴充模組 ===
async def load_extensions():
    # 建立 cogs 資料夾防呆
    if not os.path.exists("cogs"):
        os.makedirs("cogs")
        
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            # 例如把 cogs/card_commands.py 載入為 cogs.card_commands
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f"已成功載入指令模組: {filename}")

async def main():
    keep_alive()
    async with bot:
        await load_extensions()
        token = os.environ.get("DISCORD_TOKEN")
        if token:
            await bot.start(token)
        else:
            print("錯誤：找不到 DISCORD_TOKEN 環境變數")

if __name__ == "__main__":
    asyncio.run(main())
