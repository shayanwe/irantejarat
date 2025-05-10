from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from bot.database.db import Database
from bot.utils.helpers import *
from bot import config
from datetime import datetime

db = Database()

# حالت‌های گفتگو
TITLE, DESCRIPTION, PRICE, CATEGORY, IMAGES, CONTACT, HASHTAGS, CONFIRM = range(8)

# هشتگ‌های پیشنهادی برای هر دسته‌بندی
CATEGORY_HASHTAGS = {
    'restaurant': ['رستوران', 'کافه', 'غذا', 'کافه_گردی', 'رستوران_گردی', 'کافه_شبانه', 'کافه_کتاب', 'کافه_کار', 'کافه_دنج', 'کافه_مدرن'],
    'retail': ['خرید', 'فروشگاه', 'مغازه', 'خرید_آنلاین', 'فروش_عمده', 'خرید_عمده', 'فروش_تخفیف', 'حراج', 'فروش_ویژه', 'خرید_مستقیم'],
    'service': ['خدمات', 'سرویس', 'خدمات_مشتری', 'خدمات_حرفه_ای', 'خدمات_تخصصی', 'خدمات_در_منزل', 'خدمات_شرکتی', 'خدمات_آنلاین', 'خدمات_فوری', 'خدمات_مشاوره'],
    'education': ['آموزش', 'کلاس', 'دوره', 'مدرسه', 'دانشگاه', 'آموزش_آنلاین', 'آموزش_مجازی', 'آموزش_تخصصی', 'آموزش_زبان', 'آموزش_مهارت'],
    'health': ['سلامت', 'زیبایی', 'پزشکی', 'درمان', 'بهداشت', 'سلامتی', 'زیبایی_صورت', 'زیبایی_مو', 'سلامت_روان', 'سلامت_جسم'],
    'other': ['کسب_و_کار', 'کارآفرینی', 'استارتاپ', 'تجارت', 'بازاریابی', 'فروش', 'خدمات', 'تولید', 'صنعت', 'کسب_و_کار_آنلاین']
}

