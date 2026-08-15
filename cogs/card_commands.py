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
    # 🔴 功能二：查看角色卡指令 (Embed 資訊卡升級版)
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

            # 💡 狀況 A：玩家想查「特定單一數值」（例如：.show 昼間和歌子 偵查）
            if skill_name:
                skill_name = skill_name.strip()
                # 大小寫轉換相容
                if skill_name.upper() in ["HP", "MP", "SAN", "LUK"]:
                    skill_name = skill_name.upper()
                
                if skill_name in card_manager.chars_cache[name]:
                    val = card_manager.chars_cache[name][skill_name]
                    max_key = f"{skill_name}_max"
                    
                    # 建立單一數值的極簡 Embed
                    embed = discord.Embed(
                        title=f"📊 {name}", # 角色名字會變大+粗體
                        description=f"**{skill_name}**: `{val}/{card_manager.chars_cache[name][max_key]}`" if max_key in card_manager.chars_cache[name] else f"**{skill_name}**: `{val}`",
                        color=discord.Color.blue() # 設定左側邊條為藍色
                    )
                    await ctx.reply(embed=embed)
                else:
                    await ctx.reply(f"❌ 角色 ` {name} ` 沒有 ` {skill_name} ` 這項數值！")
            
            # 💡 狀況 B：玩家只打了名字（例如：.show 昼間和歌子），吐出精美全屬性列表
            else:
                # 建立全卡資訊 Embed
                embed = discord.Embed(
                    title=f"📜 {name}", # 🔴 角色名字大字+粗體
                    color=discord.Color.blue() # 🔴 完美重現截圖中的藍色左側邊條
                )
                
                # 將所有技能與數值串成一整排，文字乾淨俐落
                skills_list = []
                for k, v in card_manager.chars_cache[name].items():
                    # 略過 _max 欄位，因為等一下會直接跟主數值結合
                    if k.endswith("_max"):
                        continue
                        
                    # 檢查這項數值有沒有最大值（HP/MP/SAN/LUK）
                    max_key = f"{k}_max"
                    if max_key in card_manager.chars_cache[name]:
                        max_val = card_manager.chars_cache[name][max_key]
                        skills_list.append(f"· {k}: `{v}/{max_val}`")
                    else:
                        skills_list.append(f"· {k}: `{v}`")
                
                # 把整排技能塞進卡片的核心內容區
                embed.description = "\n".join(skills_list)
                
                # 發送精美卡片
                await ctx.reply(embed=embed)

        except Exception as e:
            await ctx.reply(f"❌ 查看角色卡失敗: {str(e)}")
