import os
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی
load_dotenv()

# تنظیمات ربات
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))

# تنظیمات دیتابیس
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
DB_NAME = os.getenv('DB_NAME', 'irantejarat')

# تنظیمات Redis
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

# قیمت‌های اشتراک (به تومان)
SUBSCRIPTION_PRICES = {
    'monthly': 99000,
    'quarterly': 285000,
    'biannual': 540000,
    'yearly': 999000
}

# دسته‌بندی‌های آگهی
CATEGORIES = {
    'electronics': 'الکترونیک',
    'furniture': 'مبلمان',
    'clothing': 'پوشاک',
    'food': 'مواد غذایی',
    'services': 'خدمات',
    'other': 'سایر'
}

# محدودیت‌های سیستم
MAX_ADS_PER_DAY = 5
MAX_MESSAGES_PER_DAY = 50
MAX_IMAGES_PER_AD = 5
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# تنظیمات امنیتی
MAX_REQUESTS_PER_MINUTE = 30

# تنظیمات فایل
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf'}

# محدودیت‌های کاربری
DAILY_AD_LIMIT = 5
DAILY_MESSAGE_LIMIT = 20 