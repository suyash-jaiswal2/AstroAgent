import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({ baseURL: BASE, timeout: 30000 })

export const createSession = () => api.post('/api/sessions').then(r => r.data)

export const saveBirthDetails = (sessionId: string, details: Record<string, unknown>) =>
  api.post(`/api/sessions/${sessionId}/birth`, details).then(r => r.data)

export const getSession = (sessionId: string) =>
  api.get(`/api/sessions/${sessionId}`).then(r => r.data)

export const getPanchang = (date: string, lat: number, lon: number, tz: string) =>
  api.get(`/api/panchang`, { params: { date, lat, lon, tz } }).then(r => r.data)

export const getDashas = (sessionId: string) =>
  api.get(`/api/sessions/${sessionId}/dashas`).then(r => r.data)

export const getYogas = (sessionId: string) =>
  api.get(`/api/sessions/${sessionId}/yogas`).then(r => r.data)

export const CHAT_STREAM_URL = (sessionId: string, message: string) =>
  `${BASE}/api/chat/stream`

export const buildSSEBody = (message: string, sessionId: string) =>
  JSON.stringify({ message, session_id: sessionId })