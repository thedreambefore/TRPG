import discord
from discord.ext import commands
import random
import re
from flask import Flask
from threading import Thread
import os

# === 1. Flask 網頁伺服器設定 (Render 24小時續命用) ===
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


# ==============================================================================
# 函式一：負責「雙D10骰子計算」（包含獎勵骰、懲罰骰）
# ==============================================================================
def roll_d100_with_modifiers(dice_count: int, is_bonus: bool = True) -> tuple[int, list[int]]:
    ones = random.randint(0, 9)
    base_tens = random.randint(0, 9) * 10
    
    extra_tens = [random.randint(0, 9) * 10 for _ in range(dice_count)]
    all_tens = [base_tens] + extra_tens

    detail_rolls = []
    for t in all_tens:
        val = t + ones
        detail_rolls.append(100 if val == 0 else val)

    if dice_count > 0:
        if is_bonus:
            rolled_val = min(detail_rolls)  
        else:
            rolled_val = max(detail_rolls)  
    else:
        rolled_val = detail_rolls[0]

    return rolled_val, detail_rolls


# ==============================================================================
# 函式二：判定成功等級評級
# ==============================================================================
def judge_success_level(rolled_val: int, target: int) -> str:
    crit_success_high = 5 if target >= 50 else 1
    fumble_low = 100 if target >= 50 else 96

    extreme_success = target // 5
    hard_success = target // 2

    if rolled_val >= fumble_low or rolled_val == 100:
        return "大失敗"
    elif rolled_val <= crit_success_high:
        return "大成功"
    elif rolled_val <= extreme_success:
        return "極限成功"
    elif rolled_val <= hard_success:
        return "困難成功"
    elif rolled_val <= target:
        return "成功"
    else:
        return "失敗"


# ==============================================================================
# 指令幫助
# ==============================================================================
@bot.command(name="help",aliases=["HELP"])
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
        "🧠 **理智檢定**\n"
        "格式：`.sc  目標值 (技能名稱)`\n"
        "· 普通判定 ： `.r 50 偵查`\n"
        "· 獎勵骰+1 ： `.r + 60 射擊`\n"
        "· 懲罰骰-2 ： `.r -2 40`\n\n"
        "🔀 **多組任務同時輸入 (用逗號隔開)**\n"
        "· 範例 ： `.r 1d20+5, + 60 幸運, 3d6 2`\n\n"
        "**優彩會絕對公平的丟完骰子並告知你結果！**"
    )
    await ctx.reply(help_text)


# ==============================================================================
# 擲骰與技能判定指令 (.r) 
# ==============================================================================
@bot.command(name="r")
async def roll(ctx, *, args: str):
    try:
        tasks = args.split(',')
        final_response = []

        for task in tasks:
            task = task.strip()
            if not task:
                continue

            # --------------------------------------------------------------------
            # 🔴 分流點 1：CoC 技能判定邏輯 
            # --------------------------------------------------------------------
            if re.match(r'^[+-]', task) or (task and task.isdigit() and 'd' not in task.lower()):
                
                check_match = re.search(r'^(?:([+-]\d*)\s+)?(\d+)(?:\s+(.+))?$', task)

                if not check_match:
                    final_response.append(f"❌ 格式無法解析：`{task}`")
                    continue

                mod_str = check_match.group(1) if check_match.group(1) else ""
                dice_count = 0  
                is_bonus = True 

                if mod_str:
                    is_bonus = mod_str.startswith('+')
                    dice_count = int(mod_str[1:]) if len(mod_str) > 1 and mod_str[1:].isdigit() else 1

                target = int(check_match.group(2))
                name = check_match.group(3).strip() if check_match.group(3) else "判定"

                # 💡 調用優化函式一：計算百面骰點數與明細
                rolled_val, detail_rolls = roll_d100_with_modifiers(dice_count, is_bonus)

                # 💡 調用優化函式二：判定成功評級
                result_text = judge_success_level(rolled_val, target)

                details_str = ",".join(map(str, detail_rolls))
                display_mod = mod_str if mod_str else ""
                
                line_result = f"{name}{display_mod}({target})={rolled_val}({details_str})：{result_text}"
                final_response.append(line_result)
                continue 

            # --------------------------------------------------------------------
            # 🟢 分流點 2：普通 XdY 
            # --------------------------------------------------------------------
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
                    
                    rolls_log.append(str(rolls))
                    expr = expr[:dice_match.start()] + str(dice_total) + expr[dice_match.end():]

                final_total = safe_eval(expr)
                rolls_str = ", ".join(rolls_log)
                
                if raw_formula != expr:
                    line_result = f"`{raw_formula}`={rolls_str}➡️`{expr}`=**{final_total}**"
                else:
                    line_result = f"`{raw_formula}`={rolls_str}=**{final_total}**"
                
                final_response.append(line_result)

        await ctx.reply("\n".join(final_response))

    except Exception as e:
        await ctx.reply(f"❌ 發生未知錯誤: {str(e)}")


