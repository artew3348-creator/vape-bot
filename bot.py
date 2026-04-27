from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, ContextTypes, filters
import json
import os

TOKEN = os.getenv("TOKEN")
ADMIN_ID = 8514413454  # твой Telegram ID
USERNAME = "Senpai66666"  # без @

# ===== база =====
def load_data():
    try:
        with open("data.json", "r") as f:
            return json.load(f)
    except:
        return {"products": [], "users": []}

def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f)

# ===== старт =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user_id = update.effective_user.id

    if user_id not in data["users"]:
        data["users"].append(user_id)
        save_data(data)

    keyboard = [
        [InlineKeyboardButton("🛒 Каталог", callback_data="catalog")],
        [InlineKeyboardButton("💨 Написать продавцу", url=f"https://t.me/{USERNAME}")]
    ]

    await update.message.reply_text(
        "💨 Добро пожаловать в Vape Shop!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ===== каталог =====
async def catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = load_data()

    if not data["products"]:
        await query.message.reply_text("❌ Товаров пока нет")
        return

    for product in data["products"]:
        await query.message.reply_photo(
            photo=product["photo"],
            caption=f"{product['name']}\n💰 {product['price']}\n\n{product['desc']}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💨 Купить", url=f"https://t.me/{USERNAME}")]
            ])
        )

# ===== админка =====
ADD_NAME, ADD_DESC, ADD_PRICE, ADD_PHOTO, BROADCAST = range(5)

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    keyboard = [
        [InlineKeyboardButton("➕ Добавить товар", callback_data="add")],
        [InlineKeyboardButton("📢 Рассылка", callback_data="broadcast")]
    ]

    await update.message.reply_text("⚙️ Админка", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        return

    if query.data == "add":
        await query.message.reply_text("Введите название товара:")
        return ADD_NAME

    if query.data == "broadcast":
        await query.message.reply_text("Отправь сообщение для рассылки:")
        return BROADCAST

async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Введите описание:")
    return ADD_DESC

async def add_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["desc"] = update.message.text
    await update.message.reply_text("Введите цену:")
    return ADD_PRICE

async def add_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["price"] = update.message.text
    await update.message.reply_text("Отправь фото товара:")
    return ADD_PHOTO

async def add_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()

    product = {
        "name": context.user_data["name"],
        "desc": context.user_data["desc"],
        "price": context.user_data["price"],
        "photo": update.message.photo[-1].file_id
    }

    data["products"].append(product)
    save_data(data)

    await update.message.reply_text("✅ Товар добавлен!")
    return ConversationHandler.END

# ===== рассылка =====
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    text = update.message.text

    for user in data["users"]:
        try:
            await context.bot.send_message(user, text)
        except:
            pass

    await update.message.reply_text("✅ Рассылка отправлена")
    return ConversationHandler.END

# ===== запуск =====
app = ApplicationBuilder().token(TOKEN).build()

conv = ConversationHandler(
    entry_points=[
        CommandHandler("admin", admin),
        CallbackQueryHandler(admin_buttons)
    ],
    states={
        ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_name)],
        ADD_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_desc)],
        ADD_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_price)],
        ADD_PHOTO: [MessageHandler(filters.PHOTO, add_photo)],
        BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast)]
    },
    fallbacks=[]
)

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(catalog, pattern="catalog"))
app.add_handler(conv)

print("Бот запущен...")
app.run_polling()
