from pymongo import MongoClient
from datetime import datetime
from bot import config

class Database:
    def __init__(self):
        self.client = MongoClient(config.MONGODB_URI)
        self.db = self.client[config.DB_NAME]
        
        # ایجاد ایندکس‌ها
        self._create_indexes()
    
    def _create_indexes(self):
        # ایندکس برای کاربران
        self.db.users.create_index('user_id', unique=True)
        self.db.users.create_index('phone_number', unique=True)
        
        # ایندکس برای آگهی‌ها
        self.db.ads.create_index('ad_id', unique=True)
        self.db.ads.create_index('user_id')
        self.db.ads.create_index('category')
        
        # ایندکس برای پیام‌ها
        self.db.messages.create_index('message_id', unique=True)
        self.db.messages.create_index('user_id')
        
        # ایندکس برای اشتراک‌ها
        self.db.users.create_index('subscription.expires_at')
    
    # توابع مربوط به کاربران
    def add_user(self, user_data):
        user_data['created_at'] = datetime.now()
        user_data['is_admin'] = False
        user_data['subscription'] = {
            'type': 'free',
            'expires_at': None
        }
        return self.db.users.insert_one(user_data)
    
    def get_user(self, user_id):
        return self.db.users.find_one({'user_id': user_id})
    
    def update_user(self, user_id, update_data):
        return self.db.users.update_one(
            {'user_id': user_id},
            {'$set': update_data}
        )
    
    def delete_user(self, user_id):
        return self.db.users.delete_one({'user_id': user_id})
    
    # توابع مربوط به آگهی‌ها
    def add_ad(self, ad_data):
        ad_data['created_at'] = datetime.now()
        ad_data['status'] = 'pending'
        return self.db.ads.insert_one(ad_data)
    
    def get_ad(self, ad_id):
        return self.db.ads.find_one({'ad_id': ad_id})
    
    def update_ad(self, ad_id, update_data):
        return self.db.ads.update_one(
            {'ad_id': ad_id},
            {'$set': update_data}
        )
    
    def delete_ad(self, ad_id):
        return self.db.ads.delete_one({'ad_id': ad_id})
    
    def get_user_ads(self, user_id):
        return list(self.db.ads.find({'user_id': user_id}))
    
    def get_category_ads(self, category):
        return list(self.db.ads.find({'category': category}))
    
    # توابع مربوط به پیام‌ها
    def add_message(self, message_data):
        message_data['created_at'] = datetime.now()
        return self.db.messages.insert_one(message_data)
    
    def get_user_messages(self, user_id):
        return list(self.db.messages.find({'user_id': user_id}))
    
    def get_chat_messages(self, user_id1, user_id2):
        return list(self.db.messages.find({
            '$or': [
                {'sender_id': user_id1, 'receiver_id': user_id2},
                {'sender_id': user_id2, 'receiver_id': user_id1}
            ]
        }))
    
    # توابع مربوط به اشتراک‌ها
    def update_subscription(self, user_id, subscription_data):
        return self.db.users.update_one(
            {'user_id': user_id},
            {'$set': {'subscription': subscription_data}}
        )
    
    def get_expired_subscriptions(self):
        return list(self.db.users.find({
            'subscription.expires_at': {'$lt': datetime.now()}
        }))
    
    # توابع مربوط به ادمین
    def set_admin(self, user_id, is_admin=True):
        return self.db.users.update_one(
            {'user_id': user_id},
            {'$set': {'is_admin': is_admin}}
        )
    
    def get_admins(self):
        return list(self.db.users.find({'is_admin': True}))
    
    # توابع آماری
    def get_stats(self):
        return {
            'total_users': self.db.users.count_documents({}),
            'total_ads': self.db.ads.count_documents({}),
            'total_messages': self.db.messages.count_documents({}),
            'active_subscriptions': self.db.users.count_documents({
                'subscription.expires_at': {'$gt': datetime.now()}
            })
        }

    def search_ads(self, filters, sort):
        """جستجوی آگهی‌ها با فیلتر و مرتب‌سازی"""
        try:
            return list(self.db.ads.find(filters).sort(list(sort.items())[0]))
        except Exception as e:
            print(f"Error searching ads: {e}")
            return []

    def get_user_rating(self, ad_id, user_id):
        """دریافت امتیاز کاربر برای یک آگهی"""
        try:
            return self.ratings.find_one({'ad_id': ad_id, 'user_id': user_id})
        except Exception as e:
            print(f"Error getting user rating: {e}")
            return None

    def add_rating(self, ad_id, user_id, rating):
        """افزودن امتیاز جدید"""
        try:
            self.ratings.insert_one({
                'ad_id': ad_id,
                'user_id': user_id,
                'rating': rating,
                'created_at': datetime.now()
            })
            return True
        except Exception as e:
            print(f"Error adding rating: {e}")
            return False

    def update_rating(self, ad_id, user_id, rating):
        """بروزرسانی امتیاز"""
        try:
            self.ratings.update_one(
                {'ad_id': ad_id, 'user_id': user_id},
                {'$set': {'rating': rating, 'updated_at': datetime.now()}}
            )
            return True
        except Exception as e:
            print(f"Error updating rating: {e}")
            return False

    def get_user_review(self, ad_id, user_id):
        """دریافت نظر کاربر برای یک آگهی"""
        try:
            return self.reviews.find_one({'ad_id': ad_id, 'user_id': user_id})
        except Exception as e:
            print(f"Error getting user review: {e}")
            return None

    def add_review(self, ad_id, user_id, review_text):
        """افزودن نظر جدید"""
        try:
            self.reviews.insert_one({
                'ad_id': ad_id,
                'user_id': user_id,
                'review': review_text,
                'created_at': datetime.now()
            })
            return True
        except Exception as e:
            print(f"Error adding review: {e}")
            return False

    def update_review(self, ad_id, user_id, review_text):
        """بروزرسانی نظر"""
        try:
            self.reviews.update_one(
                {'ad_id': ad_id, 'user_id': user_id},
                {'$set': {'review': review_text, 'updated_at': datetime.now()}}
            )
            return True
        except Exception as e:
            print(f"Error updating review: {e}")
            return False

    def add_report(self, ad_id, user_id, report_type):
        """افزودن گزارش تخلف"""
        try:
            self.reports.insert_one({
                'ad_id': ad_id,
                'user_id': user_id,
                'report_type': report_type,
                'status': 'pending',
                'created_at': datetime.now()
            })
            return True
        except Exception as e:
            print(f"Error adding report: {e}")
            return False

    def get_notification_settings(self, user_id):
        """دریافت تنظیمات اعلان کاربر"""
        try:
            settings = self.notifications.find_one({'user_id': user_id})
            return settings if settings else {
                'user_id': user_id,
                'new_ads': True,
                'new_messages': True,
                'subscription_expiry': True,
                'category_notifications': {}
            }
        except Exception as e:
            print(f"Error getting notification settings: {e}")
            return {}

    def update_notification_settings(self, user_id, setting_type, value):
        """بروزرسانی تنظیمات اعلان"""
        try:
            self.notifications.update_one(
                {'user_id': user_id},
                {'$set': {setting_type: value}},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Error updating notification settings: {e}")
            return False

    def get_users_with_notification(self, notification_type, value=True):
        """دریافت کاربران با اعلان فعال"""
        try:
            return list(self.notifications.find({notification_type: value}))
        except Exception as e:
            print(f"Error getting users with notification: {e}")
            return []

    def add_payment(self, payment_data):
        """افزودن پرداخت جدید"""
        try:
            self.payments.insert_one(payment_data)
            return True
        except Exception as e:
            print(f"Error adding payment: {e}")
            return False

    def get_latest_payment(self, user_id):
        """دریافت آخرین پرداخت کاربر"""
        try:
            return self.payments.find_one(
                {'user_id': user_id},
                sort=[('created_at', -1)]
            )
        except Exception as e:
            print(f"Error getting latest payment: {e}")
            return None

    def update_payment_status(self, payment_id, status):
        """بروزرسانی وضعیت پرداخت"""
        try:
            self.payments.update_one(
                {'payment_id': payment_id},
                {'$set': {'status': status, 'updated_at': datetime.now()}}
            )
            return True
        except Exception as e:
            print(f"Error updating payment status: {e}")
            return False

    def get_user_payments(self, user_id):
        """دریافت تاریخچه پرداخت‌های کاربر"""
        try:
            return list(self.payments.find(
                {'user_id': user_id},
                sort=[('created_at', -1)]
            ))
        except Exception as e:
            print(f"Error getting user payments: {e}")
            return []

    def get_all_users(self):
        """دریافت لیست تمام کاربران"""
        return list(self.db.users.find())

    def get_notification_settings(self, user_id):
        """دریافت تنظیمات اعلان‌های کاربر"""
        user = self.get_user(user_id)
        return user.get('notification_settings', {
            'new_ads': True,
            'new_messages': True,
            'subscription_expiry': True
        })
    
    def update_notification_settings(self, user_id, settings):
        """بروزرسانی تنظیمات اعلان‌های کاربر"""
        return self.db.users.update_one(
            {'user_id': user_id},
            {'$set': {'notification_settings': settings}}
        ) 