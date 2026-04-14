"use client";

import type { CSSProperties } from "react";
import type { ResumeTemplate } from "@/lib/templates";

export interface ContactInfo {
  name: string;
  title: string;
  email: string;
  phone: string;
  location: string;
  summary: string;
}

export interface ExpItem {
  title: string;
  company: string;
  period: string;
  bullets: string[];
}

export interface EduItem {
  degree: string;
  school: string;
  year: string;
}

export interface SkillGroup {
  category: string;
  items: string[];
}

export interface LanguageItem {
  name: string;
  level?: string;
}

export interface AwardItem {
  title: string;
  institution?: string;
}

export interface ProjectItem {
  title: string;
  description: string;
  technologies?: string[];
  bullets: string[];
}

export interface ResumePreviewProps {
  contact: ContactInfo;
  experience: ExpItem[];
  education: EduItem[];
  skills: SkillGroup[];
  tpl: ResumeTemplate;
  linkedin?: string;
  languages?: LanguageItem[];
  awards?: AwardItem[];
  certificates?: string[];
  projects?: ProjectItem[];
  nationality?: string;
  dateOfBirth?: string;
}

const A4_W = 794;
const A4_H = 1123;

const paper: CSSProperties = {
  width: A4_W,
  minHeight: A4_H,
  boxSizing: "border-box",
  padding: "36px 32px",
  overflow: "visible",
};

/** Use readable strip on right column when template accent is a light placeholder */
function sidebarSectionStripColor(accent: string, sidebarBg?: string): { bg: string; fg: string } {
  const a = accent.toLowerCase();
  if (a === "#f0f0f0" || (a.startsWith("#f") && a.length <= 7 && a !== "#ffffff")) {
    const bg = sidebarBg ?? "#1e293b";
    return { bg, fg: "#ffffff" };
  }
  return { bg: accent, fg: "#ffffff" };
}

const serif = { fontFamily: "Georgia, serif" } as const;
const sans = { fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, sans-serif" } as const;

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0]!.slice(0, 2).toUpperCase();
  return (parts[0]![0]! + parts[parts.length - 1]![0]!).toUpperCase();
}

function dotRating(level?: string): string {
  if (!level) return "● ● ● ○ ○";
  const l = level.toLowerCase();
  if (l.includes("native") || l.includes("fluent")) return "● ● ● ● ●";
  if (l.includes("advanced") || l.includes("professional")) return "● ● ● ● ○";
  if (l.includes("intermediate")) return "● ● ● ○ ○";
  if (l.includes("basic") || l.includes("elementary")) return "● ● ○ ○ ○";
  return "● ● ● ○ ○";
}

function LayoutClassicCenter({
  contact,
  experience,
  education,
  skills,
  languages,
  awards,
  certificates,
  projects,
  linkedin,
  tpl,
}: Omit<ResumePreviewProps, "nationality" | "dateOfBirth">) {
  const contactBits = [
    contact.location && `📍 ${contact.location}`,
    contact.email && `✉ ${contact.email}`,
    contact.phone && `📞 ${contact.phone}`,
    linkedin && `🔗 ${linkedin}`,
  ].filter(Boolean);

  return (
    <div style={{ ...paper, background: tpl.bg, color: "#000000", ...serif }}>
      <div style={{ textAlign: "center" }}>
        <h1 style={{ margin: 0, fontSize: 26, fontWeight: 700, letterSpacing: 0.5 }}>{contact.name}</h1>
        <p style={{ margin: "6px 0 0", fontSize: 16, fontStyle: "italic", fontWeight: 400 }}>{contact.title}</p>
        <p style={{ margin: "10px 0 0", fontSize: 16, lineHeight: 1.4 }}>{contactBits.join(" | ")}</p>
      </div>
      <div style={{ borderBottom: "1px solid #000", margin: "12px 0 14px" }} />

      <SectionHeaderClassic text="PROFILE" />
      <p style={{ margin: "0 0 14px", fontSize: 16, textAlign: "justify", lineHeight: 1.45 }}>{contact.summary}</p>

      <SectionHeaderClassic text="PROFESSIONAL EXPERIENCE" />
      {experience.map((job, i) => (
        <div key={i} style={{ marginBottom: 21 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 10 }}>
            <span style={{ fontSize: 13, fontWeight: 700 }}>{job.title}</span>
            <span style={{ fontSize: 16, whiteSpace: "nowrap" }}>{job.period}</span>
          </div>
          <div style={{ fontSize: 16, fontStyle: "italic", marginBottom: 5 }}>{job.company}</div>
          <ul style={{ margin: 0, paddingLeft: 26, fontSize: 16, lineHeight: 1.4 }}>
            {job.bullets.map((b, j) => (
              <li key={j}>{b}</li>
            ))}
          </ul>
        </div>
      ))}

      <SectionHeaderClassic text="EDUCATION" />
      {education.map((ed, i) => (
        <div key={i} style={{ marginBottom: 10 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 10 }}>
            <span style={{ fontSize: 13, fontWeight: 700 }}>{ed.degree}</span>
            <span style={{ fontSize: 16 }}>{ed.year}</span>
          </div>
          <div style={{ fontSize: 16, fontStyle: "italic" }}>{ed.school}</div>
        </div>
      ))}

      <SectionHeaderClassic text="SKILLS" />
      <div style={{ fontSize: 16, lineHeight: 1.6, marginBottom: 10 }}>
        {skills.map((g, gi) => (
          <div key={gi} style={{ marginBottom: 3 }}>
            {g.category && <strong>{g.category}: </strong>}
            {g.items.join(" · ")}
          </div>
        ))}
      </div>

      {languages && languages.length > 0 && (
        <>
          <SectionHeaderClassic text="LANGUAGES" />
          <p style={{ margin: 0, fontSize: 16, lineHeight: 1.5 }}>
            {languages.map((lang, i) => (
              <span key={i}>
                {i > 0 ? " · " : ""}
                <strong>{lang.name}</strong> {dotRating(lang.level)}
              </span>
            ))}
          </p>
        </>
      )}

      {projects && projects.length > 0 && (
        <>
          <SectionHeaderClassic text="PROJECTS" />
          {projects.map((p, i) => (
            <div key={i} style={{ marginBottom: 10 }}>
              <div style={{ fontSize: 13, fontWeight: 700 }}>{p.title}</div>
              {p.technologies && p.technologies.length > 0 && (
                <div style={{ fontSize: 14, color: "#666", marginBottom: 2 }}>{p.technologies.join(" | ")}</div>
              )}
              {p.bullets.map((b, j) => (
                <p key={j} style={{ fontSize: 16, color: "#333", lineHeight: 1.6, paddingLeft: 8 }}>• {b}</p>
              ))}
              {p.description && p.bullets.length === 0 && (
                <p style={{ fontSize: 16, color: "#333", lineHeight: 1.6 }}>{p.description}</p>
              )}
            </div>
          ))}
        </>
      )}

      {certificates && certificates.length > 0 && (
        <>
          <SectionHeaderClassic text="CERTIFICATIONS" />
          {certificates.map((c, i) => (
            <p key={i} style={{ fontSize: 16, color: "#333", lineHeight: 1.7, paddingLeft: 8 }}>• {c}</p>
          ))}
        </>
      )}

      {awards && awards.length > 0 && (
        <>
          <SectionHeaderClassic text="AWARDS" />
          {awards.map((a, i) => (
            <div key={i} style={{ marginBottom: 10 }}>
              <div style={{ fontSize: 13, fontWeight: 700 }}>{a.title}</div>
              {a.institution && <div style={{ fontSize: 16, fontStyle: "italic" }}>{a.institution}</div>}
            </div>
          ))}
        </>
      )}
    </div>
  );
}

