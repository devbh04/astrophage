/**
 * API client for the Astrophage backend.
 * All requests include credentials (cookies) for auth.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:7860";

interface ApiOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
}

export async function api<T = unknown>(
  path: string,
  options: ApiOptions = {}
): Promise<T> {
  const { body, headers, ...rest } = options;

  const response = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
    body: body ? JSON.stringify(body) : undefined,
    ...rest,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || `API error: ${response.status}`);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// ── Auth API ───────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  name: string;
  default_language: string;
  chart_format: string;
}

export interface RegisterData {
  email: string;
  password: string;
  name: string;
  default_language?: string;
}

export interface LoginData {
  email: string;
  password: string;
}

export const authApi = {
  register: (data: RegisterData) =>
    api<User>("/auth/register", { method: "POST", body: data }),

  login: (data: LoginData) =>
    api<User>("/auth/login", { method: "POST", body: data }),

  logout: () =>
    api("/auth/logout", { method: "POST" }),

  me: () =>
    api<User>("/auth/me"),
};

// ── Profiles API ───────────────────────────────────────────────

export interface BirthProfile {
  id: string;
  user_id: string;
  name: string;
  relationship?: string;
  birth_date: string;
  birth_time?: string;
  lat: number;
  lng: number;
  timezone: string;
  place_name?: string;
  computed_chart?: Record<string, unknown>;
  computed_dashas?: Record<string, unknown>;
}

export interface BirthDetailsInput {
  name: string;
  relationship?: string;
  birth_date: string;
  birth_time?: string;
  place_name: string;
  lat: number;
  lng: number;
  timezone: string;
}

export const profilesApi = {
  list: () =>
    api<BirthProfile[]>("/api/profiles/"),

  get: (id: string) =>
    api<BirthProfile>(`/api/profiles/${id}`),

  create: (data: BirthDetailsInput) =>
    api<BirthProfile>("/api/profiles/", { method: "POST", body: data }),

  delete: (id: string) =>
    api(`/api/profiles/${id}`, { method: "DELETE" }),
};

// ── Conversations API ──────────────────────────────────────────

export interface Conversation {
  id: string;
  user_id: string;
  profile_id?: string;
  title?: string;
  created_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  language?: string;
  tool_calls?: Record<string, unknown>;
  created_at: string;
}

export const conversationsApi = {
  list: () =>
    api<Conversation[]>("/api/conversations/"),

  create: (profileId?: string, title?: string) =>
    api<Conversation>("/api/conversations/", {
      method: "POST",
      body: { profile_id: profileId, title },
    }),

  messages: (conversationId: string) =>
    api<Message[]>(`/api/conversations/${conversationId}/messages`),
};
