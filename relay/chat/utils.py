import redis
from django.conf import settings
from channels.db import database_sync_to_async
redis_client = redis.Redis.from_url(settings.REDIS_URL)

@database_sync_to_async
def check_message_rate_limit(user_id):
    key = f'ws:messages:user:{user_id}'
    count = redis_client.incr(key)
    
    if count == 1: 
        redis_client.expire(key, 60) # delete after 60 second

    return count <= 30