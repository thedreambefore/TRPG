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

            # 正規表達式精簡（移除了取高）：
            # 1組: (\d+)d(\d+) -> 骰子 (數量d面數)
            # 2組: ([+\-*/]\d+)? -> 選填四則運算 (如 +5, -2)
            # 3組: (?:\s+(\d+))? -> 選填次數 (結尾空格加數字)
            match = re.search(r'(\d+)d(\d+)([+\-*/]\d+)?(?:\s+(\d+))?', task)

            if not match:
                final_response.append(f"❌ 格式無法解析：`{task}`")
                continue

            dice_num = int(match.group(1))
            dice_sides = int(match.group(2))
            modifier = match.group(3) if match.group(3) else ""
            times = int(match.group(4)) if match.group(4) else 1

            task_output = f"🎲 **項目**：`{task}`"
            
            # 開始依「次數」跑迴圈
            for i in range(times):
                # 擲骰並計算總和
                rolls = [random.randint(1, dice_sides) for _ in range(dice_num)]
                dice_total = sum(rolls)

                # 計算四則運算
                if modifier:
                    final_total = safe_eval(f"{dice_total}{modifier}")
                    math_str = f" ({dice_total}){modifier}"
                else:
                    final_total = dice_total
                    math_str = ""

                # 設定每輪輸出的開頭（多輪時換行，單輪時直接串接）
                prefix = f"\n  第 {i+1} 次:" if times > 1 else ""
                
                # 根據骰子數量優化排版顯示
                if dice_num == 1:
                    task_output += f"{prefix} 投出 {rolls}{modifier} = **{final_total}**"
                else:
                    task_output += f"{prefix} 投出 {rolls}{math_str} = **{final_total}**"

            final_response.append(task_output)

        # 發送到 Discord
        await ctx.send("\n".join(final_response))

    except Exception as e:
        await ctx.send(f"❌ 發生未知錯誤: {str(e)}")

# === 3. 啟動進入點 ===
if __name__ == "__main__":
    keep_alive()
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("錯誤：找不到 DISCORD_TOKEN 環境變數")