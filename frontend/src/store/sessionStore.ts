import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface BirthDetails {
  name: string
  date: string
  time: string | null
  place: string
  latitude?: number
  longitude?: number
  timezone?: string
  time_unknown?: boolean
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  toolCalls?: string[]
  timestamp: number
}

export interface ToolCallState {
  tool: string
  status: 'running' | 'done' | 'error'
  step: number
}

export interface OrbMood {
  primaryColor: string
  secondaryColor: string
  mood: 'favorable' | 'introspective' | 'dynamic' | 'spiritual' | 'neutral' | 'communicative'
  pulseSpeed: 'slow' | 'medium' | 'fast'
}

const DEFAULT_ORB: OrbMood = {
  primaryColor: '#3D7FBF',
  secondaryColor: '#1a3d5c',
  mood: 'neutral',
  pulseSpeed: 'slow',
}

interface SessionStore {
  sessionId: string | null
  birthDetails: BirthDetails | null
  natalChart: Record<string, unknown> | null
  messages: ChatMessage[]
  isStreaming: boolean
  currentToolCalls: ToolCallState[]
  streamingContent: string
  orbMood: OrbMood

  // Actions
  setSessionId: (id: string) => void
  setBirthDetails: (d: BirthDetails) => void
  setNatalChart: (c: Record<string, unknown>) => void
  addUserMessage: (text: string) => string
  startAssistantMessage: () => string
  addToken: (text: string) => void
  finalizeMessage: (meta: Record<string, unknown>) => void
  setToolCall: (tc: Partial<ToolCallState> & { tool: string }) => void
  clearActiveTools: () => void
  setOrbMood: (mood: Partial<OrbMood>) => void
  reset: () => void
}

export const useSessionStore = create<SessionStore>()(
  persist(
    (set, get) => ({
      sessionId: null,
      birthDetails: null,
      natalChart: null,
      messages: [],
      isStreaming: false,
      currentToolCalls: [],
      streamingContent: '',
      orbMood: DEFAULT_ORB,

      setSessionId: (id) => set({ sessionId: id }),
      setBirthDetails: (d) => set({ birthDetails: d }),
      setNatalChart: (c) => set({ natalChart: c }),

      addUserMessage: (text) => {
        const id = `u_${Date.now()}`
        set((s) => ({
          messages: [...s.messages, { id, role: 'user', content: text, timestamp: Date.now() }],
        }))
        return id
      },

      startAssistantMessage: () => {
        const id = `a_${Date.now()}`
        set({ isStreaming: true, streamingContent: '' })
        return id
      },

      addToken: (text) => set((s) => ({ streamingContent: s.streamingContent + text })),

      finalizeMessage: (meta) => {
        const { streamingContent } = get()
        if (!streamingContent.trim()) {
          set({ isStreaming: false, streamingContent: '', currentToolCalls: [] })
          return
        }
        const id = `a_${Date.now()}`
        set((s) => ({
          messages: [
            ...s.messages,
            {
              id,
              role: 'assistant',
              content: streamingContent,
              toolCalls: meta.tool_calls as string[] | undefined,
              timestamp: Date.now(),
            },
          ],
          isStreaming: false,
          streamingContent: '',
          currentToolCalls: [],
        }))
      },

      setToolCall: (tc) =>
        set((s) => {
          const existing = s.currentToolCalls.findIndex((t) => t.tool === tc.tool)
          if (existing >= 0) {
            const updated = [...s.currentToolCalls]
            updated[existing] = { ...updated[existing], ...tc }
            return { currentToolCalls: updated }
          }
          return { currentToolCalls: [...s.currentToolCalls, { status: 'running' as const, step: 0, ...tc }] }
        }),

      clearActiveTools: () => set({ currentToolCalls: [] }),
      setOrbMood: (mood) => set((s) => ({ orbMood: { ...s.orbMood, ...mood } })),
      reset: () => set({ messages: [], birthDetails: null, natalChart: null, sessionId: null }),
    }),
    {
      name: 'astroagent-session',
      partialize: (s) => ({
        sessionId: s.sessionId,
        birthDetails: s.birthDetails,
        natalChart: s.natalChart,
        messages: s.messages.slice(-50), // Keep last 50 messages
      }),
    }
  )
)