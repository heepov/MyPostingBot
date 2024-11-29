from .common import router
from .start import router as start_router
from .add_channel import router as add_channel_router
from .chat_member import router as chat_member_router
from .forwarded_messages import router as forwarded_messages_router

# Импортируем все обработчики, чтобы они зарегистрировались
from . import show_schedule
from . import channel_settings
from . import add_post


# Теперь у нас только один роутер
routers = [
    router,
    add_channel_router,
    start_router,
    chat_member_router,
    forwarded_messages_router,
]
