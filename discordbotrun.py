# discordbotrun.py（トークンを.envから読み込むように修正）
import os
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button
from dotenv import load_dotenv

# .envから環境変数を読み込む
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree

session_data = {}  # 発表会ごとの参加者
session_dates = []  # 登録済み発表会の日付

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Botが起動しました: {bot.user.name}")

@tree.command(name="req", description="発表会に参加希望を出します")
async def req(interaction: discord.Interaction):
    if not session_dates:
        await interaction.response.send_message("まだ発表会の日付が作成されていません", ephemeral=True)
        return

    view = View(timeout=None)
    added = False
    sorted_dates = sorted(session_dates)

    for date in sorted_dates:
        if len(session_data.get(date, [])) >= 2:
            continue

        button = Button(label=date, style=discord.ButtonStyle.primary)

        async def callback(interaction_button: discord.Interaction, d=date):
            modal = discord.ui.Modal(title="名前の入力")
            name_input = discord.ui.TextInput(label="名前", placeholder="自分の名前", required=True)
            title_input = discord.ui.TextInput(label="内容/タイトル", placeholder="発表内容", required=True)
            modal.add_item(name_input)
            modal.add_item(title_input)

            async def on_submit(modal_interaction: discord.Interaction):
                name = name_input.value
                title = title_input.value
                entries = session_data.setdefault(d, [])

                if any(e['name'] == name for e in entries):
                    await modal_interaction.response.send_message(f"{d} はすでに同じ名前で参加しています", ephemeral=True)
                    return

                entries.append({"name": name, "title": title})
                await modal_interaction.response.send_message(f"{name}さんが {d} に「{title}」で参加希望しました！")

            modal.on_submit = on_submit
            await interaction_button.response.send_modal(modal)

        button.callback = callback
        view.add_item(button)
        added = True

    if added:
        await interaction.response.send_message("参加したい発表会の日付を選んでください：", view=view, ephemeral=True)
    else:
        await interaction.response.send_message("参加可能な日付（空きあり）はありません。", ephemeral=True)

@tree.command(name="can", description="参加をキャンセル")
@app_commands.describe(name="名前", date="発表会の日付")
async def can(interaction: discord.Interaction, name: str, date: str):
    for entry in session_data.get(date, []):
        if entry["name"] == name:
            session_data[date].remove(entry)
            await interaction.response.send_message(f"❌ {name}さんの {date} の発表会参加をキャンセルしました")
            return
    await interaction.response.send_message(f"{date} の発表会に {name} は参加していません")

@tree.command(name="create", description="発表会の日付を作成")
@app_commands.describe(date="発表会の日付")
async def create(interaction: discord.Interaction, date: str):
    if date in session_dates:
        await interaction.response.send_message(f"{date} はすでに作成されています")
        return
    session_dates.append(date)
    session_data[date] = []
    await interaction.response.send_message(f"✅ {date} を発表会日として登録しました")

@tree.command(name="list", description="参加者一覧")
async def list_participants(interaction: discord.Interaction):
    if not session_data:
        await interaction.response.send_message("まだ参加希望者はいません")
        return

    message = "**📅 参加者一覧:**\n"
    for date in sorted(session_data.keys()):
        entries = session_data[date]
        if entries:
            entry_text = "\n".join([f"- {e['name']}「{e['title']}」" for e in entries])
            message += f"**{date}**\n{entry_text}\n"
        else:
            message += f"**{date}**: （参加者なし）\n"

    await interaction.response.send_message(message)

@tree.command(name="reset", description="すべての予定と参加希望をリセット")
async def reset(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("⚠️ 管理者のみ実行可能", ephemeral=True)
        return

    session_data.clear()
    session_dates.clear()
    await interaction.response.send_message("🗑️ データを初期化しました")

# 実行
bot.run(DISCORD_TOKEN)
