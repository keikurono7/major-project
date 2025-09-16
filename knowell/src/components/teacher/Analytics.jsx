import React, { useState, useEffect } from 'react';
import ParallaxSection from '../common/ParallaxSection';
import Card from '../common/Card';
import Button from '../common/Button';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';

// This would ideally use a charting library like Chart.js or Recharts
// For now, I'm using basic HTML/CSS to represent charts

const Analytics = () => {
  const [timeframe, setTimeframe] = useState('month');
  const [loading, setLoading] = useState(true);
  const [analyticsData, setAnalyticsData] = useState(null);
  
  useEffect(() => {
    // Mock API call to get analytics data
    setTimeout(() => {
      const mockData = {
        topicPerformance: [
          { topic: 'Neural Networks', avgScore: 78 },
          { topic: 'Decision Trees', avgScore: 65 },
          { topic: 'Clustering', avgScore: 82 },
          { topic: 'Linear Regression', avgScore: 90 },
          { topic: 'Support Vector Machines', avgScore: 58 },
        ],
        studentEngagement: {
          daily: 12,
          weekly: 68,
          monthly: 240,
          trend: '+15%'
        },
        topWeaknesses: [
          'Support Vector Machines',
          'Decision Trees',
          'Data Preprocessing'
        ],
        topStrengths: [
          'Linear Regression',
          'Clustering',
          'Neural Networks'
        ],
        quizCompletionRate: 76,
        assignmentCompletionRate: 62,
      };
      
      setAnalyticsData(mockData);
      setLoading(false);
    }, 1000);
  }, [timeframe]);
  
  const handleTimeframeChange = (newTimeframe) => {
    setTimeframe(newTimeframe);
    setLoading(true);
    // In a real application, you would make a new API call here
  };
  
  if (loading) {
    return (
      <div className="analytics-loading p-8 text-center">
        <p>Loading analytics data...</p>
      </div>
    );
  }
  
  return (
    <div className="analytics p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h2 className="text-2xl font-bold mb-2">Analytics Dashboard</h2>
          <p className="text-gray-600">Track student performance and engagement</p>
        </div>

        {/* Timeframe Selector */}
        <div className="timeframe-selector mb-4 flex space-x-2">
          <Button
            type={timeframe === 'week' ? 'primary' : 'secondary'}
            onClick={() => handleTimeframeChange('week')}
          >
            Last Week
          </Button>
          <Button
            type={timeframe === 'month' ? 'primary' : 'secondary'}
            onClick={() => handleTimeframeChange('month')}
          >
            Last Month
          </Button>
          <Button
            type={timeframe === 'quarter' ? 'primary' : 'secondary'}
            onClick={() => handleTimeframeChange('quarter')}
          >
            Last Quarter
          </Button>
          <Button
            type={timeframe === 'year' ? 'primary' : 'secondary'}
            onClick={() => handleTimeframeChange('year')}
          >
            Last Year
          </Button>
        </div>
        
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {/* Student Engagement Card */}
          <Card title="Student Engagement">
            <div className="grid grid-cols-3 gap-2 mb-4">
              <div className="stat-box p-2 border border-gray-200 text-center">
                <div className="text-2xl font-bold">{analyticsData.studentEngagement.daily}</div>
                <div className="text-xs text-gray-500">Daily Active</div>
              </div>
              <div className="stat-box p-2 border border-gray-200 text-center">
                <div className="text-2xl font-bold">{analyticsData.studentEngagement.weekly}</div>
                <div className="text-xs text-gray-500">Weekly Active</div>
              </div>
              <div className="stat-box p-2 border border-gray-200 text-center">
                <div className="text-2xl font-bold">{analyticsData.studentEngagement.monthly}</div>
                <div className="text-xs text-gray-500">Monthly Active</div>
              </div>
            </div>
            <div className="trend-indicator flex items-center justify-center">
              <span className={`text-${analyticsData.studentEngagement.trend.startsWith('+') ? 'green' : 'red'}-500`}>
                {analyticsData.studentEngagement.trend} from previous period
              </span>
            </div>
          </Card>
          
          {/* Completion Rates Card */}
          <Card title="Completion Rates">
            <div className="completion-rates">
              <div className="mb-4">
                <div className="flex justify-between mb-1">
                  <span>Quizzes</span>
                  <span>{analyticsData.quizCompletionRate}%</span>
                </div>
                <div className="progress-bar">
                  <div 
                    className="progress-fill bg-blue-500" 
                    style={{ width: `${analyticsData.quizCompletionRate}%` }}
                  ></div>
                </div>
              </div>
              
              <div>
                <div className="flex justify-between mb-1">
                  <span>Assignments</span>
                  <span>{analyticsData.assignmentCompletionRate}%</span>
                </div>
                <div className="progress-bar">
                  <div 
                    className="progress-fill bg-green-500" 
                    style={{ width: `${analyticsData.assignmentCompletionRate}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </Card>
          
          {/* Areas of Improvement Card */}
          <Card title="Areas for Focus">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium mb-2 text-red-500">Weaknesses</h4>
                <ul className="list-disc pl-5">
                  {analyticsData.topWeaknesses.map((topic, index) => (
                    <li key={index}>{topic}</li>
                  ))}
                </ul>
              </div>
              
              <div>
                <h4 className="font-medium mb-2 text-green-500">Strengths</h4>
                <ul className="list-disc pl-5">
                  {analyticsData.topStrengths.map((topic, index) => (
                    <li key={index}>{topic}</li>
                  ))}
                </ul>
              </div>
            </div>
          </Card>
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <Card className="h-fit">
            <h3 className="text-lg font-semibold mb-4">Topic Performance</h3>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={analyticsData.topicPerformance}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="topic" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="avgScore" fill="#ca404f" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card className="h-fit">
            <h3 className="text-lg font-semibold mb-4">Student Progress</h3>
            {/* Add your student progress chart here */}
          </Card>
        </div>

        <div className="mt-4">
          <Card>
            <div className="flex justify-end">
              <Button type="secondary">Export Data</Button>
              <Button className="ml-2">Generate Detailed Report</Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Analytics;