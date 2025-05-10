from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from bot.database.db import Database
from bot.utils.helpers import *
from bot import config
from datetime import datetime, timedelta
import uuid

db = Database()

# حالت‌های گفتگو
PAYMENT_METHOD, PAYMENT_CONFIRM = range(2)

async def show_payment_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش منوی پرداخت"""
    subscription_type = context.user_data.get('subscription_type')
    if not subscription_type:
        await update.callback_query.edit_message_text(
            "❌ خطا: نوع اشتراک انتخاب نشده است.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data='back_to_subscription')]])
        )
        return ConversationHandler.END
    
    price = config.SUBSCRIPTION_PRICES.get(subscription_type)
    if not price:
        await update.callback_query.edit_message_text(
            "❌ خطا: قیمت اشتراک نامعتبر است.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data='back_to_subscription')]])
        )
        return ConversationHandler.END
    
    keyboard = [
        [InlineKeyboardButton("💳 پرداخت آنلاین", callback_data='payment_online')],
        [InlineKeyboardButton("🏦 پرداخت کارت به کارت", callback_data='payment_card')],
        [InlineKeyboardButton("بازگشت", callback_data='back_to_subscription')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        f"💰 پرداخت اشتراک {subscription_type}:\n\n"
        f"مبلغ قابل پرداخت: {format_price(price)} تومان\n\n"
        "لطفاً روش پرداخت را انتخاب کنید:",
        reply_markup=reply_markup
    )
    return PAYMENT_METHOD

async def handle_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت روش پرداخت"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'back_to_subscription':
        return ConversationHandler.END
    
    payment_method = query.data.split('_')[1]
    subscription_type = context.user_data.get('subscription_type')
    price = config.SUBSCRIPTION_PRICES.get(subscription_type)
    
    if payment_method == 'online':
        # ایجاد لینک پرداخت
        payment_id = str(uuid.uuid4())
        payment_link = f"https://payment.example.com/pay/{payment_id}"
        
        # ذخیره اطلاعات پرداخت
        db.add_payment({
            'payment_id': payment_id,
            'user_id': update.effective_user.id,
            'subscription_type': subscription_type,
            'amount': price,
            'status': 'pending',
            'created_at': datetime.now()
        })
        
        keyboard = [
            [InlineKeyboardButton("🔗 پرداخت آنلاین", url=payment_link)],
            [InlineKeyboardButton("✅ تایید پرداخت", callback_data='confirm_payment')],
            [InlineKeyboardButton("❌ انصراف", callback_data='cancel_payment')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"💳 پرداخت آنلاین:\n\n"
            f"مبلغ قابل پرداخت: {format_price(price)} تومان\n\n"
            "لطفاً روی دکمه پرداخت آنلاین کلیک کنید و پس از پرداخت، دکمه تایید پرداخت را بزنید.",
            reply_markup=reply_markup
        )
    else:
        # اطلاعات کارت بانکی
        card_number = "6037-XXXX-XXXX-1234"
        card_holder = "بانک ملت"
        
        keyboard = [
            [InlineKeyboardButton("✅ تایید پرداخت", callback_data='confirm_payment')],
            [InlineKeyboardButton("❌ انصراف", callback_data='cancel_payment')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🏦 پرداخت کارت به کارت:\n\n"
            f"مبلغ قابل پرداخت: {format_price(price)} تومان\n"
            f"شماره کارت: {card_number}\n"
            f"به نام: {card_holder}\n\n"
            "پس از پرداخت، دکمه تایید پرداخت را بزنید.",
            reply_markup=reply_markup
        )
    
    return PAYMENT_CONFIRM

async def handle_payment_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت تایید پرداخت"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'cancel_payment':
        await query.edit_message_text(
            "❌ پرداخت لغو شد.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data='back_to_subscription')]])
        )
        return ConversationHandler.END
    
    user_id = update.effective_user.id
    subscription_type = context.user_data.get('subscription_type')
    
    # بروزرسانی وضعیت پرداخت
    payment = db.get_latest_payment(user_id)
    if payment:
        db.update_payment_status(payment['payment_id'], 'completed')
    
    # فعال‌سازی اشتراک
    duration = config.SUBSCRIPTION_DURATIONS.get(subscription_type, 30)
    expiry_date = datetime.now() + timedelta(days=duration)
    db.update_user_subscription(user_id, subscription_type, expiry_date)
    
    # ارسال پیام موفقیت
    await query.edit_message_text(
        "✅ پرداخت با موفقیت انجام شد.\n\n"
        f"اشتراک {subscription_type} شما فعال شد.\n"
        f"تاریخ انقضا: {format_date(expiry_date)}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت به منو", callback_data='back_to_main')]])
    )
    
    return ConversationHandler.END

async def show_payment_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش تاریخچه پرداخت‌ها"""
    user_id = update.effective_user.id
    payments = db.get_user_payments(user_id)
    
    if not payments:
        await update.callback_query.edit_message_text(
            "📝 تاریخچه پرداخت‌ها:\n\n"
            "شما هنوز هیچ پرداختی انجام نداده‌اید.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data='back_to_main')]])
        )
        return ConversationHandler.END
    
    message = "📝 تاریخچه پرداخت‌ها:\n\n"
    for payment in payments:
        message += (
            f"تاریخ: {format_date(payment['created_at'])}\n"
            f"نوع اشتراک: {payment['subscription_type']}\n"
            f"مبلغ: {format_price(payment['amount'])} تومان\n"
            f"وضعیت: {get_payment_status(payment['status'])}\n\n"
        )
    
    await update.callback_query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data='back_to_main')]])
    )
    return ConversationHandler.END

def get_payment_status(status):
    """دریافت وضعیت پرداخت به فارسی"""
    statuses = {
        'pending': 'در انتظار پرداخت',
        'completed': 'تکمیل شده',
        'failed': 'ناموفق',
        'cancelled': 'لغو شده'
    }
    return statuses.get(status, status) 