# ==============================================================================
# 理智檢定指令 (.sc / .SC)
# ==============================================================================
@bot.command(name="sc", aliases=["SC"])
async def sanity_check(ctx, *, args: str):
    try:
        match = re.search(r'^(?:([+-]?\d+|[+-])\s+)?(\d+)\s+([^\s/]+)/([^\s]+)(?:\s+(.+))?$', args.strip())

        if not match:
            await ctx.reply("❌ 格式不對喔！範例：`.sc 45 0/1d3`")
            return

        mod_str = match.group(1) if match.group(1) else ""
        dice_count = 0  
        is_bonus = False # 預設純數字為懲罰骰（取高）

        if mod_str:
            if mod_str.startswith('+'):
                is_bonus = True
                dice_count = int(mod_str[1:]) if len(mod_str) > 1 and mod_str[1:].isdigit() else 1
            elif mod_str.startswith('-'):
                is_bonus = False
                dice_count = int(mod_str[1:]) if len(mod_str) > 1 and mod_str[1:].isdigit() else 1
            else:
                is_bonus = False
                dice_count = int(mod_str) if mod_str.isdigit() else 1

        current_san = int(match.group(2))
        success_expr = match.group(3)
        failure_expr = match.group(4)
        event_name = match.group(5).strip() if match.group(5) else "理智"

        rolled_val, detail_rolls = roll_d100_with_modifiers(dice_count, is_bonus)

        result_text = judge_success_level(rolled_val, current_san)
        is_success = result_text in ["大成功", "極限成功", "困難成功", "成功"]

        chosen_expr = success_expr if is_success else failure_expr
        expr_to_eval = chosen_expr

        while True:
            dice_match = re.search(r'(\d+)[dD](\d+)', expr_to_eval)
            if not dice_match:
                break
            d_num = int(dice_match.group(1))
            d_sides = int(dice_match.group(2))
            d_sum = sum(random.randint(1, d_sides) for _ in range(d_num))
            expr_to_eval = expr_to_eval[:dice_match.start()] + str(d_sum) + expr_to_eval[dice_match.end():]

        san_loss = safe_eval(expr_to_eval)
        remaining_san = max(0, current_san - san_loss)

        if mod_str and mod_str.isdigit():
            display_mod = f"-{mod_str}"
        else:
            display_mod = mod_str

        details_str = f"({','.join(map(str, detail_rolls))})" if dice_count > 0 else ""

        reply_message = (
            f"**{event_name}{display_mod}判定**:\n"
            f"{result_text}({rolled_val}{details_str}/{current_san})\n"
            f"減少了 {san_loss} ({chosen_expr}) 剩餘 {remaining_san} 理智"
        )

        await ctx.reply(reply_message)

    except Exception as e:
        await ctx.reply(f"❌ 理智檢定發生未知錯誤: {str(e)}")


# === 3. 啟動進入點 ===
if __name__ == "__main__":
    keep_alive()
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("錯誤：找不到 DISCORD_TOKEN 環境變數")