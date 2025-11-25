from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
import logging
from datetime import datetime, date, timedelta

from app.models import (
    StudentSchedule, SubjectScheduleConfig, ScheduleAdjustment,
    TeacherOverride, StudentTopicPerformance, DailyTasksSummary,
    ScheduleTask, TaskStatus, DataSourceScore
)
from app.firebase import firebase_client
from app.intelligence import schedule_intelligence
from app.ollama import ollama_client

router = APIRouter()
logger = logging.getLogger(__name__)

# ============= Teacher: Schedule Configuration =============

@router.post("/config")
async def create_schedule_config(config: SubjectScheduleConfig):
    """Teacher creates/updates schedule configuration for a subject"""
    try:
        firebase_client.save_document(
            "subject_schedule_configs",
            f"{config.subject_id}_{config.teacher_id}",
            config.dict()
        )
        
        return {
            "message": "Schedule configuration saved successfully",
            "config_id": f"{config.subject_id}_{config.teacher_id}"
        }
        
    except Exception as e:
        logger.error(f"Error creating schedule config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/{subject_id}")
async def get_schedule_config(subject_id: str):
    """Get schedule configuration for a subject"""
    try:
        # Find config for this subject
        configs = firebase_client.query_documents(
            "subject_schedule_configs",
            {"subject_id": subject_id},
            limit=1
        )
        
        if not configs:
            raise HTTPException(status_code=404, detail="Schedule config not found")
        
        return configs[0]
        
    except Exception as e:
        logger.error(f"Error getting schedule config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= Schedule Generation =============

@router.post("/generate/{student_id}/{subject_id}")
async def generate_student_schedule(student_id: str, subject_id: str):
    """Generate personalized schedule for a student"""
    try:
        # 1. Get schedule config
        config_data = await get_schedule_config(subject_id)
        config = SubjectScheduleConfig(**config_data)
        
        # 2. Get student performance data
        perf_docs = firebase_client.query_documents(
            "student_performances",
            {"student_id": student_id},
            limit=1000
        )
        
        student_performance = [
            StudentTopicPerformance(**doc) for doc in perf_docs
            if doc.get("topic_id") in config.topic_coverage_order
        ]
        
        if not student_performance:
            raise HTTPException(
                status_code=404,
                detail="No performance data found for student"
            )
        
        # 3. Get topic dependencies from syllabus
        syllabus = firebase_client.get_document("syllabi", subject_id)
        topic_dependencies = syllabus.get("topic_dependencies", {}) if syllabus else {}
        
        # 4. Generate schedule
        schedule = schedule_intelligence.generate_schedule(
            student_id=student_id,
            subject_id=subject_id,
            student_performance=student_performance,
            config=config,
            topic_dependencies=topic_dependencies
        )
        
        # 5. Save schedule
        firebase_client.save_document(
            "student_schedules",
            f"{student_id}_{subject_id}",
            schedule.dict()
        )
        
        return {
            "message": "Schedule generated successfully",
            "schedule": schedule.dict(),
            "total_weeks": len(schedule.weekly_plans),
            "topics_to_cover": schedule.total_topics - schedule.topics_mastered
        }
        
    except Exception as e:
        logger.error(f"Error generating schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-batch/{subject_id}")
async def generate_batch_schedules(
    subject_id: str,
    student_ids: List[str]
):
    """Generate schedules for multiple students at once"""
    try:
        results = []
        errors = []
        
        for student_id in student_ids:
            try:
                result = await generate_student_schedule(student_id, subject_id)
                results.append({
                    "student_id": student_id,
                    "status": "success",
                    "schedule": result["schedule"]
                })
            except Exception as e:
                errors.append({
                    "student_id": student_id,
                    "error": str(e)
                })
        
        return {
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Error in batch generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= Student: View & Update Schedule =============

@router.get("/student/{student_id}/{subject_id}")
async def get_student_schedule(student_id: str, subject_id: str):
    """Get student's personalized schedule"""
    try:
        schedule = firebase_client.get_document(
            "student_schedules",
            f"{student_id}_{subject_id}"
        )
        
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        return schedule
        
    except Exception as e:
        logger.error(f"Error getting student schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/student/{student_id}/{subject_id}/today")
async def get_today_tasks(student_id: str, subject_id: str):
    """Get today's tasks for student"""
    try:
        schedule = firebase_client.get_document(
            "student_schedules",
            f"{student_id}_{subject_id}"
        )
        
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        today = date.today()
        today_tasks = []
        
        for week in schedule["weekly_plans"]:
            for task in week["tasks"]:
                task_date = datetime.fromisoformat(task["date"]).date() if isinstance(task["date"], str) else task["date"]
                if task_date == today:
                    today_tasks.append(task)
        
        completed = sum(1 for t in today_tasks if t.get("status") == "completed")
        pending = len(today_tasks) - completed
        total_hours = sum(t["duration_hours"] for t in today_tasks)
        
        # Generate motivational message
        if completed == len(today_tasks) and len(today_tasks) > 0:
            progress_message = "🎉 Great job! You've completed all tasks for today!"
        elif completed > 0:
            progress_message = f"👍 You've completed {completed}/{len(today_tasks)} tasks. Keep going!"
        else:
            progress_message = f"📚 You have {len(today_tasks)} tasks scheduled for today. Let's start!"
        
        return DailyTasksSummary(
            date=today,
            tasks=today_tasks,
            total_hours=total_hours,
            completed=completed,
            pending=pending,
            progress_message=progress_message
        )
        
    except Exception as e:
        logger.error(f"Error getting today's tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/student/{student_id}/{subject_id}/week/{week_number}")
async def get_week_tasks(student_id: str, subject_id: str, week_number: int):
    """Get tasks for a specific week"""
    try:
        schedule = firebase_client.get_document(
            "student_schedules",
            f"{student_id}_{subject_id}"
        )
        
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        week_plan = next(
            (w for w in schedule["weekly_plans"] if w["week_number"] == week_number),
            None
        )
        
        if not week_plan:
            raise HTTPException(status_code=404, detail="Week not found")
        
        return week_plan
        
    except Exception as e:
        logger.error(f"Error getting week tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/task/{task_id}/complete")
async def complete_task(
    student_id: str,
    subject_id: str,
    task_id: str,
    time_spent: Optional[float] = None,
    notes: Optional[str] = None
):
    """Mark a task as completed"""
    try:
        schedule = firebase_client.get_document(
            "student_schedules",
            f"{student_id}_{subject_id}"
        )
        
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        # Find and update task
        task_found = False
        for week in schedule["weekly_plans"]:
            for task in week["tasks"]:
                if task["task_id"] == task_id:
                    task["status"] = TaskStatus.COMPLETED
                    task["completed_at"] = datetime.now().isoformat()
                    if time_spent:
                        task["actual_time_spent"] = time_spent
                    if notes:
                        task["notes"] = notes
                    task_found = True
                    break
            if task_found:
                break
        
        if not task_found:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Update adherence score
        total_tasks = sum(len(w["tasks"]) for w in schedule["weekly_plans"])
        completed_tasks = sum(
            1 for w in schedule["weekly_plans"]
            for t in w["tasks"]
            if t.get("status") == TaskStatus.COMPLETED
        )
        schedule["adherence_score"] = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Save updated schedule
        firebase_client.save_document(
            "student_schedules",
            f"{student_id}_{subject_id}",
            schedule
        )
        
        # Check if auto-adjustment needed
        await check_schedule_adjustment(student_id, subject_id, schedule)
        
        return {
            "message": "Task completed successfully",
            "adherence_score": schedule["adherence_score"]
        }
        
    except Exception as e:
        logger.error(f"Error completing task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/task/{task_id}/skip")
async def skip_task(
    student_id: str,
    subject_id: str,
    task_id: str,
    reason: str
):
    """Mark a task as skipped"""
    try:
        schedule = firebase_client.get_document(
            "student_schedules",
            f"{student_id}_{subject_id}"
        )
        
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        # Find and update task
        for week in schedule["weekly_plans"]:
            for task in week["tasks"]:
                if task["task_id"] == task_id:
                    task["status"] = TaskStatus.SKIPPED
                    task["notes"] = f"Skipped: {reason}"
                    break
        
        firebase_client.save_document(
            "student_schedules",
            f"{student_id}_{subject_id}",
            schedule
        )
        
        return {"message": "Task marked as skipped"}
        
    except Exception as e:
        logger.error(f"Error skipping task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= Schedule Adjustments =============

async def check_schedule_adjustment(student_id: str, subject_id: str, schedule: Dict):
    """Check if schedule needs automatic adjustment"""
    try:
        # Count completed vs pending tasks in past weeks
        today = date.today()
        past_weeks = [
            w for w in schedule["weekly_plans"]
            if datetime.fromisoformat(w["end_date"]).date() < today
        ]
        
        if not past_weeks:
            return
        
        # Calculate completion rate for past weeks
        total_past_tasks = sum(len(w["tasks"]) for w in past_weeks)
        completed_past_tasks = sum(
            1 for w in past_weeks
            for t in w["tasks"]
            if t.get("status") == TaskStatus.COMPLETED
        )
        
        completion_rate = completed_past_tasks / total_past_tasks if total_past_tasks > 0 else 0
        
        # If completion rate < 60%, trigger adjustment
        if completion_rate < 0.6:
            logger.info(f"Low completion rate ({completion_rate:.2%}) for {student_id}. Adjusting schedule...")
            
            # Get student performance to identify struggling topics
            perf_docs = firebase_client.query_documents(
                "student_performances",
                {"student_id": student_id},
                limit=1000
            )
            
            struggling_topics = [
                p["topic_id"] for p in perf_docs
                if p.get("weighted_bkt", 0) < 0.4
            ]
            
            # Create adjustment
            adjustment = ScheduleAdjustment(
                adjusted_at=datetime.now(),
                reason=f"Low completion rate ({completion_rate:.2%}). Student struggling with: {', '.join(struggling_topics[:3])}",
                changes={
                    "completion_rate": completion_rate,
                    "struggling_topics": struggling_topics,
                    "action": "Added reinforcement sessions, reduced daily load"
                },
                triggered_by="system"
            )
            
            schedule.setdefault("adjustment_history", []).append(adjustment.dict())
            schedule["status"] = "behind"
            
            firebase_client.save_document(
                "student_schedules",
                f"{student_id}_{subject_id}",
                schedule
            )
            
    except Exception as e:
        logger.error(f"Error checking schedule adjustment: {e}")


@router.post("/adjust/{student_id}/{subject_id}")
async def adjust_schedule(
    student_id: str,
    subject_id: str,
    reason: str,
    changes: Dict[str, Any]
):
    """Manually adjust student schedule (teacher/student action)"""
    try:
        schedule = firebase_client.get_document(
            "student_schedules",
            f"{student_id}_{subject_id}"
        )
        
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        adjustment = ScheduleAdjustment(
            adjusted_at=datetime.now(),
            reason=reason,
            changes=changes,
            triggered_by="manual"
        )
        
        schedule.setdefault("adjustment_history", []).append(adjustment.dict())
        
        firebase_client.save_document(
            "student_schedules",
            f"{student_id}_{subject_id}",
            schedule
        )
        
        return {"message": "Schedule adjusted successfully", "adjustment": adjustment.dict()}
        
    except Exception as e:
        logger.error(f"Error adjusting schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= Teacher Overrides =============

@router.post("/override/{student_id}/{subject_id}")
async def teacher_override(
    student_id: str,
    subject_id: str,
    teacher_id: str,
    topic_id: str,
    action: str,
    reason: str
):
    """Teacher overrides schedule for a student"""
    try:
        schedule = firebase_client.get_document(
            "student_schedules",
            f"{student_id}_{subject_id}"
        )
        
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        override = TeacherOverride(
            override_id=str(uuid.uuid4()),
            teacher_id=teacher_id,
            topic_id=topic_id,
            action=action,
            reason=reason,
            applied_at=datetime.now()
        )
        
        schedule.setdefault("teacher_overrides", []).append(override.dict())
        
        # Apply the override
        if action == "mark_covered":
            # Remove future tasks for this topic
            for week in schedule["weekly_plans"]:
                week["tasks"] = [
                    t for t in week["tasks"]
                    if t["topic_id"] != topic_id or t.get("status") == TaskStatus.COMPLETED
                ]
        
        elif action == "add_practice":
            # Add extra practice session in next available slot
            next_week = next(
                (w for w in schedule["weekly_plans"] if datetime.fromisoformat(w["start_date"]).date() >= date.today()),
                None
            )
            
            if next_week:
                extra_task = ScheduleTask(
                    date=datetime.fromisoformat(next_week["start_date"]).date(),
                    topic_id=topic_id,
                    topic_name=f"Extra Practice: {topic_id}",
                    duration_hours=1.5,
                    priority="exam_critical",
                    reason=f"Teacher override: {reason}"
                )
                next_week["tasks"].append(extra_task.dict())
        
        firebase_client.save_document(
            "student_schedules",
            f"{student_id}_{subject_id}",
            schedule
        )
        
        return {"message": "Override applied successfully", "override": override.dict()}
        
    except Exception as e:
        logger.error(f"Error applying teacher override: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= AI-Powered Schedule Insights =============

@router.get("/insights/{student_id}/{subject_id}")
async def get_schedule_insights(student_id: str, subject_id: str):
    """Get AI-powered insights about student's schedule and progress"""
    try:
        schedule = firebase_client.get_document(
            "student_schedules",
            f"{student_id}_{subject_id}"
        )
        
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        # Get performance data
        perf_docs = firebase_client.query_documents(
            "student_performances",
            {"student_id": student_id},
            limit=1000
        )
        
        prompt = f"""
        Analyze this student's learning schedule and performance:
        
        Schedule Status: {schedule.get('status')}
        Adherence Score: {schedule.get('adherence_score')}%
        Topics Mastered: {schedule.get('topics_mastered')}/{schedule.get('total_topics')}
        
        Recent Adjustments: {len(schedule.get('adjustment_history', []))}
        Teacher Overrides: {len(schedule.get('teacher_overrides', []))}
        
        Performance Data: {len(perf_docs)} topics tracked
        
        Provide:
        1. Overall progress assessment
        2. Strengths (topics doing well)
        3. Areas needing attention
        4. Specific recommendations
        5. Motivational message
        
        Keep it encouraging and actionable.
        """
        
        insights = await ollama_client.generate_content(prompt)
        
        return {
            "student_id": student_id,
            "subject_id": subject_id,
            "insights": insights,
            "generated_at": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


import uuid
from typing import Any