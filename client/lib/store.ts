/**
 * Zustand store for global application state.
 */

import { create } from "zustand";
import type { User, BirthProfile, Conversation, Message } from "./api";

/**
 * A single artefact rendered in the chat stream — either text from the
 * assistant, an SVG chart, or a structured card emitted by a tool.
 */
export type ChatArtifact =
  | {
      kind: "text";
      id: string;
      role: "user" | "assistant";
      content: string;
      streaming?: boolean;
      created_at: string;
    }
  | {
      kind: "card";
      id: string;
      card_type: string;
      data: Record<string, unknown>;
      created_at: string;
    }
  | {
      kind: "chart_svg";
      id: string;
      svg: string;
      created_at: string;
    };

interface AppState {
  // Auth
  user: User | null;
  setUser: (user: User | null) => void;

  // Active profile
  activeProfile: BirthProfile | null;
  setActiveProfile: (profile: BirthProfile | null) => void;

  // Profiles (family vault)
  profiles: BirthProfile[];
  setProfiles: (profiles: BirthProfile[]) => void;
  addProfile: (profile: BirthProfile) => void;
  removeProfile: (id: string) => void;

  // Conversations
  conversations: Conversation[];
  setConversations: (conversations: Conversation[]) => void;
  activeConversationId: string | null;
  setActiveConversationId: (id: string | null) => void;

  // Chat — the stream is a sequence of artefacts (text + cards + chart svgs)
  artifacts: ChatArtifact[];
  setArtifacts: (a: ChatArtifact[]) => void;
  pushArtifact: (a: ChatArtifact) => void;
  clearArtifacts: () => void;
  appendStreamingText: (id: string, chunk: string) => void;
  finalizeStreamingText: (id: string) => void;
  hydrateFromMessages: (messages: Message[]) => void;

  // Streaming state
  isStreaming: boolean;
  setStreaming: (streaming: boolean) => void;

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

const newId = () =>
  typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `art-${Date.now()}-${Math.random().toString(36).slice(2)}`;

export const useAppStore = create<AppState>((set) => ({
  user: null,
  setUser: (user) => set({ user }),

  activeProfile: null,
  setActiveProfile: (profile) => set({ activeProfile: profile }),

  profiles: [],
  setProfiles: (profiles) => set({ profiles }),
  addProfile: (profile) =>
    set((state) => ({ profiles: [...state.profiles, profile] })),
  removeProfile: (id) =>
    set((state) => ({ profiles: state.profiles.filter((p) => p.id !== id) })),

  conversations: [],
  setConversations: (conversations) => set({ conversations }),
  activeConversationId: null,
  setActiveConversationId: (id) => set({ activeConversationId: id }),

  artifacts: [],
  setArtifacts: (artifacts) => set({ artifacts }),
  pushArtifact: (a) =>
    set((state) => ({ artifacts: [...state.artifacts, a] })),
  clearArtifacts: () => set({ artifacts: [] }),
  appendStreamingText: (id, chunk) =>
    set((state) => ({
      artifacts: state.artifacts.map((a) =>
        a.kind === "text" && a.id === id
          ? { ...a, content: a.content + chunk }
          : a
      ),
    })),
  finalizeStreamingText: (id) =>
    set((state) => ({
      artifacts: state.artifacts.map((a) =>
        a.kind === "text" && a.id === id ? { ...a, streaming: false } : a
      ),
    })),
  hydrateFromMessages: (messages) =>
    set({
      artifacts: messages.map((m) => ({
        kind: "text" as const,
        id: m.id || newId(),
        role: (m.role === "assistant" ? "assistant" : "user") as
          | "user"
          | "assistant",
        content: m.content,
        created_at: m.created_at || new Date().toISOString(),
      })),
    }),

  isStreaming: false,
  setStreaming: (streaming) => set({ isStreaming: streaming }),

  activeTool: null,
  setActiveTool: (tool) => set({ activeTool: tool }),

  language: "en",
  setLanguage: (lang) => set({ language: lang }),

  sidebarOpen: true,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
}));

export { newId as createArtifactId };
