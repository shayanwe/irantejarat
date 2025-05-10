from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from bot.database.db import Database
from bot.utils.helpers import *
from bot import config
from datetime import datetime, timedelta

db = Database()

# حالت‌های گفتگو
SEARCH_TYPE, SEARCH_QUERY, FILTER_PRICE, FILTER_DATE, SORT_RESULTS = range(5)

async def show_search_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش منوی جستجو"""
    keyboard = [
        [InlineKeyboardButton("جستجو در عنوان", callback_data='search_title')],
        [InlineKeyboardButton("جستجو در توضیحات", callback_data='search_description')],
        [InlineKeyboardButton("جستجو در هشتگ‌ها", callback_data='search_hashtags')],
        [InlineKeyboardButton("جستجوی پیشرفته", callback_data='search_advanced')],
        [InlineKeyboardButton("بازگشت", callback_data='back_to_ads_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "🔍 منوی جستجو:\n\n"
            "لطفاً نوع جستجو را انتخاب کنید:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "🔍 منوی جستجو:\n\n"
            "لطفاً نوع جستجو را انتخاب کنید:",
            reply_markup=reply_markup
        )
    return SEARCH_TYPE

async def handle_search_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت نوع جستجو"""
    query = update.callback_query
    await query.answer()
    
    search_type = query.data.split('_')[1]
    context.user_data['search_type'] = search_type
    
    if search_type == 'advanced':
        return await show_advanced_search(update, context)
    
    await query.edit_message_text(
        f"لطفاً عبارت مورد نظر برای جستجو در {get_search_type_name(search_type)} را وارد کنید:"
    )
    return SEARCH_QUERY

