import discord
from discord.ext import commands
import re
import card_manager  # 引入資料庫模組

class CardCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ====================================================================
    # 🔴 功能一：智慧角色卡錄入 (.add 角色名 貼上卡片) (免引號升級版)
    # ====================================================================
    @commands.command(name="add")
    async def add_character(self, ctx, *, args: str):
        try:
            parts = args.split(maxsplit=1)
            if len(parts) < 2:
                await ctx.reply("❌ 格式不對喔！範例：`.add 晝間和歌子 [換行貼上卡片]`")
                return
                
            name = parts[0].strip()
            card_text = parts[1].strip()

            if name not in card_manager.chars_cache:
                card_manager.chars_cache[name] = {}

            # 將全形的「：」和「／」統一替換成半形
            clean_text = card_text.replace("：", ":").replace("／", "/")
            lines = clean_text.split("\n")
            recorded_count = 0

            for line in lines:
                line = line.strip()
                match = re.search(r"^([^:]+):([+-]?\d+.*)$", line)
                
                if match:
                    key = match.group(1).strip()
                    val_str = match.group(2).strip()
                    
                    if ":" in val_str:
                        sub_parts = val_str.rsplit(":", 1)
                        if re.match(r"^[+-]?\d+", sub_parts.strip()):
                            key = f"{key}:{sub_parts.strip()}"
                            val_str = sub_parts.strip()

                    # 抓取第一筆數字（當前值）
                    num_match = re.search(r"^[+-]?\d+", val_str)
                    if num_match:
                        current_val = int(num_match.group(0))
                        card_manager.chars_cache[name][key] = current_val
                        recorded_count += 1
                        
                        # 核心關鍵欄位最大值備份
                        if key.upper() in ["HP", "MP", "SAN", "LUK"]:
                            max_match = re.search(r"/\s*([+-]?\d+)", val_str)
                            if max_match:
                                card_manager.chars_cache[name][f"{key}_max"] = int(max_match.group(1))
                                recorded_count += 1

            # 呼叫背景偷偷儲存中心
            card_manager.save_data()

            await ctx.reply(f"✅ 角色卡 ` {name} ` 錄入成功！共建立 {recorded_count} 個屬性欄位。")

        except Exception as e:
            await ctx.reply(f"❌ 角色卡錄入失敗: {str(e)}")

    # ====================================================================
    # 🔴 功能二：查看角色卡指令 (Embed 資訊卡 完美安全修正版)
    # 格式：.show 昼間和歌子  或  .show 昼間和歌子 偵查
    # ====================================================================
    @commands.command(name="show")
    async def show_character(self, ctx, name: str, skill_name: str = None):
        try:
            name = name.strip()
            
            # 防呆：有沒有這張角色卡
            if name not in card_manager.chars_cache:
                await ctx.reply(f"❌ 找不到角色卡 ` {name} `，請先使用 `.add` 建立！")
                return

            # 💡 狀況 A：玩家想查「特定單一數值」
            if skill_name:
                skill_name = skill_name.strip()
                if skill_name.upper() in ["HP", "MP", "SAN", "LUK"]:
                    skill_name = skill_name.upper()
                
                if skill_name in card_manager.chars_cache[name]:
                    val = card_manager.chars_cache[name][skill_name]
                    max_key = f"{skill_name}_max"
                    
                    # 💡 核心安全修正：改用 0x3498db (這是在 Discord 中最標準、最絕對能通的湖水藍色)
                    embed = discord.Embed(
                        title=f"📊 {name}", 
                        color=0x3498db 
                    )
                    if max_key in card_manager.chars_cache[name]:
                        embed.description = f"**{skill_name}**: `{val}/{card_manager.chars_cache[name][max_key]}`"
                    else:
                        embed.description = f"**{skill_name}**: `{val}`"
                        
                    await ctx.reply(embed=embed)
                else:
                    await ctx.reply(f"❌ 角色 ` {name} ` 沒有 ` {skill_name} ` 這項數值！")
            
            # 💡 狀況 B：玩家只打了名字，顯示全卡資訊
            else:
                # 💡 核心安全修正：改用 0x3498db 代碼，保證絕不卡死
                embed = discord.Embed(
                    title=f"📜 {name}", 
                    color=0x3498db
                )
                
                skills_list = []
                for k, v in card_manager.chars_cache[name].items():
                    if k.endswith("_max"):
                        continue
                        
                    max_key = f"{k}_max"
                    if max_key in card_manager.chars_cache[name]:
                        max_val = card_manager.chars_cache[name][max_key]
                        skills_list.append(f"· {k}: `{v}/{max_val}`")
                    else:
                        skills_list.append(f"· {k}: `{v}`")
                
                embed.description = "\n".join(skills_list)
                await ctx.reply(embed=embed)

        except Exception as e:
            await ctx.reply(f"❌ 查看角色卡失敗: {str(e)}")

# 初始化 Cog
async def setup(bot):
    await bot.add_cog(CardCommands(bot))