async def show_ads_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش منوی آگهی‌ها"""
    keyboard = [
        [InlineKeyboardButton("جستجوی آگهی", callback_data='search_ads')],
        [InlineKeyboardButton("ثبت آگهی جدید", callback_data='new_ad')],
        [InlineKeyboardButton("آگهی‌های من", callback_data='my_ads')],
        [InlineKeyboardButton("بازگشت به منو", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "منوی آگهی‌ها:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "منوی آگهی‌ها:",
            reply_markup=reply_markup
        )

async def search_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """جستجوی آگهی‌ها"""
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for category_id, category_name in config.CATEGORIES.items():
        keyboard.append([InlineKeyboardButton(category_name, callback_data=f'search_{category_id}')])
    keyboard.append([InlineKeyboardButton("همه دسته‌بندی‌ها", callback_data='search_all')])
    keyboard.append([InlineKeyboardButton("بازگشت", callback_data='back_to_ads_menu')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "لطفاً دسته‌بندی مورد نظر را انتخاب کنید:",
        reply_markup=reply_markup
    )

async def show_category_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آگهی‌های یک دسته‌بندی"""
    query = update.callback_query
    await query.answer()
    
    category = query.data.split('_')[1]
    ads = db.get_category_ads(category)
    
    if not ads:
        await query.edit_message_text(
            "هیچ آگهی فعالی در این دسته‌بندی وجود ندارد.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data='back_to_ads_menu')]])
        )
        return
    
    # نمایش 5 آگهی اول
    for ad in ads[:5]:
        keyboard = [
            [InlineKeyboardButton("ارسال پیام", callback_data=f'message_{ad["user_id"]}')],
            [InlineKeyboardButton("ذخیره", callback_data=f'save_{ad["ad_id"]}')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            format_ad_info(ad),
            reply_markup=reply_markup
        )
    
    # دکمه‌های ناوبری
    nav_keyboard = []
    if len(ads) > 5:
        nav_keyboard.append([
            InlineKeyboardButton("صفحه بعد", callback_data=f'next_page_{category}_1')
        ])
    nav_keyboard.append([InlineKeyboardButton("بازگشت", callback_data='back_to_ads_menu')])
    
    await query.message.reply_text(
        "برای مشاهده آگهی‌های بیشتر، از اشتراک استفاده کنید.",
        reply_markup=InlineKeyboardMarkup(nav_keyboard)
    )

async def new_ad_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع ثبت آگهی جدید"""
    query = update.callback_query
    await query.answer()
    
    # بررسی محدودیت آگهی
    if not check_ad_limit(update.effective_user.id):
        await query.edit_message_text(
            "شما به محدودیت تعداد آگهی روزانه رسیده‌اید.\n"
            "لطفاً فردا مجدداً تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data='back_to_ads_menu')]])
        )
        return
    
    # بررسی اشتراک
    user = db.get_user(update.effective_user.id)
    if not is_subscription_active(user.get('subscription', {}).get('expires_at')):
        await query.edit_message_text(
            "برای ثبت آگهی نیاز به اشتراک دارید.\n"
            "لطفاً ابتدا اشتراک تهیه کنید.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data='back_to_ads_menu')]])
        )
        return
    
    await query.edit_message_text(
        "لطفاً عنوان آگهی را وارد کنید:\n"
        "(حداکثر 50 کاراکتر)"
    )
    return TITLE

async def new_ad_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت عنوان آگهی"""
    title = update.message.text.strip()
    
    if len(title) > 50:
        await update.message.reply_text(
            "عنوان آگهی نباید بیشتر از 50 کاراکتر باشد.\n"
            "لطفاً عنوان کوتاه‌تری وارد کنید:"
        )
        return TITLE
    
    context.user_data['ad_title'] = title
    await update.message.reply_text(
        "لطفاً توضیحات آگهی را وارد کنید:\n"
        "(حداکثر 500 کاراکتر)"
    )
    return DESCRIPTION

async def new_ad_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت توضیحات آگهی"""
    description = update.message.text.strip()
    
    if len(description) > 500:
        await update.message.reply_text(
            "توضیحات آگهی نباید بیشتر از 500 کاراکتر باشد.\n"
            "لطفاً توضیحات کوتاه‌تری وارد کنید:"
        )
        return DESCRIPTION
    
    context.user_data['ad_description'] = description
    
    keyboard = [
        [InlineKeyboardButton("قیمت توافقی", callback_data='price_negotiable')],
        [InlineKeyboardButton("بازگشت", callback_data='back_to_ads_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "لطفاً قیمت را به تومان وارد کنید:",
        reply_markup=reply_markup
    )
    return PRICE

async def new_ad_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت قیمت آگهی"""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        
        if query.data == 'price_negotiable':
            context.user_data['ad_price'] = 'توافقی'
            return await show_category_selection(update, context)
        elif query.data == 'back_to_ads_menu':
            return ConversationHandler.END
    
    try:
        price = int(update.message.text)
        if price <= 0:
            raise ValueError
        context.user_data['ad_price'] = price
    except ValueError:
        await update.message.reply_text(
            "لطفاً یک عدد معتبر وارد کنید:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("قیمت توافقی", callback_data='price_negotiable')],
                [InlineKeyboardButton("بازگشت", callback_data='back_to_ads_menu')]
            ])
        )
        return PRICE
    
    return await show_category_selection(update, context)

