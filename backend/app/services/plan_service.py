from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..repositories.plan_repository import PlanRepository
from ..repositories.user_repository import UserRepository
from ..schemas.study_plan import (
    PlanMetrics,
    PlanRebalance,
    ScheduledTask,
    ScheduledWeek,
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

    def get_rebalance(self, plan_id: int) -> PlanRebalance:
        plan = self.repo.get_by_id(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        tasks = sorted(plan.tasks, key=lambda t: t.id)
        total = sum(t.estimated_hours for t in tasks)

        if total <= plan.hours_per_week:
            return PlanRebalance(
                overloaded=False,
                hours_per_week=plan.hours_per_week,
                total_estimated_hours=total,
                weeks_needed=1 if tasks else 0,
                schedule=[],
            )

        schedule = self._schedule_into_weeks(tasks, plan.hours_per_week)
        return PlanRebalance(
            overloaded=True,
            hours_per_week=plan.hours_per_week,
            total_estimated_hours=total,
            weeks_needed=len(schedule),
            schedule=schedule,
        )

    def _schedule_into_weeks(
        self, tasks: list, hours_per_week: float
    ) -> list[ScheduledWeek]:
        units = self._to_weekly_units(tasks, hours_per_week)
        weeks: list[ScheduledWeek] = []
        current: list[ScheduledTask] = []
        current_hours = 0.0
        for unit in units:
            if current and current_hours + unit.hours > hours_per_week:
                weeks.append(self._build_week(len(weeks) + 1, current, current_hours))
                current = []
                current_hours = 0.0
            current.append(unit)
            current_hours += unit.hours
        if current:
            weeks.append(self._build_week(len(weeks) + 1, current, current_hours))
        return weeks

    @staticmethod
    def _to_weekly_units(tasks: list, hours_per_week: float) -> list[ScheduledTask]:
        units: list[ScheduledTask] = []
        for task in tasks:
            if task.estimated_hours <= hours_per_week:
                units.append(
                    ScheduledTask(
                        task_id=task.id, title=task.title, hours=task.estimated_hours
                    )
                )
                continue
            remaining = task.estimated_hours
            part = 1
            while remaining > 0:
                chunk = min(hours_per_week, remaining)
                units.append(
                    ScheduledTask(
                        task_id=task.id,
                        title=f"{task.title} -{part}",
                        hours=round(chunk, 2),
                    )
                )
                remaining = round(remaining - chunk, 2)
                part += 1
        return units

    @staticmethod
    def _build_week(
        week: int, units: list[ScheduledTask], total_hours: float
    ) -> ScheduledWeek:
        return ScheduledWeek(
            week=week, tasks=list(units), total_hours=round(total_hours, 2)
        )
