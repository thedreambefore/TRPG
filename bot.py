import discord
from discord.ext import commands
import random
import re
import os
from flask import Flask
from threading import Thread

# === 1. Flask 網頁伺服器設定 (讓 Render 偵測存活) ===
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    # Render 會自動提供 PORT 環境變數，預設為 10000
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# === 2. Discord 機器人主程式 ===
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"機器人已上線: {bot.user}")

@bot.command(name="roll")
async def roll(ctx, *, args: str):
    try:
        match = re.search(r'(?:(\d+)次\s*)?(\d+)d(\d+)(?:取高(\d+))?', args)
        if not match:
            await ctx.send("指令格式錯誤！範例：`!roll 5次 4d6取高3`")
            return
            
        times = int(match.group(1)) if match.group(1) else 1
        dice_num = int(match.group(2))
        dice_sides = int(match.group(3))
        keep_high = int(match.group(4)) if match.group(4) else dice_num

        if keep_high > dice_num:
            await ctx.send("錯誤：取高的數量不能大於骰子總數！")
            return

        response = f"**擲骰要求**：{args}\n"
        for i in range(times):
            rolls = [random.randint(1, dice_sides) for _ in range(dice_num)]
            sorted_rolls = sorted(rolls, reverse=True)
            highest_rolls = sorted_rolls[:keep_high]
            total = sum(highest_rolls)
            response += f"第 {i+1} 次: 投出 {rolls} -> 取高得 {highest_rolls} = **{total}**\n"
            
        await ctx.send(response)
    except Exception as e:
        await ctx.send(f"發生錯誤: {str(e)}")

# === 3. 啟動進入點 ===
if __name__ == "__main__":
    # 啟動網頁伺服器
    keep_alive()
    # 讀取 Token (這裡改用環境變數，絕對不要把 Token 明打在代碼裡傳上 GitHub！)
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("錯誤：找不到 DISCORD_TOKEN 環境變數")
