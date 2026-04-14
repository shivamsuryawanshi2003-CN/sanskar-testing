"use client";

import {
  Document,
  Page,
  Text,
  View,
  StyleSheet,
  pdf,
} from "@react-pdf/renderer";

interface ContactInfo {
  name: string;
  title: string;
  email: string;
  phone: string;
  location: string;
  summary: string;
  linkedin: string;
}
interface ExpItem { title: string; company: string; period: string; bullets: string[]; }
interface EduItem { degree: string; school: string; year: string; }
interface SkillGroup { category: string; items: string[]; }
interface ProjectItem { title: string; description: string; technologies?: string[]; bullets: string[]; }
interface AwardItem { title: string; institution?: string; }
interface LanguageItem { name: string; level?: string; }

const s = StyleSheet.create({
  page: { padding: "12mm 14mm", fontFamily: "Helvetica", fontSize: 10, color: "#222" },
  name: { fontSize: 22, fontWeight: "bold", fontFamily: "Helvetica-Bold", marginBottom: 2 },
  jobTitle: { fontSize: 11, color: "#555", marginBottom: 6 },
  contactRow: { fontSize: 8.5, color: "#444", marginBottom: 12, flexDirection: "row", flexWrap: "wrap", gap: 6 },
  sectionTitle: {
    fontSize: 11, fontWeight: "bold", fontFamily: "Helvetica-Bold",
    textTransform: "uppercase" as const, letterSpacing: 0.5,
    borderBottomWidth: 1, borderBottomColor: "#222", borderBottomStyle: "solid" as const,
    paddingBottom: 3, marginTop: 12, marginBottom: 6,
  },
  summary: { fontSize: 9.5, lineHeight: 1.5, textAlign: "justify" as const, marginBottom: 4 },
  expBlock: { marginBottom: 8 },
  expHeader: { flexDirection: "row" as const, justifyContent: "space-between" as const, marginBottom: 1 },
  expTitle: { fontSize: 10, fontWeight: "bold", fontFamily: "Helvetica-Bold" },
  expPeriod: { fontSize: 9, color: "#555" },
  expCompany: { fontSize: 9, fontStyle: "italic" as const, color: "#555", marginBottom: 3 },
  bullet: { fontSize: 9, lineHeight: 1.45, paddingLeft: 10, marginBottom: 2 },
  eduBlock: { marginBottom: 5 },
  eduRow: { flexDirection: "row" as const, justifyContent: "space-between" as const },
  eduDegree: { fontSize: 10, fontWeight: "bold", fontFamily: "Helvetica-Bold" },
  eduSchool: { fontSize: 9, fontStyle: "italic" as const, color: "#555" },
  eduYear: { fontSize: 9, color: "#555" },
  skillLine: { fontSize: 9, lineHeight: 1.6, marginBottom: 2 },
  skillCat: { fontWeight: "bold", fontFamily: "Helvetica-Bold" },
  projTitle: { fontSize: 10, fontWeight: "bold", fontFamily: "Helvetica-Bold" },
  projTech: { fontSize: 8, color: "#555", marginBottom: 2 },
  certItem: { fontSize: 9, lineHeight: 1.5, marginBottom: 1 },
  awardTitle: { fontSize: 9.5, fontWeight: "bold", fontFamily: "Helvetica-Bold" },
  awardInst: { fontSize: 9, color: "#555", fontStyle: "italic" as const },
  langItem: { fontSize: 9 },
});

function SectionHeader({ title }: { title: string }) {
  return <Text style={s.sectionTitle}>{title}</Text>;
}

interface ResumePDFProps {
  contact: ContactInfo;
  experience: ExpItem[];
  education: EduItem[];
  skills: SkillGroup[];
  projects: ProjectItem[];
  certifications: string[];
  achievements: AwardItem[];
  languages: LanguageItem[];
}

