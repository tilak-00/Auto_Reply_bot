import logging
from telegram import Update, ChatPermissions
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)
import os
TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

SPAM_WORDS = ["free money", "crypto", "loan", "porn", "xxx", "click here"]
WARN_LIMIT = 3
WARN_DB = {}   # Stores warnings: {user_id: count}

# ---------- Helper ---------- #
async def is_admin(update: Update):
    chat_admins = [admin.user.id for admin in await update.effective_chat.get_administrators()]
    return update.effective_user.id in chat_admins


# ---------- Commands ---------- #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Advanced Group Protector is Active!\n"
        "Add me to a group & make me ADMIN 🔐"
    )


async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """📌 Group Rules:
1️⃣ Be respectful
2️⃣ No spam / NSFW
3️⃣ No links without permission
4️⃣ Follow admin instructions
Enjoy 😊"""
    await update.message.reply_text(text)


# ---------- Welcome & Goodbye ---------- #
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        await update.message.reply_text(
            f"🎉 Welcome {member.mention_html()}!\nBehave well 😄",
            parse_mode="HTML"
        )


async def goodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Someone left the group!")


# ---------- Anti Spam ---------- #
async def anti_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.lower()

    # Block spam words
    for word in SPAM_WORDS:
        if word in msg:
            await update.message.delete()
            await update.message.reply_text("⚠️ Spam detected & removed!")
            return

    # Block Links
    if "http://" in msg or "https://" in msg or "t.me" in msg:
        if not await is_admin(update):
            await update.message.delete()
            await update.message.reply_text("🚫 Links are not allowed!")
            return


# ---------- Warn System ---------- #
async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        return await update.message.reply_text("❌ Admins only!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("Reply to user to warn ❗")

    user = update.message.reply_to_message.from_user
    user_id = user.id

    WARN_DB[user_id] = WARN_DB.get(user_id, 0) + 1
    warns = WARN_DB[user_id]

    if warns >= WARN_LIMIT:
        await update.effective_chat.ban_member(user_id)
        WARN_DB[user_id] = 0
        await update.message.reply_text(f"🚫 {user.first_name} banned after 3 warnings!")
    else:
        await update.message.reply_text(f"⚠️ {user.first_name} warned ({warns}/3)")


# ---------- Mute / Ban ---------- #
async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        return await update.message.reply_text("❌ Admins only!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("Reply to user to mute ❗")

    user = update.message.reply_to_message.from_user
    await update.effective_chat.restrict_member(
        user.id,
        ChatPermissions(can_send_messages=False)
    )
    await update.message.reply_text(f"🔇 {user.first_name} muted!")


async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        return await update.message.reply_text("❌ Admins only!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("Reply to user to unmute ❗")

    user = update.message.reply_to_message.from_user

    await update.effective_chat.restrict_member(
        user.id,
        ChatPermissions(can_send_messages=True)
    )
    await update.message.reply_text(f"🔊 {user.first_name} unmuted!")


async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        return await update.message.reply_text("❌ Admins only!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("Reply to user to ban ❗")

    user = update.message.reply_to_message.from_user
    await update.effective_chat.ban_member(user.id)
    await update.message.reply_text(f"🚫 {user.first_name} banned!")


# ---------- Main ---------- #
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("rules", rules))
app.add_handler(CommandHandler("warn", warn))
app.add_handler(CommandHandler("mute", mute))
app.add_handler(CommandHandler("unmute", unmute))
app.add_handler(CommandHandler("ban", ban))

app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, goodbye))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, anti_spam))

print("🔥 Advanced Bot Running…")
app.run_polling()

