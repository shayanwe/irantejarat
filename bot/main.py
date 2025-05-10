import logging
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ConversationHandler
from bot.handlers.main import *
from bot.handlers.main import cancel
from bot.handlers.ads import *
from bot.handlers.messages import *
from bot.handlers.search import *
from bot.handlers.ratings import *
from bot.handlers.notifications import *
from bot.handlers.payment import *
from bot.handlers.admin import *
from bot.handlers.subscription import *
from bot.utils.ui import *
from bot import config

# تنظیمات لاگینگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# تعریف حالت‌های گفتگو
TITLE, DESCRIPTION, PRICE, CATEGORY, IMAGES, CONTACT, HASHTAGS, CONFIRM = range(8)
SELECT_CHAT, SEND_MESSAGE = range(2)
SEARCH_TYPE, SEARCH_QUERY, FILTER_PRICE, FILTER_DATE, SORT_RESULTS = range(5)
RATE_AD, WRITE_REVIEW, REPORT_AD = range(3)
NOTIFICATION_SETTINGS, CATEGORY_NOTIFICATIONS = range(2)
PAYMENT_METHOD, PAYMENT_CONFIRM = range(2)
BROADCAST, USER_MANAGEMENT, AD_MANAGEMENT = range(3)
SUBSCRIPTION_TYPE, SUBSCRIPTION_CONFIRM = range(2)

def main():
    """تابع اصلی ربات"""
    # ایجاد نمونه از برنامه
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # هندلرهای اصلی
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # هندلر آگهی‌ها
    ad_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(show_ads_menu, pattern='^ads_menu$'),
            CallbackQueryHandler(show_category_ads, pattern='^category_'),
            CallbackQueryHandler(new_ad_start, pattern='^new_ad$'),
            CallbackQueryHandler(show_my_ads, pattern='^my_ads$')
        ],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, new_ad_title)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, new_ad_description)],
            PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, new_ad_price)
            ],
            CATEGORY: [CallbackQueryHandler(new_ad_category, pattern='^category_')],
            IMAGES: [
                MessageHandler(filters.PHOTO, handle_image),
                CommandHandler("finish", finish_images)
            ],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, new_ad_contact)],
            CONFIRM: [CallbackQueryHandler(confirm_new_ad, pattern='^confirm_')],
            HASHTAGS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_hashtags)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )
    application.add_handler(ad_conv_handler)
    
    # هندلر پیام‌ها
    message_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(show_messages_menu, pattern='^messages_menu$'),
            CallbackQueryHandler(show_chat, pattern='^chat_'),
            CallbackQueryHandler(start_new_message, pattern='^new_message$')
        ],
        states={
            SELECT_CHAT: [CallbackQueryHandler(show_chat, pattern='^select_chat_')],
            SEND_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_message)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )
    application.add_handler(message_conv_handler)
    
    # هندلر جستجو
    search_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(show_search_menu, pattern='^search_menu$'),
            CallbackQueryHandler(handle_search_type, pattern='^search_')
        ],
        states={
            SEARCH_TYPE: [CallbackQueryHandler(handle_search_type, pattern='^search_')],
            SEARCH_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, perform_search)],
            FILTER_PRICE: [CallbackQueryHandler(handle_price_filter, pattern='^price_')],
            FILTER_DATE: [CallbackQueryHandler(handle_date_filter, pattern='^date_')],
            SORT_RESULTS: [CallbackQueryHandler(handle_sort_results, pattern='^sort_')]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )
    application.add_handler(search_conv_handler)
    
    # هندلر امتیازدهی
    rating_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(show_rating_menu, pattern='^rate_ad_'),
            CallbackQueryHandler(handle_rating, pattern='^rate_')
        ],
        states={
            RATE_AD: [CallbackQueryHandler(save_rating, pattern='^rate_')],
            WRITE_REVIEW: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_review)],
            REPORT_AD: [CallbackQueryHandler(save_report, pattern='^report_')]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )
    application.add_handler(rating_conv_handler)
    
    # هندلر اعلان‌ها
    notification_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(show_notification_menu, pattern='^notifications_menu$'),
            CallbackQueryHandler(toggle_notification, pattern='^toggle_')
        ],
        states={
            NOTIFICATION_SETTINGS: [CallbackQueryHandler(toggle_notification, pattern='^toggle_')],
            CATEGORY_NOTIFICATIONS: [CallbackQueryHandler(toggle_category_notification, pattern='^toggle_category_')]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )
    application.add_handler(notification_conv_handler)
    
    # هندلر پرداخت
    payment_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(show_payment_menu, pattern='^payment_menu$'),
            CallbackQueryHandler(handle_payment_method, pattern='^payment_')
        ],
        states={
            PAYMENT_METHOD: [CallbackQueryHandler(handle_payment_method, pattern='^payment_')],
            PAYMENT_CONFIRM: [CallbackQueryHandler(handle_payment_confirmation, pattern='^confirm_')]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )
    application.add_handler(payment_conv_handler)
    
    # هندلر ادمین
    admin_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("admin", show_admin_panel),
            CallbackQueryHandler(show_stats, pattern='^admin_stats$'),
            CallbackQueryHandler(show_user_management, pattern='^admin_users$'),
            CallbackQueryHandler(show_ad_management, pattern='^admin_ads$'),
            CallbackQueryHandler(start_broadcast, pattern='^admin_broadcast$')
        ],
        states={
            BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_broadcast)],
            USER_MANAGEMENT: [CallbackQueryHandler(manage_user, pattern='^user_')],
            AD_MANAGEMENT: [CallbackQueryHandler(manage_ad, pattern='^ad_')]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )
    application.add_handler(admin_conv_handler)
    
    # هندلر اشتراک
    subscription_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(show_subscription_menu, pattern='^subscription_menu$'),
            CallbackQueryHandler(handle_subscription_selection, pattern='^subscription_')
        ],
        states={
            SUBSCRIPTION_TYPE: [CallbackQueryHandler(handle_subscription_selection, pattern='^subscription_')],
            SUBSCRIPTION_CONFIRM: [CallbackQueryHandler(confirm_subscription, pattern='^confirm_')]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )
    application.add_handler(subscription_conv_handler)
    
    # شروع ربات
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 
