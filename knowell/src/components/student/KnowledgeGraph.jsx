import React, { useState, useEffect } from 'react';
import { analyticsApi } from '../../services/api';
import  Card from '../common/Card';
import { TrendingUp, TrendingDown, MinusCircle, Info } from 'lucide-react';

export const KnowledgeGraph = ({ studentId, subjectId }) => {
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedTopic, setSelectedTopic] = useState(null);

  useEffect(() => {
    loadGraphData();
  }, [studentId, subjectId]);

  const loadGraphData = async () => {
    try {
      setLoading(true);
      const data = await analyticsService.getKnowledgeGraph(studentId, subjectId);
      setGraphData(data);
    } catch (error) {
      console.error('Error loading knowledge graph:', error);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (bkt) => {
    if (bkt >= 0.8) return 'text-green-600 bg-green-50 border-green-200';
    if (bkt >= 0.6) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    if (bkt >= 0.4) return 'text-orange-600 bg-orange-50 border-orange-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  const getTrendIcon = (bkt) => {
    if (bkt >= 0.8) return <TrendingUp className="w-4 h-4" />;
    if (bkt >= 0.6) return <MinusCircle className="w-4 h-4" />;
    return <TrendingDown className="w-4 h-4" />;
  };

  const formatDataSources = (sources) => {
    const parts = [];
    if (sources.quiz > 0) parts.push(`Quiz: ${(sources.quiz * 100).toFixed(0)}%`);
    if (sources.assignment > 0) parts.push(`Assignment: ${(sources.assignment * 100).toFixed(0)}%`);
    if (sources.pbl > 0) parts.push(`PBL: ${(sources.pbl * 100).toFixed(0)}%`);
    if (sources.ia_test > 0) parts.push(`IA: ${(sources.ia_test * 100).toFixed(0)}%`);
    if (sources.semester_exam > 0) parts.push(`Exam: ${(sources.semester_exam * 100).toFixed(0)}%`);
    return parts.join(' • ');
  };

  if (loading) {
    return <div className="text-center py-8">Loading knowledge graph...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4 bg-gradient-to-br from-green-500 to-green-600 text-white">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold">Mastered Topics</h3>
            <TrendingUp className="w-5 h-5" />
          </div>
          <div className="text-3xl font-bold">
            {graphData?.summary?.strong_topics?.length || 0}
          </div>
          <div className="text-sm opacity-90 mt-1">
            {((graphData?.summary?.strong_topics?.length || 0) / (graphData?.topics?.length || 1) * 100).toFixed(0)}% of total
          </div>
        </Card>

        <Card className="p-4 bg-gradient-to-br from-yellow-500 to-yellow-600 text-white">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold">Learning</h3>
            <MinusCircle className="w-5 h-5" />
          </div>
          <div className="text-3xl font-bold">
            {graphData?.summary?.learning_topics?.length || 0}
          </div>
          <div className="text-sm opacity-90 mt-1">In progress</div>
        </Card>

        <Card className="p-4 bg-gradient-to-br from-red-500 to-red-600 text-white">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold">Need Attention</h3>
            <TrendingDown className="w-5 h-5" />
          </div>
          <div className="text-3xl font-bold">
            {graphData?.summary?.weak_topics?.length || 0}
          </div>
          <div className="text-sm opacity-90 mt-1">Focus areas</div>
        </Card>
      </div>

      {/* Topic List */}
      <Card className="p-6">
        <h3 className="text-xl font-bold mb-4">Topic-wise Mastery</h3>
        <div className="space-y-3">
          {graphData?.topics
            ?.sort((a, b) => a.weighted_bkt - b.weighted_bkt)
            .map((topic, idx) => (
              <div
                key={idx}
                className={`p-4 border rounded-lg cursor-pointer transition-all ${
                  getScoreColor(topic.weighted_bkt)
                } ${selectedTopic?.topic_id === topic.topic_id ? 'ring-2 ring-blue-500' : ''}`}
                onClick={() => setSelectedTopic(topic)}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    {getTrendIcon(topic.weighted_bkt)}
                    <h4 className="font-semibold">{topic.topic_name}</h4>
                  </div>
                  <div className="text-2xl font-bold">
                    {(topic.weighted_bkt * 100).toFixed(0)}%
                  </div>
                </div>

                <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                  <div
                    className={`h-2 rounded-full ${
                      topic.weighted_bkt >= 0.8 ? 'bg-green-500' :
                      topic.weighted_bkt >= 0.6 ? 'bg-yellow-500' :
                      topic.weighted_bkt >= 0.4 ? 'bg-orange-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${topic.weighted_bkt * 100}%` }}
                  ></div>
                </div>

                <div className="text-xs opacity-75">
                  {formatDataSources(topic.data_sources)}
                </div>

                {topic.prerequisite_gaps?.length > 0 && (
                  <div className="mt-2 text-xs bg-red-100 text-red-800 px-2 py-1 rounded inline-block">
                    ⚠️ Prerequisite gaps detected
                  </div>
                )}

                {topic.last_practiced && (
                  <div className="mt-1 text-xs opacity-60">
                    Last practiced: {new Date(topic.last_practiced).toLocaleDateString()}
                  </div>
                )}
              </div>
            ))}
        </div>
      </Card>

      {/* Topic Details Modal */}
      {selectedTopic && (
        <Card className="p-6 bg-blue-50 border-2 border-blue-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold flex items-center gap-2">
              <Info className="w-5 h-5" />
              Detailed Analysis: {selectedTopic.topic_name}
            </h3>
            <button
              onClick={() => setSelectedTopic(null)}
              className="text-gray-600 hover:text-gray-800"
            >
              ✕
            </button>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <p className="text-sm text-gray-600 mb-1">Overall Mastery</p>
              <p className="text-3xl font-bold text-blue-600">
                {(selectedTopic.weighted_bkt * 100).toFixed(0)}%
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Learning Velocity</p>
              <p className="text-3xl font-bold text-blue-600">
                {selectedTopic.learning_velocity?.toFixed(2) || '1.0'}x
              </p>
            </div>
          </div>

          <div className="space-y-3">
            <div>
              <h4 className="font-semibold mb-2">Performance by Source:</h4>
              <div className="space-y-2">
                {selectedTopic.data_sources.quiz > 0 && (
                  <SourceBar label="Quiz" score={selectedTopic.data_sources.quiz} />
                )}
                {selectedTopic.data_sources.assignment > 0 && (
                  <SourceBar label="Assignment" score={selectedTopic.data_sources.assignment} />
                )}
                {selectedTopic.data_sources.pbl > 0 && (
                  <SourceBar label="PBL Project" score={selectedTopic.data_sources.pbl} />
                )}
                {selectedTopic.data_sources.ia_test > 0 && (
                  <SourceBar label="IA Test" score={selectedTopic.data_sources.ia_test} />
                )}
                {selectedTopic.data_sources.semester_exam > 0 && (
                  <SourceBar label="Semester Exam" score={selectedTopic.data_sources.semester_exam} />
                )}
              </div>
            </div>

            {selectedTopic.error_patterns?.length > 0 && (
              <div>
                <h4 className="font-semibold mb-2">Common Mistakes:</h4>
                <ul className="list-disc list-inside space-y-1 text-sm">
                  {selectedTopic.error_patterns.map((error, idx) => (
                    <li key={idx}>{error}</li>
                  ))}
                </ul>
              </div>
            )}

            {selectedTopic.next_review_date && (
              <div className="bg-yellow-100 border border-yellow-300 rounded-lg p-3">
                <p className="text-sm text-yellow-800">
                  📅 Scheduled for review on: {new Date(selectedTopic.next_review_date).toLocaleDateString()}
                </p>
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  );
};

const SourceBar = ({ label, score }) => (
  <div className="flex items-center gap-3">
    <div className="w-32 text-sm font-medium">{label}</div>
    <div className="flex-1 bg-gray-200 rounded-full h-2">
      <div
        className={`h-2 rounded-full ${
          score >= 0.8 ? 'bg-green-500' :
          score >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
        }`}
        style={{ width: `${score * 100}%` }}
      ></div>
    </div>
    <div className="w-12 text-sm font-bold text-right">
      {(score * 100).toFixed(0)}%
    </div>
  </div>
);