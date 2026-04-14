"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { DashboardLayout } from "@/components/DashboardLayout";
import {
  ChevronLeft, ChevronRight, Plus, MoreVertical, X, Sparkles,
  Eye, Download, Wrench, GraduationCap, Briefcase, UserIcon,
  ZoomIn, ZoomOut, Printer, Loader2,
} from "lucide-react";
import { templates } from "@/lib/templates";
import { ResumePreview, type ProjectItem, type LanguageItem, type AwardItem } from "@/components/ResumeLayouts";
import { generateResumePDF } from "@/components/ResumePDF";

function extractField(data: Record<string, unknown>, ...keys: string[]): string {
  for (const k of keys) {
    for (const dk of Object.keys(data)) {
      if (dk.toLowerCase().replace(/[_\s]/g, "") === k.toLowerCase().replace(/[_\s]/g, "")) {
        const v = data[dk];
        if (typeof v === "string") return v;
        if (typeof v === "object" && v !== null) return JSON.stringify(v);
      }
    }
  }
  return "";
}

function extractObject(data: Record<string, unknown>, ...keys: string[]): Record<string, unknown> | null {
  for (const k of keys) {
    for (const dk of Object.keys(data)) {
      if (dk.toLowerCase().replace(/[_\s]/g, "") === k.toLowerCase().replace(/[_\s]/g, "")) {
        const v = data[dk];
        if (typeof v === "object" && v !== null && !Array.isArray(v)) return v as Record<string, unknown>;
      }
    }
  }
  return null;
}

function extractArray(data: Record<string, unknown>, ...keys: string[]): unknown[] {
  for (const k of keys) {
    for (const dk of Object.keys(data)) {
      if (dk.toLowerCase().replace(/[_\s]/g, "") === k.toLowerCase().replace(/[_\s]/g, "")) {
        const v = data[dk];
        if (Array.isArray(v)) return v;
      }
    }
  }
  return [];
}

interface ContactInfo { name: string; title: string; email: string; phone: string; location: string; summary: string; linkedin: string; }
interface ExpItem { title: string; company: string; period: string; bullets: string[]; }
interface EduItem { degree: string; school: string; year: string; }
interface SkillGroup { category: string; items: string[]; }

interface ParsedResume {
  contact: ContactInfo;
  experience: ExpItem[];
  education: EduItem[];
  skills: SkillGroup[];
  projects: ProjectItem[];
  certifications: string[];
  achievements: AwardItem[];
  languages: LanguageItem[];
}

