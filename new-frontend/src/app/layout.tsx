import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

import { ThemeProvider } from "@/components/ThemeProvider";

const geistSans = localFont({
  src: "../../public/fonts/geist-regular.woff2",
  variable: "--font-geist-sans",
  display: "swap",
});

const geistMono = localFont({
  src: "../../public/fonts/geist-mono-regular.woff2",
  variable: "--font-geist-mono",
  display: "swap",
});

const abhayaLibre = localFont({
  src: "../../public/fonts/abhaya-libre-regular.woff2",
  variable: "--font-abhaya-libre",
  display: "swap",
});

export const metadata: Metadata = {
  title: "JobRaai",
  description: "JobRaai - Your AI-powered job platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="scroll-smooth dark" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} ${abhayaLibre.variable} antialiased overscroll-none`}
        style={{ WebkitFontSmoothing: "antialiased", MozOsxFontSmoothing: "grayscale" }}
      >
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
