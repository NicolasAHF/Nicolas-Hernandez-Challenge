from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..repositories.plan_repository import PlanRepository
from ..repositories.user_repository import UserRepository
from ..schemas.study_plan import (
    PlanMetrics,
    StudyPlanCreate,
    StudyPlanRead,
    StudyPlanUpdate,
)


class PlanService:
    def __init__(self, db: Session) -> None:
        self.repo = PlanRepository(db)
        self.user_repo = UserRepository(db)

    def create_plan(self, data: StudyPlanCreate) -> StudyPlanRead:
        if not self.user_repo.get_by_id(data.user_id):
            raise HTTPException(status_code=404, detail="User not found")
        plan = self.repo.create(data)
        return StudyPlanRead.model_validate(plan)

    def get_plan(self, plan_id: int) -> StudyPlanRead:
        plan = self.repo.get_by_id(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        return StudyPlanRead.model_validate(plan)

    def get_plans_by_user(self, user_id: int) -> list[StudyPlanRead]:
        if not self.user_repo.get_by_id(user_id):
            raise HTTPException(status_code=404, detail="User not found")
        plans = self.repo.get_by_user_id(user_id)
        return [StudyPlanRead.model_validate(p) for p in plans]

    def update_plan(self, plan_id: int, data: StudyPlanUpdate) -> StudyPlanRead:
        plan = self.repo.update(plan_id, data)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        return StudyPlanRead.model_validate(plan)

    def get_metrics(self, plan_id: int) -> PlanMetrics:
        plan = self.repo.get_by_id(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        tasks = plan.tasks
        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks if t.completed)
        total_estimated_hours = sum(t.estimated_hours for t in tasks)
        completed_hours = sum(t.estimated_hours for t in tasks if t.completed)
        completion_percentage = (
            round(completed_tasks / total_tasks * 100) if total_tasks else 0
        )

        return PlanMetrics(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            completion_percentage=completion_percentage,
            total_estimated_hours=total_estimated_hours,
            completed_hours=completed_hours,
        )