function parseImprovedResume(data: Record<string, unknown>): ParsedResume {
  const contactObj = extractObject(data, "Contact_Information", "ContactInformation", "Contact") || {};
  const co = contactObj as Record<string, unknown>;
  const contact: ContactInfo = {
    name: extractField(co, "Name", "Full_Name", "FullName") || "Your Name",
    title: extractField(co, "Title", "Job_Title", "JobTitle", "Position") || extractField(data, "Title", "Job_Title") || "Your Title",
    email: extractField(co, "Email", "Email_Address") || "",
    phone: extractField(co, "Phone", "Phone_Number", "Mobile") || "",
    location: extractField(co, "Location", "Address", "City") || "",
    summary: extractField(data, "Professional_Summary", "ProfessionalSummary", "Summary", "Bio", "Profile") || "",
    linkedin: extractField(co, "LinkedIn", "Linkedin", "LinkedIn_Url", "LinkedIn_Profile") || "",
  };

  const expRaw = extractArray(data, "Work_Experience", "WorkExperience", "Experience", "Professional_Experience");
  const experience: ExpItem[] = expRaw.map((e) => {
    if (typeof e !== "object" || !e) return { title: "", company: "", period: "", bullets: [] };
    const obj = e as Record<string, unknown>;
    const title = extractField(obj, "Title", "Job_Title", "Position", "Role");
    const company = extractField(obj, "Company", "Organization", "Employer");
    const start = extractField(obj, "Start_Date", "StartDate", "From");
    const end = extractField(obj, "End_Date", "EndDate", "To");
    const period = start && end ? `${start} - ${end}` : extractField(obj, "Duration", "Period", "Dates");
    const bulletsRaw = extractArray(obj, "Responsibilities", "Achievements", "Bullets", "Description", "Key_Achievements", "Key_Responsibilities");
    const bullets = bulletsRaw.map((b) => (typeof b === "string" ? b : String(b)));
    return { title, company, period, bullets };
  }).filter((e) => e.title || e.company);

  const eduRaw = extractArray(data, "Education", "Academic_Background");
  const education: EduItem[] = eduRaw.map((e) => {
    if (typeof e !== "object" || !e) return { degree: "", school: "", year: "" };
    const obj = e as Record<string, unknown>;
    return {
      degree: extractField(obj, "Degree", "Qualification", "Program"),
      school: extractField(obj, "Institution", "School", "University", "College"),
      year: extractField(obj, "Graduation_Date", "Year", "GraduationDate", "Graduated", "Graduation_Year"),
    };
  }).filter((e) => e.degree || e.school);

  const skillsObj = extractObject(data, "Skills", "Technical_Skills", "Core_Skills");
  const skills: SkillGroup[] = [];
  if (skillsObj) {
    for (const [cat, val] of Object.entries(skillsObj)) {
      if (Array.isArray(val)) skills.push({ category: cat.replace(/_/g, " "), items: val.map(String) });
      else if (typeof val === "string") skills.push({ category: cat.replace(/_/g, " "), items: val.split(",").map((s) => s.trim()) });
    }
  }

  const projRaw = extractArray(data, "Projects", "Key_Projects", "Personal_Projects");
  const projects: ProjectItem[] = projRaw.map((p) => {
    if (typeof p !== "object" || !p) return { title: "", description: "", technologies: [], bullets: [] };
    const obj = p as Record<string, unknown>;
    const techRaw = extractArray(obj, "Technologies", "Tech_Stack", "Tools", "Technologies_Used");
    const bulletsRaw = extractArray(obj, "Description", "Bullets", "Key_Features", "Highlights", "Details");
    return {
      title: extractField(obj, "Title", "Project_Title", "Name", "Project_Name"),
      description: extractField(obj, "Description", "Summary", "Overview"),
      technologies: techRaw.map((t) => String(t)),
      bullets: bulletsRaw.map((b) => String(b)),
    };
  }).filter((p) => p.title);

  const certRaw = extractArray(data, "Certifications", "Certificates", "Professional_Certifications");
  const certifications: string[] = certRaw.map((c) => {
    if (typeof c === "string") return c;
    if (typeof c === "object" && c) {
      const obj = c as Record<string, unknown>;
      const name = extractField(obj, "Name", "Title", "Certification_Name", "Certificate_Name");
      const issuer = extractField(obj, "Issuer", "Organization", "Issued_By", "Institution");
      return issuer ? `${name} - ${issuer}` : name;
    }
    return String(c);
  }).filter(Boolean);

  const achRaw = extractArray(data, "Achievements", "Awards", "Honors", "Awards_And_Achievements");
  const achievements: AwardItem[] = achRaw.map((a) => {
    if (typeof a === "string") return { title: a };
    if (typeof a === "object" && a) {
      const obj = a as Record<string, unknown>;
      return {
        title: extractField(obj, "Title", "Name", "Award"),
        institution: extractField(obj, "Institution", "Organization", "Issuer", "Company") || undefined,
      };
    }
    return { title: String(a) };
  }).filter((a) => a.title);

  const langRaw = extractArray(data, "Languages", "Language_Skills");
  const languages: LanguageItem[] = langRaw.map((l) => {
    if (typeof l === "string") return { name: l };
    if (typeof l === "object" && l) {
      const obj = l as Record<string, unknown>;
      return {
        name: extractField(obj, "Name", "Language"),
        level: extractField(obj, "Level", "Proficiency", "Fluency") || undefined,
      };
    }
    return { name: String(l) };
  }).filter((l) => l.name);

  return { contact, experience, education, skills, projects, certifications, achievements, languages };
}

// ─── MAIN PAGE ─────────────────────────────────────────

