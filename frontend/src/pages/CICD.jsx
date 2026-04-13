import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, Copy, Check, GithubLogo, Gear, ToggleLeft, ToggleRight } from '@phosphor-icons/react';
import Header from '../components/Header';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CICD = () => {
  const navigate = useNavigate();
  const [config, setConfig] = useState(null);
  const [yamlContent, setYamlContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [copiedField, setCopiedField] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchConfig();
    fetchYaml();
  }, []);

  const fetchConfig = async () => {
    try {
      const response = await axios.get(`${API}/webhook/config`);
      setConfig(response.data);
    } catch (err) {
      setError('Error fetching webhook config');
    } finally {
      setLoading(false);
    }
  };

  const fetchYaml = async () => {
    try {
      const response = await axios.get(`${API}/webhook/github-actions-yaml`);
      setYamlContent(response.data.yaml);
    } catch (err) {
      console.error('Error fetching YAML:', err);
    }
  };

  const toggleConfig = async (field) => {
    try {
      const update = { [field]: !config[field] };
      const response = await axios.put(`${API}/webhook/config`, update);
      setConfig(response.data);
      setSuccess(`${field === 'enabled' ? 'Webhook' : field === 'auto_scan' ? 'Auto-scan' : 'AI suggestions'} ${response.data[field] ? 'enabled' : 'disabled'}`);
      setTimeout(() => setSuccess(''), 2000);
    } catch (err) {
      setError('Error updating config');
      setTimeout(() => setError(''), 3000);
    }
  };

  const copyToClipboard = (text, field) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(''), 2000);
  };

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
          <h1 data-testid="cicd-title" className="text-4xl sm:text-5xl font-black tracking-tighter" style={{ fontFamily: 'IBM Plex Sans, sans-serif' }}>
            CI/CD INTEGRATION
          </h1>
          <p className="text-base leading-relaxed mt-4" style={{ color: '#52525B' }}>
            Automate code quality scans on every PR using GitHub Actions webhooks.
          </p>
        </div>

        {error && (
          <div className="border-l-4 p-4 mb-6" style={{ borderLeftColor: '#FF2B2B', background: '#FEF2F2' }}>
            <p className="text-sm" style={{ color: '#FF2B2B' }}>{error}</p>
          </div>
        )}

        {success && (
          <div className="border-l-4 p-4 mb-6" style={{ borderLeftColor: '#00C853', background: '#F0FFF4' }}>
            <p className="text-sm" style={{ color: '#00C853' }}>{success}</p>
          </div>
        )}

        {/* Webhook Config */}
        {config && (
          <div className="bg-white border p-6 mb-8" style={{ borderColor: '#E4E4E7' }} data-testid="webhook-config-section">
            <h3 className="text-xl font-semibold tracking-tight mb-6" style={{ fontFamily: 'IBM Plex Sans, sans-serif' }}>
              <Gear size={24} className="inline mr-2" color="#002FA7" />
              WEBHOOK CONFIGURATION
            </h3>

            {/* Toggle Controls */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="flex items-center justify-between p-4 border" style={{ borderColor: '#E4E4E7' }}>
                <div>
                  <p className="text-sm font-semibold" style={{ fontFamily: 'IBM Plex Sans, sans-serif' }}>Webhook Enabled</p>
                  <p className="text-xs" style={{ color: '#A1A1AA' }}>Receive GitHub events</p>
                </div>
                <button data-testid="toggle-enabled" onClick={() => toggleConfig('enabled')}>
                  {config.enabled ? <ToggleRight size={32} weight="fill" color="#002FA7" /> : <ToggleLeft size={32} weight="fill" color="#A1A1AA" />}
                </button>
              </div>

              <div className="flex items-center justify-between p-4 border" style={{ borderColor: '#E4E4E7' }}>
                <div>
                  <p className="text-sm font-semibold" style={{ fontFamily: 'IBM Plex Sans, sans-serif' }}>Auto-Scan PRs</p>
                  <p className="text-xs" style={{ color: '#A1A1AA' }}>Scan on PR creation</p>
                </div>
                <button data-testid="toggle-auto-scan" onClick={() => toggleConfig('auto_scan')}>
                  {config.auto_scan ? <ToggleRight size={32} weight="fill" color="#002FA7" /> : <ToggleLeft size={32} weight="fill" color="#A1A1AA" />}
                </button>
              </div>

              <div className="flex items-center justify-between p-4 border" style={{ borderColor: '#E4E4E7' }}>
                <div>
                  <p className="text-sm font-semibold" style={{ fontFamily: 'IBM Plex Sans, sans-serif' }}>AI Suggestions</p>
                  <p className="text-xs" style={{ color: '#A1A1AA' }}>Include AI fix tips</p>
                </div>
                <button data-testid="toggle-ai" onClick={() => toggleConfig('enable_ai')}>
                  {config.enable_ai ? <ToggleRight size={32} weight="fill" color="#002FA7" /> : <ToggleLeft size={32} weight="fill" color="#A1A1AA" />}
                </button>
              </div>
            </div>

            {/* Webhook URL & Secret */}
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase tracking-widest mb-1" style={{ color: '#A1A1AA' }}>Webhook URL</label>
                <div className="flex items-center gap-2">
                  <input
                    data-testid="webhook-url"
                    type="text"
                    readOnly
                    value={config.webhook_url}
                    className="input flex-1"
                    style={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: '0.875rem' }}
                  />
                  <button
                    data-testid="copy-url"
                    onClick={() => copyToClipboard(config.webhook_url, 'url')}
                    className="btn btn-secondary px-3 py-2"
                  >
                    {copiedField === 'url' ? <Check size={20} color="#00C853" /> : <Copy size={20} />}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-widest mb-1" style={{ color: '#A1A1AA' }}>Webhook Secret</label>
                <div className="flex items-center gap-2">
                  <input
                    data-testid="webhook-secret"
                    type="text"
                    readOnly
                    value={config.webhook_secret}
                    className="input flex-1"
                    style={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: '0.875rem' }}
                  />
                  <button
                    data-testid="copy-secret"
                    onClick={() => copyToClipboard(config.webhook_secret, 'secret')}
                    className="btn btn-secondary px-3 py-2"
                  >
                    {copiedField === 'secret' ? <Check size={20} color="#00C853" /> : <Copy size={20} />}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Setup Steps */}
        <div className="bg-white border p-6 mb-8" style={{ borderColor: '#E4E4E7' }} data-testid="setup-steps">
          <h3 className="text-xl font-semibold tracking-tight mb-6" style={{ fontFamily: 'IBM Plex Sans, sans-serif' }}>
            <GithubLogo size={24} className="inline mr-2" color="#002FA7" />
            SETUP INSTRUCTIONS
          </h3>

          <div className="space-y-6">
            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 flex items-center justify-center font-bold text-white" style={{ background: '#002FA7', fontFamily: 'IBM Plex Mono' }}>1</div>
              <div>
                <h4 className="font-semibold mb-1" style={{ fontFamily: 'IBM Plex Sans, sans-serif' }}>Add Webhook Secret to GitHub</h4>
                <p className="text-sm" style={{ color: '#52525B' }}>
                  Go to your repository Settings &gt; Secrets &gt; Actions &gt; New Repository Secret.
                  Add a secret named <code style={{ background: '#F1F3F5', padding: '2px 6px', fontFamily: 'IBM Plex Mono' }}>QUALITYGATE_WEBHOOK_SECRET</code> with
                  the value shown above.
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 flex items-center justify-center font-bold text-white" style={{ background: '#002FA7', fontFamily: 'IBM Plex Mono' }}>2</div>
              <div>
                <h4 className="font-semibold mb-1" style={{ fontFamily: 'IBM Plex Sans, sans-serif' }}>Create GitHub Actions Workflow</h4>
                <p className="text-sm mb-2" style={{ color: '#52525B' }}>
                  Create a file at <code style={{ background: '#F1F3F5', padding: '2px 6px', fontFamily: 'IBM Plex Mono' }}>.github/workflows/quality-gate.yml</code> in
                  your repository with the YAML configuration below.
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 flex items-center justify-center font-bold text-white" style={{ background: '#002FA7', fontFamily: 'IBM Plex Mono' }}>3</div>
              <div>
                <h4 className="font-semibold mb-1" style={{ fontFamily: 'IBM Plex Sans, sans-serif' }}>Open a Pull Request</h4>
                <p className="text-sm" style={{ color: '#52525B' }}>
                  When a PR is opened, the workflow will trigger and send the code to CodeQuality Gate for automatic scanning.
                  Results appear in your scan history.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* GitHub Actions YAML */}
        {yamlContent && (
          <div className="bg-white border p-6" style={{ borderColor: '#E4E4E7' }} data-testid="yaml-section">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold tracking-tight" style={{ fontFamily: 'IBM Plex Sans, sans-serif' }}>
                GITHUB ACTIONS WORKFLOW YAML
              </h3>
              <button
                data-testid="copy-yaml"
                onClick={() => copyToClipboard(yamlContent, 'yaml')}
                className="btn btn-primary"
              >
                {copiedField === 'yaml' ? (
                  <><Check size={20} className="inline mr-2" /> COPIED</>
                ) : (
                  <><Copy size={20} className="inline mr-2" /> COPY YAML</>
                )}
              </button>
            </div>

            <pre
              data-testid="yaml-content"
              className="p-4 overflow-x-auto text-sm leading-relaxed"
              style={{
                background: '#09090B',
                color: '#00C853',
                fontFamily: 'IBM Plex Mono, monospace',
                borderRadius: 0,
                maxHeight: '400px',
                overflowY: 'auto'
              }}
            >
              {yamlContent}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};

export default CICD;