function SectionHeaderClassic({ text }: { text: string }) {
  return (
    <div style={{ marginBottom: 8 }}>
      <span
        style={{
          display: "inline-block",
          fontSize: 13,
          fontWeight: 700,
          letterSpacing: 0.5,
          borderBottom: "2px solid #000",
          paddingBottom: 2,
        }}
      >
        {text}
      </span>
    </div>
  );
}

function LayoutSidebarDark({
  contact,
  experience,
  education,
  skills,
  languages,
  awards,
  certificates,
  projects,
  linkedin,
  tpl,
}: Omit<ResumePreviewProps, "nationality" | "dateOfBirth">) {
  const side = tpl.sidebarBg ?? "#1e293b";
  const strip = sidebarSectionStripColor(tpl.accent, tpl.sidebarBg);

  return (
    <div style={{ ...paper, padding: 0, display: "flex", background: tpl.bg, ...sans }}>
      <div
        style={{
          width: "35%",
          minWidth: 0,
          background: side,
          color: "#ffffff",
          padding: "18px 14px",
          boxSizing: "border-box",
        }}
      >
        <div
          style={{
            width: 74,
            height: 74,
            borderRadius: "50%",
            border: "3px solid #fff",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 32,
            fontWeight: 700,
            margin: "0 auto 12px",
          }}
        >
          {initials(contact.name)}
        </div>
        <h1 style={{ margin: 0, fontSize: 21, fontWeight: 700, textAlign: "center" }}>{contact.name}</h1>
        <p style={{ margin: "6px 0 0", fontSize: 13, textAlign: "center", opacity: 0.95 }}>{contact.title}</p>

        <div style={{ marginTop: 14, fontSize: 14, lineHeight: 1.6 }}>
          <div>✉ {contact.email}</div>
          <div>📞 {contact.phone}</div>
          <div>📍 {contact.location}</div>
          {linkedin && <div>🔗 {linkedin}</div>}
        </div>

        <p style={{ fontSize: 16, fontWeight: 700, letterSpacing: 1, margin: "16px 0 6px" }}>PROFILE</p>
        <p style={{ margin: 0, fontSize: 14, lineHeight: 1.45, opacity: 0.95 }}>{contact.summary}</p>

        {languages && languages.length > 0 && (
          <>
            <p style={{ fontSize: 16, fontWeight: 700, letterSpacing: 1, margin: "14px 0 6px" }}>LANGUAGES</p>
            {languages.map((lang, i) => (
              <div key={i} style={{ fontSize: 14, marginBottom: 5 }}>
                {lang.name} <span style={{ opacity: 0.85 }}>{dotRating(lang.level)}</span>
              </div>
            ))}
          </>
        )}

        {awards && awards.length > 0 && (
          <>
            <p style={{ fontSize: 16, fontWeight: 700, letterSpacing: 1, margin: "14px 0 6px" }}>AWARDS</p>
            {awards.map((a, i) => (
              <div key={i} style={{ marginBottom: 10, fontSize: 14 }}>
                <div style={{ fontWeight: 700 }}>{a.title}</div>
                {a.institution && <div style={{ fontStyle: "italic", opacity: 0.9 }}>{a.institution}</div>}
              </div>
            ))}
          </>
        )}
      </div>

      <div style={{ width: "65%", padding: "18px 14px", boxSizing: "border-box", color: tpl.textColor }}>
        <RightSectionHeader label="WORK EXPERIENCE" stripBg={strip.bg} stripFg={strip.fg} />
        {experience.map((job, i) => (
          <div key={i} style={{ marginBottom: 21 }}>
            <div style={{ fontSize: 13, fontWeight: 700 }}>{job.company}</div>
            <div style={{ fontSize: 16, color: tpl.mutedColor }}>
              {job.title} · {job.period}
            </div>
            <div style={{ fontSize: 14, color: tpl.mutedColor, marginBottom: 5 }}>{contact.location}</div>
            <ul style={{ margin: 0, paddingLeft: 24, fontSize: 16, lineHeight: 1.35 }}>
              {job.bullets.map((b, j) => (
                <li key={j}>{b}</li>
              ))}
            </ul>
          </div>
        ))}

        <RightSectionHeader label="EDUCATION" stripBg={strip.bg} stripFg={strip.fg} />
        {education.map((ed, i) => (
          <div key={i} style={{ marginBottom: 10, fontSize: 16 }}>
            <strong>{ed.degree}</strong> — {ed.school} ({ed.year})
          </div>
        ))}

        <RightSectionHeader label="SKILLS" stripBg={strip.bg} stripFg={strip.fg} />
        <div style={{ fontSize: 16, lineHeight: 1.6 }}>
          {skills.map((g, gi) => (
            <div key={gi} style={{ marginBottom: 3 }}>
              {g.category && <strong>{g.category}: </strong>}
              {g.items.join(" · ")}
            </div>
          ))}
        </div>

        {projects && projects.length > 0 && (
          <>
            <RightSectionHeader label="PROJECTS" stripBg={strip.bg} stripFg={strip.fg} />
            {projects.map((p, i) => (
              <div key={i} style={{ marginBottom: 13 }}>
                <div style={{ fontSize: 13, fontWeight: 700 }}>{p.title}</div>
                {p.technologies && p.technologies.length > 0 && (
                  <div style={{ fontSize: 14, color: tpl.mutedColor, marginBottom: 2 }}>{p.technologies.join(" | ")}</div>
                )}
                <ul style={{ margin: "2px 0 0", paddingLeft: 24, fontSize: 16, lineHeight: 1.35 }}>
                  {p.bullets.map((b, j) => <li key={j}>{b}</li>)}
                </ul>
              </div>
            ))}
          </>
        )}

        {certificates && certificates.length > 0 && (
          <>
            <RightSectionHeader label="CERTIFICATIONS" stripBg={strip.bg} stripFg={strip.fg} />
            <ul style={{ margin: 0, paddingLeft: 24, fontSize: 16, lineHeight: 1.35 }}>
              {certificates.map((c, i) => <li key={i}>{c}</li>)}
            </ul>
          </>
        )}
      </div>
    </div>
  );
}

