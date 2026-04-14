const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function fetchWithTimeout(url: string, options: RequestInit = {}, timeoutMs = 60000): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  return fetch(url, { ...options, signal: controller.signal }).finally(() => clearTimeout(timer));
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
    throw new Error(err.detail || "Analysis failed");
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
    throw new Error(err.detail || "Analysis failed");
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
    throw new Error(err.detail || "Analysis failed");
  }
  return validateAnalysis(await res.json());
}

function validateAnalysis(data: ATSAnalysis): ATSAnalysis {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  if ((data as any)?.error) throw new Error((data as any).error);
  if (!data?.ATS_Score && data?.ATS_Score !== 0) {
    throw new Error("Analysis failed — invalid response from server");
  }
  return data;
}

export function toArray(val: string | string[] | undefined): string[] {
  if (!val) return [];
  if (Array.isArray(val)) return val;
  return [val];
}
