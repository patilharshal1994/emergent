import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import '@/App.css';
import Dashboard from './pages/Dashboard';
import ScanResults from './pages/ScanResults';
import History from './pages/History';
import Analytics from './pages/Analytics';
import Rules from './pages/Rules';
import CICD from './pages/CICD';

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/results/:scanId" element={<ScanResults />} />
          <Route path="/history" element={<History />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/rules" element={<Rules />} />
          <Route path="/cicd" element={<CICD />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
