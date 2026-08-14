import discord
from discord.ext import commands
import random
import re
from flask import Flask
from threading import Thread
import os

# === 1. Flask 網頁伺服器設定 (Render 續命用) ===
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
bot = commands.Bot(command_prefix=".", intents=intents)

@bot.event
async def on_ready():
    print(f"機器人已上線: {bot.user}")

# 安全的四則運算器
def safe_eval(expr: str) -> int:
    expr = re.sub(r'[^0-9+\-*/()]', '', expr)
    try:
        return int(eval(expr))
    except:
        return 0

@bot.command(name="r")
async def roll(ctx, *, args: str):
    try:
        # 用逗號「,」分割多個不同的擲骰任務
        tasks = args.split(',')
        final_response = []

        for task in tasks:
            task = task.strip()
            if not task:
                continue

            # 萬用正規表達式 (支援無限串接四則運算與大寫D)
            match = re.search(r'(\d+)[dD](\d+)((?:[+\-*/]\d+)*)(?:\s+(\d+))?', task)

            if not match:
                final_response.append(f"優彩聽不懂")
                continue

            dice_num = int(match.group(1))
            dice_sides = int(match.group(2))
            modifier = match.group(3) if match.group(3) else ""
            times = int(match.group(4)) if match.group(4) else 1

            # 項目名稱單獨用程式碼區塊包裹，防斜體干擾
            task_output = f"` {task} `\n"
            
            # 開始依「次數」跑迴圈
            for i in range(times):
                rolls = [random.randint(1, dice_sides) for _ in range(dice_num)]
                dice_total = sum(rolls)

                if modifier:
                    final_total = safe_eval(f"{dice_total}{modifier}")
                    math_str = f" ({dice_total}){modifier}"
                else:
                    final_total = dice_total
                    math_str = ""

                prefix = f"  第 {i+1} 次:"
                
                if dice_num == 1:
                    task_output += f"{prefix} 投出 {rolls}{modifier} = **{final_total}**\n"
                else:
                    task_output += f"{prefix} 投出 {rolls}{math_str} = **{final_total}**\n"

            final_response.append(task_output)

        # 這會直接回覆該使用者的訊息，並自動帶有 @Mention 效果
        await ctx.reply("\n".join(final_response))

    except Exception as e:
        # 錯誤訊息也改用 reply，讓使用者知道是自己打錯了
        await ctx.reply(f"發生未知錯誤: {str(e)}")

# === 3. 啟動進入點 ===
if __name__ == "__main__":
    keep_alive()
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("錯誤：找不到 DISCORD_TOKEN 環境變數")
