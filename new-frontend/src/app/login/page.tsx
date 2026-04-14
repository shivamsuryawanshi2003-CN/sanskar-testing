"use client";

import Link from "next/link";
import { useState } from "react";
import { X, Mail, ChevronDown, ArrowRight, Eye, EyeOff, Lock, Sparkles } from "lucide-react";

export default function LoginPage() {
  const [activeTab, setActiveTab] = useState<"signup" | "signin">("signup");
  const [showPassword, setShowPassword] = useState(false);

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6 relative overflow-hidden">
      {/* Background orbs */}
      <div className="absolute top-1/4 left-1/5 w-72 h-72 rounded-full blur-[100px] pointer-events-none" style={{ backgroundColor: "hsl(25 55% 58% / 0.08)" }} />
      <div className="absolute bottom-1/4 right-1/5 w-60 h-60 rounded-full blur-[100px] pointer-events-none" style={{ backgroundColor: "hsl(25 55% 58% / 0.05)" }} />

      {/* Dot grid */}
      <div className="absolute inset-0 pointer-events-none opacity-20"
        style={{
          backgroundImage: "radial-gradient(circle, hsl(25 55% 58% / 0.2) 1px, transparent 1px)",
          backgroundSize: "32px 32px",
        }}
      />

      {/* Card */}
      <div className="relative w-full max-w-[400px] bg-card rounded-2xl border border-border shadow-[0_4px_32px_rgba(0,0,0,0.3)] p-7">
        {/* Close */}
        <Link href="/" className="absolute top-5 right-5 w-8 h-8 rounded-full bg-secondary hover:bg-border flex items-center justify-center transition-colors">
          <X className="w-4 h-4 text-muted-foreground" />
        </Link>

        {/* Logo */}
        <div className="flex items-center gap-2 mb-6">
          <span className="text-[18px] font-bold text-primary tracking-tight" style={{ fontFamily: "'Playfair Display', serif" }}>Jobra AI</span>
        </div>

        {/* Tabs */}
        <div className="flex bg-secondary rounded-xl p-1 mb-6 gap-1">
          {(["signup", "signin"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 py-2 rounded-lg text-[13px] font-semibold transition-all duration-200 ${
                activeTab === tab
                  ? "bg-card text-primary shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {tab === "signup" ? "Sign up" : "Sign in"}
            </button>
          ))}
        </div>

        {/* Title */}
        <h1 className="text-[22px] font-bold text-foreground mb-5" style={{ fontFamily: "'Playfair Display', serif" }}>
          {activeTab === "signup" ? "Create an account" : "Welcome back"}
        </h1>

        {activeTab === "signup" ? (
          <>
            <div className="grid grid-cols-2 gap-2.5 mb-3">
              <input
                type="text"
                placeholder="First name"
                defaultValue="John"
                className="px-3.5 py-3 text-[13px] rounded-xl bg-secondary border border-border text-foreground outline-none focus:border-primary/50 transition-all w-full"
              />
              <input
                type="text"
                placeholder="Last name"
                className="px-3.5 py-3 text-[13px] rounded-xl bg-secondary border border-border text-foreground outline-none focus:border-primary/50 transition-all w-full"
              />
            </div>

            <div className="relative mb-3">
              <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="email"
                placeholder="Enter your email"
                className="w-full pl-10 pr-4 py-3 text-[13px] rounded-xl bg-secondary border border-border text-foreground outline-none focus:border-primary/50 transition-all"
              />
            </div>

            <div className="flex mb-6 rounded-xl bg-secondary border border-border overflow-hidden focus-within:border-primary/50 transition-all">
              <button className="flex items-center gap-1.5 px-3.5 border-r border-border text-[14px] bg-transparent shrink-0">
                <span>🇺🇸</span>
                <ChevronDown className="w-3 h-3 text-muted-foreground" />
              </button>
              <input
                type="tel"
                placeholder="(775) 351-6501"
                className="flex-1 px-3.5 py-3 text-[13px] bg-transparent text-foreground outline-none"
              />
            </div>

            <Link href="/dashboard">
              <button className="w-full py-3 rounded-xl bg-primary text-primary-foreground text-[14px] font-bold hover:opacity-90 transition-opacity shadow-[0_2px_8px_hsl(25_55%_58%/0.3)] mb-5 flex items-center justify-center gap-2">
                <Sparkles className="w-4 h-4" /> Create Account
              </button>
            </Link>
          </>
        ) : (
          <>
            <div className="relative mb-3">
              <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="email"
                placeholder="name@company.com"
                className="w-full pl-10 pr-4 py-3 text-[13px] rounded-xl bg-secondary border border-border text-foreground outline-none focus:border-primary/50 transition-all"
              />
            </div>

            <div className="relative mb-6">
              <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type={showPassword ? "text" : "password"}
                placeholder="••••••••"
                className="w-full pl-10 pr-10 py-3 text-[13px] rounded-xl bg-secondary border border-border text-foreground outline-none focus:border-primary/50 transition-all"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>

            <Link href="/dashboard">
              <button className="w-full py-3 rounded-xl bg-primary text-primary-foreground text-[14px] font-bold hover:opacity-90 transition-opacity shadow-[0_2px_8px_hsl(25_55%_58%/0.3)] mb-5 flex items-center justify-center gap-2">
                Sign In to JOBRA <ArrowRight className="w-4 h-4" />
              </button>
            </Link>
          </>
        )}

        {/* Divider */}
        <div className="relative mb-4">
          <div className="absolute top-1/2 inset-x-0 h-px bg-border" />
          <div className="relative flex justify-center">
            <span className="bg-card px-3 text-[11px] text-muted-foreground uppercase tracking-widest">or continue with</span>
          </div>
        </div>

        {/* Social */}
        <div className="grid grid-cols-2 gap-2.5 mb-5">
          <button className="flex items-center justify-center gap-2 py-2.5 rounded-xl bg-secondary border border-border hover:border-primary/30 transition-colors">
            <svg width="18" height="18" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            <span className="text-[12px] font-medium text-foreground/70">Google</span>
          </button>
          <button className="flex items-center justify-center gap-2 py-2.5 rounded-xl bg-secondary border border-border hover:border-primary/30 transition-colors">
            <svg width="18" height="18" viewBox="0 0 24 24" className="fill-foreground">
              <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.8-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/>
            </svg>
            <span className="text-[12px] font-medium text-foreground/70">Apple</span>
          </button>
        </div>

        {/* Terms */}
        <p className="text-[11.5px] text-muted-foreground text-center">
          By {activeTab === "signup" ? "creating" : "signing into"} an account, you agree to our{" "}
          <Link href="#" className="text-primary hover:underline">Terms & Service</Link>
        </p>
      </div>
    </div>
  );
}
