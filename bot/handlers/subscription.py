from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from bot.database.db import Database
from bot.utils.helpers import *
from bot import config
from datetime import datetime

db = Database()

# حالت‌های گفتگو
SUBSCRIPTION_TYPE, SUBSCRIPTION_CONFIRM = range(2)

async def show_subscription_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش منوی اشتراک"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    # بررسی وضعیت اشتراک فعلی
    subscription = user.get('subscription', {})
    is_active = is_subscription_active(subscription.get('expires_at'))
    
    keyboard = [
        [InlineKeyboardButton("اشتراک یک ماهه - 99,000 تومان", callback_data='sub_monthly')],
        [InlineKeyboardButton("اشتراک سه ماهه - 285,000 تومان", callback_data='sub_quarterly')],
        [InlineKeyboardButton("اشتراک شش ماهه - 540,000 تومان", callback_data='sub_biannual')],
        [InlineKeyboardButton("اشتراک سالانه - 999,000 تومان", callback_data='sub_yearly')],
        [InlineKeyboardButton("بازگشت به منو", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = "منوی اشتراک:\n\n"
    if is_active:
        message += f"اشتراک فعلی شما تا {format_date(subscription['expires_at'])} فعال است."
    else:
        message += "شما اشتراک فعال ندارید."
    
    if update.callback_query:
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message, reply_markup=reply_markup)
    
    return SUBSCRIPTION_TYPE

async def handle_subscription_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت انتخاب نوع اشتراک"""
    query = update.callback_query
    await query.answer()
    
    sub_type = query.data.split('_')[1]
    price = config.SUBSCRIPTION_PRICES[sub_type]
    
    # ذخیره نوع اشتراک در context
    context.user_data['subscription_type'] = sub_type
    
    # تعیین مدت زمان اشتراک
    duration_map = {
        'monthly': 1,
        'quarterly': 3,
        'biannual': 6,
        'yearly': 12
    }
    duration = duration_map[sub_type]
    
    keyboard = [
        [InlineKeyboardButton("پرداخت", callback_data=f'pay_{sub_type}')],
        [InlineKeyboardButton("انصراف", callback_data='cancel_payment')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"اشتراک {get_subscription_name(sub_type)}:\n"
        f"قیمت: {format_price(price)}\n"
        f"مدت زمان: {duration} ماه\n\n"
        "آیا مایل به پرداخت هستید؟",
        reply_markup=reply_markup
    )
    
    return SUBSCRIPTION_CONFIRM

async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش پرداخت"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'cancel_payment':
        return await show_subscription_menu(update, context)
    
    sub_type = query.data.split('_')[1]
    user_id = update.effective_user.id
    
    # در اینجا می‌توانید به درگاه پرداخت متصل شوید
    # برای مثال، از API بانک یا درگاه پرداخت استفاده کنید
    
    # شبیه‌سازی پرداخت موفق
    duration_map = {
        'monthly': 1,
        'quarterly': 3,
        'biannual': 6,
        'yearly': 12
    }
    duration = duration_map[sub_type]
    
    subscription_data = {
        'type': sub_type,
        'expires_at': calculate_subscription_end_date(duration)
    }
    
    db.update_subscription(user_id, subscription_data)
    
    await query.edit_message_text(
        "پرداخت با موفقیت انجام شد!\n"
        f"اشتراک شما تا {format_date(subscription_data['expires_at'])} فعال است."
    )
    
    return ConversationHandler.END

async def cancel_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لغو اشتراک"""
    user_id = update.effective_user.id
    db.update_subscription(user_id, {'type': 'free', 'expires_at': None})
    
    await update.message.reply_text("اشتراک شما با موفقیت لغو شد.")
    return ConversationHandler.END

async def confirm_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تایید و ثبت اشتراک"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'cancel_payment':
        await query.edit_message_text(
            "عملیات لغو شد.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت به منو", callback_data='back_to_menu')]])
        )
        return ConversationHandler.END
    
    user_id = update.effective_user.id
    subscription_type = context.user_data.get('subscription_type')
    
    if not subscription_type:
        await query.edit_message_text(
            "❌ خطا: نوع اشتراک انتخاب نشده است.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data='back_to_subscription')]])
        )
        return ConversationHandler.END
    
    # محاسبه تاریخ انقضا
    duration_map = {
        'monthly': 1,
        'quarterly': 3,
        'biannual': 6,
        'yearly': 12
    }
    duration = duration_map[subscription_type]
    expires_at = calculate_subscription_end_date(duration)
    
    # ثبت اشتراک
    subscription_data = {
        'type': subscription_type,
        'started_at': datetime.now(),
        'expires_at': expires_at,
        'status': 'active'
    }
    db.update_subscription(user_id, subscription_data)
    
    # نمایش پیام موفقیت
    await query.edit_message_text(
        f"✅ اشتراک شما با موفقیت ثبت شد!\n\n"
        f"نوع اشتراک: {get_subscription_name(subscription_type)}\n"
        f"تاریخ انقضا: {format_date(expires_at)}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت به منو", callback_data='back_to_menu')]])
    )
    
    return ConversationHandler.END 