function ResumePDFDocument(props: ResumePDFProps) {
  const { contact, experience, education, skills, projects, certifications, achievements, languages } = props;
  const contactBits = [contact.email, contact.phone, contact.location, contact.linkedin].filter(Boolean);

  return (
    <Document>
      <Page size="A4" style={s.page}>
        <Text style={s.name}>{contact.name}</Text>
        <Text style={s.jobTitle}>{contact.title}</Text>
        <View style={s.contactRow}>
          {contactBits.map((c, i) => (
            <Text key={i}>{c}{i < contactBits.length - 1 ? "  |  " : ""}</Text>
          ))}
        </View>

        {contact.summary ? (
          <>
            <SectionHeader title="PROFILE" />
            <Text style={s.summary}>{contact.summary}</Text>
          </>
        ) : null}

        {experience.length > 0 && (
          <>
            <SectionHeader title="PROFESSIONAL EXPERIENCE" />
            {experience.map((job, i) => (
              <View key={i} style={s.expBlock}>
                <View style={s.expHeader}>
                  <Text style={s.expTitle}>{job.title}</Text>
                  <Text style={s.expPeriod}>{job.period}</Text>
                </View>
                <Text style={s.expCompany}>{job.company}</Text>
                {job.bullets.map((b, j) => (
                  <Text key={j} style={s.bullet}>•  {b}</Text>
                ))}
              </View>
            ))}
          </>
        )}

        {education.length > 0 && (
          <>
            <SectionHeader title="EDUCATION" />
            {education.map((ed, i) => (
              <View key={i} style={s.eduBlock}>
                <View style={s.eduRow}>
                  <Text style={s.eduDegree}>{ed.degree}</Text>
                  <Text style={s.eduYear}>{ed.year}</Text>
                </View>
                <Text style={s.eduSchool}>{ed.school}</Text>
              </View>
            ))}
          </>
        )}

        {skills.length > 0 && (
          <>
            <SectionHeader title="SKILLS" />
            {skills.map((g, i) => (
              <Text key={i} style={s.skillLine}>
                {g.category ? <Text style={s.skillCat}>{g.category}: </Text> : null}
                {g.items.join(" · ")}
              </Text>
            ))}
          </>
        )}

        {projects.length > 0 && (
          <>
            <SectionHeader title="PROJECTS" />
            {projects.map((p, i) => (
              <View key={i} style={s.expBlock}>
                <Text style={s.projTitle}>{p.title}</Text>
                {p.technologies && p.technologies.length > 0 && (
                  <Text style={s.projTech}>{p.technologies.join(" | ")}</Text>
                )}
                {p.bullets.map((b, j) => (
                  <Text key={j} style={s.bullet}>•  {b}</Text>
                ))}
                {p.description && p.bullets.length === 0 && (
                  <Text style={s.bullet}>{p.description}</Text>
                )}
              </View>
            ))}
          </>
        )}

        {certifications.length > 0 && (
          <>
            <SectionHeader title="CERTIFICATIONS" />
            {certifications.map((c, i) => (
              <Text key={i} style={s.certItem}>•  {c}</Text>
            ))}
          </>
        )}

        {achievements.length > 0 && (
          <>
            <SectionHeader title="AWARDS" />
            {achievements.map((a, i) => (
              <View key={i} style={{ marginBottom: 3 }}>
                <Text>
                  <Text style={s.awardTitle}>{a.title}</Text>
                  {a.institution ? <Text style={s.awardInst}>  —  {a.institution}</Text> : null}
                </Text>
              </View>
            ))}
          </>
        )}

        {languages.length > 0 && (
          <>
            <SectionHeader title="LANGUAGES" />
            <Text style={s.langItem}>
              {languages.map((l) => `${l.name}${l.level ? ` (${l.level})` : ""}`).join("  ·  ")}
            </Text>
          </>
        )}
      </Page>
    </Document>
  );
}

export async function generateResumePDF(props: ResumePDFProps): Promise<void> {
  const blob = await pdf(<ResumePDFDocument {...props} />).toBlob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = props.contact.name && props.contact.name !== "Your Name"
    ? `${props.contact.name.replace(/\s+/g, "_")}_Resume.pdf`
    : "Resume.pdf";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
