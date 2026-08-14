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

bot.remove_command('help') 

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
                    is_bonus = mod_str.startswith('+')
                    dice_count = int(mod_str[1:]) if len(mod_str) > 1 else 1

                # 2. 解析技能目標值與名稱
                target = int(check_match.group(2))
                name = check_match.group(3).strip() if check_match.group(3) else "判定"

                # 3. 雙 D10 骰子邏輯
                ones = random.randint(0, 9)
                base_tens = random.randint(0, 9) * 10
                extra_tens = [random.randint(0, 9) * 10 for _ in range(dice_count)]
                all_tens = [base_tens] + extra_tens

                # 先算出每一組的真實百面骰點數 (00+0 視為 100)
                detail_rolls = []
                for t in all_tens:
                    val = t + ones
                    detail_rolls.append(100 if val == 0 else val)

                # 💡 極簡關鍵：直接依獎懲規則決定最終點數
                if dice_count > 0:
                    if is_bonus:
                        # 獎勵骰取最小（100 點最大，所以自然會被過濾掉，除非全都是100）
                        rolled_val = min(detail_rolls)
                    else:
                        # 懲罰骰取最大（只要明細裡有 100 點，max 自然會把它抓出來變成大失敗）
                        rolled_val = max(detail_rolls)
                else:
                    rolled_val = detail_rolls[0]

                # 4. 計算成功等級臨界點
                crit_success_high = 5 if target >= 50 else 1
                fumble_low = 100 if target >= 50 else 96

                extreme_success = target // 5
                hard_success = target // 2

                # 5. 判定分級邏輯 (100點必定直接大失敗)
                if rolled_val >= fumble_low or rolled_val == 100:
                    result_text = "大失敗"
                elif rolled_val <= crit_success_high:
                    result_text = "大成功"
                elif rolled_val <= extreme_success:
                    result_text = "極限成功"
                elif rolled_val <= hard_success:
                    result_text = "困難成功"
                elif rolled_val <= target:
                    result_text = "成功"
                else:
                    result_text = "失敗"

                # 6. 輸出明細：展示十位組合加上個位，例如十位 40, 90 個位 5 -> 顯示為 (45,95)
                # 💡 明細特例：若是 00 加 0，則該組合顯示為 100
                detail_rolls = []
                for t in all_tens:
                    if t == 0 and ones == 0:
                        detail_rolls.append(100)
                    else:
                        detail_rolls.append(t + ones)
                        
                details_str = ",".join(map(str, detail_rolls))
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


@bot.command(name="help")
async def help_command(ctx):
    help_text = (
        "**【優彩說明書】**\n\n"
        "🎲 **普通擲骰**\n"
        "格式：`.r XdY` \n"
        "· 範例 ： `.r (2D6+6)*5`\n\n"
        "🔁 **多次擲骰**\n"
        "格式：`.r XdY 次數`\n"
        "· 範例 ： `.r 3d6 5` (連續骰 5 次 3d6)\n\n"
        "🔮 **技能判定**\n"
        "格式：`.r (獎懲) 目標值 (技能名稱)`\n"
        "· 普通判定 ： `.r 50 偵查`\n"
        "· 獎勵骰+1 ： `.r + 60 射擊`\n"
        "· 懲罰骰-2 ： `.r -2 40`\n\n"
        "🔀 **多組任務同時輸入 (用逗號隔開)**\n"
        "· 範例 ： `.r 1d20+5, + 60 幸運, 3d6 2`\n\n"
        "**優彩會絕對公平的丟完骰子並告知你結果！**"
    )
    await ctx.reply(help_text)


# === 3. 啟動進入點 ===
if __name__ == "__main__":
    keep_alive()
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("錯誤：找不到 DISCORD_TOKEN 環境變數")
