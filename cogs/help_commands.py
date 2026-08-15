import discord
from discord.ext import commands

class HelpCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ====================================================================
    # 💡 專屬極簡幫助說明書指令 (.help / .HELP)
    # ====================================================================
    @commands.command(name="help")
    async def help_command(self, ctx):
        help_text = (
            "**【小優彩說明書DA】**\n\n"
            "🗃️ **角色卡管理 (.add/.show/.set)**\n"
            "· 格式： `.add [角色名稱] [角色卡內容(記得刪除前後"")]`\n"
            "· 範例： `.add 藍川優彩 APP/99`\n"
            "· 查看全卡/特定數值： `.show 藍川優彩` 或 `.show 藍川優彩 APP`\n"
            "· 調整角卡數值： `.set 藍川優彩 信用 90` 或 `.set 藍川優彩 信用 +10`\n\n"
            "🎲 **普通擲骰 (.r)**\n"
            "· 範例： `.r (2D6+6)*5`\n"
            "· 重複骰 N 次： `.r 3d6 N`\n\n"
            "🔮 **技能判定 (.r)**\n"
            "· 格式： `.r (獎懲骰) [技能數值] (技能名稱)`\n"            
            "· 範例： `.r -1 60 偵查` \n"
            "· 範例： `.r 藍川優彩 +1 偵查` \n\n"
            "🧠 **理智檢定 (.sc) **\n"
            "· 格式： `.sc (次數) [角色名稱/數值] [成功扣的數值/失敗扣的數值] `\n"
            "· 範例： `.sc 2 藍川優彩 1d20/1d100 看見KP真身`\n\n"
            "🔀 **多組任務同時輸入 (用逗號隔開)**\n"
            "· 範例： `.r 1d20+5, 藍川優彩 心理學, 3d6 2`\n"
            "**優彩會公平公正的骰完後並回覆你！**"
        )
        await ctx.reply(help_text)

# 初始化 Cog
async def setup(bot):
    await bot.add_cog(HelpCommands(bot))
