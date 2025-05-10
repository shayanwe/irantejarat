from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.constants import ParseMode
from bot import config

def create_main_menu():
    """ایجاد منوی اصلی با دکمه‌های شیشه‌ای"""
    keyboard = [
        [KeyboardButton("📢 آگهی‌ها"), KeyboardButton("💬 پیام‌ها")],
        [KeyboardButton("⭐ امتیازدهی"), KeyboardButton("🔔 اعلان‌ها")],
        [KeyboardButton("💰 اشتراک"), KeyboardButton("⚙️ تنظیمات")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def create_glass_button(text, callback_data):
    """ایجاد دکمه شیشه‌ای"""
    return InlineKeyboardButton(
        text,
        callback_data=callback_data,
        web_app=None
    )

def create_glass_keyboard(buttons):
    """ایجاد کیبورد شیشه‌ای"""
    keyboard = []
    for row in buttons:
        keyboard.append([create_glass_button(btn[0], btn[1]) for btn in row])
    return InlineKeyboardMarkup(keyboard)

def format_message(text, parse_mode=ParseMode.HTML):
    """قالب‌بندی پیام با استایل‌های زیبا"""
    return {
        'text': text,
        'parse_mode': parse_mode
    }

def create_help_message():
    """ایجاد پیام راهنما"""
    return format_message(
        "🤖 راهنمای ربات:\n\n"
        "📢 <b>آگهی‌ها</b>\n"
        "• مشاهده آگهی‌های جدید\n"
        "• ثبت آگهی جدید\n"
        "• جستجوی آگهی‌ها\n\n"
        "💬 <b>پیام‌ها</b>\n"
        "• مشاهده پیام‌های جدید\n"
        "• ارسال پیام جدید\n"
        "• مدیریت چت‌ها\n\n"
        "⭐ <b>امتیازدهی</b>\n"
        "• امتیازدهی به آگهی‌ها\n"
        "• ثبت نظر\n"
        "• گزارش تخلف\n\n"
        "🔔 <b>اعلان‌ها</b>\n"
        "• تنظیم اعلان‌های جدید\n"
        "• مدیریت اعلان‌های دسته‌بندی\n\n"
        "💰 <b>اشتراک</b>\n"
        "• مشاهده وضعیت اشتراک\n"
        "• تمدید اشتراک\n"
        "• تاریخچه پرداخت‌ها\n\n"
        "⚙️ <b>تنظیمات</b>\n"
        "• ویرایش پروفایل\n"
        "• تغییر دسته‌بندی\n"
        "• تنظیمات اعلان‌ها"
    )

def create_welcome_message(user_name):
    """ایجاد پیام خوش‌آمدگویی"""
    return format_message(
        f"👋 سلام {user_name} عزیز!\n\n"
        "به ربات آگهی‌های تجاری خوش آمدید.\n"
        "برای شروع، لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    )

def create_error_message(error_type):
    """ایجاد پیام خطا"""
    error_messages = {
        'subscription_expired': "❌ اشتراک شما به پایان رسیده است.\nلطفاً اشتراک خود را تمدید کنید.",
        'daily_limit': "❌ به محدودیت روزانه رسیده‌اید.\nلطفاً فردا دوباره تلاش کنید.",
        'invalid_input': "❌ ورودی نامعتبر است.\nلطفاً دوباره تلاش کنید.",
        'permission_denied': "❌ شما دسترسی لازم را ندارید.",
        'not_found': "❌ مورد مورد نظر یافت نشد.",
        'server_error': "❌ خطای سرور.\nلطفاً بعداً دوباره تلاش کنید."
    }
    return format_message(error_messages.get(error_type, "❌ خطای ناشناخته"))

def create_success_message(message_type):
    """ایجاد پیام موفقیت"""
    success_messages = {
        'ad_created': "✅ آگهی شما با موفقیت ثبت شد.",
        'ad_updated': "✅ آگهی شما با موفقیت بروزرسانی شد.",
        'ad_deleted': "✅ آگهی شما با موفقیت حذف شد.",
        'message_sent': "✅ پیام شما با موفقیت ارسال شد.",
        'rating_added': "✅ امتیاز شما با موفقیت ثبت شد.",
        'review_added': "✅ نظر شما با موفقیت ثبت شد.",
        'subscription_activated': "✅ اشتراک شما با موفقیت فعال شد.",
        'settings_updated': "✅ تنظیمات شما با موفقیت بروزرسانی شد."
    }
    return format_message(success_messages.get(message_type, "✅ عملیات با موفقیت انجام شد"))

def create_loading_message():
    """ایجاد پیام در حال بارگذاری"""
    return format_message("⏳ لطفاً صبر کنید...")

def create_confirmation_message(action):
    """ایجاد پیام تایید"""
    confirmation_messages = {
        'delete_ad': "⚠️ آیا از حذف این آگهی اطمینان دارید؟",
        'cancel_subscription': "⚠️ آیا از لغو اشتراک اطمینان دارید؟",
        'delete_account': "⚠️ آیا از حذف حساب کاربری اطمینان دارید؟"
    }
    return format_message(confirmation_messages.get(action, "⚠️ آیا از انجام این عملیات اطمینان دارید؟"))

def create_pagination_keyboard(current_page, total_pages, callback_prefix):
    """ایجاد کیبورد صفحه‌بندی"""
    keyboard = []
    
    # دکمه‌های صفحه‌بندی
    nav_buttons = []
    if current_page > 1:
        nav_buttons.append(create_glass_button("⬅️ قبلی", f"{callback_prefix}_prev"))
    if current_page < total_pages:
        nav_buttons.append(create_glass_button("بعدی ➡️", f"{callback_prefix}_next"))
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # دکمه‌های عملیات
    keyboard.append([
        create_glass_button("🔄 بروزرسانی", f"{callback_prefix}_refresh"),
        create_glass_button("❌ بستن", f"{callback_prefix}_close")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def create_category_keyboard(categories, callback_prefix):
    """ایجاد کیبورد دسته‌بندی‌ها"""
    keyboard = []
    row = []
    
    for i, category in enumerate(categories):
        row.append(create_glass_button(category, f"{callback_prefix}_{category}"))
        if len(row) == 2 or i == len(categories) - 1:
            keyboard.append(row)
            row = []
    
    keyboard.append([create_glass_button("بازگشت", f"{callback_prefix}_back")])
    return InlineKeyboardMarkup(keyboard)

def create_settings_keyboard(settings):
    """ایجاد کیبورد تنظیمات"""
    keyboard = []
    
    for setting, value in settings.items():
        keyboard.append([
            create_glass_button(
                f"{setting} {'✅' if value else '❌'}",
                f"setting_{setting}"
            )
        ])
    
    keyboard.append([create_glass_button("بازگشت", "settings_back")])
    return InlineKeyboardMarkup(keyboard) 