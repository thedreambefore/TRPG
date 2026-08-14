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
        # 用逗號「,」分割多個不同的任務
        tasks = args.split(',')
        final_response = []

        for task in tasks:
            task = task.strip()
            if not task:
                continue

            # ====================================================================
            # 🔴 分流點 1：CoC 技能判定邏輯
            # ====================================================================
            if re.match(r'^[+-]', task) or (task and task.isdigit() and 'd' not in task.lower()):
                
                check_match = re.search(r'^(?:([+-]\d*)\s+)?(\d+)(?:\s+(.+))?$', task)

                if not check_match:
                    final_response.append(f"❌ 格式無法解析：`{task}`")
                    continue

                # 1. 解析獎懲骰
                mod_str = check_match.group(1) if check_match.group(1) else ""
                dice_count = 0  
                is_bonus = True 

                if mod_str:
                    is_bonus = mod_str == '+'
                    dice_count = int(mod_str[1:]) if len(mod_str) > 1 else 1

                # 2. 解析技能目標值與名稱 (沒寫預設為 "判定")
                target = int(check_match.group(2))
                name = check_match.group(3).strip() if check_match.group(3) else "判定"

                # 3. 骰子邏輯：骰個位數(0-9)與基本十位數(00-90)
                ones = random.randint(0, 9)
                base_tens = random.randint(0, 9) * 10
                
                extra_tens = [random.randint(0, 9) * 10 for _ in range(dice_count)]
                all_tens = [base_tens] + extra_tens

                if dice_count > 0:
                    if is_bonus:
                        final_tens = min(all_tens) 
                    else:
                        final_tens = max(all_tens) 
                else:
                    final_tens = base_tens

                rolled_val = final_tens + ones
                if rolled_val == 0:
                    rolled_val = 100

                # 4. 計算成功等級臨界點
                crit_success_high = 5 if target >= 50 else 1
                fumble_low = 100 if target >= 50 else 96

                extreme_success = target // 5
                hard_success = target // 2

                # 5. 判定分級邏輯
                if rolled_val <= crit_success_high:
                    result_text = "大成功"
                elif rolled_val <= extreme_success:
                    result_text = "極限成功"
                elif rolled_val <= hard_success:
                    result_text = "困難成功"
                elif rolled_val <= target:
                    result_text = "成功"
                elif rolled_val >= fumble_low:
                    result_text = "大失敗"
                else:
                    result_text = "失敗"

                # 6. 🔴 技能判定排版優化：名稱+獎懲(目標值)=最終結果(十位+個位的點數明細)：分級
                # 組合出每顆十位骰加個位骰的明細，例如十位40個位5 -> 45
                detail_rolls = []
                for t in all_tens:
                    val = t + ones
                    detail_rolls.append(str(100 if val == 0 else val))
                details_str = ",".join(detail_rolls)

                # 決定名稱旁邊要不要顯示 +1, -2 等符號
                display_mod = mod_str if mod_str else ""
                
                line_result = f"{name}{display_mod}({target})={rolled_val}({details_str})：{result_text}"
                final_response.append(line_result)
                continue 


            # ====================================================================
            # 🟢 分流點 2：普通 XdY 擲骰與四則運算核心
            # ====================================================================
            times_match = re.search(r'\s+(\d+)$', task)
            if times_match:
                times = int(times_match.group(1))
                expr_template = task[:times_match.start()].strip()
            else:
                times = 1
                expr_template = task

            if not re.search(r'[dD]', expr_template):
                final_response.append(f"❌ 格式無法解析：`{task}`")
                continue

            for i in range(times):
                expr = expr_template
                raw_formula = expr_template
                rolls_log = []
                
                while True:
                    dice_match = re.search(r'(\d+)[dD](\d+)', expr)
                    if not dice_match:
                        break
                    
                    dice_num = int(dice_match.group(1))
                    dice_sides = int(dice_match.group(2))
                    
                    rolls = [random.randint(1, dice_sides) for _ in range(dice_num)]
                    dice_total = sum(rolls)
                    
                    # 移除了外層的 str() 轉換包裝，保持純數值陣列外觀
                    rolls_log.append(str(rolls))
                    expr = expr[:dice_match.start()] + str(dice_total) + expr[dice_match.end():]

                final_total = safe_eval(expr)
                rolls_str = ", ".join(rolls_log)
                

                line_result = f"`{raw_formula}`={rolls_str}=**{final_total}**"
                
                final_response.append(line_result)

        # 統一回覆到 Discord
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
