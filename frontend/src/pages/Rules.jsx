import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, Plus, Trash, ToggleLeft, ToggleRight, Export, UploadSimple } from '@phosphor-icons/react';
import Header from '../components/Header';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SEVERITY_OPTIONS = ['critical', 'high', 'medium', 'low'];
const CATEGORY_LABELS = {
  'code-quality': 'Code Quality',
  'security': 'Security',
  'typescript': 'TypeScript',
  'custom': 'Custom',
  'eslint': 'ESLint'
};

const Rules = () => {
  const navigate = useNavigate();
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newRule, setNewRule] = useState({
    name: '',
    description: '',
    severity: 'medium',
    pattern: '',
    file_types: ['.js', '.jsx', '.ts', '.tsx'],
    category: 'custom'
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const importInputRef = useRef(null);

  useEffect(() => {
    fetchRules();
  }, []);

  const fetchRules = async () => {
    try {
      const response = await axios.get(`${API}/rules`);
      setRules(response.data.rules);
    } catch (err) {
      console.error('Error fetching rules:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleRule = async (rule_id, currentEnabled) => {
    try {
      await axios.put(`${API}/rules/${rule_id}`, { enabled: !currentEnabled });
      setRules(prev => prev.map(r => r.rule_id === rule_id ? { ...r, enabled: !currentEnabled } : r));
      setSuccess(`Rule ${!currentEnabled ? 'enabled' : 'disabled'} successfully`);
      setTimeout(() => setSuccess(''), 2000);
    } catch (err) {
      setError('Error updating rule');
      setTimeout(() => setError(''), 3000);
    }
  };

  const changeSeverity = async (rule_id, newSeverity) => {
    try {
      await axios.put(`${API}/rules/${rule_id}`, { severity: newSeverity });
      setRules(prev => prev.map(r => r.rule_id === rule_id ? { ...r, severity: newSeverity } : r));
      setSuccess('Severity updated successfully');
      setTimeout(() => setSuccess(''), 2000);
    } catch (err) {
      setError('Error updating severity');
      setTimeout(() => setError(''), 3000);
    }
  };

  const deleteRule = async (rule_id) => {
    try {
      await axios.delete(`${API}/rules/${rule_id}`);
      setRules(prev => prev.filter(r => r.rule_id !== rule_id));
      setSuccess('Rule deleted successfully');
      setTimeout(() => setSuccess(''), 2000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error deleting rule');
      setTimeout(() => setError(''), 3000);
    }
  };

  const createRule = async (e) => {
    e.preventDefault();
    if (!newRule.name || !newRule.pattern) {
      setError('Name and pattern are required');
      return;
    }

    try {
      const response = await axios.post(`${API}/rules`, newRule);
      setSuccess('Custom rule created!');
      setShowCreate(false);
      setNewRule({ name: '', description: '', severity: 'medium', pattern: '', file_types: ['.js', '.jsx', '.ts', '.tsx'], category: 'custom' });
      fetchRules();
      setTimeout(() => setSuccess(''), 2000);
    } catch (err) {
      setError('Error creating rule');
      setTimeout(() => setError(''), 3000);
    }
  };

  const exportRules = async () => {
    try {
      const response = await axios.get(`${API}/rules/export`);
      const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `qualitygate-rules-${new Date().toISOString().slice(0,10)}.json`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      setSuccess('Rules exported successfully');
      setTimeout(() => setSuccess(''), 2000);
    } catch (err) {
      setError('Error exporting rules');
      setTimeout(() => setError(''), 3000);
    }
  };

  const importRules = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API}/rules/import`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setSuccess(`${response.data.message}`);
      fetchRules();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error importing rules');
      setTimeout(() => setError(''), 3000);
    }

    // Reset file input
    if (importInputRef.current) importInputRef.current.value = '';
  };

  const getSeverityBadgeClass = (severity) => `badge badge-${severity}`;

  const groupedRules = rules.reduce((acc, rule) => {
    const cat = rule.category || 'general';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(rule);
    return acc;
  }, {});

  if (loading) {
    return (
      <div className="min-h-screen bg-white"><Header /><div className="loading"><div className="spinner"></div></div></div>
    );
  }

  return (
    <div className="min-h-screen" style={{ background: '#F1F3F5' }}>
      <Header />

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-8">
          <button data-testid="back-button" onClick={() => navigate('/')} className="btn btn-secondary mb-4">
            <ArrowLeft size={20} className="inline mr-2" /> BACK
          </button>
          <div className="flex items-center justify-between">
            <div>
              <h1 data-testid="rules-title" className="text-4xl sm:text-5xl font-black tracking-tighter" style={{ fontFamily: 'IBM Plex Sans, sans-serif' }}>
                SCANNING RULES
              </h1>
              <p className="text-base leading-relaxed mt-4" style={{ color: '#52525B' }}>
                Configure which rules to enforce. Toggle rules on/off, adjust severity, or create custom pattern-based rules.
              </p>
            </div>
            <div className="flex gap-3 items-start flex-shrink-0">
              <button
                data-testid="export-rules-button"
                onClick={exportRules}
                className="btn btn-secondary"
              >
                <Export size={20} className="inline mr-2" />
                EXPORT
              </button>
              <label
                data-testid="import-rules-button"
                className="btn btn-secondary cursor-pointer inline-flex items-center"
              >
                <UploadSimple size={20} className="inline mr-2" />
                IMPORT
                <input
                  ref={importInputRef}
                  type="file"
                  accept=".json"
                  onChange={importRules}
                  className="hidden"
                />
              </label>
              <button
                data-testid="create-rule-button"
                onClick={() => setShowCreate(!showCreate)}
                className="btn btn-primary"
              >
                <Plus size={20} className="inline mr-2" />
                {showCreate ? 'CANCEL' : 'NEW RULE'}
              </button>
            </div>
          </div>
        </div>

        {error && (
          <div className="border-l-4 p-4 mb-6" style={{ borderLeftColor: '#FF2B2B', background: '#FEF2F2' }} data-testid="rules-error">
            <p className="text-sm" style={{ color: '#FF2B2B' }}>{error}</p>
          </div>
        )}

        {success && (
          <div className="border-l-4 p-4 mb-6" style={{ borderLeftColor: '#00C853', background: '#F0FFF4' }} data-testid="rules-success">
            <p className="text-sm" style={{ color: '#00C853' }}>{success}</p>
          </div>
        )}

        {/* Create New Rule Form */}
        {showCreate && (
          <div className="bg-white border-2 p-6 mb-8" style={{ borderColor: '#002FA7' }} data-testid="create-rule-form">
            <h3 className="text-xl font-semibold tracking-tight mb-4" style={{ fontFamily: 'IBM Plex Sans, sans-serif' }}>
              CREATE CUSTOM RULE
            </h3>
            <form onSubmit={createRule}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-widest mb-1" style={{ color: '#A1A1AA' }}>Rule Name</label>
                  <input
                    data-testid="rule-name-input"
                    type="text"
                    value={newRule.name}
                    onChange={(e) => setNewRule(p => ({ ...p, name: e.target.value }))}
                    placeholder="e.g., No TODO Comments"
                    className="input"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-widest mb-1" style={{ color: '#A1A1AA' }}>Severity</label>
                  <select
                    data-testid="rule-severity-select"
                    value={newRule.severity}
                    onChange={(e) => setNewRule(p => ({ ...p, severity: e.target.value }))}
                    className="input"
                  >
                    {SEVERITY_OPTIONS.map(s => <option key={s} value={s}>{s.toUpperCase()}</option>)}
                  </select>
                </div>
              </div>

              <div className="mb-4">
                <label className="block text-xs font-bold uppercase tracking-widest mb-1" style={{ color: '#A1A1AA' }}>Description</label>
                <input
                  data-testid="rule-description-input"
                  type="text"
                  value={newRule.description}
                  onChange={(e) => setNewRule(p => ({ ...p, description: e.target.value }))}
                  placeholder="Brief description of what this rule checks"
                  className="input"
                />
              </div>

              <div className="mb-4">
                <label className="block text-xs font-bold uppercase tracking-widest mb-1" style={{ color: '#A1A1AA' }}>Regex Pattern</label>
                <input
                  data-testid="rule-pattern-input"
                  type="text"
                  value={newRule.pattern}
                  onChange={(e) => setNewRule(p => ({ ...p, pattern: e.target.value }))}
                  placeholder="e.g., TODO|FIXME|HACK"
                  className="input"
                  style={{ fontFamily: 'IBM Plex Mono, monospace' }}
                />
                <p className="text-xs mt-1" style={{ color: '#A1A1AA' }}>
                  Enter a regular expression pattern. Each line matching this pattern will be flagged.
                </p>
              </div>

              <div className="mb-4">
                <label className="block text-xs font-bold uppercase tracking-widest mb-1" style={{ color: '#A1A1AA' }}>File Types</label>
                <div className="flex gap-3 flex-wrap">
                  {['.js', '.jsx', '.ts', '.tsx', '.py'].map(ext => (
                    <label key={ext} className="flex items-center gap-1 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={newRule.file_types.includes(ext)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setNewRule(p => ({ ...p, file_types: [...p.file_types, ext] }));
                          } else {
                            setNewRule(p => ({ ...p, file_types: p.file_types.filter(t => t !== ext) }));
                          }
                        }}
                        className="w-4 h-4"
                      />
                      <span className="text-sm" style={{ fontFamily: 'IBM Plex Mono, monospace' }}>{ext}</span>
                    </label>
                  ))}
                </div>
              </div>

              <button data-testid="submit-rule-button" type="submit" className="btn btn-primary">
                CREATE RULE
              </button>
            </form>
          </div>
        )}

        {/* Rules List by Category */}
        {Object.entries(groupedRules).map(([category, categoryRules]) => (
          <div key={category} className="mb-8">
            <h2 className="text-xl font-bold tracking-tight mb-4 uppercase" style={{ fontFamily: 'IBM Plex Sans, sans-serif', color: '#002FA7' }}>
              {CATEGORY_LABELS[category] || category}
            </h2>

            <div className="space-y-3">
              {categoryRules.map((rule, index) => (
                <div
                  key={rule.rule_id}
                  data-testid={`rule-item-${rule.rule_id}`}
                  className="card flex items-center justify-between"
                  style={{ opacity: rule.enabled ? 1 : 0.5 }}
                >
                  <div className="flex items-center gap-4 flex-1">
                    <button
                      data-testid={`toggle-${rule.rule_id}`}
                      onClick={() => toggleRule(rule.rule_id, rule.enabled)}
                      className="flex-shrink-0"
                    >
                      {rule.enabled ? (
                        <ToggleRight size={32} weight="fill" color="#002FA7" />
                      ) : (
                        <ToggleLeft size={32} weight="fill" color="#A1A1AA" />
                      )}
                    </button>

                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="text-base font-semibold" style={{ fontFamily: 'IBM Plex Sans, sans-serif' }}>
                          {rule.name}
                        </h4>
                        <span className={getSeverityBadgeClass(rule.severity)}>{rule.severity}</span>
                      </div>
                      <p className="text-sm" style={{ color: '#52525B' }}>{rule.description}</p>
                      {rule.pattern && (
                        <p className="text-xs mt-1" style={{ color: '#A1A1AA', fontFamily: 'IBM Plex Mono, monospace' }}>
                          Pattern: {rule.pattern}
                        </p>
                      )}
                      <p className="text-xs mt-1" style={{ color: '#A1A1AA', fontFamily: 'IBM Plex Mono, monospace' }}>
                        {rule.rule_id}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 flex-shrink-0">
                    <select
                      data-testid={`severity-select-${rule.rule_id}`}
                      value={rule.severity}
                      onChange={(e) => changeSeverity(rule.rule_id, e.target.value)}
                      className="text-xs px-2 py-1 border"
                      style={{ borderColor: '#E4E4E7', fontFamily: 'IBM Plex Mono, monospace' }}
                    >
                      {SEVERITY_OPTIONS.map(s => <option key={s} value={s}>{s.toUpperCase()}</option>)}
                    </select>

                    {rule.category === 'custom' && (
                      <button
                        data-testid={`delete-${rule.rule_id}`}
                        onClick={() => deleteRule(rule.rule_id)}
                        className="p-1 hover:bg-red-50 transition-colors"
                      >
                        <Trash size={20} color="#FF2B2B" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Rules;
