import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, ChartLine, Warning, ShieldCheck, Files } from '@phosphor-icons/react';
import Header from '../components/Header';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const COLORS = ['#FF2B2B', '#FFD500', '#002FA7', '#00C853'];

const Analytics = () => {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await axios.get(`${API}/analytics/trends`);
      setData(response.data);
    } catch (err) {
      console.error('Error fetching analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white">
        <Header />
        <div className="loading"><div className="spinner"></div></div>
      </div>
    );
  }

  if (!data || data.trends.length === 0) {
    return (
      <div className="min-h-screen" style={{ background: '#F1F3F5' }}>
        <Header />
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <button data-testid="back-button" onClick={() => navigate('/')} className="btn btn-secondary mb-4">
            <ArrowLeft size={20} className="inline mr-2" /> BACK
          </button>
          <h1 className="text-4xl sm:text-5xl font-black tracking-tighter" style={{ fontFamily: 'IBM Plex Sans, sans-serif' }}>
            ANALYTICS
          </h1>
          <div className="card text-center py-12 mt-8" data-testid="no-analytics">
            <p className="text-xl" style={{ color: '#52525B' }}>No scan data available yet. Run some scans first.</p>
            <button onClick={() => navigate('/')} className="btn btn-primary mt-6">START SCANNING</button>
          </div>
        </div>
      </div>
    );
  }

  const { trends, severity_distribution, top_issues, totals } = data;

  return (
    <div className="min-h-screen" style={{ background: '#F1F3F5' }}>
      <Header />

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-8">
          <button data-testid="back-button" onClick={() => navigate('/')} className="btn btn-secondary mb-4">
            <ArrowLeft size={20} className="inline mr-2" /> BACK
          </button>
          <h1 data-testid="analytics-title" className="text-4xl sm:text-5xl font-black tracking-tighter" style={{ fontFamily: 'IBM Plex Sans, sans-serif' }}>
            CODE QUALITY ANALYTICS
          </h1>
          <p className="text-base leading-relaxed mt-4" style={{ color: '#52525B' }}>
            Track code quality trends across your scans over time.
          </p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="card" data-testid="analytics-total-scans">
            <p className="text-xs font-bold uppercase tracking-widest" style={{ color: '#A1A1AA' }}>Total Scans</p>
            <p className="text-3xl font-bold mt-2" style={{ fontFamily: 'IBM Plex Mono, monospace' }}>{totals.total_scans}</p>
          </div>
          <div className="card" data-testid="analytics-total-issues">
            <p className="text-xs font-bold uppercase tracking-widest" style={{ color: '#A1A1AA' }}>Total Issues</p>
            <p className="text-3xl font-bold mt-2" style={{ fontFamily: 'IBM Plex Mono, monospace', color: '#FF2B2B' }}>{totals.total_issues}</p>
          </div>
          <div className="card" data-testid="analytics-total-files">
            <p className="text-xs font-bold uppercase tracking-widest" style={{ color: '#A1A1AA' }}>Files Scanned</p>
            <p className="text-3xl font-bold mt-2" style={{ fontFamily: 'IBM Plex Mono, monospace' }}>{totals.total_files}</p>
          </div>
          <div className="card" data-testid="analytics-critical">
            <p className="text-xs font-bold uppercase tracking-widest" style={{ color: '#A1A1AA' }}>Critical Issues</p>
            <p className="text-3xl font-bold mt-2" style={{ fontFamily: 'IBM Plex Mono, monospace', color: '#FF2B2B' }}>{totals.critical}</p>
          </div>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Issues Over Time */}
          <div className="bg-white border p-6" style={{ borderColor: '#E4E4E7' }} data-testid="chart-trends">
            <h3 className="text-lg font-semibold tracking-tight mb-4" style={{ fontFamily: 'IBM Plex Sans, sans-serif' }}>
              <ChartLine size={20} className="inline mr-2" color="#002FA7" />
              ISSUES OVER TIME
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trends}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E4E4E7" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fontFamily: 'IBM Plex Mono' }} stroke="#A1A1AA" />
                <YAxis tick={{ fontSize: 11, fontFamily: 'IBM Plex Mono' }} stroke="#A1A1AA" />
                <Tooltip contentStyle={{ fontFamily: 'IBM Plex Mono', fontSize: 12, border: '1px solid #09090B' }} />
                <Legend wrapperStyle={{ fontFamily: 'IBM Plex Sans', fontSize: 12 }} />
                <Line type="monotone" dataKey="critical" stroke="#FF2B2B" strokeWidth={2} dot={{ r: 4 }} name="Critical" />
                <Line type="monotone" dataKey="high" stroke="#FFD500" strokeWidth={2} dot={{ r: 4 }} name="High" />
                <Line type="monotone" dataKey="medium" stroke="#002FA7" strokeWidth={2} dot={{ r: 4 }} name="Medium" />
                <Line type="monotone" dataKey="low" stroke="#00C853" strokeWidth={2} dot={{ r: 4 }} name="Low" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Severity Distribution */}
          <div className="bg-white border p-6" style={{ borderColor: '#E4E4E7' }} data-testid="chart-severity">
            <h3 className="text-lg font-semibold tracking-tight mb-4" style={{ fontFamily: 'IBM Plex Sans, sans-serif' }}>
              <ShieldCheck size={20} className="inline mr-2" color="#002FA7" />
              SEVERITY DISTRIBUTION
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={severity_distribution.filter(d => d.value > 0)}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {severity_distribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ fontFamily: 'IBM Plex Mono', fontSize: 12, border: '1px solid #09090B' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Issues Bar Chart */}
        <div className="bg-white border p-6" style={{ borderColor: '#E4E4E7' }} data-testid="chart-top-issues">
          <h3 className="text-lg font-semibold tracking-tight mb-4" style={{ fontFamily: 'IBM Plex Sans, sans-serif' }}>
            <Warning size={20} className="inline mr-2" color="#002FA7" />
            MOST COMMON ISSUES
          </h3>
          {top_issues.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={top_issues} layout="vertical" margin={{ left: 120 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E4E4E7" />
                <XAxis type="number" tick={{ fontSize: 11, fontFamily: 'IBM Plex Mono' }} stroke="#A1A1AA" />
                <YAxis
                  dataKey="type"
                  type="category"
                  tick={{ fontSize: 11, fontFamily: 'IBM Plex Mono' }}
                  stroke="#A1A1AA"
                  tickFormatter={(v) => v.replace(/_/g, ' ').toUpperCase()}
                  width={110}
                />
                <Tooltip contentStyle={{ fontFamily: 'IBM Plex Mono', fontSize: 12, border: '1px solid #09090B' }} />
                <Bar dataKey="count" fill="#002FA7" radius={[0, 2, 2, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm" style={{ color: '#52525B' }}>No issue data available yet.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Analytics;