function RightSectionHeader({ label, stripBg, stripFg }: { label: string; stripBg: string; stripFg: string }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        margin: "14px 0 8px",
        fontSize: 16,
        fontWeight: 700,
        letterSpacing: 0.5,
      }}
    >
      <span style={{ fontSize: 13 }}>▸</span>
      <span
        style={{
          background: stripBg,
          color: stripFg,
          padding: "3px 8px",
          flex: 1,
          textTransform: "uppercase",
        }}
      >
        {label}
      </span>
    </div>
  );
}

function LayoutHarvard({
  contact,
  experience,
  education,
  skills,
  languages,
  awards,
  certificates,
  projects,
  linkedin,
  tpl,
}: Omit<ResumePreviewProps, "nationality" | "dateOfBirth">) {
  const line = [
    contact.email && `✉ ${contact.email}`,
    contact.phone && `📞 ${contact.phone}`,
    linkedin && `🔗 ${linkedin}`,
  ]
    .filter(Boolean)
    .join(" • ");

  return (
    <div style={{ ...paper, background: tpl.bg, color: "#000000", ...serif }}>
      <div style={{ borderTop: "1px solid #000", borderBottom: "1px solid #000", textAlign: "center", padding: "12px 0 14px", marginBottom: 18 }}>
        <h1 style={{ margin: 0, fontSize: 32, fontWeight: 700 }}>{contact.name}</h1>
        <p style={{ margin: "6px 0 0", fontSize: 18, fontStyle: "italic" }}>{contact.title}</p>
        <p style={{ margin: "8px 0 0", fontSize: 16 }}>{line}</p>
      </div>

      <HarvardSection title="PROFILE" />
      <p style={{ margin: "0 0 14px", fontSize: 16, textAlign: "justify", lineHeight: 1.45 }}>{contact.summary}</p>

      <HarvardSection title="PROFESSIONAL EXPERIENCE" />
      {experience.map((job, i) => (
        <div key={i} style={{ marginBottom: 21 }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
            <span style={{ fontSize: 13, fontWeight: 700 }}>{job.title}</span>
            <span style={{ fontSize: 16 }}>{job.period}</span>
          </div>
          <div style={{ fontSize: 16, fontStyle: "italic", marginBottom: 5 }}>{job.company}</div>
          <ul style={{ margin: 0, paddingLeft: 26, fontSize: 16, lineHeight: 1.4 }}>
            {job.bullets.map((b, j) => (
              <li key={j}>{b}</li>
            ))}
          </ul>
        </div>
      ))}

      <HarvardSection title="EDUCATION" />
      {education.map((ed, i) => (
        <div key={i} style={{ marginBottom: 10 }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
            <span style={{ fontSize: 13, fontWeight: 700 }}>{ed.degree}</span>
            <span style={{ fontSize: 16 }}>{ed.year}</span>
          </div>
          <div style={{ fontSize: 16, fontStyle: "italic" }}>{ed.school}</div>
        </div>
      ))}

      <HarvardSection title="SKILLS" />
      <div style={{ fontSize: 16, lineHeight: 1.6, marginBottom: 21 }}>
        {skills.map((g, gi) => (
          <div key={gi} style={{ marginBottom: 3 }}>
            {g.category && <strong>{g.category}: </strong>}
            {g.items.join(" · ")}
          </div>
        ))}
      </div>

      {projects && projects.length > 0 && (
        <>
          <HarvardSection title="PROJECTS" />
          {projects.map((p, i) => (
            <div key={i} style={{ marginBottom: 13 }}>
              <div style={{ fontSize: 13, fontWeight: 700 }}>{p.title}</div>
              {p.technologies && p.technologies.length > 0 && (
                <div style={{ fontSize: 14, fontStyle: "italic", color: "#555", marginBottom: 2 }}>{p.technologies.join(" | ")}</div>
              )}
              <ul style={{ margin: "2px 0 0", paddingLeft: 26, fontSize: 16, lineHeight: 1.4 }}>
                {p.bullets.map((b, j) => <li key={j}>{b}</li>)}
              </ul>
            </div>
          ))}
        </>
      )}

      {certificates && certificates.length > 0 && (
        <>
          <HarvardSection title="CERTIFICATIONS" />
          <ul style={{ margin: "0 0 12px", paddingLeft: 26, fontSize: 16, lineHeight: 1.4 }}>
            {certificates.map((c, i) => <li key={i}>{c}</li>)}
          </ul>
        </>
      )}

      {languages && languages.length > 0 && (
        <>
          <HarvardSection title="LANGUAGES" />
          <p style={{ margin: "0 0 12px", fontSize: 16 }}>
            {languages.map((lang, i) => (
              <span key={i}>
                {i > 0 ? " · " : ""}
                <strong>{lang.name}</strong> {dotRating(lang.level)}
              </span>
            ))}
          </p>
        </>
      )}

      {awards && awards.length > 0 && (
        <>
          <HarvardSection title="AWARDS" />
          {awards.map((a, i) => (
            <div key={i} style={{ marginBottom: 10 }}>
              <div style={{ fontSize: 13, fontWeight: 700 }}>{a.title}</div>
              {a.institution && <div style={{ fontSize: 16, fontStyle: "italic" }}>{a.institution}</div>}
            </div>
          ))}
        </>
      )}
    </div>
  );
}

function HarvardSection({ title }: { title: string }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        margin: "16px 0 10px",
        fontSize: 13,
        fontWeight: 700,
        letterSpacing: 0.5,
        textTransform: "uppercase",
      }}
    >
      <span style={{ flex: 1, borderBottom: "1px solid #000", opacity: 0.85 }} />
      <span style={{ whiteSpace: "nowrap" }}>{title}</span>
      <span style={{ flex: 1, borderBottom: "1px solid #000", opacity: 0.85 }} />
    </div>
  );
}

