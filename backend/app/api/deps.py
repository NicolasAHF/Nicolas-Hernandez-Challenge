import redis
from fastapi import Depends
from sqlalchemy.orm import Session

from ..core.cache import Cache, RedisCache
from ..core.config import settings
from ..core.database import get_db
from ..services.plan_service import PlanService
from ..services.task_service import TaskService
from ..services.user_service import UserService

_cache: Cache = RedisCache(
    redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
)


def get_cache() -> Cache:
    return _cache


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


def get_plan_service(
    db: Session = Depends(get_db), cache: Cache = Depends(get_cache)
) -> PlanService:
    return PlanService(db, cache)


def get_task_service(
    db: Session = Depends(get_db), cache: Cache = Depends(get_cache)
) -> TaskService:
    return TaskService(db, cache)
