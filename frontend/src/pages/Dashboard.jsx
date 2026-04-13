import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { UploadSimple, GitBranch, Clock, FileCode, FolderOpen, CodeBlock } from '@phosphor-icons/react';
import Header from '../components/Header';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Dashboard = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('upload');
  const [files, setFiles] = useState([]);
  const [repo, setRepo] = useState('');
  const [prNumber, setPrNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [enableAI, setEnableAI] = useState(true);
  const [pasteCode, setPasteCode] = useState('');
  const [pasteFilename, setPasteFilename] = useState('code.js');
  const [uploadMode, setUploadMode] = useState('files');
  const [stats, setStats] = useState({ totalScans: 0, totalIssues: 0, totalSuggestions: 0 });
  const folderInputRef = useRef(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/scan/history`);
      const history = response.data.history || [];
      const totalScans = history.length;
      const totalIssues = history.reduce((acc, scan) => acc + (scan.issues_found || 0), 0);
      const totalSuggestions = history.reduce((acc, scan) => {
        const issues = scan.issues || [];
        return acc + issues.filter(i => i.ai_suggestion).length;
      }, 0);
      setStats({ totalScans, totalIssues, totalSuggestions });
    } catch (err) {
      // Stats are non-critical
    }
  };

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    setFiles(selectedFiles);
    setError('');
  };

  const handleFolderChange = (e) => {
    const selectedFiles = Array.from(e.target.files).filter(file => {
      const ext = file.name.split('.').pop().toLowerCase();
      return ['js', 'jsx', 'ts', 'tsx', 'py'].includes(ext);
    });
    setFiles(selectedFiles);
    setError('');
  };

  const handleUploadScan = async (e) => {
    e.preventDefault();
    if (files.length === 0) {
      setError('Please select at least one file or folder');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      files.forEach(file => {
        const relativePath = file.webkitRelativePath || file.name;
        formData.append('files', file, relativePath);
      });
      formData.append('enable_ai', enableAI);

      const response = await axios.post(`${API}/scan/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      navigate(`/results/${response.data.scan_id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error scanning files');
    } finally {
      setLoading(false);
    }
  };

  const handlePasteScan = async (e) => {
    e.preventDefault();
    if (!pasteCode.trim()) {
      setError('Please paste some code to scan');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const blob = new Blob([pasteCode], { type: 'text/plain' });
      const file = new File([blob], pasteFilename, { type: 'text/plain' });

      const formData = new FormData();
      formData.append('files', file);
      formData.append('enable_ai', enableAI);

      const response = await axios.post(`${API}/scan/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      navigate(`/results/${response.data.scan_id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error scanning code');
    } finally {
      setLoading(false);
    }
  };

  const handleGitHubScan = async (e) => {
    e.preventDefault();
    if (!repo || !prNumber) {
      setError('Please enter repository and PR number');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('repo', repo);
      formData.append('pr_number', prNumber);
      formData.append('enable_ai', enableAI);

      const response = await axios.post(`${API}/scan/github-pr`, formData);
      navigate(`/results/${response.data.scan_id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error scanning GitHub PR');
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'upload', label: 'Upload Files / Folder', icon: UploadSimple },
    { id: 'paste', label: 'Paste Code', icon: CodeBlock },
    { id: 'github', label: 'GitHub PR', icon: GitBranch },
  ];

  return (
    <div className="min-h-screen bg-white">
      <Header />
      
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-12">
          <h1 
            data-testid="page-title"
            className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tighter" 
            style={{fontFamily: 'IBM Plex Sans, sans-serif'}}
          >
            CODE QUALITY GATE
          </h1>
          <p className="text-base leading-relaxed mt-4" style={{color: '#52525B'}}>
            Automated code scanning with AI-powered fix suggestions. Upload files, scan folders, paste code, or scan GitHub PRs.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="card" data-testid="stat-card-scans">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-widest" style={{color: '#A1A1AA'}}>Total Scans</p>
                <p className="text-3xl font-bold mt-2" style={{fontFamily: 'IBM Plex Mono, monospace'}}>{stats.totalScans}</p>
              </div>
              <FileCode size={32} weight="duotone" color="#002FA7" />
            </div>
          </div>

          <div className="card" data-testid="stat-card-issues">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-widest" style={{color: '#A1A1AA'}}>Issues Found</p>
                <p className="text-3xl font-bold mt-2" style={{fontFamily: 'IBM Plex Mono, monospace'}}>{stats.totalIssues}</p>
              </div>
              <Clock size={32} weight="duotone" color="#FF2B2B" />
            </div>
          </div>

          <div className="card" data-testid="stat-card-fixed">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-widest" style={{color: '#A1A1AA'}}>AI Suggestions</p>
                <p className="text-3xl font-bold mt-2" style={{fontFamily: 'IBM Plex Mono, monospace'}}>{stats.totalSuggestions}</p>
              </div>
              <GitBranch size={32} weight="duotone" color="#00C853" />
            </div>
          </div>
        </div>

        <div className="bg-white border p-8" style={{borderColor: '#E4E4E7'}}>
          <div className="flex gap-4 mb-8 border-b" style={{borderColor: '#E4E4E7'}}>
            {tabs.map(tab => (
              <button
                key={tab.id}
                data-testid={`tab-${tab.id}`}
                onClick={() => { setActiveTab(tab.id); setError(''); }}
                className="pb-4 px-2 font-semibold uppercase text-sm tracking-wider transition-colors"
                style={{
                  fontFamily: 'IBM Plex Sans, sans-serif',
                  borderBottom: activeTab === tab.id ? '2px solid #002FA7' : '2px solid transparent',
                  color: activeTab === tab.id ? '#002FA7' : '#52525B'
                }}
              >
                <tab.icon size={20} className="inline mr-2" />
                {tab.label}
              </button>
            ))}
          </div>

          {error && (
            <div 
              data-testid="error-message"
              className="border-l-4 p-4 mb-6" 
              style={{borderLeftColor: '#FF2B2B', background: '#FEF2F2'}}
            >
              <p className="text-sm" style={{color: '#FF2B2B'}}>{error}</p>
            </div>
          )}

          {activeTab === 'upload' && (
            <form onSubmit={handleUploadScan}>
              <div className="mb-6">
                <div className="flex gap-4 mb-4">
                  <button
                    type="button"
                    data-testid="mode-files"
                    onClick={() => { setUploadMode('files'); setFiles([]); }}
                    className="px-4 py-2 text-sm font-semibold uppercase tracking-wider border-2 transition-all"
                    style={{
                      background: uploadMode === 'files' ? '#002FA7' : '#FFFFFF',
                      color: uploadMode === 'files' ? '#FFFFFF' : '#002FA7',
                      borderColor: '#002FA7'
                    }}
                  >
                    <UploadSimple size={16} className="inline mr-2" />
                    Individual Files
                  </button>
                  <button
                    type="button"
                    data-testid="mode-folder"
                    onClick={() => { setUploadMode('folder'); setFiles([]); }}
                    className="px-4 py-2 text-sm font-semibold uppercase tracking-wider border-2 transition-all"
                    style={{
                      background: uploadMode === 'folder' ? '#002FA7' : '#FFFFFF',
                      color: uploadMode === 'folder' ? '#FFFFFF' : '#002FA7',
                      borderColor: '#002FA7'
                    }}
                  >
                    <FolderOpen size={16} className="inline mr-2" />
                    Entire Folder
                  </button>
                </div>

                <label 
                  className="block text-sm font-semibold mb-2 uppercase tracking-wider" 
                  style={{color: '#09090B', fontFamily: 'IBM Plex Sans, sans-serif'}}
                >
                  {uploadMode === 'folder' ? 'Select Folder to Scan' : 'Select Files to Scan'}
                </label>

                {uploadMode === 'files' ? (
                  <input
                    data-testid="file-input"
                    type="file"
                    multiple
                    onChange={handleFileChange}
                    className="input"
                    accept=".js,.jsx,.ts,.tsx,.py"
                  />
                ) : (
                  <input
                    data-testid="folder-input"
                    ref={folderInputRef}
                    type="file"
                    onChange={handleFolderChange}
                    className="input"
                    {...{ webkitdirectory: "", directory: "" }}
                  />
                )}

                {files.length > 0 && (
                  <div className="mt-3 p-3" style={{background: '#F1F3F5', border: '1px solid #E4E4E7'}}>
                    <p className="text-sm font-semibold mb-2" style={{color: '#09090B', fontFamily: 'IBM Plex Mono, monospace'}}>
                      {files.length} scannable file(s) selected
                    </p>
                    <div className="max-h-32 overflow-y-auto">
                      {files.slice(0, 20).map((file, idx) => (
                        <p key={idx} className="text-xs" style={{color: '#52525B', fontFamily: 'IBM Plex Mono, monospace'}}>
                          {file.webkitRelativePath || file.name}
                        </p>
                      ))}
                      {files.length > 20 && (
                        <p className="text-xs mt-1" style={{color: '#A1A1AA'}}>...and {files.length - 20} more files</p>
                      )}
                    </div>
                  </div>
                )}
              </div>

              <div className="mb-6">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    data-testid="ai-toggle"
                    type="checkbox"
                    checked={enableAI}
                    onChange={(e) => setEnableAI(e.target.checked)}
                    className="w-5 h-5"
                  />
                  <span className="text-sm font-medium" style={{color: '#09090B'}}>Enable AI-powered fix suggestions</span>
                </label>
              </div>

              <button
                data-testid="scan-upload-button"
                type="submit"
                disabled={loading || files.length === 0}
                className="btn btn-primary"
                style={{opacity: loading || files.length === 0 ? 0.5 : 1}}
              >
                {loading ? 'SCANNING...' : uploadMode === 'folder' ? 'SCAN FOLDER' : 'SCAN FILES'}
              </button>
            </form>
          )}

          {activeTab === 'paste' && (
            <form onSubmit={handlePasteScan}>
              <div className="mb-6">
                <label 
                  className="block text-sm font-semibold mb-2 uppercase tracking-wider" 
                  style={{color: '#09090B', fontFamily: 'IBM Plex Sans, sans-serif'}}
                >
                  Filename (with extension)
                </label>
                <input
                  data-testid="paste-filename"
                  type="text"
                  value={pasteFilename}
                  onChange={(e) => setPasteFilename(e.target.value)}
                  placeholder="e.g., app.js, utils.ts, main.py"
                  className="input"
                />
              </div>

              <div className="mb-6">
                <label 
                  className="block text-sm font-semibold mb-2 uppercase tracking-wider" 
                  style={{color: '#09090B', fontFamily: 'IBM Plex Sans, sans-serif'}}
                >
                  Paste Your Code
                </label>
                <textarea
                  data-testid="paste-code-input"
                  value={pasteCode}
                  onChange={(e) => setPasteCode(e.target.value)}
                  placeholder="Paste your code here..."
                  rows={12}
                  className="input"
                  style={{
                    fontFamily: 'IBM Plex Mono, monospace',
                    fontSize: '0.875rem',
                    lineHeight: '1.6',
                    resize: 'vertical',
                    minHeight: '200px'
                  }}
                />
              </div>

              <div className="mb-6">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    data-testid="ai-toggle-paste"
                    type="checkbox"
                    checked={enableAI}
                    onChange={(e) => setEnableAI(e.target.checked)}
                    className="w-5 h-5"
                  />
                  <span className="text-sm font-medium" style={{color: '#09090B'}}>Enable AI-powered fix suggestions</span>
                </label>
              </div>

              <button
                data-testid="scan-paste-button"
                type="submit"
                disabled={loading || !pasteCode.trim()}
                className="btn btn-primary"
                style={{opacity: loading || !pasteCode.trim() ? 0.5 : 1}}
              >
                {loading ? 'SCANNING...' : 'SCAN CODE'}
              </button>
            </form>
          )}

          {activeTab === 'github' && (
            <form onSubmit={handleGitHubScan}>
              <div className="mb-6">
                <label 
                  className="block text-sm font-semibold mb-2 uppercase tracking-wider" 
                  style={{color: '#09090B', fontFamily: 'IBM Plex Sans, sans-serif'}}
                >
                  Repository (owner/repo)
                </label>
                <input
                  data-testid="repo-input"
                  type="text"
                  value={repo}
                  onChange={(e) => setRepo(e.target.value)}
                  placeholder="e.g., facebook/react"
                  className="input"
                />
              </div>

              <div className="mb-6">
                <label 
                  className="block text-sm font-semibold mb-2 uppercase tracking-wider" 
                  style={{color: '#09090B', fontFamily: 'IBM Plex Sans, sans-serif'}}
                >
                  PR Number
                </label>
                <input
                  data-testid="pr-number-input"
                  type="number"
                  value={prNumber}
                  onChange={(e) => setPrNumber(e.target.value)}
                  placeholder="e.g., 123"
                  className="input"
                />
              </div>

              <div className="mb-6">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    data-testid="ai-toggle-github"
                    type="checkbox"
                    checked={enableAI}
                    onChange={(e) => setEnableAI(e.target.checked)}
                    className="w-5 h-5"
                  />
                  <span className="text-sm font-medium" style={{color: '#09090B'}}>Enable AI-powered fix suggestions</span>
                </label>
              </div>

              <button
                data-testid="scan-github-button"
                type="submit"
                disabled={loading || !repo || !prNumber}
                className="btn btn-primary"
                style={{opacity: loading || !repo || !prNumber ? 0.5 : 1}}
              >
                {loading ? 'SCANNING...' : 'SCAN PR'}
              </button>
            </form>
          )}
        </div>

        <div className="mt-8 text-center">
          <button
            data-testid="view-history-button"
            onClick={() => navigate('/history')}
            className="btn btn-secondary"
          >
            VIEW SCAN HISTORY
          </button>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