function LayoutModernTeal({
  contact,
  experience,
  education,
  skills,
  languages,
  certificates,
  projects,
  awards,
  linkedin,
  nationality,
  dateOfBirth,
  tpl,
}: Omit<ResumePreviewProps, never>) {
  const a = tpl.accent;

  const contactGrid = [
    { icon: "✉", text: contact.email },
    { icon: "📞", text: contact.phone },
    { icon: "🔗", text: linkedin ?? "—" },
    { icon: "📍", text: contact.location },
    { icon: "🌐", text: nationality ?? "—" },
    { icon: "🎂", text: dateOfBirth ?? "—" },
  ];

  return (
    <div style={{ ...paper, background: tpl.bg, color: tpl.textColor, position: "relative", ...sans }}>
      <div style={{ position: "absolute", top: 20, right: 22, width: 70, height: 70, borderRadius: "50%", background: tpl.mutedColor + "33", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 24, fontWeight: 700, color: tpl.textColor }}>
        {initials(contact.name)}
      </div>

      <div style={{ paddingRight: 64 }}>
        <h1 style={{ margin: 0, fontSize: 29, fontWeight: 700, display: "inline" }}>{contact.name}</h1>
        <span style={{ marginLeft: 8, fontSize: 16, fontWeight: 400, color: tpl.mutedColor }}>{contact.title}</span>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "5px 16px",
          marginTop: 10,
          fontSize: 14,
          color: tpl.mutedColor,
        }}
      >
        {contactGrid.map((c, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 5 }}>
            <span>{c.icon}</span>
            <span>{c.text}</span>
          </div>
        ))}
      </div>

      <AccentBar title="SUMMARY" accent={a} />
      <p style={{ margin: "0 0 12px", fontSize: 16, lineHeight: 1.45 }}>{contact.summary}</p>

      <AccentBar title="PROFESSIONAL EXPERIENCE" accent={a} />
      {experience.map((job, i) => (
        <div key={i} style={{ display: "grid", gridTemplateColumns: "28% 1fr", gap: 13, marginBottom: 21, fontSize: 16 }}>
          <div style={{ color: tpl.mutedColor, lineHeight: 1.35 }}>
            <div>{job.period}</div>
            <div>{contact.location}</div>
          </div>
          <div>
            <div style={{ fontWeight: 700 }}>{job.company}</div>
            <div style={{ marginBottom: 5 }}>{job.title}</div>
            <ul style={{ margin: 0, paddingLeft: 24, lineHeight: 1.35 }}>
              {job.bullets.map((b, j) => (
                <li key={j}>{b}</li>
              ))}
            </ul>
          </div>
        </div>
      ))}

      <AccentBar title="EDUCATION" accent={a} />
      {education.map((ed, i) => (
        <div key={i} style={{ display: "grid", gridTemplateColumns: "28% 1fr", gap: 13, marginBottom: 13, fontSize: 16 }}>
          <div style={{ color: tpl.mutedColor }}>{ed.year}</div>
          <div>
            <div style={{ fontWeight: 700 }}>{ed.degree}</div>
            <div>{ed.school}</div>
          </div>
        </div>
      ))}

      <AccentBar title="SKILLS" accent={a} />
      <div style={{ fontSize: 16, lineHeight: 1.6, marginBottom: 13 }}>
        {skills.map((g, gi) => (
          <div key={gi} style={{ marginBottom: 3 }}>
            {g.category && <strong>{g.category}: </strong>}
            {g.items.join(" · ")}
          </div>
        ))}
      </div>

      {languages && languages.length > 0 && (
        <>
          <AccentBar title="LANGUAGES" accent={a} />
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8, fontSize: 16, marginBottom: 13 }}>
            {languages.map((lang, i) => (
              <span key={i}>
                {lang.name}
                {lang.level ? ` (${lang.level})` : ""}
              </span>
            ))}
          </div>
        </>
      )}

      {projects && projects.length > 0 && (
        <>
          <AccentBar title="PROJECTS" accent={a} />
          {projects.map((p, i) => (
            <div key={i} style={{ display: "grid", gridTemplateColumns: "28% 1fr", gap: 13, marginBottom: 13, fontSize: 16 }}>
              <div style={{ color: tpl.mutedColor }}>
                {p.technologies && p.technologies.length > 0 ? p.technologies.slice(0, 3).join(", ") : ""}
              </div>
              <div>
                <div style={{ fontWeight: 700 }}>{p.title}</div>
                <ul style={{ margin: "2px 0 0", paddingLeft: 24, lineHeight: 1.35 }}>
                  {p.bullets.map((b, j) => <li key={j}>{b}</li>)}
                </ul>
              </div>
            </div>
          ))}
        </>
      )}

      {certificates && certificates.length > 0 && (
        <>
          <AccentBar title="CERTIFICATIONS" accent={a} />
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8, fontSize: 16 }}>
            {certificates.map((c, i) => (
              <span key={i}>{c}</span>
            ))}
          </div>
        </>
      )}

      {awards && awards.length > 0 && (
        <>
          <AccentBar title="AWARDS" accent={a} />
          {awards.map((a2, i) => (
            <div key={i} style={{ marginBottom: 5, fontSize: 16 }}>
              <span style={{ fontWeight: 700 }}>{a2.title}</span>
              {a2.institution && <span style={{ color: tpl.mutedColor, fontStyle: "italic" }}> — {a2.institution}</span>}
            </div>
          ))}
        </>
      )}
    </div>
  );
}

