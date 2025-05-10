from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from bot.database.db import Database
from bot.utils.helpers import *
from bot import config

db = Database()

# حالت‌های گفتگو
SELECT_CHAT, SEND_MESSAGE = range(2)

async def show_messages_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش منوی پیام‌ها"""
    user_id = update.effective_user.id
    
    # دریافت آخرین چت‌های کاربر
    chats = db.get_user_chats(user_id)
    
    keyboard = []
    for chat in chats:
        other_user = db.get_user(chat['other_user_id'])
        keyboard.append([
            InlineKeyboardButton(
                f"{other_user['business_name']} - {format_date(chat['last_message_time'])}",
                callback_data=f'chat_{chat["other_user_id"]}'
            )
        ])
    
    keyboard.extend([
        [InlineKeyboardButton("پیام جدید", callback_data='new_message')],
        [InlineKeyboardButton("بازگشت به منو", callback_data='back_to_menu')]
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "پیام‌های شما:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "پیام‌های شما:",
            reply_markup=reply_markup
        )

async def show_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش یک چت"""
    query = update.callback_query
    await query.answer()
    
    other_user_id = int(query.data.split('_')[1])
    user_id = update.effective_user.id
    
    # دریافت پیام‌های چت
    messages = db.get_chat_messages(user_id, other_user_id)
    
    if not messages:
        await query.edit_message_text(
            "هیچ پیامی در این چت وجود ندارد.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data='back_to_messages')]])
        )
        return
    
    # نمایش پیام‌ها
    for message in messages:
        is_sender = message['sender_id'] == user_id
        prefix = "شما: " if is_sender else f"{db.get_user(message['sender_id'])['business_name']}: "
        
        await query.message.reply_text(
            f"{prefix}{message['text']}\n"
            f"تاریخ: {format_date(message['created_at'])}"
        )
    
    # دکمه‌های مدیریت چت
    keyboard = [
        [InlineKeyboardButton("ارسال پیام", callback_data=f'send_to_{other_user_id}')],
        [InlineKeyboardButton("بازگشت", callback_data='back_to_messages')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(
        "برای ارسال پیام جدید، روی دکمه 'ارسال پیام' کلیک کنید.",
        reply_markup=reply_markup
    )

async def start_new_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع ارسال پیام جدید"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'new_message':
        # نمایش لیست کاربران برای انتخاب
        users = db.get_all_users()
        keyboard = []
        for user in users:
            if user['user_id'] != update.effective_user.id:
                keyboard.append([
                    InlineKeyboardButton(
                        user['business_name'],
                        callback_data=f'send_to_{user["user_id"]}'
                    )
                ])
        keyboard.append([InlineKeyboardButton("بازگشت", callback_data='back_to_messages')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "لطفاً کاربر مورد نظر را انتخاب کنید:",
            reply_markup=reply_markup
        )
        return SELECT_CHAT
    
    # اگر از چت موجود انتخاب شده
    other_user_id = int(query.data.split('_')[2])
    context.user_data['other_user_id'] = other_user_id
    
    await query.edit_message_text(
        "لطفاً پیام خود را وارد کنید:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("انصراف", callback_data='back_to_messages')]])
    )
    return SEND_MESSAGE

async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال پیام"""
    user_id = update.effective_user.id
    other_user_id = context.user_data['other_user_id']
    message_text = update.message.text
    
    # بررسی محدودیت پیام
    if not check_message_limit(user_id):
        await update.message.reply_text(
            "شما به محدودیت تعداد پیام روزانه رسیده‌اید.\n"
            "لطفاً فردا مجدداً تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data='back_to_messages')]])
        )
        return ConversationHandler.END
    
    # ذخیره پیام
    message_data = {
        'sender_id': user_id,
        'receiver_id': other_user_id,
        'text': message_text,
        'status': 'unread'
    }
    db.add_message(message_data)
    
    # ارسال پیام به کاربر دیگر
    other_user = db.get_user(other_user_id)
    await context.bot.send_message(
        chat_id=other_user_id,
        text=f"پیام جدید از {db.get_user(user_id)['business_name']}:\n\n{message_text}"
    )
    
    await update.message.reply_text(
        "پیام شما با موفقیت ارسال شد!",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت به پیام‌ها", callback_data='back_to_messages')]])
    )
    
    return ConversationHandler.END

async def mark_as_read(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """علامت‌گذاری پیام‌ها به عنوان خوانده شده"""
    query = update.callback_query
    await query.answer()
    
    message_id = query.data.split('_')[1]
    db.update_message(message_id, {'status': 'read'})
    
    await query.edit_message_text("پیام به عنوان خوانده شده علامت‌گذاری شد.") 