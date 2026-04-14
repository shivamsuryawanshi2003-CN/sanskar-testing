"use client";

import { useState } from "react";
import { DashboardLayout } from "@/components/DashboardLayout";
import { Briefcase, MapPin, DollarSign, Clock, Bookmark, ExternalLink, TrendingUp, Target, CheckCircle, Search } from "lucide-react";

const STATS = [
  { label: "Total Matches", value: "47", icon: Target },
  { label: "High Match (90%+)", value: "12", icon: TrendingUp },
  { label: "Saved Jobs", value: "8", icon: Bookmark },
  { label: "Applied", value: "5", icon: CheckCircle },
];

const JOBS = [
  { title: "Senior Product Designer", company: "DesignFlow Systems", location: "San Francisco, CA", salary: "$120k – $160k", posted: "2 days ago", match: 94, remote: true, description: "Leading the design of our next-generation cloud platform with a focus on user experience.", skills: ["Figma", "Design Systems", "User Research", "Prototyping"] },
  { title: "Lead UX Designer", company: "TechCorp", location: "New York, NY", salary: "$130k – $170k", posted: "3 days ago", match: 89, remote: false, description: "Drive UX strategy across multiple product lines and mentor junior designers.", skills: ["Sketch", "UX Strategy", "A/B Testing", "Mentorship"] },
  { title: "Product Design Manager", company: "Innovate Labs", location: "Remote", salary: "$140k – $180k", posted: "5 days ago", match: 86, remote: true, description: "Build and lead a world-class product design team across 3 continents.", skills: ["Leadership", "Product Strategy", "Design Systems", "Figma"] },
  { title: "UI/UX Designer", company: "StartupXYZ", location: "Austin, TX", salary: "$100k – $130k", posted: "1 week ago", match: 82, remote: true, description: "Join our fast-growing startup to design beautiful, accessible interfaces.", skills: ["Figma", "React", "Animation", "Mobile Design"] },
];

const FILTERS = ["All Matches", "90%+ Match", "Remote Only", "Senior Level", "Recently Posted"];

function MatchBadge({ match }: { match: number }) {
  return <span className="text-[11px] font-bold px-2.5 py-1 rounded-lg border border-primary/20 bg-primary/10 text-primary">{match}% Match</span>;
}

export default function JobMatchesPage() {
  const [activeFilter, setActiveFilter] = useState("All Matches");
  const [saved, setSaved] = useState<Set<number>>(new Set());

  return (
    <DashboardLayout>
      <div className="p-4 sm:p-8 max-w-5xl mx-auto">

        {/* Page Header */}
        <div className="mb-8">
          <p className="text-[11px] font-bold tracking-[0.3em] uppercase text-muted-foreground/60 mb-2">✦ AI Job Matching</p>
          <h1 className="text-2xl font-extrabold text-foreground leading-tight" style={{ fontFamily: "'Playfair Display', serif" }}>
            Your Job{" "}
            <span className="warm-text">Matches</span>
          </h1>
          <p className="text-[13px] text-muted-foreground mt-1">AI-curated opportunities that align with your skills and career goals.</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {STATS.map((stat) => (
            <div key={stat.label} className="bg-card rounded-2xl border border-border p-5">
              <div className="flex items-center justify-between mb-3">
                <p className="text-[11px] font-bold text-muted-foreground uppercase tracking-wide">{stat.label}</p>
                <div className="w-8 h-8 rounded-xl bg-primary/10 flex items-center justify-center">
                  <stat.icon className="w-4 h-4 text-primary" />
                </div>
              </div>
              <p className="text-3xl font-extrabold text-primary tabular-nums">{stat.value}</p>
            </div>
          ))}
        </div>

        {/* Filters + Search */}
        <div className="flex flex-wrap items-center gap-3 mb-6">
          {FILTERS.map((f) => (
            <button
              key={f}
              onClick={() => setActiveFilter(f)}
              className={`px-4 py-2 rounded-xl text-[12px] font-semibold border transition-all duration-200 ${
                activeFilter === f
                  ? "bg-primary text-primary-foreground border-primary shadow-[0_4px_12px_hsl(25_55%_58%/0.25)]"
                  : "bg-card text-muted-foreground border-border hover:border-primary/30 hover:text-foreground"
              }`}
            >
              {f}
            </button>
          ))}
          <div className="w-full sm:w-auto sm:ml-auto relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input placeholder="Search jobs..." className="pl-9 pr-4 py-2 bg-card border border-border rounded-xl text-[12px] text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50 w-full sm:w-48" />
          </div>
        </div>

        {/* Job Cards */}
        <div className="space-y-4">
          {JOBS.map((job, index) => (
            <div key={index} className="bg-card rounded-2xl border border-border p-6 hover:border-primary/20 transition-all duration-200 group">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center shrink-0 font-bold text-primary text-[14px]">
                  {job.company[0]}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div>
                      <div className="flex items-center gap-2.5 mb-1 flex-wrap">
                        <h3 className="text-[15px] font-bold text-foreground">{job.title}</h3>
                        <MatchBadge match={job.match} />
                        {job.remote && <span className="text-[10px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-lg bg-secondary text-muted-foreground border border-border">Remote</span>}
                      </div>
                      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[12px] text-muted-foreground font-medium mb-3">
                        <span className="flex items-center gap-1"><Briefcase className="w-3.5 h-3.5" />{job.company}</span>
                        <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5" />{job.location}</span>
                        <span className="flex items-center gap-1"><DollarSign className="w-3.5 h-3.5" />{job.salary}</span>
                        <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" />{job.posted}</span>
                      </div>
                    </div>
                  </div>

                  <p className="text-[12px] text-muted-foreground leading-relaxed mb-3">{job.description}</p>

                  <div className="flex flex-wrap gap-2">
                    {job.skills.map((skill, i) => (
                      <span key={i} className="px-2.5 py-1 rounded-lg bg-secondary border border-border text-[11px] font-semibold text-muted-foreground">{skill}</span>
                    ))}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex flex-col gap-2 shrink-0">
                  <button className="px-5 py-2 rounded-xl bg-primary text-primary-foreground text-[12px] font-bold shadow-[0_4px_12px_hsl(25_55%_58%/0.25)] hover:opacity-90 transition-all duration-200">
                    Apply Now
                  </button>
                  <button
                    onClick={() => setSaved((prev) => { const n = new Set(prev); if (n.has(index)) { n.delete(index); } else { n.add(index); } return n; })}
                    className={`px-5 py-2 rounded-xl text-[12px] font-semibold border transition-all duration-200 ${saved.has(index) ? "bg-primary/10 border-primary/20 text-primary" : "bg-card border-border text-muted-foreground hover:border-primary/30"}`}
                  >
                    <span className="flex items-center gap-1.5">
                      <Bookmark className={`w-3.5 h-3.5 ${saved.has(index) ? "fill-current" : ""}`} />
                      {saved.has(index) ? "Saved" : "Save"}
                    </span>
                  </button>
                  <button className="px-5 py-2 rounded-xl bg-card border border-border text-muted-foreground text-[12px] font-semibold hover:border-primary/30 transition-all duration-200 flex items-center justify-center">
                    <ExternalLink className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

      </div>
    </DashboardLayout>
  );
}
