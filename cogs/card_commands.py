import discord
from discord.ext import commands
import re
import card_manager  # 引入剛剛分開出去的資料庫模組

class CardCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ====================================================================
    # 🔴 功能一：智慧角色卡錄入 (.add 角色名 貼上卡片)
    # ====================================================================
    @commands.command(name="add")
    async def add_character(self, ctx, name: str, *, card_text: str):
        try:
            name = name.strip()
            # 引入 card_manager 裡面的全域字典
            if name not in card_manager.chars_cache:
                card_manager.chars_cache[name] = {}

            # 將全形的「：」和「／」統一替換成半形
            clean_text = card_text.replace("：", ":").replace("／", "/")
            lines = clean_text.split("\n")
            recorded_count = 0

            for line in lines:
                line = line.strip()
                # 尋找 欄位名稱:數字開頭的內容
                match = re.search(r"^([^:]+):([+-]?\d+.*)$", line)
                
                if match:
                    key = match.group(1).strip()
                    val_str = match.group(2).strip()
                    
                    # 抓取第一筆數字（當前值）
                    num_match = re.search(r"^[+-]?\d+", val_str)
                    if num_match:
                        current_val = int(num_match.group(0))
                        card_manager.chars_cache[name][key] = current_val
                        recorded_count += 1
                        
                        # 如果是這四個關鍵欄位，額外挖出斜線後面的「最大值」
                        if key.upper() in ["HP", "MP", "SAN", "LUK"]:
                            max_match = re.search(r"/\s*([+-]?\d+)", val_str)
                            if max_match:
                                card_manager.chars_cache[name][f"{key}_max"] = int(max_match.group(1))
                                recorded_count += 1

            # 呼叫 card_manager 的優化版背景儲存中心
            card_manager.save_data()

            await ctx.reply(f"✅ 角色卡 ` {name} ` 錄入成功！共建立 {recorded_count} 個屬性欄位。")

        except Exception as e:
            await ctx.reply(f"❌ 角色卡錄入失敗: {str(e)}")

    # ====================================================================
    # 🔴 功能二：查看角色卡指令 (.show 角色名)
    # ====================================================================
    @commands.command(name="show")
    async def show_character(self, ctx, name: str):
        try:
            name = name.strip()
            if name in card_manager.chars_cache:
                # 抓出該角色所有的屬性並排版
                skills_str = "\n".join([f"· {k}: **{v}**" for k, v in card_manager.chars_cache[name].items()])
                await ctx.reply(f"📜 **角色卡：{name}**\n{skills_str}")
            else:
                await ctx.reply(f"❌ 找不到角色卡 ` {name} `，請先使用 `.add` 建立！")
        except Exception as e:
            await ctx.reply(f"❌ 查看角色卡失敗: {str(e)}")

# Cog 必須要有的初始化函式，讓 main.py 能夠順利載入它
async def setup(bot):
    await bot.add_cog(CardCommands(bot))
