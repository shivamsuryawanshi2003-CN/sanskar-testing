/**
 * When `NEXT_PUBLIC_API_URL` is unset, call same-origin `/api-backend/*` so Next.js can
 * proxy to the Python API (see `next.config.ts` rewrites). That avoids browser CORS entirely in dev.
 */
const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "").trim().replace(/\/$/, "") || "/api-backend";

function fetchWithTimeout(url: string, options: RequestInit = {}, timeoutMs = 60000): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  return fetch(url, { ...options, signal: controller.signal }).finally(() => clearTimeout(timer));
}

function parsePercentOrNumber(v: unknown, fallback = 0): number {
  if (typeof v === "number" && !Number.isNaN(v)) {
    return Math.max(0, Math.min(100, Math.round(v)));
  }
  if (typeof v === "string") {
    const n = parseInt(v.replace(/%/g, "").trim(), 10);
    return Number.isNaN(n) ? fallback : Math.max(0, Math.min(100, n));
  }
  return fallback;
}

/** Maps FastAPI `AnalyzeResponse` JSON into the dashboard `ATSAnalysis` shape. */
function normalizeServerAnalysis(raw: Record<string, unknown>): ATSAnalysis {
  const sb = (raw.Score_Breakdown as Record<string, unknown>) || {};
  const format = parsePercentOrNumber(sb.FORMAT, 0);
  const skills = parsePercentOrNumber(sb.SKILLS, 0);
  const experience = parsePercentOrNumber(sb.EXPERIENCE, 0);
  const completeness = parsePercentOrNumber(sb.COMPLETENESS ?? sb.EDUCATION, 0);
  const education = sb.EDUCATION !== undefined ? parsePercentOrNumber(sb.EDUCATION, completeness) : completeness;

  const mk = raw.Missing_Keywords;
  let missingKeywords: string[] = [];
  if (Array.isArray(mk)) {
    missingKeywords = mk.filter((x): x is string => typeof x === "string" && x.trim().length > 0);
  } else if (mk && typeof mk === "object") {
    const list = raw.Missing_Keyword_List;
    if (Array.isArray(list)) {
      missingKeywords = list.filter((x): x is string => typeof x === "string" && x.trim().length > 0);
    }
  }

  const ats = typeof raw.ATS_Score === "number" ? raw.ATS_Score : parseInt(String(raw.ATS_Score ?? ""), 10) || 0;
  const rhRaw = raw.Resume_Health;
  const defaultHealth: ResumeHealth = {
    Content_Percent: Math.max(0, Math.min(100, ats)),
    ATS_Parse_Rate: "No issues",
    Quantifying_Impact: "No issues",
    Repetition: "No issues",
    Spelling_Grammar: "No issues",
  };
  let resumeHealth: ResumeHealth = defaultHealth;
  if (rhRaw && typeof rhRaw === "object" && "Content_Percent" in rhRaw) {
    const o = rhRaw as Record<string, unknown>;
    const cp = o.Content_Percent;
    resumeHealth = {
      Content_Percent:
        typeof cp === "number"
          ? Math.max(0, Math.min(100, Math.round(cp)))
          : parseInt(String(cp ?? ats), 10) || defaultHealth.Content_Percent,
      ATS_Parse_Rate: String(o.ATS_Parse_Rate ?? defaultHealth.ATS_Parse_Rate),
      Quantifying_Impact: String(o.Quantifying_Impact ?? defaultHealth.Quantifying_Impact),
      Repetition: String(o.Repetition ?? defaultHealth.Repetition),
      Spelling_Grammar: String(o.Spelling_Grammar ?? defaultHealth.Spelling_Grammar),
    };
  }

  return {
    ATS_Score: ats,
    Summary: String(raw.Summary ?? ""),
    Resume_Health: resumeHealth,
    Suggestions_for_Improvement: Array.isArray(raw.Suggestions_for_Improvement)
      ? (raw.Suggestions_for_Improvement as string[]).filter(Boolean)
      : [],
    Score_Breakdown: {
      FORMAT: format,
      SKILLS: skills,
      EXPERIENCE: experience,
      EDUCATION: education,
    },
    Missing_Keywords: missingKeywords,
    Achievements_or_Certifications: Array.isArray(raw.Achievements_or_Certifications)
      ? (raw.Achievements_or_Certifications as string[]).filter(Boolean)
      : [],
    Resume_Strength: Array.isArray(raw.Resume_Strength) ? (raw.Resume_Strength as string[]).filter(Boolean) : [],
    Key_Skills: Array.isArray(raw.Key_Skills) ? (raw.Key_Skills as string[]).filter(Boolean) : [],
    Repeated_Word_Frequency:
      raw.Repeated_Word_Frequency && typeof raw.Repeated_Word_Frequency === "object"
        ? Object.fromEntries(
            Object.entries(raw.Repeated_Word_Frequency as Record<string, unknown>).map(([k, v]) => [
              k,
              typeof v === "number" ? v : parseInt(String(v), 10) || 0,
            ]),
          )
        : {},
    Word_Replacement_Suggestions: Array.isArray(raw.Word_Replacement_Suggestions)
      ? (raw.Word_Replacement_Suggestions as string[]).filter(Boolean)
      : [],
  };
}

