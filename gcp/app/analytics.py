from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
import logging
from datetime import datetime, date, timedelta

from .firebase import firebase_client
from .models import ClassHeatmap

router = APIRouter()
logger = logging.getLogger(__name__)

# ============= Student Analytics =============

@router.get("/student/{student_id}/overview")
async def get_student_overview(student_id: str):
    """Get complete overview of student's performance across all subjects"""
    try:
        # Get all schedules for student
        schedules = firebase_client.query_documents(
            "student_schedules",
            {"student_id": student_id},
            limit=100
        )
        
        # Get all performance records
        performances = firebase_client.query_documents(
            "student_performances",
            {"student_id": student_id},
            limit=1000
        )
        
        # Get all marks
        marks = firebase_client.query_documents(
            "student_marks",
            {"student_id": student_id},
            limit=1000
        )
        
        # Calculate overall stats
        total_topics = len(performances)
        mastered_topics = sum(1 for p in performances if p.get("weighted_bkt", 0) >= 0.8)
        weak_topics = sum(1 for p in performances if p.get("weighted_bkt", 0) < 0.6)
        
        # Group marks by source
        marks_by_source = {}
        for mark in marks:
            source = mark.get("source_type")
            if source not in marks_by_source:
                marks_by_source[source] = []
            marks_by_source[source].append(mark)
        
        # Calculate average adherence across subjects
        avg_adherence = (
            sum(s.get("adherence_score", 0) for s in schedules) / len(schedules)
            if schedules else 0
        )
        
        return {
            "student_id": student_id,
            "total_subjects": len(schedules),
            "total_topics": total_topics,
            "mastered_topics": mastered_topics,
            "weak_topics": weak_topics,
            "overall_progress": (mastered_topics / total_topics * 100) if total_topics > 0 else 0,
            "average_adherence": avg_adherence,
            "marks_summary": {
                source: {
                    "count": len(marks_list),
                    "average": sum(m.get("marks_obtained", 0) / m.get("max_marks", 1) * 100 
                                  for m in marks_list) / len(marks_list) if marks_list else 0
                }
                for source, marks_list in marks_by_source.items()
            },
            "schedules": schedules
        }
        
    except Exception as e:
        logger.error(f"Error getting student overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/student/{student_id}/knowledge-graph")
async def get_knowledge_graph(student_id: str, subject_id: Optional[str] = None):
    """Get student's knowledge graph with BKT scores and data sources"""
    try:
        filters = {"student_id": student_id}
        if subject_id:
            filters["subject_id"] = subject_id
        
        performances = firebase_client.query_documents(
            "student_performances",
            filters,
            limit=1000
        )
        
        # Categorize topics
        weak_topics = []
        strong_topics = []
        learning_topics = []
        
        for perf in performances:
            bkt = perf.get("weighted_bkt", 0)
            topic_id = perf.get("topic_id")
            
            if bkt < 0.6:
                weak_topics.append(topic_id)
            elif bkt > 0.8:
                strong_topics.append(topic_id)
            else:
                learning_topics.append(topic_id)
        
        return {
            "student_id": student_id,
            "subject_id": subject_id,
            "topics": performances,
            "summary": {
                "weak_topics": weak_topics,
                "learning_topics": learning_topics,
                "strong_topics": strong_topics
            },
            "overall_mastery": (
                len(strong_topics) / len(performances) * 100
                if performances else 0
            )
        }
        
    except Exception as e:
        logger.error(f"Error getting knowledge graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/student/{student_id}/progress-timeline")