function AccentBar({ title, accent }: { title: string; accent: string }) {
  return (
    <div
      style={{
        background: accent,
        color: "#fff",
        textAlign: "center",
        fontSize: 13,
        fontWeight: 700,
        letterSpacing: 0.5,
        padding: "5px 0",
        margin: "12px 0 8px",
      }}
    >
      {title}
    </div>
  );
}

function LayoutCorporateClean({
  contact,
  experience,
  education,
  skills,
  languages,
  certificates,
  projects,
  awards,
  linkedin,
  tpl,
  dense,
}: Omit<ResumePreviewProps, "nationality" | "dateOfBirth"> & { dense?: boolean }) {
  const a = tpl.accent;
  const fs = dense ? { name: 26, body: 14, head: 16, sub: 14 } : { name: 29, body: 16, head: 13, sub: 16 };
  const gap = dense ? 13 : 21;

  const contactLine = [contact.email, contact.phone, contact.location, linkedin].filter(Boolean).join(" | ");

  return (
    <div style={{ ...paper, background: tpl.bg, color: tpl.textColor, ...sans }}>
      <h1 style={{ margin: 0, fontSize: fs.name, fontWeight: 700 }}>{contact.name}</h1>
      <p style={{ margin: "4px 0 0", fontSize: fs.sub, fontWeight: 600, color: a }}>{contact.title}</p>
      <p style={{ margin: "8px 0 0", fontSize: dense ? 12 : 14, color: a }}>{contactLine}</p>

      <CorpSection title="SUMMARY" accent={a} dense={dense} />
      <p style={{ margin: `0 0 ${gap}px`, fontSize: fs.body, lineHeight: 1.45, textAlign: "justify" }}>{contact.summary}</p>

      <CorpSection title="PROFESSIONAL EXPERIENCE" accent={a} dense={dense} />
      {experience.map((job, i) => (
        <div key={i} style={{ marginBottom: dense ? 13 : 21 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 10, flexWrap: "wrap" }}>
            <span style={{ fontSize: fs.sub, fontWeight: 700 }}>
              {job.title}
              <span style={{ fontWeight: 400, fontStyle: "italic" }}>, {job.company}</span>
            </span>
            <span style={{ fontSize: dense ? 12 : 14, textAlign: "right", whiteSpace: "nowrap" }}>
              {job.period}
              <br />
              <span style={{ color: tpl.mutedColor }}>{contact.location}</span>
            </span>
          </div>
          <ul style={{ margin: "4px 0 0", paddingLeft: 26, fontSize: fs.body, lineHeight: 1.35 }}>
            {job.bullets.map((b, j) => (
              <li key={j}>{b}</li>
            ))}
          </ul>
        </div>
      ))}

      <CorpSection title="EDUCATION" accent={a} dense={dense} />
      {education.map((ed, i) => (
        <div key={i} style={{ marginBottom: dense ? 10 : 13, display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap" }}>
          <span style={{ fontSize: fs.sub, fontWeight: 700 }}>
            {ed.degree}
            <span style={{ fontWeight: 400, fontStyle: "italic" }}> — {ed.school}</span>
          </span>
          <span style={{ fontSize: dense ? 12 : 14, textAlign: "right", color: tpl.mutedColor }}>
            {ed.year}
            <br />
            {contact.location}
          </span>
        </div>
      ))}

      <CorpSection title="SKILLS" accent={a} dense={dense} />
      <div style={{ fontSize: fs.body, lineHeight: 1.6, marginBottom: gap }}>
        {skills.map((g, gi) => (
          <div key={gi} style={{ marginBottom: 2 }}>
            {g.category && <strong>{g.category}: </strong>}
            {g.items.join(" · ")}
          </div>
        ))}
      </div>

      {languages && languages.length > 0 && (
        <>
          <CorpSection title="LANGUAGES" accent={a} dense={dense} />
          <p style={{ margin: `0 0 ${gap}px`, fontSize: fs.body, lineHeight: 1.45 }}>
            {languages.map((lang, i) => (
              <span key={i}>
                {i > 0 ? " · " : ""}
                {lang.name}
                {lang.level ? ` (${lang.level})` : ""}
              </span>
            ))}
          </p>
        </>
      )}

      {projects && projects.length > 0 && (
        <>
          <CorpSection title="PROJECTS" accent={a} dense={dense} />
          {projects.map((p, i) => (
            <div key={i} style={{ marginBottom: dense ? 8 : 13 }}>
              <div style={{ fontSize: fs.sub, fontWeight: 700 }}>{p.title}</div>
              {p.technologies && p.technologies.length > 0 && (
                <div style={{ fontSize: dense ? 12 : 14, color: a, marginBottom: 2 }}>{p.technologies.join(" | ")}</div>
              )}
              <ul style={{ margin: "4px 0 0", paddingLeft: 26, fontSize: fs.body, lineHeight: 1.35 }}>
                {p.bullets.map((b, j) => (
                  <li key={j}>{b}</li>
                ))}
              </ul>
              {p.description && p.bullets.length === 0 && (
                <p style={{ fontSize: fs.body, lineHeight: 1.45 }}>{p.description}</p>
              )}
            </div>
          ))}
        </>
      )}

      {certificates && certificates.length > 0 && (
        <>
          <CorpSection title="CERTIFICATIONS" accent={a} dense={dense} />
          <div style={{ display: "grid", gridTemplateColumns: dense ? "repeat(3, 1fr)" : "repeat(2, 1fr)", gap: "2px 10px", fontSize: fs.body }}>
            {certificates.map((c, i) => (
              <div key={i} style={{ display: "flex", gap: 5 }}>
                <span>•</span>
                <span>{c}</span>
              </div>
            ))}
          </div>
        </>
      )}

      {awards && awards.length > 0 && (
        <>
          <CorpSection title="AWARDS" accent={a} dense={dense} />
          {awards.map((a2, i) => (
            <div key={i} style={{ marginBottom: 5, fontSize: fs.body }}>
              <span style={{ fontWeight: 700 }}>{a2.title}</span>
              {a2.institution && <span style={{ fontStyle: "italic", color: tpl.mutedColor }}> — {a2.institution}</span>}
            </div>
          ))}
        </>
      )}
    </div>
  );
}

function CorpSection({ title, accent, dense }: { title: string; accent: string; dense?: boolean }) {
  return (
    <div
      style={{
        fontSize: dense ? 16 : 13,
        fontWeight: 700,
        color: accent,
        borderBottom: `1px solid ${accent}`,
        paddingBottom: 3,
        margin: dense ? "10px 0 6px" : "14px 0 8px",
      }}
    >
      {title}
    </div>
  );
}

function LayoutSingleMinimal({
  contact,
  experience,
  education,
  skills,
  projects,
  certificates,
  awards,
  languages,
  linkedin,
  tpl,
}: Omit<ResumePreviewProps, "nationality" | "dateOfBirth">) {
  const contactLine = [contact.email, contact.phone, contact.location, linkedin].filter(Boolean).join(" · ");

  return (
    <div style={{ ...paper, background: tpl.bg, color: tpl.textColor, ...serif }}>
      <h1 style={{ margin: 0, fontSize: 32, fontWeight: 700 }}>{contact.name}</h1>
      <p style={{ margin: "6px 0 0", fontSize: 18, color: tpl.mutedColor }}>{contact.title}</p>
      <p style={{ margin: "10px 0 0", fontSize: 16, color: tpl.mutedColor }}>{contactLine}</p>

      <MinimalSection title="Profile" tpl={tpl} />
      <p style={{ margin: "0 0 20px", fontSize: 16, lineHeight: 1.55, textAlign: "justify" }}>{contact.summary}</p>

      <MinimalSection title="Experience" tpl={tpl} />
      {experience.map((job, i) => (
        <div key={i} style={{ marginBottom: 21 }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 10, fontSize: 13, fontWeight: 700 }}>
            <span>{job.title}</span>
            <span style={{ fontWeight: 400, color: tpl.mutedColor }}>{job.period}</span>
          </div>
          <div style={{ fontSize: 16, fontStyle: "italic", color: tpl.mutedColor, marginBottom: 8 }}>{job.company}</div>
          <ul style={{ margin: 0, paddingLeft: 32, fontSize: 16, lineHeight: 1.45 }}>
            {job.bullets.map((b, j) => (
              <li key={j}>{b}</li>
            ))}
          </ul>
        </div>
      ))}

      <MinimalSection title="Education" tpl={tpl} />
      {education.map((ed, i) => (
        <div key={i} style={{ marginBottom: 13, fontSize: 16 }}>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <span style={{ fontWeight: 700 }}>{ed.degree}</span>
            <span style={{ color: tpl.mutedColor }}>{ed.year}</span>
          </div>
          <div style={{ fontStyle: "italic", color: tpl.mutedColor }}>{ed.school}</div>
        </div>
      ))}

      <MinimalSection title="Skills" tpl={tpl} />
      <div style={{ fontSize: 16, lineHeight: 1.6, marginBottom: 10 }}>
        {skills.map((g, gi) => (
          <div key={gi} style={{ marginBottom: 3 }}>
            {g.category && <strong>{g.category}: </strong>}
            {g.items.join(" · ")}
          </div>
        ))}
      </div>

      {projects && projects.length > 0 && (
        <>
          <MinimalSection title="Projects" tpl={tpl} />
          {projects.map((p, i) => (
            <div key={i} style={{ marginBottom: 18 }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 10, fontSize: 13, fontWeight: 700 }}>
                <span>{p.title}</span>
              </div>
              {p.technologies && p.technologies.length > 0 && (
                <div style={{ fontSize: 14, fontStyle: "italic", color: tpl.mutedColor, marginBottom: 5 }}>{p.technologies.join(" | ")}</div>
              )}
              <ul style={{ margin: 0, paddingLeft: 32, fontSize: 16, lineHeight: 1.45 }}>
                {p.bullets.map((b, j) => <li key={j}>{b}</li>)}
              </ul>
            </div>
          ))}
        </>
      )}

      {certificates && certificates.length > 0 && (
        <>
          <MinimalSection title="Certifications" tpl={tpl} />
          <ul style={{ margin: 0, paddingLeft: 32, fontSize: 16, lineHeight: 1.45 }}>
            {certificates.map((c, i) => <li key={i}>{c}</li>)}
          </ul>
        </>
      )}

      {awards && awards.length > 0 && (
        <>
          <MinimalSection title="Awards" tpl={tpl} />
          {awards.map((a, i) => (
            <div key={i} style={{ marginBottom: 8, fontSize: 16 }}>
              <span style={{ fontWeight: 700 }}>{a.title}</span>
              {a.institution && <span style={{ fontStyle: "italic", color: tpl.mutedColor }}> — {a.institution}</span>}
            </div>
          ))}
        </>
      )}

      {languages && languages.length > 0 && (
        <>
          <MinimalSection title="Languages" tpl={tpl} />
          <p style={{ margin: 0, fontSize: 16 }}>
            {languages.map((l, i) => (
              <span key={i}>{i > 0 ? " · " : ""}<strong>{l.name}</strong>{l.level ? ` (${l.level})` : ""}</span>
            ))}
          </p>
        </>
      )}
    </div>
  );
}

