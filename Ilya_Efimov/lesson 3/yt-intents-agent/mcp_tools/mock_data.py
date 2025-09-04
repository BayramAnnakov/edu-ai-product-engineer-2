import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Mock YouTube comments data for demonstration (Russian channel)
MOCK_COMMENTS = [
    {
        "id": "1",
        "text": "Как начать заниматься йогой дома? Подскажите с чего лучше начать?",
        "author": "YogaLover123",
        "like_count": 15,
        "published_at": "2024-08-20T12:30:00Z",
        "video_id": "abc123",
        "video_title": "Йога для начинающих"
    },
    {
        "id": "2", 
        "text": "Что делать, если болит спина после упражнений?",
        "author": "HealthyLife",
        "like_count": 8,
        "published_at": "2024-08-21T14:15:00Z",
        "video_id": "abc123",
        "video_title": "Йога для начинающих"
    },
    {
        "id": "3",
        "text": "Спасибо за отличный урок! Советую сделать больше видео про медитацию.",
        "author": "MeditationFan",
        "like_count": 12,
        "published_at": "2024-08-22T09:45:00Z",
        "video_id": "def456",
        "video_title": "Утренняя йога"
    },
    {
        "id": "4",
        "text": "Потрясающе! Рекомендую добавить упражнения для шеи и плеч.",
        "author": "OfficeWorker",
        "like_count": 7,
        "published_at": "2024-08-23T16:20:00Z",
        "video_id": "def456", 
        "video_title": "Утренняя йога"
    },
    {
        "id": "5",
        "text": "Сколько времени нужно заниматься, чтобы увидеть результат?",
        "author": "Newbie2024",
        "like_count": 20,
        "published_at": "2024-08-24T11:30:00Z",
        "video_id": "ghi789",
        "video_title": "Йога для похудения"
    },
    {
        "id": "6",
        "text": "Класс! Можно бы ещё показать вариации для новичков.",
        "author": "BeginnerYogi",
        "like_count": 5,
        "published_at": "2024-08-25T13:45:00Z",
        "video_id": "ghi789",
        "video_title": "Йога для похудения"
    },
    {
        "id": "7",
        "text": "А как правильно дышать во время асан?",
        "author": "BreathWork",
        "like_count": 18,
        "published_at": "2024-08-26T08:15:00Z",
        "video_id": "jkl012",
        "video_title": "Дыхательные практики"
    },
    {
        "id": "8",
        "text": "Супер контент! Предлагаю сделать серию про йога-терапию.",
        "author": "YogaTherapist",
        "like_count": 11,
        "published_at": "2024-08-26T15:30:00Z",
        "video_id": "jkl012",
        "video_title": "Дыхательные практики"
    },
    {
        "id": "9",
        "text": "Где лучше заниматься - дома или в зале?",
        "author": "PlaceSeeker",
        "like_count": 9,
        "published_at": "2024-08-27T10:00:00Z",
        "video_id": "mno345",
        "video_title": "Оборудование для йоги"
    },
    {
        "id": "10",
        "text": "Великолепный урок! Очень полезно и понятно объясняете.",
        "author": "GratefulStudent",
        "like_count": 14,
        "published_at": "2024-08-27T12:45:00Z",
        "video_id": "mno345",
        "video_title": "Оборудование для йоги"
    }
]

def get_mock_comments():
    """Returns mock comments for demonstration purposes"""
    logger.info("Using mock data for demonstration")
    return MOCK_COMMENTS