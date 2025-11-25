import React, { useState, useEffect } from 'react';
import { analyticsApi } from '../../services/api';
import Card from '../common/Card';
import { AlertTriangle, TrendingUp, Users } from 'lucide-react';

export const ClassHeatmap = ({ subjectId }) => {
  const [heatmapData, setHeatmapData] = useState(null);
  const [weakTopics, setWeakTopics] = useState([]);
  const [classOverview, setClassOverview] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadClassData();
  }, [subjectId]);

  const loadClassData = async () => {
    try {
      setLoading(true);
      const [heatmap, weak, overview] = await Promise.all([
        analyticsApi.getClassHeatmap(subjectId),
        analyticsApi.getWeakTopics(subjectId, 0.5),
        analyticsApi.getClassOverview(subjectId),
      ]);
      
      setHeatmapData(heatmap);
      setWeakTopics(weak.weak_topics);
      setClassOverview(overview);
    } catch (error) {
      console.error('Error loading class data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getColorForScore = (score) => {
    if (score >= 0.8) return 'bg-green-500';
    if (score >= 0.6) return 'bg-yellow-500';
    if (score >= 0.4) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const getColorIntensity = (score) => {
    const intensity = Math.round(score * 100);
    if (score >= 0.8) return `rgba(34, 197, 94, ${intensity / 100})`;
    if (score >= 0.6) return `rgba(234, 179, 8, ${intensity / 100})`;
    if (score >= 0.4) return `rgba(249, 115, 22, ${intensity / 100})`;
    return `rgba(239, 68, 68, ${intensity / 100})`;
  };

  if (loading) {
    return <div className="text-center py-8">Loading class analytics...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Class Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Students</p>
              <p className="text-2xl font-bold">{classOverview?.total_students || 0}</p>
            </div>
            <Users className="w-8 h-8 text-blue-500" />
          </div>
        </Card>

        <Card className="p-4 bg-green-50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-green-700">On Track</p>
              <p className="text-2xl font-bold text-green-600">{classOverview?.on_track || 0}</p>
            </div>
            <TrendingUp className="w-8 h-8 text-green-500" />
          </div>
        </Card>

        <Card className="p-4 bg-yellow-50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-yellow-700">Behind</p>
              <p className="text-2xl font-bold text-yellow-600">{classOverview?.behind || 0}</p>
            </div>
            <AlertTriangle className="w-8 h-8 text-yellow-500" />
          </div>
        </Card>

        <Card className="p-4 bg-blue-50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-blue-700">Avg Adherence</p>
              <p className="text-2xl font-bold text-blue-600">
                {classOverview?.average_adherence?.toFixed(0) || 0}%
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Weak Topics Alert */}
      {weakTopics.length > 0 && (
        <Card className="p-6 bg-red-50 border-l-4 border-red-500">
          <h3 className="text-lg font-bold text-red-800 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" />
            Topics Needing Attention
          </h3>
          <div className="space-y-3">
            {weakTopics.slice(0, 5).map((topic, index) => (
              <div key={index} className="flex items-center justify-between bg-white p-3 rounded-lg">
                <div className="flex-1">
                  <p className="font-semibold text-red-900">{topic.topic}</p>
                  <p className="text-sm text-red-700">
                    {topic.weak_students} students struggling • Average: {(topic.average_score * 100).toFixed(0)}%
                  </p>
                </div>
                <button className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm">
                  Schedule Review
                </button>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Heatmap */}
      <Card className="p-6">
        <h3 className="text-xl font-bold mb-4">Student-Topic Mastery Heatmap</h3>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <th className="sticky left-0 bg-white border p-2 text-left min-w-[150px]">
                  Student
                </th>
                {heatmapData?.topics.map((topic, idx) => (
                  <th key={idx} className="border p-2 text-sm min-w-[100px]">
                    <div className="rotate-45 origin-left whitespace-nowrap">
                      {topic}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {heatmapData?.students.map((student, studentIdx) => (
                <tr key={studentIdx} className="hover:bg-gray-50">
                  <td className="sticky left-0 bg-white border p-2 font-medium">
                    Student {student.student_id.slice(-6)}
                  </td>
                  {heatmapData?.topics.map((topic, topicIdx) => {
                    const bkt = student.topics[topic]?.bkt || 0;
                    return (
                      <td
                        key={topicIdx}
                        className="border p-0"
                        title={`BKT: ${(bkt * 100).toFixed(0)}%`}
                      >
                        <div
                          className="w-full h-12 flex items-center justify-center text-white text-xs font-bold"
                          style={{ backgroundColor: getColorIntensity(bkt) }}
                        >
                          {(bkt * 100).toFixed(0)}%
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Legend */}
        <div className="mt-4 flex items-center gap-4 text-sm">
          <span className="font-semibold">Legend:</span>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-500"></div>
            <span>Mastered (80%+)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-yellow-500"></div>
            <span>Learning (60-80%)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-orange-500"></div>
            <span>Struggling (40-60%)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-red-500"></div>
            <span>Needs Help (&lt;40%)</span>
          </div>
        </div>
      </Card>

      {/* Topic Statistics */}
      <Card className="p-6">
        <h3 className="text-xl font-bold mb-4">Topic-wise Statistics</h3>
        <div className="space-y-2">
          {heatmapData?.topics.map((topic, idx) => {
            const stats = heatmapData.statistics[topic];
            return (
              <div key={idx} className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <p className="font-semibold">{topic}</p>
                  <div className="flex gap-4 text-xs text-gray-600 mt-1">
                    <span>Avg: {(stats.average * 100).toFixed(0)}%</span>
                    <span className="text-red-600">{stats.weak_students} weak</span>
                    <span className="text-green-600">{stats.strong_students} strong</span>
                  </div>
                </div>
                <div className="w-48 bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${getColorForScore(stats.average)}`}
                    style={{ width: `${stats.average * 100}%` }}
                  ></div>
                </div>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
};