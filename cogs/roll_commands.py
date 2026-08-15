import discord
from discord.ext import commands
import random
import re
import dice_tools     # 💡 引入數學與成功評級工具
import card_manager   # 💡 引入角色卡快取與背景儲存工具

class RollCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ====================================================================
    # ⚔️ 功能一：萬用核心擲骰、多重四則運算與技能判定指令 (.r)
    # ====================================================================
    @commands.command(name="r")
    async def roll(self, ctx, *, args: str):
        try:
            tasks = args.split(',')
            final_response = []

            for task in tasks:
                task = task.strip()
                if not task:
                    continue

                # ----------------------------------------------------------------
                # 🔴 分流點 A：CoC 技能判定邏輯（支援手動輸入 或 角色卡自動調用）
                # ----------------------------------------------------------------
                check_args = task.split()
                # 檢查第一個字是不是已經儲存的角色名字
                has_stored_char = len(check_args) >= 2 and check_args[0] in card_manager.chars_cache
                
                # 判斷是否為判定模式：開頭有正負號、純數字（無d）、或是已儲存的角色調用
                if re.match(r'^[+-]', task) or (task and task.isdigit() and 'd' not in task.lower()) or has_stored_char:
                    dice_count = 0
                    is_bonus = True
                    mod_str = ""
                    
                    if has_stored_char:
                        # 格式 A：.r 晝間和歌子 偵查  或  .r 晝間和歌子 + 偵查
                        char_name = check_args[0]
                        
                        # 檢查名字後面有沒有穿插獎懲骰
                        if len(check_args) >= 3 and (check_args[1] in ['+', '-'] or re.match(r'^[+-]\d+', check_args[1])):
                            mod_str = check_args[1]
                            skill_name = check_args[2]
                        else:
                            skill_name = check_args[1]
                            
                        if skill_name not in card_manager.chars_cache[char_name]:
                            final_response.append(f"❌ 角色 ` {char_name} ` 沒有 ` {skill_name} ` 這項數值！")
                            continue
                            
                        target = card_manager.chars_cache[char_name][skill_name]
                        name = f"{char_name} {skill_name}"
                    else:
                        # 格式 B：手動輸入舊格式 (.r 50 偵查、.r +2 60)
                        check_match = re.search(r'^(?:([+-]\d*)\s+)?(\d+)(?:\s+(.+))?$', task)
                        if not check_match:
                            final_response.append(f"❌ 格式無法解析：`{task}`")
                            continue
                        mod_str = check_match.group(1) if check_match.group(1) else ""
                        target = int(check_match.group(2))
                        name = check_match.group(3).strip() if check_match.group(3) else "判定"

                    # 解析提取出的獎懲骰數量
                    if mod_str:
                        is_bonus = mod_str.startswith('+')
                        dice_count = int(mod_str[1:]) if len(mod_str) > 1 and mod_str[1:].isdigit() else 1

                    # 💡 調用獨立出的工具函式進行百面骰與六級成功判定
                    rolled_val, detail_rolls = dice_tools.roll_d100_with_modifiers(dice_count, is_bonus)
                    result_text = dice_tools.judge_success_level(rolled_val, target)

                    details_str = ",".join(map(str, detail_rolls))
                    display_mod = mod_str if mod_str else ""
                    
                    # 呈現格式：名稱+獎懲(目標值)=最終結果(詳細點數明細)：成功分級
                    line_result = f"{name}{display_mod}({target})={rolled_val}({details_str})：{result_text}"
                    final_response.append(line_result)
                    continue 

                # ----------------------------------------------------------------
                # 🟢 分流點 B：普通 XdY 舊邏輯（包含四則運算與多次重複骰）
                # ----------------------------------------------------------------
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

                    # 💡 調用獨立出的工具函式進行安全的四則運算
                    final_total = dice_tools.safe_eval(expr)
                    rolls_str = ", ".join(rolls_log)
                    
                    if raw_formula != expr:
                        line_result = f"`{raw_formula}`={rolls_str}➡️`{expr}`=**{final_total}**"
                    else:
                        line_result = f"`{raw_formula}`={rolls_str}=**{final_total}**"
                    final_response.append(line_result)

            # 統一回覆到 Discord
            await ctx.reply("\n".join(final_response))

        except Exception as e:
            await ctx.reply(f"❌ 擲骰發生未知錯誤: {str(e)}")

    # ====================================================================
    # 🧠 功能二：理智檢定專用指令 (.sc) (支援手動 或 角色卡智慧連動扣除)
    # ====================================================================
    @commands.command(name="sc")
    async def sanity_check(self, ctx, *, args: str):
        try:
            check_args = args.split()
            # 檢查第一個字是不是已經儲存的角色名字
            has_stored_char = len(check_args) >= 2 and check_args[0] in card_manager.chars_cache
            
            if has_stored_char:
                # 💡 格式 A：角色卡智慧調用模式 (.sc 晝間和歌子 1/1d6) 或 (.sc 晝間和歌子 2 1/1d6)
                char_name = check_args[0]
                
                # 判斷第二個變數是「次數」還是直接是「算式」
                if '/' in check_args[1]:
                    total_times = 1
                    success_expr = check_args[1].split('/')[0]
                    failure_expr = check_args[1].split('/')[1]
                    event_name = " ".join(check_args[2:]).strip() if len(check_args) > 2 else "理智"
                else:
                    total_times = int(check_args[1]) if check_args[1].isdigit() else 1
                    success_expr = check_args[2].split('/')[0]
                    failure_expr = check_args[2].split('/')[1]
                    event_name = " ".join(check_args[3:]).strip() if len(check_args) > 3 else "理智"
                    
                if "SAN" not in card_manager.chars_cache[char_name]:
                    await ctx.reply(f"❌ 角色 ` {char_name} ` 沒有登錄「SAN」理智數值！請重新使用 `.add` 錄入。")
                    return
                    
                current_san = card_manager.chars_cache[char_name]["SAN"]
                is_stored_mode = True
            else:
                # 💡 格式 B：手動輸入舊格式 (.sc 50 1/1d6) 或 (.sc 2 50 1/1d6)
                match = re.search(r'^(?:(\d+)\s+)?(\d+)\s+([^\s/]+)/([^\s]+)(?:\s+(.+))?$', args.strip())
                if not match:
                    await ctx.reply("❌ 格式不對喔！範例：`.sc 晝間和歌子 1/1d6` 或手動 `.sc 50 1/1d6`")
                    return
                total_times = int(match.group(1)) if match.group(1) else 1
                current_san = int(match.group(2))
                success_expr = match.group(3)
                failure_expr = match.group(4)
                event_name = match.group(5).strip() if match.group(5) else "理智"
                is_stored_mode = False

            # 計算理智懲罰骰次數 (N次代表總共骰N次取高，所以額外追加 N-1 顆)
            dice_count = max(0, total_times - 1) 

            # 💡 調用優化工具進行百面判定與分級 (理智只有懲罰骰，is_bonus 固定傳入 False)
            rolled_val, detail_rolls = dice_tools.roll_d100_with_modifiers(dice_count, is_bonus=False)
            result_text = dice_tools.judge_success_level(rolled_val, current_san)
            is_success = result_text in ["大成功", "極限成功", "困難成功", "成功"]

            # 解析並骰出理智扣除數值
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

            san_loss = dice_tools.safe_eval(expr_to_eval)
            remaining_san = max(0, current_san - san_loss)

            # 🔴 自動同步扣除：如果是角色卡調用，直接將剩餘值更新並透過背景線程 Push 備份回 GitHub！
            if is_stored_mode:
                card_manager.chars_cache[char_name]["SAN"] = remaining_san
                card_manager.save_data()

            display_mod = f"-{total_times - 1}" if total_times > 1 else ""
            details_str = f"({','.join(map(str, detail_rolls))})" if dice_count > 0 else ""

            # 輸出三行式極簡排版
            prefix_name = f"{char_name} {event_name}" if is_stored_mode else event_name
            reply_message = (
                f"**{prefix_name}{display_mod}判定**:\n"
                f"{result_text}({rolled_val}{details_str}/{current_san})\n"
                f"減少了 {san_loss} ({chosen_expr}) 剩餘 {remaining_san} 理智")

            await ctx.reply(reply_message)

        except Exception as e:
            await ctx.reply(f"❌ 理智檢定發生未知錯誤: {str(e)}")

# 初始化 Cog
async def setup(bot):
    await bot.add_cog(RollCommands(bot))