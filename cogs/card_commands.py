import discord
from discord.ext import commands
import re
import card_manager  # 引入資料庫模組

class CardCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ====================================================================
    # 🔴 功能一：智慧角色卡錄入 (.add 角色名 貼上卡片)
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
                        if re.match(r"^[+-]?\d+", sub_parts[0].strip()):
                            key = f"{key}:{sub_parts[0].strip()}"
                            val_str = sub_parts[1].strip()

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
    # 🔴 功能二：查看角色卡指令 (Embed 資訊卡版)
    # ====================================================================
    @commands.command(name="show")
    async def show_character(self, ctx, name: str, skill_name: str = None):
        try:
            name = name.strip()
            
            if name not in card_manager.chars_cache:
                await ctx.reply(f"❌ 找不到角色卡 ` {name} `，請先使用 `.add` 建立！")
                return

            if skill_name:
                skill_name = skill_name.strip()
                if skill_name.upper() in ["HP", "MP", "SAN", "LUK"]:
                    skill_name = skill_name.upper()
                
                if skill_name in card_manager.chars_cache[name]:
                    val = card_manager.chars_cache[name][skill_name]
                    max_key = f"{skill_name}_max"
                    
                    embed = discord.Embed(title=f"📊 {name}", color=0x3498db)
                    if max_key in card_manager.chars_cache[name]:
                        embed.description = f"**{skill_name}**: `{val}/{card_manager.chars_cache[name][max_key]}`"
                    else:
                        embed.description = f"**{skill_name}**: `{val}`"
                        
                    await ctx.reply(embed=embed)
                else:
                    await ctx.reply(f"❌ 角色 ` {name} ` 沒有 ` {skill_name} ` 這項數值！")
            
            else:
                embed = discord.Embed(title=f"📜 {name}", color=0x3498db)
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

    # ====================================================================
    # 🔴 功能三：全新登錄！微調個別數值指令 (.set 角色名 屬性名 數字或+-多少)
    # 格式：.set 昼間和歌子 HP -2  或  .set 昼間和歌子 偵查 75
    # ====================================================================
    @commands.command(name="set")
    async def set_skill(self, ctx, *, args: str):
        try:
            # 正規表達式拆分：第一個詞是名字，第二個詞是屬性，第三個詞是數值(可帶+或-)
            match = re.search(r'^(\S+)\s+(\S+)\s+([+-]?\d+)$', args.strip())
            if not match:
                await ctx.reply("❌ 格式錯誤！")
                return
                
            char_name = match.group(1).strip()
            skill_name = match.group(2).strip()
            val_str = match.group(3).strip()
            
            # 相容大寫
            if skill_name.upper() in ["HP", "MP", "SAN", "LUK"]:
                skill_name = skill_name.upper()
            
            if char_name not in card_manager.chars_cache:
                await ctx.reply(f"❌ 找不到角色卡 ` {char_name} `，請先用 `.add` 建立！")
                return
                
            old_val = card_manager.chars_cache[char_name].get(skill_name, 0)
            
            # 判斷是加減微調還是直接覆蓋數字
            if val_str.startswith('+') or val_str.startswith('-'):
                new_val = max(0, old_val + int(val_str))
                action_text = f"`{old_val}` {val_str} = **`{new_val}`**"
            else:
                new_val = max(0, int(val_str))
                action_text = f"修改為: `{old_val}` ➡️ **`{new_val}`**"
                
            card_manager.chars_cache[char_name][skill_name] = new_val
            card_manager.save_data() # 背景自動同步至 GitHub
            
            # 用極簡的 Embed 卡片進行回覆，保持視覺統一
            embed = discord.Embed(
                title=f"📊 {char_name}",
                description=f"**{skill_name}** {action_text}",
                color=0x3498db
            )
            await ctx.reply(embed=embed)
            
        except Exception as e:
            await ctx.reply(f"❌ 調整數值失敗: {str(e)}")

# 初始化 Cog
async def setup(bot):
    await bot.add_cog(CardCommands(bot))
