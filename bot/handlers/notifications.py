from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from bot.database.db import Database
from bot.utils.helpers import *
from bot import config
from datetime import datetime, timedelta

db = Database()

# حالت‌های گفتگو
NOTIFICATION_SETTINGS, CATEGORY_NOTIFICATIONS = range(2)

async def show_notification_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش منوی اعلان‌ها"""
    user_id = update.effective_user.id
    settings = db.get_notification_settings(user_id)
    
    keyboard = [
        [InlineKeyboardButton(
            "🔔 اعلان آگهی‌های جدید" + (" ✅" if settings.get('new_ads', True) else " ❌"),
            callback_data='toggle_new_ads'
        )],
        [InlineKeyboardButton(
            "📨 اعلان پیام‌های جدید" + (" ✅" if settings.get('new_messages', True) else " ❌"),
            callback_data='toggle_new_messages'
        )],
        [InlineKeyboardButton(
            "⏰ اعلان پایان اشتراک" + (" ✅" if settings.get('subscription_expiry', True) else " ❌"),
            callback_data='toggle_subscription'
        )],
        [InlineKeyboardButton(
            "📊 اعلان‌های دسته‌بندی",
            callback_data='category_notifications'
        )],
        [InlineKeyboardButton("بازگشت", callback_data='back_to_main')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "🔔 تنظیمات اعلان‌ها:\n\n"
            "لطفاً اعلان‌های مورد نظر خود را انتخاب کنید:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "🔔 تنظیمات اعلان‌ها:\n\n"
            "لطفاً اعلان‌های مورد نظر خود را انتخاب کنید:",
            reply_markup=reply_markup
        )
    return NOTIFICATION_SETTINGS

async def toggle_notification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تغییر وضعیت اعلان"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'back_to_main':
        return ConversationHandler.END
    
    notification_type = query.data.split('_')[1]
    user_id = update.effective_user.id
    
    # تغییر وضعیت اعلان
    settings = db.get_notification_settings(user_id)
    current_value = settings.get(notification_type, True)
    db.update_notification_settings(user_id, notification_type, not current_value)
    
    # نمایش مجدد منو
    return await show_notification_menu(update, context)

async def show_category_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش اعلان‌های دسته‌بندی"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'back_to_main':
        return ConversationHandler.END
    
    user_id = update.effective_user.id
    settings = db.get_notification_settings(user_id)
    category_notifications = settings.get('category_notifications', {})
    
    keyboard = []
    for category in config.CATEGORIES:
        keyboard.append([InlineKeyboardButton(
            f"{category} {'✅' if category_notifications.get(category, False) else '❌'}",
            callback_data=f'toggle_category_{category}'
        )])
    keyboard.append([InlineKeyboardButton("بازگشت", callback_data='back_to_notifications')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "📊 اعلان‌های دسته‌بندی:\n\n"
        "لطفاً دسته‌بندی‌های مورد نظر برای دریافت اعلان را انتخاب کنید:",
        reply_markup=reply_markup
    )
    return CATEGORY_NOTIFICATIONS

async def toggle_category_notification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تغییر وضعیت اعلان دسته‌بندی"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'back_to_notifications':
        return await show_notification_menu(update, context)
    
    category = query.data.split('_')[2]
    user_id = update.effective_user.id
    
    # تغییر وضعیت اعلان دسته‌بندی
    settings = db.get_notification_settings(user_id)
    category_notifications = settings.get('category_notifications', {})
    current_value = category_notifications.get(category, False)
    category_notifications[category] = not current_value
    db.update_notification_settings(user_id, 'category_notifications', category_notifications)
    
    # نمایش مجدد منو
    return await show_category_notifications(update, context)

async def send_notification(user_id, message, context: ContextTypes.DEFAULT_TYPE):
    """ارسال اعلان به کاربر"""
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='HTML'
        )
        return True
    except Exception as e:
        print(f"Error sending notification: {e}")
        return False

async def notify_new_ad(ad, context: ContextTypes.DEFAULT_TYPE):
    """اعلان آگهی جدید"""
    # دریافت کاربران با اعلان فعال
    users = db.get_users_with_notification('new_ads', True)
    
    # ارسال اعلان به کاربران
    for user in users:
        # بررسی اعلان دسته‌بندی
        settings = db.get_notification_settings(user['user_id'])
        category_notifications = settings.get('category_notifications', {})
        
        if category_notifications.get(ad['category'], False):
            message = (
                "🔔 آگهی جدید:\n\n"
                f"عنوان: {ad['title']}\n"
                f"دسته‌بندی: {ad['category']}\n"
                f"قیمت: {format_price(ad['price'])} تومان\n\n"
                f"برای مشاهده آگهی کلیک کنید: /ad_{ad['_id']}"
            )
            await send_notification(user['user_id'], message, context)

async def notify_new_message(user_id, sender_id, message, context: ContextTypes.DEFAULT_TYPE):
    """اعلان پیام جدید"""
    # بررسی اعلان پیام
    settings = db.get_notification_settings(user_id)
    if settings.get('new_messages', True):
        sender = db.get_user(sender_id)
        message_text = (
            "📨 پیام جدید:\n\n"
            f"از: {sender['name']}\n"
            f"پیام: {message}\n\n"
            "برای مشاهده پیام کلیک کنید: /messages"
        )
        await send_notification(user_id, message_text, context)

async def notify_subscription_expiry(user_id, days_left, context: ContextTypes.DEFAULT_TYPE):
    """اعلان پایان اشتراک"""
    # بررسی اعلان اشتراک
    settings = db.get_notification_settings(user_id)
    if settings.get('subscription_expiry', True):
        message = (
            "⏰ یادآوری اشتراک:\n\n"
            f"اشتراک شما تا {days_left} روز دیگر به پایان می‌رسد.\n"
            "برای تمدید اشتراک کلیک کنید: /subscription"
        )
        await send_notification(user_id, message, context) 