function formatApiErrorDetail(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((e) => (typeof e === "object" && e && "msg" in e ? String((e as { msg: unknown }).msg) : JSON.stringify(e)))
      .filter(Boolean)
      .join("; ");
  }
  if (detail && typeof detail === "object" && "message" in detail) {
    return String((detail as { message: unknown }).message);
  }
  return "Analysis failed";
}

export interface ResumeHealth {
  Content_Percent: number;
  ATS_Parse_Rate: string;
  Quantifying_Impact: string;
  Repetition: string;
  Spelling_Grammar: string;
}

export interface ScoreBreakdown {
  FORMAT: number;
  SKILLS: number;
  EXPERIENCE: number;
  EDUCATION: number;
}

export interface ATSAnalysis {
  ATS_Score: number;
  Summary: string;
  Resume_Health: ResumeHealth;
  Suggestions_for_Improvement: string[];
  Score_Breakdown: ScoreBreakdown;
  Missing_Keywords: string[];
  Achievements_or_Certifications: string[];
  Resume_Strength: string[];
  Key_Skills: string[];
  Repeated_Word_Frequency: Record<string, number>;
  Word_Replacement_Suggestions: string[];
}

export interface RoleItem {
  id: string;
  title: string;
  skills?: string[];
}

export interface RolesResponse {
  roles: RoleItem[];
}

export async function fetchRoles(): Promise<RolesResponse> {
  const res = await fetchWithTimeout(`${API_BASE}/roles`, {}, 30000);
  if (!res.ok) throw new Error("Failed to fetch roles");
  const data = await res.json();
  if (Array.isArray(data)) return { roles: data };
  return data;
}

export async function analyzeGeneral(file: File): Promise<ATSAnalysis> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetchWithTimeout(`${API_BASE}/analyse/general`, { method: "POST", body: formData }, 180000);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(formatApiErrorDetail((err as { detail?: unknown }).detail) || "Analysis failed");
  }
  return validateAnalysis(await res.json());
}

export async function analyzeWithRole(file: File, roleId: string): Promise<ATSAnalysis> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("role", roleId);
  const res = await fetchWithTimeout(`${API_BASE}/analyse/with-role`, { method: "POST", body: formData }, 180000);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(formatApiErrorDetail((err as { detail?: unknown }).detail) || "Analysis failed");
  }
  return validateAnalysis(await res.json());
}

export async function analyzeWithJD(file: File, roleId: string, jobDescription: string): Promise<ATSAnalysis> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("role", roleId);
  formData.append("job_description", jobDescription);
  const res = await fetchWithTimeout(`${API_BASE}/analyse/with-jd`, { method: "POST", body: formData }, 180000);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(formatApiErrorDetail((err as { detail?: unknown }).detail) || "Analysis failed");
  }
  return validateAnalysis(await res.json());
}

function validateAnalysis(data: unknown): ATSAnalysis {
  if (!data || typeof data !== "object") {
    throw new Error("Analysis failed — invalid response from server");
  }
  const raw = data as Record<string, unknown>;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  if ((raw as any)?.error) throw new Error(String((raw as any).error));
  if (raw.ATS_Score === undefined || raw.ATS_Score === null) {
    throw new Error("Analysis failed — invalid response from server");
  }
  const normalized = normalizeServerAnalysis(raw);
  if (!Number.isFinite(normalized.ATS_Score)) {
    throw new Error("Analysis failed — invalid response from server");
  }
  return normalized;
}

export function toArray(val: string | string[] | undefined): string[] {
  if (!val) return [];
  if (Array.isArray(val)) return val;
  return [val];
}
