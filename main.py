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
# 💡 case_insensitive=True 確保大小寫混打通通自動相容
bot = commands.Bot(command_prefix=".", intents=intents, case_insensitive=True)
bot.remove_command('help')

# 🔴 核心導正 1：改寫開機事件，加入最關鍵的 process_commands 傳遞器
@bot.event
async def on_ready():
    card_manager.load_data() # 開機時自動載入角色卡
    print(f"機器人已上線: {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    # 🔴 強制將所有訊息向下推送給 cogs 模組處理，否則指令會死在 on_ready 的大門外
    await bot.process_commands(message)

# === 3. 完美載入 cogs 模組的核心函式 ===
async def load_extensions():
    if not os.path.exists("cogs"):
        os.makedirs("cogs")
        
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            # 🔴 核心導正 2：使用 try-except 包裹，萬一 Cog 內部載入時卡住，會在日誌噴出真正原因
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f"【成功】已成功載入指令模組: {filename}")
            except Exception as e:
                print(f"【失敗】載入模組 {filename} 時發生錯誤: {str(e)}")

# === 4. 主程式啟動進入點 ===
async def main():
    keep_alive()
    # 🔴 核心導正 3：嚴格遵守 discord.py 官方最新規範，先載入完所有 Cog 檔案，才執行 bot.start
    async with bot:
        await load_extensions()
        token = os.environ.get("DISCORD_TOKEN")
        if token:
            await bot.start(token)
        else:
            print("錯誤：找不到 DISCORD_TOKEN 環境變數")

if __name__ == "__main__":
    asyncio.run(main())
