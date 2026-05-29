import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { lazy, Suspense, useEffect } from 'react'
import Landing from './pages/Landing'
import BirthDetails from './pages/BirthDetails'
import Chat from './pages/Chat'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const ChartExplorer = lazy(() => import('./pages/ChartExplorer'))
const DashaView = lazy(() => import('./pages/DashaView'))
const Compatibility = lazy(() => import('./pages/Compatibility'))

function KeepAlive() {
  useEffect(() => {
    // Ping /api/health every 10 minutes to prevent Render.com cold starts
    const ping = () => fetch(`${BASE}/api/health`).catch(() => {})
    ping() // Initial ping
    const interval = setInterval(ping, 10 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])
  return null
}

function LoadingFallback() {
  return <div style={{ height: '100vh', background: '#080818', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#9090C0', fontFamily: 'Cinzel, serif', letterSpacing: '0.2em', fontSize: '0.85rem' }}>Loading...</div>
}

export default function App() {
  return (
    <BrowserRouter>
      <KeepAlive />
      <Suspense fallback={<LoadingFallback />}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/birth" element={<BirthDetails />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/chart" element={<ChartExplorer />} />
          <Route path="/dasha" element={<DashaView />} />
          <Route path="/compatibility" element={<Compatibility />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}