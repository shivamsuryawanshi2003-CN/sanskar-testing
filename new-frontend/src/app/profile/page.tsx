"use client";

import { DashboardLayout } from "@/components/DashboardLayout";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Mail, Phone, MapPin, Briefcase, Save, Camera, User, Target, Link2 } from "lucide-react";

function SectionCard({ title, icon: Icon, children }: { title: string; icon: React.ElementType<{ className?: string }>; children: React.ReactNode }) {
  return (
    <div className="bg-card rounded-2xl border border-border p-6 mb-5">
      <div className="flex items-center gap-2.5 mb-5 pb-4 border-b border-border">
        <div className="w-8 h-8 rounded-xl bg-primary/10 flex items-center justify-center">
          <Icon className="w-4 h-4 text-primary" />
        </div>
        <h2 className="text-[14px] font-bold text-foreground">{title}</h2>
      </div>
      {children}
    </div>
  );
}

function FieldInput({ id, label, icon: Icon, type = "text", defaultValue }: { id: string; label: string; icon?: React.ElementType<{ className?: string }>; type?: string; defaultValue?: string }) {
  return (
    <div>
      <Label htmlFor={id} className="text-[11px] font-bold text-muted-foreground mb-1.5 block uppercase tracking-wider">{label}</Label>
      <div className="relative">
        {Icon && <Icon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />}
        <Input
          id={id}
          type={type}
          defaultValue={defaultValue}
          className={`${Icon ? "pl-10" : ""} bg-secondary border-border text-foreground placeholder:text-muted-foreground focus:border-primary/50 rounded-xl text-[13px] h-10`}
        />
      </div>
    </div>
  );
}

export default function ProfilePage() {
  return (
    <DashboardLayout>
      <div className="p-4 sm:p-8 max-w-3xl mx-auto">

        {/* Page Header */}
        <div className="mb-8 flex items-start justify-between">
          <div>
            <p className="text-[11px] font-bold tracking-[0.3em] uppercase text-muted-foreground/60 mb-2">✦ Account</p>
            <h1 className="text-2xl font-extrabold text-foreground leading-tight" style={{ fontFamily: "'Playfair Display', serif" }}>
              Profile{" "}
              <span className="warm-text">Settings</span>
            </h1>
            <p className="text-[13px] text-muted-foreground mt-1">Manage your personal information and career goals</p>
          </div>
          <button className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary text-primary-foreground text-[13px] font-bold shadow-[0_4px_16px_hsl(25_55%_58%/0.25)] hover:opacity-90 transition-all duration-200">
            <Save className="w-4 h-4" />
            Save Changes
          </button>
        </div>

        {/* Avatar */}
        <SectionCard title="Profile Photo" icon={Camera}>
          <div className="flex items-center gap-5">
            <div className="relative group">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary to-warm-dim flex items-center justify-center text-primary-foreground text-2xl font-bold shadow-[0_4px_16px_hsl(25_55%_58%/0.25)]">
                MV
              </div>
              <div className="absolute inset-0 rounded-2xl bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center justify-center cursor-pointer">
                <Camera className="w-5 h-5 text-white" />
              </div>
            </div>
            <div>
              <button className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-border text-muted-foreground text-[12px] font-semibold hover:bg-secondary hover:text-foreground transition-colors duration-200 mb-1.5">
                <Camera className="w-3.5 h-3.5" /> Change Photo
              </button>
              <p className="text-[11px] text-muted-foreground">JPG, PNG or GIF. Max size 2MB.</p>
            </div>
          </div>
        </SectionCard>

        {/* Personal Info */}
        <SectionCard title="Personal Information" icon={User}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FieldInput id="firstName" label="First Name" defaultValue="Marcus" />
            <FieldInput id="lastName" label="Last Name" defaultValue="Vane" />
            <div className="md:col-span-2">
              <FieldInput id="email" label="Email" icon={Mail} type="email" defaultValue="marcus.vane@email.com" />
            </div>
            <FieldInput id="phone" label="Phone" icon={Phone} type="tel" defaultValue="+1 (555) 123-4567" />
            <FieldInput id="location" label="Location" icon={MapPin} defaultValue="San Francisco, CA" />
          </div>
        </SectionCard>

        {/* Professional Info */}
        <SectionCard title="Professional Information" icon={Briefcase}>
          <div className="grid grid-cols-1 gap-4">
            <FieldInput id="title" label="Current Title" icon={Briefcase} defaultValue="Lead Product Designer" />
            <FieldInput id="company" label="Company" defaultValue="DesignFlow Systems" />
            <div className="grid grid-cols-2 gap-4">
              <FieldInput id="experience" label="Years of Experience" type="number" defaultValue="8" />
              <div>
                <Label htmlFor="industry" className="text-[11px] font-bold text-muted-foreground mb-1.5 block uppercase tracking-wider">Industry</Label>
                <select id="industry" className="w-full px-3 py-2.5 bg-secondary border border-border rounded-xl text-foreground text-[13px] focus:outline-none focus:border-primary/50">
                  <option>Technology</option>
                  <option>Design</option>
                  <option>Finance</option>
                  <option>Healthcare</option>
                </select>
              </div>
            </div>
            <FieldInput id="linkedin" label="LinkedIn Profile" icon={Link2} defaultValue="linkedin.com/in/marcusvane" />
            <FieldInput id="portfolio" label="Portfolio URL" icon={Link2} defaultValue="marcusvane.design" />
          </div>
        </SectionCard>

        {/* Career Goals */}
        <SectionCard title="Career Goals" icon={Target}>
          <div className="space-y-4">
            <FieldInput id="targetRole" label="Target Role" defaultValue="Design Director" />
            <FieldInput id="targetCompanies" label="Target Companies" defaultValue="Apple, Meta, Google, Airbnb" />
            <div>
              <Label htmlFor="timeline" className="text-[11px] font-bold text-muted-foreground mb-1.5 block uppercase tracking-wider">Timeline</Label>
              <select id="timeline" className="w-full px-3 py-2.5 bg-secondary border border-border rounded-xl text-foreground text-[13px] focus:outline-none focus:border-primary/50">
                <option>Within 3 months</option>
                <option>3-6 months</option>
                <option>6-12 months</option>
                <option>1+ years</option>
              </select>
            </div>
          </div>
        </SectionCard>

      </div>
    </DashboardLayout>
  );
}
