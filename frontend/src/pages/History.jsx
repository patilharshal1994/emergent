import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, FileCode, GitBranch } from '@phosphor-icons/react';
import Header from '../components/Header';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const History = () => {
  const navigate = useNavigate();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await axios.get(`${API}/scan/history`);
      setHistory(response.data.history);
    } catch (err) {
      console.error('Error fetching history:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

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
            data-testid="history-title"
            className="text-4xl sm:text-5xl font-black tracking-tighter" 
            style={{fontFamily: 'IBM Plex Sans, sans-serif'}}
          >
            SCAN HISTORY
          </h1>
          <p className="text-base leading-relaxed mt-4" style={{color: '#52525B'}}>
            View all previous code quality scans and their results.
          </p>
        </div>

        {history.length === 0 ? (
          <div className="card text-center py-12" data-testid="no-history">
            <p className="text-xl" style={{color: '#52525B'}}>No scan history available.</p>
            <button
              onClick={() => navigate('/')}
              className="btn btn-primary mt-6"
            >
              START FIRST SCAN
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {history.map((scan, index) => (
              <div
                key={scan.scan_id}
                data-testid={`history-item-${index}`}
                className="card cursor-pointer"
                onClick={() => navigate(`/results/${scan.scan_id}`)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      {scan.type === 'file_upload' ? (
                        <FileCode size={24} weight="duotone" color="#002FA7" />
                      ) : (
                        <GitBranch size={24} weight="duotone" color="#002FA7" />
                      )}
                      <h3 
                        className="text-xl font-semibold tracking-tight" 
                        style={{fontFamily: 'IBM Plex Sans, sans-serif'}}
                      >
                        {scan.type === 'file_upload' ? 'File Upload Scan' : `PR Scan: ${scan.repo}#${scan.pr_number}`}
                      </h3>
                    </div>
                    
                    <p className="text-sm mb-2" style={{color: '#52525B', fontFamily: 'IBM Plex Mono, monospace'}}>
                      {formatDate(scan.timestamp)}
                    </p>

                    <div className="flex gap-4 mt-3">
                      <div>
                        <span className="text-xs font-bold uppercase tracking-widest" style={{color: '#A1A1AA'}}>Files: </span>
                        <span className="font-semibold" style={{fontFamily: 'IBM Plex Mono, monospace'}}>{scan.files_scanned}</span>
                      </div>
                      <div>
                        <span className="text-xs font-bold uppercase tracking-widest" style={{color: '#A1A1AA'}}>Issues: </span>
                        <span className="font-semibold" style={{fontFamily: 'IBM Plex Mono, monospace'}}>{scan.issues_found}</span>
                      </div>
                      {scan.summary && (
                        <>
                          <div>
                            <span className="badge badge-critical">{scan.summary.critical} Critical</span>
                          </div>
                          <div>
                            <span className="badge badge-high">{scan.summary.high} High</span>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default History;