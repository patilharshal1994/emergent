import React, { useState } from 'react';
import { CaretDown, CaretUp } from '@phosphor-icons/react';

const IssueCard = ({ issue, index }) => {
  const [expanded, setExpanded] = useState(false);

  const getSeverityColor = (severity) => {
    const colors = {
      critical: '#FF2B2B',
      high: '#FFD500',
      medium: '#002FA7',
      low: '#00C853'
    };
    return colors[severity] || '#002FA7';
  };

  return (
    <div
      data-testid={`issue-card-${index}`}
      className={`card severity-${issue.severity}`}
      style={{borderLeftWidth: '4px', borderLeftColor: getSeverityColor(issue.severity)}}
    >
      <div 
        className="flex items-start justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <span className={`badge badge-${issue.severity}`}>
              {issue.severity}
            </span>
            <h3 
              className="text-lg font-semibold"
              style={{fontFamily: 'IBM Plex Sans, sans-serif'}}
            >
              {issue.type.replace(/_/g, ' ').toUpperCase()}
            </h3>
          </div>

          <p className="text-sm mb-2" style={{color: '#52525B'}}>
            {issue.message}
          </p>

          <div className="flex gap-4 text-xs" style={{fontFamily: 'IBM Plex Mono, monospace', color: '#A1A1AA'}}>
            <span><strong>File:</strong> {issue.file}</span>
            <span><strong>Line:</strong> {issue.line}</span>
            {issue.rule_id && <span><strong>Rule:</strong> {issue.rule_id}</span>}
          </div>
        </div>

        <button
          data-testid={`expand-button-${index}`}
          className="ml-4"
        >
          {expanded ? (
            <CaretUp size={24} color="#002FA7" weight="bold" />
          ) : (
            <CaretDown size={24} color="#002FA7" weight="bold" />
          )}
        </button>
      </div>

      {expanded && issue.ai_suggestion && (
        <div 
          data-testid={`ai-suggestion-${index}`}
          className="mt-4 pt-4 border-t"
          style={{borderColor: '#E4E4E7'}}
        >
          <h4 
            className="text-sm font-bold uppercase tracking-wider mb-2" 
            style={{color: '#002FA7', fontFamily: 'IBM Plex Sans, sans-serif'}}
          >
            AI-POWERED FIX SUGGESTION
          </h4>
          <div 
            className="p-4"
            style={{
              background: '#F1F3F5',
              fontFamily: 'IBM Plex Mono, monospace',
              fontSize: '0.875rem',
              lineHeight: '1.6',
              color: '#09090B'
            }}
          >
            {issue.ai_suggestion}
          </div>
        </div>
      )}
    </div>
  );
};

export default IssueCard;