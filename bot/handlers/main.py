from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from bot.database.db import Database
from bot.utils.helpers import *
from bot import config

# ایجاد نمونه از دیتابیس
db = Database()

# تعریف حالت‌های گفتگو
REGISTER, CATEGORY, MAIN_MENU = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع ربات"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if user:
        return await show_main_menu(update, context)
    
    await update.message.reply_text(
        "به ربات تعاملات بین اصناف خوش آمدید!\n"
        "لطفاً نام کسب و کار خود را وارد کنید:"
    )
    return REGISTER

async def register_business(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ثبت‌نام کسب و کار"""
    user_id = update.effective_user.id
    business_name = update.message.text
    
    # ذخیره نام کسب و کار در context
    context.user_data['business_name'] = business_name
    
    # ایجاد دکمه‌های دسته‌بندی
    keyboard = []
    for category_id, category_name in config.CATEGORIES.items():
        keyboard.append([InlineKeyboardButton(category_name, callback_data=f'category_{category_id}')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "لطفاً دسته‌بندی کسب و کار خود را انتخاب کنید:",
        reply_markup=reply_markup
    )
    return CATEGORY

async def category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """انتخاب دسته‌بندی"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    category = query.data.split('_')[1]
    
    # ذخیره اطلاعات کاربر
    user_data = {
        'user_id': user_id,
        'business_name': context.user_data['business_name'],
        'category': category,
        'username': update.effective_user.username,
        'first_name': update.effective_user.first_name,
        'last_name': update.effective_user.last_name
    }
    
    db.add_user(user_data)
    
    await query.edit_message_text(
        f"ثبت‌نام شما با موفقیت انجام شد!\n"
        f"دسته‌بندی: {get_category_name(category)}"
    )
    return await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش منوی اصلی"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    keyboard = [
        [InlineKeyboardButton("مشاهده آگهی‌ها", callback_data='view_ads')],
        [InlineKeyboardButton("ثبت آگهی", callback_data='new_ad')],
        [InlineKeyboardButton("پیام‌های من", callback_data='my_messages')],
        [InlineKeyboardButton("پروفایل", callback_data='profile')]
    ]
    
    # اضافه کردن دکمه‌های ادمین
    if is_admin(user_id):
        keyboard.append([InlineKeyboardButton("پنل ادمین", callback_data='admin_panel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "منوی اصلی:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "منوی اصلی:",
            reply_markup=reply_markup
        )
    return MAIN_MENU

async def handle_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت انتخاب‌های منو"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'view_ads':
        # نمایش آگهی‌ها
        ads = db.get_category_ads('all')
        if not ads:
            await query.edit_message_text("هیچ آگهی فعالی وجود ندارد.")
            return MAIN_MENU
        
        for ad in ads[:5]:  # نمایش 5 آگهی اول
            await query.message.reply_text(format_ad_info(ad))
        
        await query.message.reply_text("برای مشاهده آگهی‌های بیشتر، از اشتراک استفاده کنید.")
    
    elif query.data == 'new_ad':
        # بررسی محدودیت آگهی
        if not check_ad_limit(update.effective_user.id):
            await query.edit_message_text(
                "شما به محدودیت تعداد آگهی روزانه رسیده‌اید.\n"
                "لطفاً فردا مجدداً تلاش کنید."
            )
            return MAIN_MENU
        
        # بررسی اشتراک
        user = db.get_user(update.effective_user.id)
        if not is_subscription_active(user.get('subscription', {}).get('expires_at')):
            await query.edit_message_text(
                "برای ثبت آگهی نیاز به اشتراک دارید.\n"
                "لطفاً ابتدا اشتراک تهیه کنید."
            )
            return MAIN_MENU
        
        await query.edit_message_text(
            "لطفاً عنوان آگهی را وارد کنید:"
        )
        # اینجا می‌توانید منطق ثبت آگهی را پیاده‌سازی کنید
    
    elif query.data == 'my_messages':
        # نمایش پیام‌ها
        messages = db.get_user_messages(update.effective_user.id)
        if not messages:
            await query.edit_message_text("هیچ پیامی ندارید.")
            return MAIN_MENU
        
        for message in messages[:5]:  # نمایش 5 پیام اول
            await query.message.reply_text(
                f"از: {message.get('sender_name', 'نامشخص')}\n"
                f"پیام: {message.get('text', 'نامشخص')}\n"
                f"تاریخ: {format_date(message.get('created_at'))}"
            )
    
    elif query.data == 'profile':
        # نمایش پروفایل
        user = db.get_user(update.effective_user.id)
        await query.edit_message_text(format_user_info(user))
    
    elif query.data == 'admin_panel':
        # نمایش پنل ادمین
        if not is_admin(update.effective_user.id):
            await query.edit_message_text("شما دسترسی به این بخش را ندارید.")
            return MAIN_MENU
        
        keyboard = [
            [InlineKeyboardButton("آمار کلی", callback_data='admin_stats')],
            [InlineKeyboardButton("مدیریت کاربران", callback_data='admin_users')],
            [InlineKeyboardButton("مدیریت آگهی‌ها", callback_data='admin_ads')],
            [InlineKeyboardButton("ارسال پیام به همه", callback_data='admin_broadcast')],
            [InlineKeyboardButton("بازگشت به منو", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "پنل مدیریت:",
            reply_markup=reply_markup
        )
    
    return MAIN_MENU

async def admin_verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """احراز هویت ادمین"""
    if not context.args:
        await update.message.reply_text("لطفاً کد ادمین را وارد کنید.")
        return
    
    code = context.args[0]
    if verify_admin_code(code):
        db.set_admin(update.effective_user.id)
        await update.message.reply_text("شما با موفقیت به عنوان ادمین ثبت شدید.")
    else:
        await update.message.reply_text("کد ادمین نامعتبر است.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش راهنمای ربات"""
    help_text = (
        "🤖 راهنمای ربات تعاملات بین اصناف:\n\n"
        "📌 دستورات اصلی:\n"
        "/start - شروع ربات\n"
        "/help - نمایش این راهنما\n\n"
        "📌 امکانات ربات:\n"
        "• مشاهده و ثبت آگهی‌ها\n"
        "• ارسال و دریافت پیام\n"
        "• جستجو در آگهی‌ها\n"
        "• امتیازدهی به آگهی‌ها\n"
        "• مدیریت پروفایل\n\n"
        "📌 نکات مهم:\n"
        "• برای ثبت آگهی نیاز به اشتراک دارید\n"
        "• تعداد آگهی‌های روزانه محدود است\n"
        "• برای استفاده از امکانات ویژه، اشتراک تهیه کنید"
    )
    await update.message.reply_text(help_text)

async def cancel(update, context):
    await update.message.reply_text("عملیات لغو شد.")
    return ConversationHandler.END 