function MinimalSection({ title, tpl }: { title: string; tpl: ResumeTemplate }) {
  return (
    <div
      style={{
        fontSize: 13,
        fontWeight: 700,
        letterSpacing: 1,
        textTransform: "uppercase",
        borderBottom: `1px solid ${tpl.mutedColor}99`,
        paddingBottom: 4,
        margin: "22px 0 10px",
        color: tpl.textColor,
      }}
    >
      {title}
    </div>
  );
}

function LayoutTwoColAccent({
  contact,
  experience,
  education,
  skills,
  projects,
  certificates,
  awards,
  languages,
  linkedin,
  tpl,
}: Omit<ResumePreviewProps, "nationality" | "dateOfBirth">) {
  const a = tpl.accent;
  const contactLine = [contact.email, contact.phone, linkedin].filter(Boolean).join(" · ");

  return (
    <div style={{ ...paper, background: tpl.bg, color: tpl.textColor, ...sans }}>
      <h1 style={{ margin: 0, fontSize: 32, fontWeight: 700 }}>{contact.name}</h1>
      <p style={{ margin: "4px 0 0", fontSize: 18, fontWeight: 600, color: a }}>{contact.title}</p>
      <p style={{ margin: "8px 0 0", fontSize: 16, color: tpl.mutedColor }}>{contactLine}</p>

      <div style={{ display: "flex", gap: 14, marginTop: 14 }}>
        <div style={{ width: "65%", minWidth: 0 }}>
          <TwoColHeader label="EXPERIENCE" accent={a} />
          {experience.map((job, i) => (
            <div key={i} style={{ marginBottom: 21, fontSize: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 10, fontWeight: 700 }}>
                <span>{job.title}</span>
                <span style={{ fontWeight: 400, color: tpl.mutedColor, whiteSpace: "nowrap" }}>{job.period}</span>
              </div>
              <div style={{ fontStyle: "italic", color: tpl.mutedColor, marginBottom: 5 }}>{job.company}</div>
              <ul style={{ margin: 0, paddingLeft: 24, lineHeight: 1.35 }}>
                {job.bullets.map((b, j) => (
                  <li key={j}>{b}</li>
                ))}
              </ul>
            </div>
          ))}

          <TwoColHeader label="EDUCATION" accent={a} />
          {education.map((ed, i) => (
            <div key={i} style={{ marginBottom: 10, fontSize: 16 }}>
              <strong>{ed.degree}</strong>
              <div style={{ color: tpl.mutedColor }}>{ed.school} · {ed.year}</div>
            </div>
          ))}

          {projects && projects.length > 0 && (
            <>
              <TwoColHeader label="PROJECTS" accent={a} />
              {projects.map((p, i) => (
                <div key={i} style={{ marginBottom: 13, fontSize: 16 }}>
                  <div style={{ fontWeight: 700 }}>{p.title}</div>
                  {p.technologies && p.technologies.length > 0 && (
                    <div style={{ fontSize: 14, color: tpl.mutedColor, marginBottom: 2 }}>{p.technologies.join(" | ")}</div>
                  )}
                  <ul style={{ margin: "2px 0 0", paddingLeft: 24, lineHeight: 1.35 }}>
                    {p.bullets.map((b, j) => <li key={j}>{b}</li>)}
                  </ul>
                </div>
              ))}
            </>
          )}
        </div>

        <div style={{ width: "35%", minWidth: 0 }}>
          <TwoColHeader label="SKILLS" accent={a} />
          <div style={{ display: "flex", flexWrap: "wrap", gap: 5, marginBottom: 18 }}>
            {skills.flatMap((g) => g.items).map((s, i) => (
              <span
                key={i}
                style={{
                  fontSize: 12,
                  padding: "2px 6px",
                  borderRadius: 3,
                  background: a,
                  color: "#ffffff",
                }}
              >
                {s}
              </span>
            ))}
          </div>

          <TwoColHeader label="EDUCATION" accent={a} />
          {education.map((ed, i) => (
            <div key={i} style={{ marginBottom: 10, fontSize: 14, lineHeight: 1.35 }}>
              <div style={{ fontWeight: 700 }}>{ed.degree}</div>
              <div style={{ color: tpl.mutedColor }}>{ed.school}</div>
              <div style={{ color: tpl.mutedColor }}>{ed.year}</div>
            </div>
          ))}

          {certificates && certificates.length > 0 && (
            <>
              <TwoColHeader label="CERTIFICATIONS" accent={a} />
              {certificates.map((c, i) => (
                <div key={i} style={{ fontSize: 14, marginBottom: 5, color: tpl.mutedColor }}>• {c}</div>
              ))}
            </>
          )}

          {languages && languages.length > 0 && (
            <>
              <TwoColHeader label="LANGUAGES" accent={a} />
              {languages.map((l, i) => (
                <div key={i} style={{ fontSize: 14, marginBottom: 5 }}>
                  <strong>{l.name}</strong>{l.level ? <span style={{ color: tpl.mutedColor }}> ({l.level})</span> : ""}
                </div>
              ))}
            </>
          )}

          {awards && awards.length > 0 && (
            <>
              <TwoColHeader label="AWARDS" accent={a} />
              {awards.map((a2, i) => (
                <div key={i} style={{ fontSize: 14, marginBottom: 5 }}>
                  <strong>{a2.title}</strong>
                  {a2.institution && <div style={{ color: tpl.mutedColor }}>{a2.institution}</div>}
                </div>
              ))}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function TwoColHeader({ label, accent }: { label: string; accent: string }) {
  return (
    <div
      style={{
        fontSize: 16,
        fontWeight: 700,
        letterSpacing: 0.5,
        color: accent,
        textTransform: "uppercase",
        borderBottom: `2px solid ${accent}`,
        paddingBottom: 4,
        marginBottom: 10,
      }}
    >
      {label}
    </div>
  );
}

export function ResumePreview({
  contact,
  experience,
  education,
  skills,
  tpl,
  linkedin,
  languages,
  awards,
  certificates,
  projects,
  nationality,
  dateOfBirth,
}: ResumePreviewProps) {
  const common = {
    contact,
    experience,
    education,
    skills,
    linkedin,
    languages,
    awards,
    certificates,
    projects,
    nationality,
    dateOfBirth,
  };

  switch (tpl.layout) {
    case "classic-center":
      return <LayoutClassicCenter {...common} tpl={tpl} />;
    case "sidebar-dark":
      return <LayoutSidebarDark {...common} tpl={tpl} />;
    case "harvard":
      return <LayoutHarvard {...common} tpl={tpl} />;
    case "modern-teal":
      return <LayoutModernTeal {...common} tpl={tpl} />;
    case "corporate-clean":
      return <LayoutCorporateClean {...common} tpl={tpl} dense={false} />;
    case "corporate-dense":
      return <LayoutCorporateClean {...common} tpl={tpl} dense />;
    case "single-minimal":
      return <LayoutSingleMinimal {...common} tpl={tpl} />;
    case "two-col-accent":
      return <LayoutTwoColAccent {...common} tpl={tpl} />;
    default:
      return <LayoutClassicCenter {...common} tpl={tpl} />;
  }
}
