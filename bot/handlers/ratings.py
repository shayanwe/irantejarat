from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from bot.database.db import Database
from bot.utils.helpers import *
from bot import config
from datetime import datetime

db = Database()

# حالت‌های گفتگو
RATE_AD, WRITE_REVIEW, REPORT_AD = range(3)

async def show_rating_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش منوی امتیازدهی"""
    ad_id = context.user_data.get('selected_ad_id')
    if not ad_id:
        await update.callback_query.edit_message_text(
            "❌ خطا: آگهی مورد نظر یافت نشد.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data='back_to_ad')]])
        )
        return ConversationHandler.END
    
    keyboard = [
        [InlineKeyboardButton("⭐ امتیازدهی", callback_data='rate_ad')],
        [InlineKeyboardButton("💬 ثبت نظر", callback_data='write_review')],
        [InlineKeyboardButton("⚠️ گزارش تخلف", callback_data='report_ad')],
        [InlineKeyboardButton("بازگشت", callback_data='back_to_ad')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        "📊 منوی امتیازدهی و نظرات:\n\n"
        "لطفاً عملیات مورد نظر را انتخاب کنید:",
        reply_markup=reply_markup
    )
    return RATE_AD

async def handle_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت امتیازدهی"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'back_to_ad':
        return ConversationHandler.END
    
    keyboard = []
    for i in range(1, 6):
        keyboard.append([InlineKeyboardButton("⭐" * i, callback_data=f'rate_{i}')])
    keyboard.append([InlineKeyboardButton("بازگشت", callback_data='back_to_rating')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "⭐ امتیازدهی:\n\n"
        "لطفاً امتیاز خود را انتخاب کنید:",
        reply_markup=reply_markup
    )
    return RATE_AD

async def save_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ذخیره امتیاز"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'back_to_rating':
        return await show_rating_menu(update, context)
    
    rating = int(query.data.split('_')[1])
    ad_id = context.user_data.get('selected_ad_id')
    user_id = update.effective_user.id
    
    # بررسی امتیاز قبلی
    existing_rating = db.get_user_rating(ad_id, user_id)
    if existing_rating:
        db.update_rating(ad_id, user_id, rating)
        message = "✅ امتیاز شما با موفقیت بروزرسانی شد."
    else:
        db.add_rating(ad_id, user_id, rating)
        message = "✅ امتیاز شما با موفقیت ثبت شد."
    
    # نمایش منوی امتیازدهی
    return await show_rating_menu(update, context)

async def handle_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت ثبت نظر"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'back_to_rating':
        return await show_rating_menu(update, context)
    
    await query.edit_message_text(
        "💬 ثبت نظر:\n\n"
        "لطفاً نظر خود را در مورد این آگهی بنویسید:\n"
        "(حداکثر 500 کاراکتر)"
    )
    return WRITE_REVIEW

async def save_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ذخیره نظر"""
    review_text = update.message.text
    
    if len(review_text) > 500:
        await update.message.reply_text(
            "❌ خطا: نظر شما نباید بیشتر از 500 کاراکتر باشد.\n"
            "لطفاً نظر کوتاه‌تری بنویسید."
        )
        return WRITE_REVIEW
    
    ad_id = context.user_data.get('selected_ad_id')
    user_id = update.effective_user.id
    
    # بررسی نظر قبلی
    existing_review = db.get_user_review(ad_id, user_id)
    if existing_review:
        db.update_review(ad_id, user_id, review_text)
        message = "✅ نظر شما با موفقیت بروزرسانی شد."
    else:
        db.add_review(ad_id, user_id, review_text)
        message = "✅ نظر شما با موفقیت ثبت شد."
    
    # نمایش منوی امتیازدهی
    keyboard = [[InlineKeyboardButton("بازگشت", callback_data='back_to_rating')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(message, reply_markup=reply_markup)
    return ConversationHandler.END

async def handle_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت گزارش تخلف"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'back_to_rating':
        return await show_rating_menu(update, context)
    
    keyboard = [
        [InlineKeyboardButton("محتوای نامناسب", callback_data='report_inappropriate')],
        [InlineKeyboardButton("کلاهبرداری", callback_data='report_scam')],
        [InlineKeyboardButton("تکرار آگهی", callback_data='report_duplicate')],
        [InlineKeyboardButton("سایر موارد", callback_data='report_other')],
        [InlineKeyboardButton("بازگشت", callback_data='back_to_rating')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "⚠️ گزارش تخلف:\n\n"
        "لطفاً نوع تخلف را انتخاب کنید:",
        reply_markup=reply_markup
    )
    return REPORT_AD

async def save_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ذخیره گزارش تخلف"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'back_to_rating':
        return await show_rating_menu(update, context)
    
    report_type = query.data.split('_')[1]
    ad_id = context.user_data.get('selected_ad_id')
    user_id = update.effective_user.id
    
    # ثبت گزارش
    db.add_report(ad_id, user_id, report_type)
    
    # اطلاع‌رسانی به ادمین
    admin_message = (
        f"⚠️ گزارش تخلف جدید:\n\n"
        f"آگهی: {ad_id}\n"
        f"کاربر: {user_id}\n"
        f"نوع تخلف: {report_type}"
    )
    await context.bot.send_message(chat_id=config.ADMIN_ID, text=admin_message)
    
    # نمایش پیام موفقیت
    keyboard = [[InlineKeyboardButton("بازگشت", callback_data='back_to_rating')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "✅ گزارش تخلف شما با موفقیت ثبت شد.\n"
        "تیم پشتیبانی در اسرع وقت آن را بررسی خواهد کرد.",
        reply_markup=reply_markup
    )
    return ConversationHandler.END 