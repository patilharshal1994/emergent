import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield } from '@phosphor-icons/react';

const Header = () => {
  const navigate = useNavigate();

  return (
    <header 
      className="border-b" 
      style={{borderColor: '#09090B', background: '#FFFFFF'}}
      data-testid="main-header"
    >
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between py-6">
          <div 
            className="flex items-center gap-3 cursor-pointer" 
            onClick={() => navigate('/')}
            data-testid="logo"
          >
            <Shield size={40} weight="duotone" color="#002FA7" />
            <div>
              <h1 
                className="text-2xl font-black tracking-tighter" 
                style={{fontFamily: 'IBM Plex Sans, sans-serif', color: '#002FA7'}}
              >
                QUALITYGATE
              </h1>
              <p className="text-xs tracking-widest" style={{color: '#52525B'}}>CODE SCANNER</p>
            </div>
          </div>

          <nav className="flex gap-4">
            <button
              data-testid="nav-scan"
              onClick={() => navigate('/')}
              className="text-sm font-semibold uppercase tracking-wider hover:text-primary transition-colors"
              style={{fontFamily: 'IBM Plex Sans, sans-serif', color: '#09090B'}}
            >
              SCAN
            </button>
            <button
              data-testid="nav-history"
              onClick={() => navigate('/history')}
              className="text-sm font-semibold uppercase tracking-wider hover:text-primary transition-colors"
              style={{fontFamily: 'IBM Plex Sans, sans-serif', color: '#09090B'}}
            >
              HISTORY
            </button>
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;