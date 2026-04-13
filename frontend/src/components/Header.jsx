import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Shield, List, X } from '@phosphor-icons/react';

const NAV_ITEMS = [
  { path: '/', label: 'SCAN' },
  { path: '/history', label: 'HISTORY' },
  { path: '/analytics', label: 'ANALYTICS' },
  { path: '/rules', label: 'RULES' },
  { path: '/cicd', label: 'CI/CD' },
];

const Header = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header
      className="border-b"
      style={{ borderColor: '#09090B', background: '#FFFFFF' }}
      data-testid="main-header"
    >
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between py-4">
          <div
            className="flex items-center gap-3 cursor-pointer"
            onClick={() => navigate('/')}
            data-testid="logo"
          >
            <Shield size={36} weight="duotone" color="#002FA7" />
            <div>
              <h1
                className="text-xl font-black tracking-tighter"
                style={{ fontFamily: 'IBM Plex Sans, sans-serif', color: '#002FA7' }}
              >
                QUALITYGATE
              </h1>
              <p className="text-xs tracking-widest" style={{ color: '#52525B' }}>CODE SCANNER</p>
            </div>
          </div>

          {/* Desktop Nav */}
          <nav className="hidden md:flex gap-1">
            {NAV_ITEMS.map(item => {
              const isActive = location.pathname === item.path;
              return (
                <button
                  key={item.path}
                  data-testid={`nav-${item.label.toLowerCase().replace('/', '')}`}
                  onClick={() => navigate(item.path)}
                  className="text-xs font-semibold uppercase tracking-wider px-3 py-2 transition-all"
                  style={{
                    fontFamily: 'IBM Plex Sans, sans-serif',
                    color: isActive ? '#FFFFFF' : '#09090B',
                    background: isActive ? '#002FA7' : 'transparent',
                  }}
                >
                  {item.label}
                </button>
              );
            })}
          </nav>

          {/* Mobile Menu Toggle */}
          <button
            className="md:hidden"
            data-testid="mobile-menu-toggle"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? <X size={28} color="#09090B" /> : <List size={28} color="#09090B" />}
          </button>
        </div>

        {/* Mobile Nav */}
        {mobileOpen && (
          <nav className="md:hidden pb-4 border-t" style={{ borderColor: '#E4E4E7' }} data-testid="mobile-nav">
            {NAV_ITEMS.map(item => {
              const isActive = location.pathname === item.path;
              return (
                <button
                  key={item.path}
                  onClick={() => { navigate(item.path); setMobileOpen(false); }}
                  className="block w-full text-left text-sm font-semibold uppercase tracking-wider px-3 py-3 transition-all"
                  style={{
                    fontFamily: 'IBM Plex Sans, sans-serif',
                    color: isActive ? '#002FA7' : '#09090B',
                    borderBottom: '1px solid #E4E4E7',
                  }}
                >
                  {item.label}
                </button>
              );
            })}
          </nav>
        )}
      </div>
    </header>
  );
};

export default Header;
