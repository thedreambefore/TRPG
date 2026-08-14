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

            # 抽取尾部的「空格+次數」
            times_match = re.search(r'\s+(\d+)$', task)
            if times_match:
                times = int(times_match.group(1))
                expr_template = task[:times_match.start()].strip() # 剩下的純算式
            else:
                times = 1
                expr_template = task

            # 防呆
            if not re.search(r'[dD]', expr_template):
                final_response.append(f"❌ 格式無法解析：`{task}`")
                continue

            # 開始依「次數」跑迴圈
            for i in range(times):
                expr = expr_template
                raw_formula = expr_template # 保留原始公式
                rolls_log = []
                
                # 逐一找出算式中所有的 XdY，並原地替換成擲骰總和
                while True:
                    dice_match = re.search(r'(\d+)[dD](\d+)', expr)
                    if not dice_match:
                        break
                    
                    dice_num = int(dice_match.group(1))
                    dice_sides = int(dice_match.group(2))
                    
                    rolls = [random.randint(1, dice_sides) for _ in range(dice_num)]
                    dice_total = sum(rolls)
                    
                    # 只記錄純點數陣列，例如 [1, 2, 3]
                    rolls_log.append(str(rolls))
                    expr = expr[:dice_match.start()] + str(dice_total) + expr[dice_match.end():]

                final_total = safe_eval(expr)
                rolls_str = ", ".join(rolls_log)
                
                line_result = f"`{raw_formula}`={rolls_str}=**{final_total}**"
                
                final_response.append(line_result)

        # 回覆到 Discord
        await ctx.reply("\n".join(final_response))

    except Exception as e:
        await ctx.reply(f"❌ 發生未知錯誤: {str(e)}")

# === 3. 啟動進入點 ===
if __name__ == "__main__":
    keep_alive()
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("錯誤：找不到 DISCORD_TOKEN 環境變數")
