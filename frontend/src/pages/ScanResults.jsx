import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { DownloadSimple, ArrowLeft, Funnel } from '@phosphor-icons/react';
import Header from '../components/Header';
import IssueCard from '../components/IssueCard';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ScanResults = () => {
  const { scanId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchScanResults();
  }, [scanId]);

  const fetchScanResults = async () => {
    try {
      const response = await axios.get(`${API}/scan/${scanId}`);
      setData(response.data);
    } catch (err) {
      setError('Error fetching scan results');
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = async (format) => {
    try {
      const response = await axios.get(`${API}/scan/${scanId}/download?format=${format}`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `scan_${scanId}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Error downloading report:', err);
    }
  };

  const filteredIssues = data?.issues?.filter(issue => {
    const matchesSeverity = filterSeverity === 'all' || issue.severity === filterSeverity;
    const matchesSearch = searchTerm === '' || 
      issue.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
      issue.file.toLowerCase().includes(searchTerm.toLowerCase()) ||
      issue.type.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesSeverity && matchesSearch;
  }) || [];

  if (loading) {
    return (
      <div className="min-h-screen bg-white">
        <Header />
        <div className="loading">
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-white">
        <Header />
        <div className="container mx-auto px-4 py-12">
          <p className="text-red-500">{error || 'Scan not found'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{background: '#F1F3F5'}}>
      <Header />
      
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-8">
          <button
            data-testid="back-button"
            onClick={() => navigate('/')}
            className="btn btn-secondary mb-4"
          >
            <ArrowLeft size={20} className="inline mr-2" />
            BACK
          </button>

          <h1 
            data-testid="results-title"
            className="text-4xl sm:text-5xl font-black tracking-tighter" 
            style={{fontFamily: 'IBM Plex Sans, sans-serif'}}
          >
            SCAN RESULTS
          </h1>
          <p 
            className="text-sm mt-2" 
            style={{color: '#52525B', fontFamily: 'IBM Plex Mono, monospace'}}
          >
            Scan ID: {scanId}
          </p>
          {data.pr_info && (
            <div className="mt-4">
              <p className="text-base" style={{color: '#09090B'}}>
                <strong>PR:</strong> {data.pr_info.title} by {data.pr_info.author}
              </p>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="card" data-testid="summary-total">
            <p className="text-xs font-bold uppercase tracking-widest" style={{color: '#A1A1AA'}}>Total Issues</p>
            <p className="text-4xl font-bold mt-2" style={{fontFamily: 'IBM Plex Mono, monospace'}}>
              {data.summary.total_issues}
            </p>
          </div>

          <div className="card severity-critical" data-testid="summary-critical">
            <p className="text-xs font-bold uppercase tracking-widest" style={{color: '#A1A1AA'}}>Critical</p>
            <p className="text-4xl font-bold mt-2" style={{fontFamily: 'IBM Plex Mono, monospace', color: '#FF2B2B'}}>
              {data.summary.critical}
            </p>
          </div>

          <div className="card severity-high" data-testid="summary-high">
            <p className="text-xs font-bold uppercase tracking-widest" style={{color: '#A1A1AA'}}>High</p>
            <p className="text-4xl font-bold mt-2" style={{fontFamily: 'IBM Plex Mono, monospace', color: '#FFD500'}}>
              {data.summary.high}
            </p>
          </div>

          <div className="card severity-medium" data-testid="summary-medium">
            <p className="text-xs font-bold uppercase tracking-widest" style={{color: '#A1A1AA'}}>Medium/Low</p>
            <p className="text-4xl font-bold mt-2" style={{fontFamily: 'IBM Plex Mono, monospace', color: '#002FA7'}}>
              {data.summary.medium + data.summary.low}
            </p>
          </div>
        </div>

        <div className="bg-white border p-6 mb-6" style={{borderColor: '#E4E4E7'}}>
          <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
            <div className="flex-1 w-full md:w-auto">
              <input
                data-testid="search-input"
                type="text"
                placeholder="Search issues..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="input"
              />
            </div>

            <div className="flex gap-4 items-center">
              <div className="flex items-center gap-2">
                <Funnel size={20} color="#002FA7" />
                <select
                  data-testid="severity-filter"
                  value={filterSeverity}
                  onChange={(e) => setFilterSeverity(e.target.value)}
                  className="input"
                  style={{width: 'auto', minWidth: '150px'}}
                >
                  <option value="all">All Severities</option>
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>

              <button
                data-testid="download-json-button"
                onClick={() => downloadReport('json')}
                className="btn btn-secondary"
              >
                <DownloadSimple size={20} className="inline mr-2" />
                JSON
              </button>

              <button
                data-testid="download-html-button"
                onClick={() => downloadReport('html')}
                className="btn btn-secondary"
              >
                <DownloadSimple size={20} className="inline mr-2" />
                HTML
              </button>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          {filteredIssues.length === 0 ? (
            <div className="card text-center py-12" data-testid="no-issues">
              <p className="text-xl" style={{color: '#52525B'}}>No issues found matching your filters.</p>
            </div>
          ) : (
            filteredIssues.map((issue, index) => (
              <IssueCard key={index} issue={issue} index={index} />
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default ScanResults;