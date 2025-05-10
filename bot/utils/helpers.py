from datetime import datetime, timedelta
from bot import config
import redis
import json

# اتصال به Redis
redis_client = redis.Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    db=config.REDIS_DB
)

def is_admin(user_id):
    """بررسی ادمین بودن کاربر"""
    return str(user_id) == str(config.ADMIN_ID)

def verify_admin_code(code):
    """بررسی کد ادمین"""
    return code == config.ADMIN_CODE

def check_rate_limit(user_id, action_type):
    """بررسی محدودیت تعداد درخواست"""
    key = f"rate_limit:{user_id}:{action_type}"
    current = redis_client.get(key)
    
    if not current:
        redis_client.setex(key, 60, 1)
        return True
    
    current = int(current)
    if current >= config.MAX_REQUESTS_PER_MINUTE:
        return False
    
    redis_client.incr(key)
    return True

def check_message_limit(user_id):
    """بررسی محدودیت تعداد پیام"""
    key = f"message_limit:{user_id}:{datetime.now().date()}"
    current = redis_client.get(key)
    
    if not current:
        redis_client.setex(key, 86400, 1)
        return True
    
    current = int(current)
    if current >= config.MAX_MESSAGES_PER_DAY:
        return False
    
    redis_client.incr(key)
    return True

def check_ad_limit(user_id):
    """بررسی محدودیت تعداد آگهی"""
    key = f"ad_limit:{user_id}:{datetime.now().date()}"
    current = redis_client.get(key)
    
    if not current:
        redis_client.setex(key, 86400, 1)
        return True
    
    current = int(current)
    if current >= config.MAX_ADS_PER_DAY:
        return False
    
    redis_client.incr(key)
    return True

def format_date(date):
    """فرمت‌بندی تاریخ"""
    return date.strftime("%Y-%m-%d %H:%M:%S")

def format_price(price):
    """فرمت‌بندی قیمت"""
    return f"{price:,} تومان"

def is_subscription_active(expires_at):
    """بررسی فعال بودن اشتراک"""
    if not expires_at:
        return False
    return datetime.now() < expires_at

def calculate_subscription_end_date(months):
    """محاسبه تاریخ انقضای اشتراک"""
    return datetime.now() + timedelta(days=30*months)

def validate_phone_number(phone):
    """اعتبارسنجی شماره موبایل"""
    return phone.startswith('09') and len(phone) == 11

def validate_file(file_data):
    """اعتبارسنجی فایل"""
    if not file_data:
        return False
    
    # بررسی حجم فایل
    if len(file_data) > config.MAX_FILE_SIZE:
        return False
    
    # بررسی نوع فایل
    file_ext = file_data.filename.split('.')[-1].lower()
    if file_ext not in config.ALLOWED_EXTENSIONS:
        return False
    
    return True

def get_category_name(category_id):
    """دریافت نام فارسی دسته‌بندی"""
    return config.CATEGORIES.get(category_id, 'نامشخص')

def get_subscription_name(subscription_type):
    """دریافت نام فارسی نوع اشتراک"""
    subscription_names = {
        'monthly': 'یک ماهه',
        'quarterly': 'سه ماهه',
        'biannual': 'شش ماهه',
        'yearly': 'سالانه'
    }
    return subscription_names.get(subscription_type, 'نامشخص')

def format_user_info(user):
    """فرمت‌بندی اطلاعات کاربر"""
    subscription = user.get('subscription', {})
    is_active = is_subscription_active(subscription.get('expires_at'))
    
    return f"""
👤 اطلاعات کاربر:

نام کسب و کار: {user.get('business_name', 'نامشخص')}
نام کاربری: @{user.get('username', 'نامشخص')}
دسته‌بندی: {get_category_name(user.get('category', 'other'))}
تاریخ عضویت: {format_date(user.get('created_at', datetime.now()))}

اشتراک: {'✅ فعال' if is_active else '❌ غیرفعال'}
{'' if not subscription else f'نوع اشتراک: {get_subscription_name(subscription.get("type"))}\nتاریخ انقضا: {format_date(subscription.get("expires_at"))}'}
"""

def format_ad_info(ad):
    """فرمت‌بندی اطلاعات آگهی"""
    return f"""
📢 {ad.get('title', 'بدون عنوان')}

📝 توضیحات:
{ad.get('description', 'بدون توضیحات')}

💰 قیمت: {format_price(ad.get('price', 0))}
🏷️ دسته‌بندی: {get_category_name(ad.get('category', 'other'))}
📅 تاریخ: {format_date(ad.get('created_at', datetime.now()))}
👤 آگهی‌دهنده: {ad.get('business_name', 'نامشخص')}

وضعیت: {ad.get('status', 'نامشخص')}
""" 