async def get_progress_timeline(
    student_id: str,
    subject_id: str,
    days: int = 30
):
    """Get student's progress over time"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get all marks in time range
        all_marks = firebase_client.query_documents(
            "student_marks",
            {"student_id": student_id, "subject_id": subject_id},
            limit=1000
        )
        
        marks_in_range = [
            m for m in all_marks
            if start_date <= datetime.fromisoformat(m.get("synced_at")) <= end_date
        ]
        
        # Group by date and calculate daily progress
        daily_progress = {}
        for mark in marks_in_range:
            date_key = datetime.fromisoformat(mark.get("synced_at")).date().isoformat()
            if date_key not in daily_progress:
                daily_progress[date_key] = {
                    "date": date_key,
                    "activities": [],
                    "total_marks": 0,
                    "max_marks": 0
                }
            
            daily_progress[date_key]["activities"].append({
                "type": mark.get("source_type"),
                "marks": mark.get("marks_obtained"),
                "max_marks": mark.get("max_marks")
            })
            daily_progress[date_key]["total_marks"] += mark.get("marks_obtained", 0)
            daily_progress[date_key]["max_marks"] += mark.get("max_marks", 0)
        
        timeline = sorted(daily_progress.values(), key=lambda x: x["date"])
        
        return {
            "student_id": student_id,
            "subject_id": subject_id,
            "period": f"{days} days",
            "timeline": timeline,
            "total_activities": len(marks_in_range)
        }
        
    except Exception as e:
        logger.error(f"Error getting progress timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= Class/Subject Analytics =============

@router.get("/class/{subject_id}/overview")
async def get_class_overview(subject_id: str):
    """Get overview of entire class for a subject"""
    try:
        # Get all schedules for this subject
        schedules = firebase_client.query_documents(
            "student_schedules",
            {"subject_id": subject_id},
            limit=1000
        )
        
        if not schedules:
            raise HTTPException(status_code=404, detail="No schedules found for this subject")
        
        on_track = sum(1 for s in schedules if s.get("status") == "on_track")
        behind = sum(1 for s in schedules if s.get("status") == "behind")
        ahead = sum(1 for s in schedules if s.get("status") == "ahead")
        
        avg_adherence = (
            sum(s.get("adherence_score", 0) for s in schedules) / len(schedules)
            if schedules else 0
        )
        
        avg_mastery = (
            sum(s.get("topics_mastered", 0) / s.get("total_topics", 1) * 100 
                for s in schedules) / len(schedules)
            if schedules else 0
        )
        
        return {
            "subject_id": subject_id,
            "total_students": len(schedules),
            "on_track": on_track,
            "behind": behind,
            "ahead": ahead,
            "average_adherence": avg_adherence,
            "average_mastery": avg_mastery,
            "students": [
                {
                    "student_id": s.get("student_id"),
                    "status": s.get("status"),
                    "adherence": s.get("adherence_score"),
                    "progress": s.get("topics_mastered", 0) / s.get("total_topics", 1) * 100
                }
                for s in schedules
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting class overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/class/{subject_id}/heatmap")
async def get_class_heatmap(subject_id: str):
    """Get class heatmap: students × topics with mastery levels"""
    try:
        # Get all students for this subject
        schedules = firebase_client.query_documents(
            "student_schedules",
            {"subject_id": subject_id},
            limit=1000
        )
        
        student_ids = [s["student_id"] for s in schedules]
        
        # Get performance for all students
        all_performance = []
        topics_set = set()
        
        for student_id in student_ids:
            perf_docs = firebase_client.query_documents(
                "student_performances",
                {"student_id": student_id},
                limit=1000
            )
            
            student_perf = {
                "student_id": student_id,
                "topics": {}
            }
            
            for perf in perf_docs:
                topic_id = perf.get("topic_id")
                topics_set.add(topic_id)
                student_perf["topics"][topic_id] = {
                    "bkt": perf.get("weighted_bkt", 0),
                    "data_sources": perf.get("data_sources", {})
                }
            
            all_performance.append(student_perf)
        
        topics = sorted(list(topics_set))
        
        # Calculate statistics per topic
        stats = {}
        for topic in topics:
            scores = [
                student["topics"].get(topic, {}).get("bkt", 0)
                for student in all_performance
            ]
            stats[topic] = {
                "average": sum(scores) / len(scores) if scores else 0,
                "weak_students": sum(1 for s in scores if s < 0.6),
                "strong_students": sum(1 for s in scores if s > 0.8),
                "min": min(scores) if scores else 0,
                "max": max(scores) if scores else 0
            }
        
        return ClassHeatmap(
            subject_id=subject_id,
            students=all_performance,
            topics=topics,
            statistics=stats
        )
        
    except Exception as e:
        logger.error(f"Error getting class heatmap: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/class/{subject_id}/weak-topics")
async def identify_weak_topics(subject_id: str, threshold: float = 0.5):
    """Identify topics where majority of class is struggling"""
    try:
        heatmap = await get_class_heatmap(subject_id)
        
        weak_topics = []
        for topic, stats in heatmap.statistics.items():
            if stats["average"] < threshold:
                weak_topics.append({
                    "topic": topic,
                    "average_score": stats["average"],
                    "weak_students": stats["weak_students"],
                    "total_students": len(heatmap.students),
                    "percentage_weak": (stats["weak_students"] / len(heatmap.students) * 100) 
                                       if heatmap.students else 0,
                    "recommendation": "Consider additional lecture or practice session"
                })
        
        weak_topics.sort(key=lambda x: x["average_score"])
        
        return {
            "subject_id": subject_id,
            "weak_topics": weak_topics,
            "total_weak_topics": len(weak_topics)
        }
        
    except Exception as e:
        logger.error(f"Error identifying weak topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/class/{subject_id}/performance-distribution")
async def get_performance_distribution(subject_id: str):
    """Get distribution of student performance levels"""
    try:
        schedules = firebase_client.query_documents(
            "student_schedules",
            {"subject_id": subject_id},
            limit=1000
        )
        
        distribution = {
            "excellent": 0,    # 80-100%
            "good": 0,         # 60-80%
            "average": 0,      # 40-60%
            "needs_help": 0    # 0-40%
        }
        
        for schedule in schedules:
            mastery = (schedule.get("topics_mastered", 0) / 
                      schedule.get("total_topics", 1) * 100)
            
            if mastery >= 80:
                distribution["excellent"] += 1
            elif mastery >= 60:
                distribution["good"] += 1
            elif mastery >= 40:
                distribution["average"] += 1
            else:
                distribution["needs_help"] += 1
        
        return {
            "subject_id": subject_id,
            "total_students": len(schedules),
            "distribution": distribution,
            "percentages": {
                k: (v / len(schedules) * 100) if schedules else 0
                for k, v in distribution.items()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting performance distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))