async def show_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش انتخاب دسته‌بندی"""
    keyboard = []
    for category_id, category_name in config.CATEGORIES.items():
        keyboard.append([InlineKeyboardButton(category_name, callback_data=f'cat_{category_id}')])
    keyboard.append([InlineKeyboardButton("بازگشت", callback_data='back_to_ads_menu')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "لطفاً دسته‌بندی آگهی را انتخاب کنید:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "لطفاً دسته‌بندی آگهی را انتخاب کنید:",
            reply_markup=reply_markup
        )
    return CATEGORY

async def new_ad_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت دسته‌بندی آگهی"""
    query = update.callback_query
    await query.answer()
    
    category = query.data.split('_')[1]
    context.user_data['ad_category'] = category
    
    await query.edit_message_text(
        "لطفاً تصاویر آگهی را ارسال کنید:\n"
        "(حداکثر 3 تصویر، هر تصویر حداکثر 5MB)\n\n"
        "برای اتمام آپلود تصاویر، دستور /done را ارسال کنید."
    )
    return IMAGES

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش تصاویر آگهی"""
    if not update.message.photo:
        await update.message.reply_text(
            "لطفاً فقط تصویر ارسال کنید.\n"
            "برای اتمام آپلود تصاویر، دستور /done را ارسال کنید."
        )
        return IMAGES
    
    if 'ad_images' not in context.user_data:
        context.user_data['ad_images'] = []
    
    if len(context.user_data['ad_images']) >= 3:
        await update.message.reply_text(
            "حداکثر تعداد تصاویر مجاز 3 عدد است.\n"
            "برای ادامه، دستور /done را ارسال کنید."
        )
        return IMAGES
    
    photo = update.message.photo[-1]  # بزرگترین سایز تصویر
    if photo.file_size > config.MAX_FILE_SIZE:
        await update.message.reply_text(
            "حجم تصویر نباید بیشتر از 5MB باشد.\n"
            "لطفاً تصویر دیگری ارسال کنید."
        )
        return IMAGES
    
    # ذخیره تصویر
    file = await context.bot.get_file(photo.file_id)
    file_path = f"{config.UPLOAD_FOLDER}/{photo.file_id}.jpg"
    await file.download_to_drive(file_path)
    
    context.user_data['ad_images'].append(file_path)
    
    remaining = 3 - len(context.user_data['ad_images'])
    await update.message.reply_text(
        f"تصویر با موفقیت ذخیره شد.\n"
        f"تعداد تصاویر باقیمانده: {remaining}\n\n"
        "برای اتمام آپلود تصاویر، دستور /done را ارسال کنید."
    )
    return IMAGES

async def finish_images(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پایان آپلود تصاویر"""
    await update.message.reply_text(
        "لطفاً شماره تماس خود را وارد کنید:"
    )
    return CONTACT

async def new_ad_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت اطلاعات تماس"""
    contact = update.message.text.strip()
    
    # اعتبارسنجی شماره تماس
    if not is_valid_phone(contact):
        await update.message.reply_text(
            "شماره تماس نامعتبر است.\n"
            "لطفاً شماره تماس معتبر وارد کنید:"
        )
        return CONTACT
    
    context.user_data['ad_contact'] = contact
    
    # نمایش هشتگ‌های پیشنهادی
    category = context.user_data['ad_category']
    suggested_hashtags = CATEGORY_HASHTAGS.get(category, CATEGORY_HASHTAGS['other'])
    
    # اضافه کردن هشتگ‌های مرتبط با عنوان و توضیحات
    title_words = context.user_data['ad_title'].split()
    desc_words = context.user_data['ad_description'].split()
    
    # استخراج کلمات کلیدی از عنوان و توضیحات
    keywords = set()
    for word in title_words + desc_words:
        if len(word) > 3:  # فقط کلمات با طول بیشتر از 3 حرف
            keywords.add(word)
    
    # اضافه کردن هشتگ‌های مرتبط با کلمات کلیدی
    for keyword in keywords:
        hashtag = f"#{keyword}"
        if len(hashtag) <= 20:  # محدودیت طول هشتگ
            suggested_hashtags.append(hashtag)
    
    # حذف هشتگ‌های تکراری و محدود کردن به 10 هشتگ
    suggested_hashtags = list(set(suggested_hashtags))[:10]
    
    # ذخیره هشتگ‌های پیشنهادی
    context.user_data['suggested_hashtags'] = suggested_hashtags
    
    # نمایش هشتگ‌های پیشنهادی
    hashtag_text = "\n".join([f"#{tag}" for tag in suggested_hashtags])
    await update.message.reply_text(
        f"هشتگ‌های پیشنهادی برای آگهی شما:\n\n{hashtag_text}\n\n"
        "آیا مایلید هشتگ‌های دیگری اضافه کنید؟\n"
        "می‌توانید هشتگ‌های خود را با فاصله وارد کنید یا برای ادامه، دستور /done را ارسال کنید."
    )
    return HASHTAGS

async def handle_hashtags(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش هشتگ‌های اضافه شده توسط کاربر"""
    if update.message.text == '/done':
        return await show_ad_summary(update, context)
    
    # دریافت هشتگ‌های جدید
    new_hashtags = update.message.text.strip().split()
    new_hashtags = [tag.strip('#') for tag in new_hashtags if tag.strip('#')]
    
    # ترکیب هشتگ‌های پیشنهادی و جدید
    all_hashtags = context.user_data.get('suggested_hashtags', []) + new_hashtags
    all_hashtags = list(set(all_hashtags))  # حذف تکراری‌ها
    
    # محدود کردن به 10 هشتگ
    context.user_data['ad_hashtags'] = all_hashtags[:10]
    
    # نمایش هشتگ‌های نهایی
    hashtag_text = "\n".join([f"#{tag}" for tag in context.user_data['ad_hashtags']])
    await update.message.reply_text(
        f"هشتگ‌های نهایی آگهی شما:\n\n{hashtag_text}\n\n"
        "برای ادامه، دستور /done را ارسال کنید."
    )
    return HASHTAGS

