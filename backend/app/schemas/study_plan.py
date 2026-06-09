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


class ScheduledTask(BaseModel):
    task_id: int
    title: str
    hours: float


class ScheduledWeek(BaseModel):
    week: int
    tasks: list[ScheduledTask]
    total_hours: float


class PlanRebalance(BaseModel):
    overloaded: bool
    hours_per_week: float
    total_estimated_hours: float
    weeks_needed: int
    schedule: list[ScheduledWeek]
