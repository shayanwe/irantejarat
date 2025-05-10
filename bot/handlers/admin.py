from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from bot.database.db import Database
from bot.utils.helpers import *
from bot import config

db = Database()

# حالت‌های گفتگو
BROADCAST, USER_MANAGEMENT, AD_MANAGEMENT = range(3)

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش پنل ادمین"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("شما دسترسی به این بخش را ندارید.")
        return
    
    keyboard = [
        [InlineKeyboardButton("آمار کلی", callback_data='admin_stats')],
        [InlineKeyboardButton("مدیریت کاربران", callback_data='admin_users')],
        [InlineKeyboardButton("مدیریت آگهی‌ها", callback_data='admin_ads')],
        [InlineKeyboardButton("ارسال پیام به همه", callback_data='admin_broadcast')],
        [InlineKeyboardButton("بازگشت به منو", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "پنل مدیریت:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "پنل مدیریت:",
            reply_markup=reply_markup
        )

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آمار کلی"""
    query = update.callback_query
    await query.answer()
    
    stats = db.get_stats()
    
    message = "📊 آمار کلی:\n\n"
    message += f"👥 تعداد کل کاربران: {stats['total_users']}\n"
    message += f"📝 تعداد کل آگهی‌ها: {stats['total_ads']}\n"
    message += f"💬 تعداد کل پیام‌ها: {stats['total_messages']}\n"
    message += f"⭐ تعداد اشتراک‌های فعال: {stats['active_subscriptions']}\n"
    
    keyboard = [[InlineKeyboardButton("بازگشت", callback_data='back_to_admin')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup)

async def show_user_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش مدیریت کاربران"""
    query = update.callback_query
    await query.answer()
    
    users = db.get_all_users()
    
    keyboard = []
    for user in users:
        keyboard.append([
            InlineKeyboardButton(
                f"{user['business_name']} - {get_category_name(user['category'])}",
                callback_data=f'user_{user["user_id"]}'
            )
        ])
    
    keyboard.append([InlineKeyboardButton("بازگشت", callback_data='back_to_admin')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "مدیریت کاربران:\nلطفاً کاربر مورد نظر را انتخاب کنید:",
        reply_markup=reply_markup
    )

async def manage_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت یک کاربر خاص"""
    query = update.callback_query
    await query.answer()
    
    user_id = int(query.data.split('_')[1])
    user = db.get_user(user_id)
    
    keyboard = [
        [InlineKeyboardButton("تغییر دسته‌بندی", callback_data=f'change_category_{user_id}')],
        [InlineKeyboardButton("تغییر وضعیت اشتراک", callback_data=f'change_sub_{user_id}')],
        [InlineKeyboardButton("مسدود کردن/رفع مسدودیت", callback_data=f'toggle_block_{user_id}')],
        [InlineKeyboardButton("حذف کاربر", callback_data=f'delete_user_{user_id}')],
        [InlineKeyboardButton("بازگشت", callback_data='admin_users')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = f"مدیریت کاربر {user['business_name']}:\n\n"
    message += f"دسته‌بندی: {get_category_name(user['category'])}\n"
    message += f"وضعیت اشتراک: {'فعال' if is_subscription_active(user.get('subscription', {}).get('expires_at')) else 'غیرفعال'}\n"
    message += f"تاریخ ثبت‌نام: {format_date(user['created_at'])}\n"
    
    await query.edit_message_text(message, reply_markup=reply_markup)

async def show_ad_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش مدیریت آگهی‌ها"""
    query = update.callback_query
    await query.answer()
    
    ads = db.get_all_ads()
    
    keyboard = []
    for ad in ads:
        user = db.get_user(ad['user_id'])
        keyboard.append([
            InlineKeyboardButton(
                f"{ad['title']} - {user['business_name']}",
                callback_data=f'ad_{ad["ad_id"]}'
            )
        ])
    
    keyboard.append([InlineKeyboardButton("بازگشت", callback_data='back_to_admin')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "مدیریت آگهی‌ها:\nلطفاً آگهی مورد نظر را انتخاب کنید:",
        reply_markup=reply_markup
    )

async def manage_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت یک آگهی خاص"""
    query = update.callback_query
    await query.answer()
    
    ad_id = query.data.split('_')[1]
    ad = db.get_ad(ad_id)
    user = db.get_user(ad['user_id'])
    
    keyboard = [
        [InlineKeyboardButton("تغییر وضعیت", callback_data=f'change_status_{ad_id}')],
        [InlineKeyboardButton("ویرایش دسته‌بندی", callback_data=f'change_ad_category_{ad_id}')],
        [InlineKeyboardButton("حذف آگهی", callback_data=f'delete_ad_{ad_id}')],
        [InlineKeyboardButton("بازگشت", callback_data='admin_ads')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = f"مدیریت آگهی {ad['title']}:\n\n"
    message += f"کاربر: {user['business_name']}\n"
    message += f"دسته‌بندی: {get_category_name(ad['category'])}\n"
    message += f"قیمت: {format_price(ad['price'])}\n"
    message += f"وضعیت: {ad['status']}\n"
    message += f"تاریخ ثبت: {format_date(ad['created_at'])}\n"
    
    await query.edit_message_text(message, reply_markup=reply_markup)

async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع ارسال پیام به همه کاربران"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "لطفاً پیام مورد نظر برای ارسال به همه کاربران را وارد کنید:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("انصراف", callback_data='back_to_admin')]])
    )
    return BROADCAST

async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال پیام به همه کاربران"""
    message_text = update.message.text
    users = db.get_all_users()
    
    success_count = 0
    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user['user_id'],
                text=f"📢 پیام مهم:\n\n{message_text}"
            )
            success_count += 1
        except Exception as e:
            logger.error(f"Error sending broadcast to {user['user_id']}: {e}")
    
    await update.message.reply_text(
        f"پیام با موفقیت به {success_count} کاربر ارسال شد.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت به پنل", callback_data='back_to_admin')]])
    )
    return ConversationHandler.END 