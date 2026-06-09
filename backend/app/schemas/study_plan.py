from datetime import date

from pydantic import BaseModel


class StudyPlanCreate(BaseModel):
    user_id: int
    goal: str
    hours_per_week: float
    description: str | None = None
    target_date: date | None = None


class StudyPlanRead(BaseModel):
    id: int
    user_id: int
    goal: str
    hours_per_week: float
    description: str | None = None
    target_date: date | None = None

    model_config = {"from_attributes": True}


class StudyPlanUpdate(BaseModel):
    description: str | None = None
    target_date: date | None = None


class PlanMetrics(BaseModel):
    total_tasks: int
    completed_tasks: int
    completion_percentage: int
    total_estimated_hours: float
    completed_hours: float
