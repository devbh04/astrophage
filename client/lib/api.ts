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

  if (response.status === 204) return undefined as T;
  return response.json();
}

// ── Auth API ───────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  name: string;
  default_language: string;
  chart_format: string;
  residence_place_name?: string | null;
  residence_lat?: number | null;
  residence_lng?: number | null;
  residence_timezone?: string | null;
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

export interface UpdatePreferences {
  name?: string;
  default_language?: string;
  chart_format?: string;
  residence_place_name?: string | null;
  residence_lat?: number | null;
  residence_lng?: number | null;
  residence_timezone?: string | null;
}

export const authApi = {
  register: (data: RegisterData) =>
    api<User>("/auth/register", { method: "POST", body: data }),
  login: (data: LoginData) =>
    api<User>("/auth/login", { method: "POST", body: data }),
  logout: () => api("/auth/logout", { method: "POST" }),
  me: () => api<User>("/auth/me"),
  updatePreferences: (data: UpdatePreferences) =>
    api<User>("/auth/me", { method: "PATCH", body: data }),
};

// ── Profiles ───────────────────────────────────────────────────

export interface Planet {
  name: string;
  sign: string;
  house?: number;
  degree?: number;
  total_degree?: number;
  retrograde?: boolean;
  nakshatra?: string;
  pada?: number;
  nakshatra_lord?: string;
}

export interface Ascendant {
  sign: string;
  degree: number;
  total_degree?: number;
  nakshatra?: string;
  pada?: number;
}

export interface NatalChart {
  sun_sign: string;
  moon_sign: string;
  ascendant: Ascendant;
  planets: Planet[];
  house_cusps?: { house: number; sign: string; degree: number }[];
  ayanamsa?: string;
  birth_time_known?: boolean;
}

export interface DashaSegment {
  lord: string;
  level: "maha" | "antar" | "pratyantar";
  start: string;
  end: string;
  years: number;
  antardashas?: DashaSegment[];
}

export interface ComputedDashas {
  balance_at_birth: { lord: string; remaining_years: number };
  timeline: DashaSegment[];
  active: { maha?: DashaSegment | null; antar?: DashaSegment | null };
}

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
  computed_chart?: NatalChart;
  computed_dashas?: ComputedDashas;
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
  list: () => api<BirthProfile[]>("/api/profiles/"),
  get: (id: string) => api<BirthProfile>(`/api/profiles/${id}`),
  create: (data: BirthDetailsInput) =>
    api<BirthProfile>("/api/profiles/", { method: "POST", body: data }),
  patch: (id: string, data: Partial<BirthDetailsInput>) =>
    api<BirthProfile>(`/api/profiles/${id}`, { method: "PATCH", body: data }),
  recompute: (id: string) =>
    api<BirthProfile>(`/api/profiles/${id}/recompute`, { method: "POST" }),
  delete: (id: string) => api(`/api/profiles/${id}`, { method: "DELETE" }),
};

// ── Conversations ──────────────────────────────────────────────

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
  list: () => api<Conversation[]>("/api/conversations/"),
  create: (profileId?: string, title?: string) =>
    api<Conversation>("/api/conversations/", {
      method: "POST",
      body: { profile_id: profileId, title },
    }),
  rename: (id: string, title: string) =>
    api<Conversation>(`/api/conversations/${id}`, {
      method: "PATCH",
      body: { title },
    }),
  delete: (id: string) => api(`/api/conversations/${id}`, { method: "DELETE" }),
  messages: (conversationId: string) =>
    api<Message[]>(`/api/conversations/${conversationId}/messages`),
};

// ── Tools (REST passthroughs) ──────────────────────────────────

export interface PanchangData {
  tithi: { name: string; number: number; ends_at: string; start: string };
  vara: { name: string; weekday: string };
  nakshatra: { name: string; lord: string; ends_at: string; start: string };
  yoga: { name: string; number: number; ends_at: string };
  karana: { name: string; ends_at: string };
  sunrise: string;
  sunset: string;
  rahu_kaal: { start: string; end: string };
  yamaganda: { start: string; end: string };
  gulika: { start: string; end: string };
  abhijit_muhurta: { start: string; end: string };
}

export interface MuhurtaWindow {
  start: string;
  end: string;
  duration_minutes: number;
  score: number;
  factors: {
    tithi: string;
    nakshatra: string;
    yoga: string;
    weekday: string;
    rahu_kaal_clash: boolean;
    abhijit_overlap: boolean;
  };
  summary: string;
}

export interface CurrentSky {
  as_of: string;
  planets: {
    name: string;
    sign: string;
    degree: number;
    retrograde: boolean;
    nakshatra: string;
  }[];
  moon_phase: {
    name: string;
    illumination: number;
    next_full_moon: string;
    next_new_moon: string;
  };
  retrogrades: string[];
  next_sign_change: { planet: string; from: string; to: string; at: string } | null;
  next_event: unknown;
}

