from typing import List, Dict, Tuple
from datetime import datetime, date, timedelta
import logging
import math

from .models import (
    StudentTopicPerformance, ScheduleTask, WeeklyPlan, StudentSchedule,
    SubjectScheduleConfig, SchedulePriority, TaskStatus
)
from .firebase import firebase_client

logger = logging.getLogger(__name__)

class ScheduleIntelligence:
    """Core intelligence for personalized schedule generation"""
    
    # BKT weights for different sources
    WEIGHTS = {
        "quiz": 0.15,
        "assignment": 0.15,
        "pbl": 0.15,
        "ia_test": 0.25,
        "semester_exam": 0.30
    }
    
    # Learning velocity factors
    FAST_LEARNER_THRESHOLD = 1.3
    SLOW_LEARNER_THRESHOLD = 0.7
    
    # BKT thresholds
    WEAK_TOPIC_THRESHOLD = 0.6
    STRONG_TOPIC_THRESHOLD = 0.8
    
    # Forgetting curve days
    REVIEW_INTERVAL_DAYS = 10
    
    def calculate_weighted_bkt(self, data_sources: Dict[str, float]) -> float:
        """Calculate weighted BKT from multiple sources"""
        total_weight = 0
        weighted_sum = 0
        
        for source, score in data_sources.items():
            if score > 0:  # Only include sources with data
                weight = self.WEIGHTS.get(source, 0)
                weighted_sum += score * weight
                total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def update_bkt_incremental(self, current_bkt: float, new_score: float, 
                               source_type: str, alpha: float = 0.3) -> float:
        """Update BKT using exponential moving average"""
        weight = self.WEIGHTS.get(source_type, 0.15)
        # Weighted EMA: new_bkt = current_bkt + alpha * weight * (new_score - current_bkt)
        return current_bkt + (alpha * weight * (new_score - current_bkt))
    
    def detect_prerequisite_gaps(self, student_performance: List[StudentTopicPerformance],
                                 topic_dependencies: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Detect which topics have prerequisite gaps"""
        gaps = {}
        performance_map = {p.topic_id: p for p in student_performance}
        
        for topic_id, prerequisites in topic_dependencies.items():
            topic_gaps = []
            for prereq_id in prerequisites:
                prereq_perf = performance_map.get(prereq_id)
                if prereq_perf and prereq_perf.weighted_bkt < self.WEAK_TOPIC_THRESHOLD:
                    topic_gaps.append(prereq_id)
            
            if topic_gaps:
                gaps[topic_id] = topic_gaps
        
        return gaps
    
    def calculate_time_needed(self, topic_id: str, current_bkt: float,
                             complexity: int, learning_velocity: float,
                             base_hours: float) -> float:
        """Calculate hours needed for a topic based on student profile"""
        # Formula: time = base_hours * complexity / velocity / (bkt + 0.1)
        # More time if: high complexity, low velocity, low BKT
        bkt_factor = max(0.1, current_bkt)  # Avoid division by zero
        time_needed = (base_hours * complexity) / (learning_velocity * bkt_factor)
        
        # Cap between 0.5 and 10 hours per topic
        return max(0.5, min(10.0, time_needed))
    
    def prioritize_topics(self, student_performance: List[StudentTopicPerformance],
                         config: SubjectScheduleConfig,
                         prerequisite_gaps: Dict[str, List[str]],
                         exam_dates: List[date]) -> List[Tuple[str, SchedulePriority, str]]:
        """Prioritize topics for scheduling"""
        priorities = []
        performance_map = {p.topic_id: p for p in student_performance}
        
        for topic_id in config.topic_coverage_order:
            perf = performance_map.get(topic_id)
            if not perf:
                continue
            
            # Check if has prerequisite gaps
            if topic_id in prerequisite_gaps:
                for prereq in prerequisite_gaps[topic_id]:
                    priorities.append((
                        prereq,
                        SchedulePriority.PREREQUISITE_GAP,
                        f"Prerequisite for {perf.topic_name}"
                    ))
            
            # Check if exam-critical (exam in next 2 weeks)
            is_exam_critical = any(
                (exam_date - date.today()).days <= 14
                for exam_date in exam_dates
                if topic_id in config.topic_coverage_order
            )
            
            if is_exam_critical and perf.weighted_bkt < self.STRONG_TOPIC_THRESHOLD:
                priorities.append((
                    topic_id,
                    SchedulePriority.EXAM_CRITICAL,
                    f"Exam in {min((e - date.today()).days for e in exam_dates)} days"
                ))
                continue
            
            # Check if weak topic
            if perf.weighted_bkt < self.WEAK_TOPIC_THRESHOLD:
                data_breakdown = self._format_data_sources(perf.data_sources)
                priorities.append((
                    topic_id,
                    SchedulePriority.LOW_BKT,
                    f"Weak topic (BKT: {perf.weighted_bkt:.2f}). {data_breakdown}"
                ))
                continue
            
            # Check if needs review (forgetting curve)
            if perf.last_practiced:
                days_since = (datetime.now() - perf.last_practiced).days
                if days_since >= self.REVIEW_INTERVAL_DAYS:
                    priorities.append((
                        topic_id,
                        SchedulePriority.REVIEW,
                        f"Not practiced in {days_since} days - forgetting curve"
                    ))
                    continue
            
            # New topic
            if perf.weighted_bkt < 0.3:
                priorities.append((
                    topic_id,
                    SchedulePriority.NEW_TOPIC,
                    "New topic to learn"
                ))
        
        # Sort by priority
        priority_order = {
            SchedulePriority.PREREQUISITE_GAP: 0,
            SchedulePriority.EXAM_CRITICAL: 1,
            SchedulePriority.LOW_BKT: 2,
            SchedulePriority.NEW_TOPIC: 3,
            SchedulePriority.REVIEW: 4
        }
        
        priorities.sort(key=lambda x: priority_order[x[1]])
        return priorities
    
    def generate_schedule(self, student_id: str, subject_id: str,
                         student_performance: List[StudentTopicPerformance],
                         config: SubjectScheduleConfig,
                         topic_dependencies: Dict[str, List[str]]) -> StudentSchedule:
        """Generate personalized schedule for student"""
        
        # 1. Detect prerequisite gaps
        prerequisite_gaps = self.detect_prerequisite_gaps(student_performance, topic_dependencies)
        
        # 2. Get exam dates
        exam_dates = [exam.date for exam in config.exam_dates]
        
        # 3. Prioritize topics
        prioritized_topics = self.prioritize_topics(
            student_performance, config, prerequisite_gaps, exam_dates
        )
        
        # 4. Calculate available time
        days_until_deadline = (config.deadline - date.today()).days
        weeks_available = days_until_deadline // 7
        buffer_weeks = math.ceil(weeks_available * 0.2)  # 20% buffer
        effective_weeks = weeks_available - buffer_weeks
        
        hours_per_week = config.weekly_hours
        
        # 5. Generate weekly plans
        weekly_plans = []
        current_date = date.today()
        performance_map = {p.topic_id: p for p in student_performance}
        
        topic_index = 0
        for week_num in range(1, effective_weeks + 1):
            week_start = current_date + timedelta(days=(week_num - 1) * 7)
            week_end = week_start + timedelta(days=6)
            
            week_tasks = []
            week_hours = 0
            topics_this_week = []
            
            # Fill week with tasks
            task_date = week_start
            while week_hours < hours_per_week and topic_index < len(prioritized_topics):
                topic_id, priority, reason = prioritized_topics[topic_index]
                perf = performance_map.get(topic_id)
                
                if not perf:
                    topic_index += 1
                    continue
                
                # Calculate time needed
                complexity = config.topic_complexity.get(topic_id, 3)
                base_hours = config.recommended_hours.get(topic_id, 2.0)
                time_needed = self.calculate_time_needed(
                    topic_id, perf.weighted_bkt, complexity,
                    perf.learning_velocity, base_hours
                )
                
                # Split into daily tasks if needed
                if time_needed > 2.0:
                    sessions = math.ceil(time_needed / 2.0)
                    session_hours = time_needed / sessions
                    
                    for _ in range(sessions):
                        if week_hours + session_hours <= hours_per_week:
                            task = ScheduleTask(
                                date=task_date,
                                topic_id=topic_id,
                                topic_name=perf.topic_name,
                                duration_hours=round(session_hours, 1),
                                priority=priority,
                                reason=reason
                            )
                            week_tasks.append(task)
                            week_hours += session_hours
                            task_date += timedelta(days=1)
                            if task_date > week_end:
                                break
                else:
                    if week_hours + time_needed <= hours_per_week:
                        task = ScheduleTask(
                            date=task_date,
                            topic_id=topic_id,
                            topic_name=perf.topic_name,
                            duration_hours=round(time_needed, 1),
                            priority=priority,
                            reason=reason
                        )
                        week_tasks.append(task)
                        week_hours += time_needed
                        task_date += timedelta(days=1)
                
                topics_this_week.append(topic_id)
                topic_index += 1
            
            weekly_plan = WeeklyPlan(
                week_number=week_num,
                start_date=week_start,
                end_date=week_end,
                tasks=week_tasks,
                total_hours=round(week_hours, 1),
                topics_covered=topics_this_week
            )
            weekly_plans.append(weekly_plan)
        
        # 6. Calculate topics mastered
        topics_mastered = sum(1 for p in student_performance if p.weighted_bkt >= self.STRONG_TOPIC_THRESHOLD)
        
        # 7. Create schedule
        schedule = StudentSchedule(
            student_id=student_id,
            subject_id=subject_id,
            deadline=config.deadline,
            total_topics=len(student_performance),
            topics_mastered=topics_mastered,
            weekly_plans=weekly_plans
        )
        
        return schedule
    
    def _format_data_sources(self, data_sources) -> str:
        """Format data source scores for explanation"""
        parts = []
        if data_sources.quiz > 0:
            parts.append(f"Quiz: {data_sources.quiz:.0%}")
        if data_sources.assignment > 0:
            parts.append(f"Assignment: {data_sources.assignment:.0%}")
        if data_sources.pbl > 0:
            parts.append(f"PBL: {data_sources.pbl:.0%}")
        if data_sources.ia_test > 0:
            parts.append(f"IA: {data_sources.ia_test:.0%}")
        if data_sources.semester_exam > 0:
            parts.append(f"Exam: {data_sources.semester_exam:.0%}")
        return ", ".join(parts)

# Singleton
schedule_intelligence = ScheduleIntelligence()