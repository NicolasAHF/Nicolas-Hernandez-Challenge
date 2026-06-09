from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..core.cache import Cache, metrics_cache_key
from ..repositories.plan_repository import PlanRepository
from ..repositories.task_repository import TaskRepository
from ..schemas.study_task import StudyTaskCreate, StudyTaskRead, StudyTaskUpdate


class TaskService:
    def __init__(self, db: Session, cache: Cache) -> None:
        self.repo = TaskRepository(db)
        self.plan_repo = PlanRepository(db)
        self.cache = cache

    def create_task(self, plan_id: int, data: StudyTaskCreate) -> StudyTaskRead:
        if not self.plan_repo.get_by_id(plan_id):
            raise HTTPException(status_code=404, detail="Plan not found")
        task = self.repo.create(plan_id, data)
        self.cache.delete(metrics_cache_key(plan_id))
        return StudyTaskRead.model_validate(task)

    def get_tasks_by_plan(self, plan_id: int) -> list[StudyTaskRead]:
        if not self.plan_repo.get_by_id(plan_id):
            raise HTTPException(status_code=404, detail="Plan not found")
        tasks = self.repo.get_by_plan_id(plan_id)
        return [StudyTaskRead.model_validate(t) for t in tasks]

    def update_task(
        self, plan_id: int, task_id: int, data: StudyTaskUpdate
    ) -> StudyTaskRead:
        if not self.plan_repo.get_by_id(plan_id):
            raise HTTPException(status_code=404, detail="Plan not found")
        task = self.repo.update(task_id, data)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        self.cache.delete(metrics_cache_key(plan_id))
        return StudyTaskRead.model_validate(task)