export default function ResumeBuilderPage() {
  const [selectedTplIdx, setSelectedTplIdx] = useState(0);
  const [templateScroll, setTemplateScroll] = useState(0);
  const [showPreview, setShowPreview] = useState(false);
  const [previewZoom, setPreviewZoom] = useState(0.85);
  const printRef = useRef<HTMLDivElement>(null);

  const [contact, setContact] = useState<ContactInfo>({
    name: "Your Name", title: "Your Title",
    email: "", phone: "", location: "",
    summary: "", linkedin: "",
  });
  const [experience, setExperience] = useState<ExpItem[]>([]);
  const [education, setEducation] = useState<EduItem[]>([]);
  const [skills, setSkills] = useState<SkillGroup[]>([]);
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [certifications, setCertifications] = useState<string[]>([]);
  const [achievements, setAchievements] = useState<AwardItem[]>([]);
  const [languages, setLanguages] = useState<LanguageItem[]>([]);

  useEffect(() => {
    const tplId = sessionStorage.getItem("selected_template");
    if (tplId) {
      const idx = templates.findIndex((t) => t.id === tplId);
      if (idx >= 0) setSelectedTplIdx(idx);
      sessionStorage.removeItem("selected_template");
    }

    const improvedRaw = sessionStorage.getItem("improved_resume");
    if (improvedRaw) {
      try {
        const improved = JSON.parse(improvedRaw);
        const parsed = parseImprovedResume(improved);
        if (parsed.contact.name !== "Your Name") setContact(parsed.contact);
        if (parsed.experience.length > 0) setExperience(parsed.experience);
        if (parsed.education.length > 0) setEducation(parsed.education);
        if (parsed.skills.length > 0) setSkills(parsed.skills);
        if (parsed.projects.length > 0) setProjects(parsed.projects);
        if (parsed.certifications.length > 0) setCertifications(parsed.certifications);
        if (parsed.achievements.length > 0) setAchievements(parsed.achievements);
        if (parsed.languages.length > 0) setLanguages(parsed.languages);
      } catch { /* ignore */ }
    }
  }, []);

  const currentTpl = templates[selectedTplIdx];
  const visibleCount = 6;

  const removeSkill = (groupIdx: number, itemIdx: number) => {
    setSkills(skills.map((g, gi) => gi === groupIdx ? { ...g, items: g.items.filter((_, ii) => ii !== itemIdx) } : g));
  };

  const updateExp = (idx: number, field: keyof ExpItem, value: string | string[]) => {
    setExperience(experience.map((e, i) => i === idx ? { ...e, [field]: value } : e));
  };

  const addExperience = () => {
    setExperience([...experience, { title: "", company: "", period: "", bullets: [""] }]);
  };

  const [downloading, setDownloading] = useState(false);

  const handleDownloadPDF = useCallback(async () => {
    if (downloading) return;
    setDownloading(true);
    try {
      await generateResumePDF({
        contact, experience, education, skills,
        projects, certifications, achievements, languages,
      });
    } catch (err) {
      console.error("PDF generation failed:", err);
    } finally {
      setDownloading(false);
    }
  }, [downloading, contact, experience, education, skills, projects, certifications, achievements, languages]);

  return (
    <DashboardLayout headerTitle="Resume Builder" hideHeader>
      <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>

        {/* Templates Carousel */}
        <div style={{ borderBottom: "1px solid hsl(var(--border))", padding: "14px 24px", backgroundColor: "hsl(var(--background))" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: "hsl(var(--foreground))" }}>Visual Templates</span>
              <span style={{ fontSize: 10, fontWeight: 600, color: "hsl(var(--primary))", backgroundColor: "hsl(var(--primary) / 0.1)", padding: "3px 10px", borderRadius: 10 }}>
                {templates.length} Designs
              </span>
            </div>
            <div style={{ display: "flex", gap: 6 }}>
              <button onClick={() => setTemplateScroll(Math.max(0, templateScroll - 1))} style={{ width: 26, height: 26, borderRadius: 6, border: "1px solid hsl(var(--border))", backgroundColor: "hsl(var(--secondary))", color: "hsl(var(--muted-foreground))", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <ChevronLeft style={{ width: 13, height: 13 }} />
              </button>
              <button onClick={() => setTemplateScroll(Math.min(templates.length - visibleCount, templateScroll + 1))} style={{ width: 26, height: 26, borderRadius: 6, border: "1px solid hsl(var(--border))", backgroundColor: "hsl(var(--secondary))", color: "hsl(var(--muted-foreground))", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <ChevronRight style={{ width: 13, height: 13 }} />
              </button>
            </div>
          </div>
          <div style={{ display: "flex", gap: 10, overflow: "hidden" }}>
            {templates.map((tpl, i) => {
              const isDark = tpl.bg.startsWith("#0") || tpl.bg.startsWith("#1");
              return (
                <div key={i} onClick={() => setSelectedTplIdx(i)} style={{
                  width: 100, height: 65, borderRadius: 6, cursor: "pointer", flexShrink: 0,
                  backgroundColor: tpl.bg, position: "relative", overflow: "hidden",
                  border: selectedTplIdx === i ? "2px solid hsl(var(--primary))" : "1px solid hsl(var(--border))",
                  transform: `translateX(-${templateScroll * 110}px)`, transition: "transform 0.3s",
                }}>
                  {tpl.layout === "sidebar-dark" ? (
                    <div style={{ display: "flex", height: "100%" }}>
                      <div style={{ width: "35%", backgroundColor: tpl.sidebarBg || tpl.accent }} />
                      <div style={{ flex: 1, padding: 4 }}>
                        {[1, 2, 3].map((j) => <div key={j} style={{ height: 2, width: `${30 + j * 12}%`, backgroundColor: isDark ? "hsl(var(--muted-foreground))" : "hsl(var(--border))", borderRadius: 1, marginBottom: 3 }} />)}
                      </div>
                    </div>
                  ) : tpl.layout === "modern-teal" ? (
                    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
                      <div style={{ height: "22%", backgroundColor: tpl.accent }} />
                      <div style={{ flex: 1, padding: 4 }}>
                        {[1, 2, 3].map((j) => <div key={j} style={{ height: 2, width: `${30 + j * 12}%`, backgroundColor: isDark ? "hsl(var(--muted-foreground))" : "hsl(var(--border))", borderRadius: 1, marginBottom: 2 }} />)}
                      </div>
                    </div>
                  ) : tpl.layout === "two-col-accent" ? (
                    <div style={{ display: "flex", height: "100%", padding: 4, gap: 4 }}>
                      <div style={{ flex: 1.8 }}>
                        {[1, 2].map((j) => <div key={j} style={{ height: 2, width: `${40 + j * 10}%`, backgroundColor: isDark ? "hsl(var(--muted-foreground))" : "hsl(var(--border))", borderRadius: 1, marginBottom: 3 }} />)}
                      </div>
                      <div style={{ width: "32%", display: "flex", flexWrap: "wrap", gap: 2, alignContent: "flex-start" }}>
                        {[1, 2, 3, 4].map((j) => <div key={j} style={{ height: 6, width: 18, backgroundColor: tpl.accent + "55", borderRadius: 2 }} />)}
                      </div>
                    </div>
                  ) : (
                    <>
                      <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 3, backgroundColor: tpl.accent }} />
                      <div style={{ padding: 5 }}>
                        {[1, 2, 3].map((j) => <div key={j} style={{ height: 2, width: `${30 + j * 12}%`, backgroundColor: isDark ? "hsl(var(--muted-foreground))" : "hsl(var(--border))", borderRadius: 1, marginBottom: 3 }} />)}
                      </div>
                    </>
                  )}
                  {selectedTplIdx === i && (
                    <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, padding: "2px 4px", backgroundColor: "hsl(var(--background) / 0.85)", fontSize: 7, color: "hsl(var(--foreground))", fontWeight: 600, textAlign: "center" }}>
                      {tpl.name}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Main Editor + Preview */}
        <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>

          {/* Left - Editor */}
          <div style={{ width: 380, borderRight: "1px solid hsl(var(--border))", overflowY: "auto", padding: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 18 }}>
              <div>
                <h3 style={{ fontSize: 15, fontWeight: 700, color: "hsl(var(--foreground))", marginBottom: 3 }}>Editor Workspace</h3>
                <p style={{ fontSize: 10, color: "hsl(var(--muted-foreground))" }}>Customize sections and content</p>
              </div>
              <span style={{ fontSize: 9, color: "hsl(var(--primary))", backgroundColor: "hsl(var(--primary) / 0.1)", padding: "3px 8px", borderRadius: 4, height: "fit-content" }}>Autosave</span>
            </div>

            <EditorSection icon={<UserIcon style={{ width: 14, height: 14, color: "hsl(var(--primary))" }} />} title="Personal Information">
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 8 }}>
                <EditorInput label="Full Name" value={contact.name} onChange={(v) => setContact({ ...contact, name: v })} />
                <EditorInput label="Job Title" value={contact.title} onChange={(v) => setContact({ ...contact, title: v })} />
              </div>
              <EditorInput label="LinkedIn" value={contact.linkedin} onChange={(v) => setContact({ ...contact, linkedin: v })} />
              <EditorTextArea label="Bio / Summary" value={contact.summary} onChange={(v) => setContact({ ...contact, summary: v })} />
            </EditorSection>

            <EditorSection icon={<Briefcase style={{ width: 14, height: 14, color: "hsl(var(--primary))" }} />} title="Work Experience">
              {experience.map((exp, i) => (
                <div key={i} style={{ marginBottom: 12 }}>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 8 }}>
                    <EditorInput label="Title" value={exp.title} onChange={(v) => updateExp(i, "title", v)} />
                    <EditorInput label="Company" value={exp.company} onChange={(v) => updateExp(i, "company", v)} />
                  </div>
                  <EditorInput label="Period" value={exp.period} onChange={(v) => updateExp(i, "period", v)} />
                  <div style={{ marginTop: 6 }}>
                    {exp.bullets.map((b, j) => (
                      <p key={j} style={{ fontSize: 11, color: "hsl(var(--muted-foreground))", lineHeight: 1.5, paddingLeft: 8, marginBottom: 4 }}>• {b}</p>
                    ))}
                  </div>
                </div>
              ))}
              <button onClick={addExperience} style={{
                width: "100%", padding: "9px", borderRadius: 8, backgroundColor: "hsl(var(--secondary))",
                border: "1px solid hsl(var(--border))", color: "hsl(var(--foreground))", fontSize: 11, cursor: "pointer",
                display: "flex", alignItems: "center", justifyContent: "center", gap: 5,
              }}>
                <Plus style={{ width: 11, height: 11 }} /> Add Experience
              </button>
            </EditorSection>

            <EditorSection icon={<Wrench style={{ width: 14, height: 14, color: "hsl(var(--primary))" }} />} title="Technical Skills">
              <div style={{ display: "flex", flexWrap: "wrap", gap: 5 }}>
                {skills.map((group, gi) =>
                  group.items.map((skill, si) => (
                    <span key={`${gi}-${si}`} style={{
                      display: "inline-flex", alignItems: "center", gap: 5,
                      padding: "4px 9px", borderRadius: 5,
                      backgroundColor: "hsl(var(--secondary))", border: "1px solid hsl(var(--border))",
                      fontSize: 10, color: "hsl(var(--foreground))",
                    }}>
                      {skill}
                      <button onClick={() => removeSkill(gi, si)} style={{ background: "none", border: "none", color: "hsl(var(--muted-foreground))", cursor: "pointer", padding: 0, display: "flex" }}>
                        <X style={{ width: 9, height: 9 }} />
                      </button>
                    </span>
                  ))
                )}
              </div>
            </EditorSection>

            <EditorSection icon={<GraduationCap style={{ width: 14, height: 14, color: "hsl(var(--primary))" }} />} title="Education">
              {education.map((edu, i) => (
                <div key={i} style={{ display: "flex", flexDirection: "column", gap: 6, marginBottom: 8 }}>
                  <EditorInput label="Degree" value={edu.degree} onChange={(v) => setEducation(education.map((e, ei) => ei === i ? { ...e, degree: v } : e))} />
                  <EditorInput label="School" value={edu.school} onChange={(v) => setEducation(education.map((e, ei) => ei === i ? { ...e, school: v } : e))} />
                </div>
              ))}
            </EditorSection>

            {projects.length > 0 && (
              <EditorSection icon={<Sparkles style={{ width: 14, height: 14, color: "hsl(var(--primary))" }} />} title="Projects">
                {projects.map((proj, i) => (
                  <div key={i} style={{ marginBottom: 10 }}>
                    <EditorInput label="Project Title" value={proj.title} onChange={(v) => setProjects(projects.map((p, pi) => pi === i ? { ...p, title: v } : p))} />
                    {proj.technologies && proj.technologies.length > 0 && (
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginTop: 4 }}>
                        {proj.technologies.map((t, ti) => (
                          <span key={ti} style={{ fontSize: 9, padding: "2px 6px", borderRadius: 4, backgroundColor: "hsl(var(--secondary))", border: "1px solid hsl(var(--border))", color: "hsl(var(--muted-foreground))" }}>{t}</span>
                        ))}
                      </div>
                    )}
                    {proj.bullets.map((b, j) => (
                      <p key={j} style={{ fontSize: 11, color: "hsl(var(--muted-foreground))", lineHeight: 1.5, paddingLeft: 8, marginTop: 3 }}>• {b}</p>
                    ))}
                  </div>
                ))}
              </EditorSection>
            )}

            {certifications.length > 0 && (
              <EditorSection icon={<GraduationCap style={{ width: 14, height: 14, color: "hsl(var(--primary))" }} />} title="Certifications">
                <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  {certifications.map((cert, i) => (
                    <div key={i} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                      <span style={{ fontSize: 11, color: "hsl(var(--muted-foreground))", flex: 1 }}>• {cert}</span>
                      <button onClick={() => setCertifications(certifications.filter((_, ci) => ci !== i))} style={{ background: "none", border: "none", color: "hsl(var(--muted-foreground))", cursor: "pointer", padding: 0, display: "flex" }}>
                        <X style={{ width: 9, height: 9 }} />
                      </button>
                    </div>
                  ))}
                </div>
              </EditorSection>
            )}

            {achievements.length > 0 && (
              <EditorSection icon={<Sparkles style={{ width: 14, height: 14, color: "hsl(var(--primary))" }} />} title="Achievements & Awards">
                <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  {achievements.map((ach, i) => (
                    <div key={i} style={{ fontSize: 11, color: "hsl(var(--muted-foreground))" }}>
                      <span style={{ fontWeight: 600, color: "hsl(var(--foreground))" }}>{ach.title}</span>
                      {ach.institution && <span style={{ color: "hsl(var(--muted-foreground))" }}> — {ach.institution}</span>}
                    </div>
                  ))}
                </div>
              </EditorSection>
            )}

            {languages.length > 0 && (
              <EditorSection icon={<Sparkles style={{ width: 14, height: 14, color: "hsl(var(--primary))" }} />} title="Languages">
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                  {languages.map((lang, i) => (
                    <span key={i} style={{
                      padding: "4px 10px", borderRadius: 5, fontSize: 10, color: "hsl(var(--foreground))",
                      backgroundColor: "hsl(var(--secondary))", border: "1px solid hsl(var(--border))",
                    }}>
                      {lang.name}{lang.level ? ` (${lang.level})` : ""}
                    </span>
                  ))}
                </div>
              </EditorSection>
            )}
          </div>

          {/* Right - Preview */}
          <div style={{ flex: 1, display: "flex", flexDirection: "column", backgroundColor: "hsl(var(--card))" }}>
            <div style={{ display: "flex", justifyContent: "flex-end", padding: "10px 20px", gap: 8, borderBottom: "1px solid hsl(var(--border))" }}>
              <button
                onClick={() => setShowPreview(true)}
                style={{ display: "flex", alignItems: "center", gap: 5, padding: "6px 14px", borderRadius: 18, fontSize: 11, fontWeight: 500, backgroundColor: "hsl(var(--secondary))", border: "1px solid hsl(var(--border))", color: "hsl(var(--foreground))", cursor: "pointer" }}
              >
                <Eye style={{ width: 12, height: 12 }} /> Preview
              </button>
              <button
                onClick={handleDownloadPDF}
                disabled={downloading}
                style={{ display: "flex", alignItems: "center", gap: 5, padding: "6px 14px", borderRadius: 18, fontSize: 11, fontWeight: 500, backgroundColor: downloading ? "hsl(var(--border))" : "hsl(var(--secondary))", border: "1px solid hsl(var(--border))", color: "hsl(var(--foreground))", cursor: downloading ? "wait" : "pointer", opacity: downloading ? 0.7 : 1 }}
              >
                {downloading ? <Loader2 style={{ width: 12, height: 12, animation: "spin 1s linear infinite" }} /> : <Download style={{ width: 12, height: 12 }} />}
                {downloading ? "Generating..." : "Export PDF"}
              </button>
            </div>

            <div style={{ flex: 1, display: "flex", justifyContent: "center", alignItems: "flex-start", padding: "24px 12px", overflowY: "auto", overflowX: "hidden" }}>
              <div style={{ transform: "scale(0.58)", transformOrigin: "top center", marginBottom: -400 }}>
                <div ref={printRef} id="resume-print-area" style={{ borderRadius: 4, boxShadow: "0 8px 40px hsl(var(--background) / 0.45)", overflow: "visible" }}>
                  <ResumePreview
                    contact={contact}
                    experience={experience}
                    education={education}
                    skills={skills}
                    tpl={currentTpl}
                    linkedin={contact.linkedin}
                    projects={projects}
                    certificates={certifications}
                    awards={achievements}
                    languages={languages}
                  />
                </div>
              </div>
            </div>

            <div style={{ borderTop: "1px solid hsl(var(--border))", padding: "12px 24px", display: "flex", justifyContent: "center", gap: 12 }}>
              <button style={{
                display: "flex", alignItems: "center", gap: 8, padding: "10px 22px", borderRadius: 22,
                backgroundColor: "hsl(var(--secondary))", border: "1px solid hsl(var(--border))", color: "hsl(var(--foreground))", fontSize: 12, fontWeight: 500, cursor: "pointer",
              }}>
                <Sparkles style={{ width: 14, height: 14, color: "hsl(var(--primary))" }} /> RE-RUN ATS CHECK
              </button>
              <button style={{
                display: "flex", alignItems: "center", gap: 8, padding: "10px 22px", borderRadius: 22,
                backgroundColor: "hsl(var(--secondary))", border: "1px solid hsl(var(--border))", color: "hsl(var(--foreground))", fontSize: 12, fontWeight: 500, cursor: "pointer",
              }}>
                <Sparkles style={{ width: 14, height: 14, color: "hsl(var(--primary))" }} /> JOB RECOMMENDATION
              </button>
            </div>
          </div>
        </div>
      </div>
      {showPreview && (
        <div
          style={{
            position: "fixed", inset: 0, zIndex: 9999,
            backgroundColor: "hsl(var(--background) / 0.92)",
            display: "flex", flexDirection: "column",
          }}
        >
          <div style={{
            display: "flex", alignItems: "center", justifyContent: "space-between",
            padding: "12px 24px", borderBottom: "1px solid hsl(var(--border))",
          }}>
            <span style={{ fontSize: 14, fontWeight: 600, color: "hsl(var(--foreground))" }}>Resume Preview</span>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <button
                onClick={() => setPreviewZoom((z) => Math.max(0.3, z - 0.1))}
                style={{ background: "hsl(var(--secondary))", border: "1px solid hsl(var(--border))", borderRadius: 8, padding: "6px 8px", color: "hsl(var(--foreground))", cursor: "pointer", display: "flex", alignItems: "center" }}
              >
                <ZoomOut style={{ width: 14, height: 14 }} />
              </button>
              <span style={{ fontSize: 11, color: "hsl(var(--muted-foreground))", minWidth: 40, textAlign: "center" }}>{Math.round(previewZoom * 100)}%</span>
              <button
                onClick={() => setPreviewZoom((z) => Math.min(1.5, z + 0.1))}
                style={{ background: "hsl(var(--secondary))", border: "1px solid hsl(var(--border))", borderRadius: 8, padding: "6px 8px", color: "hsl(var(--foreground))", cursor: "pointer", display: "flex", alignItems: "center" }}
              >
                <ZoomIn style={{ width: 14, height: 14 }} />
              </button>
              <button
                onClick={() => window.print()}
                style={{ background: "hsl(var(--secondary))", border: "1px solid hsl(var(--border))", borderRadius: 8, padding: "6px 10px", color: "hsl(var(--foreground))", cursor: "pointer", display: "flex", alignItems: "center", gap: 5, fontSize: 11 }}
              >
                <Printer style={{ width: 13, height: 13 }} /> Print
              </button>
              <button
                onClick={() => { setShowPreview(false); setTimeout(() => handleDownloadPDF(), 200); }}
                style={{ background: "hsl(var(--primary))", border: "none", borderRadius: 8, padding: "6px 14px", color: "hsl(var(--primary-foreground))", cursor: "pointer", display: "flex", alignItems: "center", gap: 5, fontSize: 11, fontWeight: 600 }}
              >
                <Download style={{ width: 13, height: 13 }} /> Download PDF
              </button>
              <button
                onClick={() => setShowPreview(false)}
                style={{ background: "none", border: "1px solid hsl(var(--border))", borderRadius: 8, padding: "6px 8px", color: "hsl(var(--foreground))", cursor: "pointer", display: "flex", alignItems: "center" }}
              >
                <X style={{ width: 16, height: 16 }} />
              </button>
            </div>
          </div>

          <div style={{ flex: 1, overflowY: "auto", display: "flex", justifyContent: "center", alignItems: "flex-start", padding: "32px 16px" }}>
            <div style={{ transform: `scale(${previewZoom})`, transformOrigin: "top center" }}>
              <div style={{ boxShadow: "0 12px 60px hsl(var(--background) / 0.55)", borderRadius: 4, overflow: "visible" }}>
                <ResumePreview
                  contact={contact}
                  experience={experience}
                  education={education}
                  skills={skills}
                  tpl={currentTpl}
                  linkedin={contact.linkedin}
                  projects={projects}
                  certificates={certifications}
                  awards={achievements}
                  languages={languages}
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}

function EditorSection({ icon, title, children }: { icon: React.ReactNode; title: string; children: React.ReactNode }) {
  return (
    <div style={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 10, padding: 14, marginBottom: 10 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
          {icon}
          <span style={{ fontSize: 12, fontWeight: 600, color: "hsl(var(--foreground))" }}>{title}</span>
        </div>
        <div style={{ display: "flex", gap: 5 }}>
          <button style={{ background: "none", border: "none", color: "hsl(var(--muted-foreground))", cursor: "pointer", padding: 0 }}><Plus style={{ width: 13, height: 13 }} /></button>
          <button style={{ background: "none", border: "none", color: "hsl(var(--muted-foreground))", cursor: "pointer", padding: 0 }}><MoreVertical style={{ width: 13, height: 13 }} /></button>
        </div>
      </div>
      {children}
    </div>
  );
}

function EditorInput({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div>
      <label style={{ fontSize: 8, color: "hsl(var(--muted-foreground))", textTransform: "uppercase", letterSpacing: 0.5, display: "block", marginBottom: 3 }}>{label}</label>
      <input value={value} onChange={(e) => onChange(e.target.value)} style={{
        width: "100%", padding: "7px 9px", borderRadius: 5,
        backgroundColor: "hsl(var(--secondary))", border: "1px solid hsl(var(--border))",
        color: "hsl(var(--foreground))", fontSize: 11, outline: "none",
      }} />
    </div>
  );
}

function EditorTextArea({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div>
      <label style={{ fontSize: 8, color: "hsl(var(--muted-foreground))", textTransform: "uppercase", letterSpacing: 0.5, display: "block", marginBottom: 3 }}>{label}</label>
      <textarea value={value} onChange={(e) => onChange(e.target.value)} rows={3} style={{
        width: "100%", padding: "7px 9px", borderRadius: 5,
        backgroundColor: "hsl(var(--secondary))", border: "1px solid hsl(var(--border))",
        color: "hsl(var(--foreground))", fontSize: 11, outline: "none", resize: "none", lineHeight: 1.5,
      }} />
    </div>
  );
}
