import os
import json
import datetime
import discord
from discord.ext import commands, tasks
from discord.ui import View, Button
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ========= ENV =========
TOKEN = os.environ["DISCORD_TOKEN"]
CHANNEL_ID = int(os.environ["CHANNEL_ID"])
SHEET_JSON = os.environ["GOOGLE_CREDS_JSON"]
SHEET_ID = os.environ["SHEET_ID"]

TRIGGER_DAYS = ["Monday", "Thursday"]
POST_HOUR = 15  # heure serveur

# ========= DISCORD =========
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ========= GOOGLE SHEETS =========
creds_dict = json.loads(SHEET_JSON)
client = gspread.service_account_from_dict(creds_dict)
sheet = client.open_by_key(SHEET_ID).sheet1

# Tester l'accès
print("✅ Google Sheet accessible :", sheet.title)
print(sheet.get_all_records()[:1])  # juste un aperçu des données

# ========= DATA =========
def load_questions():
    df = pd.DataFrame(sheet.get_all_records())
    df.columns = df.columns.str.strip().str.lower()
    if "used" not in df.columns:
        df["used"] = False
    df["used"] = df["used"].astype(str).str.upper().map({"TRUE": True}).fillna(False)
    return df

def save_questions(df):
    sheet.update([df.columns.tolist()] + df.values.tolist())

def get_next_question():
    df = load_questions()
    q = df[df["used"] == False].head(1)
    return q, df

# ========= UI =========
class QuizView(View):
    def __init__(self, correct_answer, explanation):
        super().__init__(timeout=None)
        self.correct = "Vrai" if str(correct_answer).upper() in ["TRUE", "VRAI", "1"] else "Faux"
        self.explanation = explanation or "—"

    @discord.ui.button(label="Vrai", style=discord.ButtonStyle.green)
    async def vrai(self, interaction: discord.Interaction, button: Button):
        await self.check(interaction, "Vrai")

    @discord.ui.button(label="Faux", style=discord.ButtonStyle.red)
    async def faux(self, interaction: discord.Interaction, button: Button):
        await self.check(interaction, "Faux")

    async def check(self, interaction, answer):
        msg = "✅ Bonne réponse !" if answer == self.correct else "❌ Mauvaise réponse."
        await interaction.response.send_message(
            f"{msg}\n\n📘 **Explication :** {self.explanation}",
            ephemeral=True
        )

# ========= TÂCHE ÉCOLO =========
@tasks.loop(minutes=10)
async def eco_quiz():
    now = datetime.datetime.now()

    if now.strftime("%A") not in TRIGGER_DAYS:
        return
    if now.hour != POST_HOUR:
        return

    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("⚠️ Channel introuvable")
        return

    q, df = get_next_question()
    if q.empty:
        print("ℹ️ Pas de questions disponibles")
        return

    row = q.iloc[0]
    view = QuizView(row.get("exact"), row.get("explications"))

    await channel.send(
        f"🧠 **Question du quiz**\n\n{row.get('question')}",
        view=view
    )

    df.loc[df["id"] == row["id"], "used"] = True
    save_questions(df)

# ========= COMMANDES =========
@bot.command()
async def startquiz(ctx):
    if not eco_quiz.is_running():
        eco_quiz.start()
        await ctx.send("✅ Quiz lancé (mode écolo).")

@bot.command()
async def stopquiz(ctx):
    if eco_quiz.is_running():
        eco_quiz.stop()
        await ctx.send("🛑 Quiz arrêté.")

# ========= READY =========
@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")

bot.run(TOKEN)