export interface DailyTransits {
  as_of: string;
  transits: {
    planet: string;
    current_sign: string;
    current_house_from_lagna: number;
    natal_sign: string;
    natal_house: number;
    aspects_natal: { target: string; type: string; strength: number }[];
    intensity: "high" | "medium" | "low";
    interpretation: string;
    retrograde?: boolean;
    current_nakshatra?: string;
  }[];
  activated_houses: number[];
  headline: string;
}

export interface KundaliMilanResult {
  scores: Record<string, number>;
  total: number;
  verdict: "excellent" | "good" | "average" | "low";
  mangal_dosha: {
    boy: { present: boolean; houses_affected: number[]; cancelled: boolean };
    girl: { present: boolean; houses_affected: number[]; cancelled: boolean };
    match: "both" | "one_only" | "neither";
  };
  warnings: string[];
  summary: string;
}

export interface SadeSatiResult {
  in_sade_sati: boolean;
  phase: "rising" | "peak" | "setting" | "none";
  current_status: string;
  ashtama_shani: boolean;
  start: string | null;
  peak_start: string | null;
  end: string | null;
  history: { start: string; end: string; phase: string; intensity: string }[];
}

export interface NakshatraResult {
  janma_nakshatra: string;
  pada: number;
  lord: string;
  deity: string;
  symbol: string;
  gana: string;
  yoni: string;
  nadi: string;
  varna: string;
  tatva: string;
  lucky_colors: string[];
  lucky_numbers: number[];
  compatible_nakshatras: string[];
  incompatible_nakshatras: string[];
}

export interface KnowledgeHit {
  text: string;
  source: string;
  score: number;
  chunk_id: string;
}

export interface GeocodeResult {
  lat: number;
  lng: number;
  timezone: string;
  canonical_name: string;
}

export const toolsApi = {
  geocode: (place_name: string) =>
    api<GeocodeResult>("/api/tools/geocode", {
      method: "POST",
      body: { place_name },
    }),
  birthChart: (data: {
    birth_date: string;
    birth_time?: string;
    lat: number;
    lng: number;
    timezone: string;
  }) =>
    api<NatalChart>("/api/tools/birth-chart", {
      method: "POST",
      body: data,
    }),
  dasha: (data: {
    natal_chart: NatalChart;
    birth_date: string;
    birth_time?: string;
    timezone: string;
    levels?: number;
    as_of?: string;
  }) => api<ComputedDashas>("/api/tools/dasha", { method: "POST", body: data }),
  nakshatra: (natal_chart: NatalChart) =>
    api<NakshatraResult>("/api/tools/nakshatra", {
      method: "POST",
      body: { natal_chart },
    }),
  sadeSati: (natal_chart: NatalChart, as_of?: string) =>
    api<SadeSatiResult>("/api/tools/sade-sati", {
      method: "POST",
      body: { natal_chart, as_of },
    }),
  panchang: (data: {
    date: string;
    lat: number;
    lng: number;
    timezone: string;
  }) => api<PanchangData>("/api/tools/panchang", { method: "POST", body: data }),
  muhurta: (data: {
    purpose: string;
    start_date: string;
    end_date: string;
    lat: number;
    lng: number;
    timezone: string;
  }) =>
    api<{ purpose: string; windows: MuhurtaWindow[] }>("/api/tools/muhurta", {
      method: "POST",
      body: data,
    }),
  dailyTransits: (data: {
    natal_chart: NatalChart;
    as_of?: string;
    lat?: number;
    lng?: number;
  }) =>
    api<DailyTransits>("/api/tools/daily-transits", { method: "POST", body: data }),
  currentSky: (data: { as_of?: string; lat?: number; lng?: number } = {}) =>
    api<CurrentSky>("/api/tools/current-sky", { method: "POST", body: data }),
  chartSvg: (natal_chart: NatalChart, style: string = "south_indian") =>
    api<{ svg: string }>("/api/tools/chart-svg", {
      method: "POST",
      body: { natal_chart, style },
    }),
  kundaliMilan: (boy_chart: NatalChart, girl_chart: NatalChart) =>
    api<KundaliMilanResult>("/api/tools/kundali-milan", {
      method: "POST",
      body: { boy_chart, girl_chart },
    }),
  knowledge: (query: string, top_k: number = 5) =>
    api<KnowledgeHit[]>("/api/tools/knowledge", {
      method: "POST",
      body: { query, top_k },
    }),
};

// ── Panchang convenience ───────────────────────────────────────

export const panchangApi = {
  today: (lat: number, lng: number, timezone: string) =>
    api<PanchangData>(
      `/api/panchang/today?lat=${lat}&lng=${lng}&timezone=${encodeURIComponent(
        timezone
      )}`
    ),
  forDate: (date: string, lat: number, lng: number, timezone: string) =>
    api<PanchangData>(
      `/api/panchang/?date=${date}&lat=${lat}&lng=${lng}&timezone=${encodeURIComponent(
        timezone
      )}`
    ),
};
