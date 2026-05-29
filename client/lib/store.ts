/**
 * Zustand store for global application state.
 */

import { create } from "zustand";
import type { User, BirthProfile, Conversation, Message } from "./api";

interface AppState {
  // Auth
  user: User | null;
  setUser: (user: User | null) => void;

  // Active profile (the one being chatted about)
  activeProfile: BirthProfile | null;
  setActiveProfile: (profile: BirthProfile | null) => void;

  // Profiles (family vault)
  profiles: BirthProfile[];
  setProfiles: (profiles: BirthProfile[]) => void;

  // Conversations
  conversations: Conversation[];
  setConversations: (conversations: Conversation[]) => void;
  activeConversationId: string | null;
  setActiveConversationId: (id: string | null) => void;

  // Chat messages
  currentMessages: Message[];
  setCurrentMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;

  // Streaming state
  isStreaming: boolean;
  setStreaming: (streaming: boolean) => void;
  streamingContent: string;
  setStreamingContent: (content: string) => void;
  appendStreamingContent: (chunk: string) => void;

  // Tool activity
  activeTool: { name: string; display: string } | null;
  setActiveTool: (tool: { name: string; display: string } | null) => void;

  // Language
  language: string;
  setLanguage: (lang: string) => void;

  // Sidebar
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  toggleSidebar: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Auth
  user: null,
  setUser: (user) => set({ user }),

  // Active profile
  activeProfile: null,
  setActiveProfile: (profile) => set({ activeProfile: profile }),

  // Profiles
  profiles: [],
  setProfiles: (profiles) => set({ profiles }),

  // Conversations
  conversations: [],
  setConversations: (conversations) => set({ conversations }),
  activeConversationId: null,
  setActiveConversationId: (id) => set({ activeConversationId: id }),

  // Chat
  currentMessages: [],
  setCurrentMessages: (messages) => set({ currentMessages: messages }),
  addMessage: (message) =>
    set((state) => ({
      currentMessages: [...state.currentMessages, message],
    })),

  // Streaming
  isStreaming: false,
  setStreaming: (streaming) => set({ isStreaming: streaming }),
  streamingContent: "",
  setStreamingContent: (content) => set({ streamingContent: content }),
  appendStreamingContent: (chunk) =>
    set((state) => ({
      streamingContent: state.streamingContent + chunk,
    })),

  // Tool
  activeTool: null,
  setActiveTool: (tool) => set({ activeTool: tool }),

  // Language
  language: "en",
  setLanguage: (lang) => set({ language: lang }),

  // Sidebar
  sidebarOpen: true,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
}));