async def show_advanced_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش جستجوی پیشرفته"""
    keyboard = [
        [InlineKeyboardButton("فیلتر قیمت", callback_data='filter_price')],
        [InlineKeyboardButton("فیلتر تاریخ", callback_data='filter_date')],
        [InlineKeyboardButton("مرتب‌سازی نتایج", callback_data='sort_results')],
        [InlineKeyboardButton("شروع جستجو", callback_data='start_search')],
        [InlineKeyboardButton("بازگشت", callback_data='back_to_search')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        "🔍 جستجوی پیشرفته:\n\n"
        "لطفاً فیلترهای مورد نظر را انتخاب کنید:",
        reply_markup=reply_markup
    )
    return FILTER_PRICE

async def handle_price_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت فیلتر قیمت"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'back_to_search':
        return await show_search_menu(update, context)
    
    keyboard = [
        [InlineKeyboardButton("کمتر از 1 میلیون", callback_data='price_lt_1m')],
        [InlineKeyboardButton("1 تا 5 میلیون", callback_data='price_1m_5m')],
        [InlineKeyboardButton("5 تا 10 میلیون", callback_data='price_5m_10m')],
        [InlineKeyboardButton("بیشتر از 10 میلیون", callback_data='price_gt_10m')],
        [InlineKeyboardButton("بدون محدودیت قیمت", callback_data='price_all')],
        [InlineKeyboardButton("بازگشت", callback_data='back_to_advanced')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "💰 فیلتر قیمت:\n\n"
        "لطفاً محدوده قیمت مورد نظر را انتخاب کنید:",
        reply_markup=reply_markup
    )
    return FILTER_DATE

async def handle_date_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت فیلتر تاریخ"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'back_to_advanced':
        return await show_advanced_search(update, context)
    
    # ذخیره فیلتر قیمت
    price_filter = query.data.split('_')
    if len(price_filter) > 1:
        context.user_data['price_filter'] = price_filter[1:]
    
    keyboard = [
        [InlineKeyboardButton("امروز", callback_data='date_today')],
        [InlineKeyboardButton("هفته گذشته", callback_data='date_last_week')],
        [InlineKeyboardButton("ماه گذشته", callback_data='date_last_month')],
        [InlineKeyboardButton("بدون محدودیت تاریخ", callback_data='date_all')],
        [InlineKeyboardButton("بازگشت", callback_data='back_to_advanced')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📅 فیلتر تاریخ:\n\n"
        "لطفاً بازه زمانی مورد نظر را انتخاب کنید:",
        reply_markup=reply_markup
    )
    return SORT_RESULTS

async def handle_sort_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت مرتب‌سازی نتایج"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'back_to_advanced':
        return await show_advanced_search(update, context)
    
    # ذخیره فیلتر تاریخ
    date_filter = query.data.split('_')
    if len(date_filter) > 1:
        context.user_data['date_filter'] = date_filter[1:]
    
    keyboard = [
        [InlineKeyboardButton("جدیدترین", callback_data='sort_newest')],
        [InlineKeyboardButton("قدیمی‌ترین", callback_data='sort_oldest')],
        [InlineKeyboardButton("گران‌ترین", callback_data='sort_expensive')],
        [InlineKeyboardButton("ارزان‌ترین", callback_data='sort_cheapest')],
        [InlineKeyboardButton("بازگشت", callback_data='back_to_advanced')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔄 مرتب‌سازی نتایج:\n\n"
        "لطفاً نحوه مرتب‌سازی نتایج را انتخاب کنید:",
        reply_markup=reply_markup
    )
    return SEARCH_QUERY

async def perform_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """انجام جستجو"""
    query = update.callback_query
    await query.answer()
    
    # ذخیره نحوه مرتب‌سازی
    sort_type = query.data.split('_')[1]
    context.user_data['sort_type'] = sort_type
    
    # اعمال فیلترها
    filters = {}
    
    # فیلتر قیمت
    if 'price_filter' in context.user_data:
        price_filter = context.user_data['price_filter']
        if price_filter[0] == 'lt':
            filters['price'] = {'$lt': 1000000}
        elif price_filter[0] == '1m_5m':
            filters['price'] = {'$gte': 1000000, '$lte': 5000000}
        elif price_filter[0] == '5m_10m':
            filters['price'] = {'$gte': 5000000, '$lte': 10000000}
        elif price_filter[0] == 'gt':
            filters['price'] = {'$gt': 10000000}
    
    # فیلتر تاریخ
    if 'date_filter' in context.user_data:
        date_filter = context.user_data['date_filter']
        now = datetime.now()
        if date_filter[0] == 'today':
            filters['created_at'] = {'$gte': now.replace(hour=0, minute=0, second=0)}
        elif date_filter[0] == 'last_week':
            filters['created_at'] = {'$gte': now - timedelta(days=7)}
        elif date_filter[0] == 'last_month':
            filters['created_at'] = {'$gte': now - timedelta(days=30)}
    
    # انجام جستجو
    search_type = context.user_data.get('search_type', 'title')
    search_query = context.user_data.get('search_query', '')
    
    if search_type == 'title':
        filters['title'] = {'$regex': search_query, '$options': 'i'}
    elif search_type == 'description':
        filters['description'] = {'$regex': search_query, '$options': 'i'}
    elif search_type == 'hashtags':
        filters['hashtags'] = {'$in': [search_query]}
    
    # مرتب‌سازی نتایج
    sort_options = {
        'newest': {'created_at': -1},
        'oldest': {'created_at': 1},
        'expensive': {'price': -1},
        'cheapest': {'price': 1}
    }
    sort = sort_options.get(sort_type, {'created_at': -1})
    
    # دریافت نتایج
    results = db.search_ads(filters, sort)
    
    if not results:
        await query.edit_message_text(
            "❌ هیچ نتیجه‌ای یافت نشد.\n\n"
            "لطفاً فیلترهای جستجو را تغییر دهید.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data='back_to_search')]])
        )
        return ConversationHandler.END
    
    # نمایش نتایج
    message = "🔍 نتایج جستجو:\n\n"
    for i, ad in enumerate(results[:5], 1):
        message += f"{i}. {format_ad_info(ad)}\n\n"
    
    if len(results) > 5:
        message += f"\nو {len(results) - 5} نتیجه دیگر..."
    
    keyboard = []
    if len(results) > 5:
        keyboard.append([InlineKeyboardButton("صفحه بعد", callback_data='next_page_1')])
    keyboard.append([InlineKeyboardButton("جستجوی جدید", callback_data='new_search')])
    keyboard.append([InlineKeyboardButton("بازگشت", callback_data='back_to_ads_menu')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message, reply_markup=reply_markup)
    
    return ConversationHandler.END

def get_search_type_name(search_type):
    """دریافت نام فارسی نوع جستجو"""
    types = {
        'title': 'عنوان',
        'description': 'توضیحات',
        'hashtags': 'هشتگ‌ها'
    }
    return types.get(search_type, search_type) 