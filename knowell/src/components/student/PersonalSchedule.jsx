import React, { useState, useEffect } from 'react';
import { scheduleApi, analyticsApi } from '../../services/api';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Calendar, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

export const PersonalSchedule = ({ studentId, subjectId }) => {
  const [todayTasks, setTodayTasks] = useState(null);
  const [schedule, setSchedule] = useState(null);
  const [knowledgeGraph, setKnowledgeGraph] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadScheduleData();
  }, [studentId, subjectId]);

  const loadScheduleData = async () => {
    try {
      setLoading(true);
      const [tasks, scheduleData, graph] = await Promise.all([
        scheduleApi.getTodayTasks(studentId, subjectId),
        scheduleApi.getStudentSchedule(studentId, subjectId),
        analyticsApi.getKnowledgeGraph(studentId, subjectId),
      ]);
      
      setTodayTasks(tasks);
      setSchedule(scheduleData);
      setKnowledgeGraph(graph);
    } catch (error) {
      console.error('Error loading schedule:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCompleteTask = async (taskId, timeSpent, notes) => {
    try {
      await scheduleApi.completeTask(studentId, subjectId, taskId, timeSpent, notes);
      loadScheduleData(); // Reload data
    } catch (error) {
      console.error('Error completing task:', error);
    }
  };

  const handleSkipTask = async (taskId, reason) => {
    try {
      await scheduleApi.skipTask(studentId, subjectId, taskId, reason);
      loadScheduleData();
    } catch (error) {
      console.error('Error skipping task:', error);
    }
  };

  if (loading) {
    return <div className="text-center py-8">Loading your personalized schedule...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Progress Overview */}
      <Card className="p-6 bg-gradient-to-r from-blue-500 to-purple-600 text-white">
        <h2 className="text-2xl font-bold mb-4">Your Learning Progress</h2>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <div className="text-3xl font-bold">{schedule?.topics_mastered || 0}</div>
            <div className="text-sm opacity-90">Topics Mastered</div>
          </div>
          <div>
            <div className="text-3xl font-bold">{schedule?.total_topics || 0}</div>
            <div className="text-sm opacity-90">Total Topics</div>
          </div>
          <div>
            <div className="text-3xl font-bold">{schedule?.adherence_score?.toFixed(0) || 0}%</div>
            <div className="text-sm opacity-90">Schedule Adherence</div>
          </div>
        </div>
      </Card>

      {/* Today's Tasks */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            Today's Schedule
          </h3>
          <span className="text-sm text-gray-600">
            {todayTasks?.completed || 0}/{todayTasks?.tasks?.length || 0} completed
          </span>
        </div>

        <div className="mb-4 p-4 bg-blue-50 rounded-lg">
          <p className="text-blue-800">{todayTasks?.progress_message}</p>
        </div>

        <div className="space-y-3">
          {todayTasks?.tasks?.map((task) => (
            <TaskCard
              key={task.task_id}
              task={task}
              onComplete={handleCompleteTask}
              onSkip={handleSkipTask}
            />
          ))}
        </div>
      </Card>

      {/* Knowledge Graph */}
      <Card className="p-6">
        <h3 className="text-xl font-bold mb-4">Your Knowledge Map</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-red-50 rounded-lg">
            <div className="text-2xl font-bold text-red-600">
              {knowledgeGraph?.summary?.weak_topics?.length || 0}
            </div>
            <div className="text-sm text-red-800">Topics Need Attention</div>
          </div>
          <div className="p-4 bg-yellow-50 rounded-lg">
            <div className="text-2xl font-bold text-yellow-600">
              {knowledgeGraph?.summary?.learning_topics?.length || 0}
            </div>
            <div className="text-sm text-yellow-800">Topics in Progress</div>
          </div>
          <div className="p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {knowledgeGraph?.summary?.strong_topics?.length || 0}
            </div>
            <div className="text-sm text-green-800">Topics Mastered</div>
          </div>
        </div>
      </Card>
    </div>
  );
};

const TaskCard = ({ task, onComplete, onSkip }) => {
  const [showNotes, setShowNotes] = useState(false);
  const [notes, setNotes] = useState('');
  const [timeSpent, setTimeSpent] = useState(task.duration_hours);

  const getStatusIcon = () => {
    switch (task.status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'skipped':
        return <XCircle className="w-5 h-5 text-gray-500" />;
      default:
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
    }
  };

  const getPriorityColor = () => {
    switch (task.priority) {
      case 'prerequisite_gap':
        return 'border-l-4 border-red-500';
      case 'exam_critical':
        return 'border-l-4 border-orange-500';
      case 'low_bkt':
        return 'border-l-4 border-yellow-500';
      default:
        return 'border-l-4 border-blue-500';
    }
  };

  return (
    <div className={`p-4 bg-white rounded-lg shadow ${getPriorityColor()}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            {getStatusIcon()}
            <h4 className="font-semibold">{task.topic_name}</h4>
          </div>
          <p className="text-sm text-gray-600 mb-2">{task.reason}</p>
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {task.duration_hours}h
            </span>
            <span className="capitalize">{task.priority.replace('_', ' ')}</span>
          </div>
        </div>

        {task.status === 'pending' && (
          <div className="flex gap-2">
            <Button
              size="sm"
              onClick={() => setShowNotes(!showNotes)}
              variant="outline"
            >
              Complete
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                const reason = prompt('Why are you skipping this task?');
                if (reason) onSkip(task.task_id, reason);
              }}
            >
              Skip
            </Button>
          </div>
        )}
      </div>

      {showNotes && (
        <div className="mt-4 pt-4 border-t space-y-3">
          <div>
            <label className="block text-sm font-medium mb-1">Time Spent (hours)</label>
            <input
              type="number"
              step="0.5"
              value={timeSpent}
              onChange={(e) => setTimeSpent(parseFloat(e.target.value))}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Notes (optional)</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg"
              rows="3"
              placeholder="How did it go? Any challenges?"
            />
          </div>
          <Button
            onClick={() => {
              onComplete(task.task_id, timeSpent, notes);
              setShowNotes(false);
            }}
            className="w-full"
          >
            Mark as Completed
          </Button>
        </div>
      )}
    </div>
  );
};