async def show_ad_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش خلاصه نهایی آگهی"""
    # نمایش خلاصه آگهی
    keyboard = [
        [InlineKeyboardButton("ثبت آگهی", callback_data='confirm_ad')],
        [InlineKeyboardButton("انصراف", callback_data='cancel_ad')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # تبدیل هشتگ‌ها به متن
    hashtags_text = " ".join([f"#{tag}" for tag in context.user_data.get('ad_hashtags', [])])
    
    summary = (
        f"📝 خلاصه آگهی:\n\n"
        f"عنوان: {context.user_data['ad_title']}\n"
        f"توضیحات: {context.user_data['ad_description']}\n"
        f"قیمت: {format_price(context.user_data['ad_price'])}\n"
        f"دسته‌بندی: {get_category_name(context.user_data['ad_category'])}\n"
        f"تعداد تصاویر: {len(context.user_data.get('ad_images', []))}\n"
        f"شماره تماس: {context.user_data['ad_contact']}\n"
        f"هشتگ‌ها: {hashtags_text}\n\n"
        "آیا مایل به ثبت آگهی هستید؟"
    )
    
    await update.message.reply_text(summary, reply_markup=reply_markup)
    return CONFIRM

async def confirm_new_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تایید و ثبت آگهی جدید"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'cancel_ad':
        await query.edit_message_text("ثبت آگهی لغو شد.")
        return ConversationHandler.END
    
    # ثبت آگهی در دیتابیس
    ad_data = {
        'user_id': update.effective_user.id,
        'title': context.user_data['ad_title'],
        'description': context.user_data['ad_description'],
        'price': context.user_data['ad_price'],
        'category': context.user_data['ad_category'],
        'images': context.user_data.get('ad_images', []),
        'contact': context.user_data['ad_contact'],
        'hashtags': context.user_data.get('ad_hashtags', []),
        'status': 'active',
        'created_at': datetime.now()
    }
    
    db.add_ad(ad_data)
    
    # تبدیل هشتگ‌ها به متن برای نمایش
    hashtags_text = " ".join([f"#{tag}" for tag in ad_data['hashtags']])
    
    await query.edit_message_text(
        f"✅ آگهی شما با موفقیت ثبت شد!\n\n"
        f"هشتگ‌های آگهی: {hashtags_text}\n\n"
        "برای مشاهده آگهی‌های خود، به بخش 'آگهی‌های من' مراجعه کنید.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت به منو", callback_data='back_to_ads_menu')]])
    )
    
    return ConversationHandler.END

async def show_my_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آگهی‌های کاربر"""
    query = update.callback_query
    await query.answer()
    
    ads = db.get_user_ads(update.effective_user.id)
    
    if not ads:
        await query.edit_message_text(
            "شما هیچ آگهی فعالی ندارید.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data='back_to_ads_menu')]])
        )
        return
    
    for ad in ads:
        keyboard = [
            [InlineKeyboardButton("ویرایش", callback_data=f'edit_{ad["ad_id"]}')],
            [InlineKeyboardButton("حذف", callback_data=f'delete_{ad["ad_id"]}')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            format_ad_info(ad),
            reply_markup=reply_markup
        )
    
    await query.message.reply_text(
        "برای مدیریت آگهی‌های خود، از دکمه‌های بالا استفاده کنید.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data='back_to_ads_menu')]])
    ) 