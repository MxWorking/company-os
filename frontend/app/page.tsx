"use client";

import { useEffect, useState } from "react";

type Lang = "fa" | "en";
type Health = "loading" | "online" | "offline";

const translations = {
  fa: {
    kicker: "پایه اولیه زیرساخت",
    title: "Company-OS",
    subtitle: "هسته آغازین پلتفرم هوشمند، با Next.js و Python FastAPI",
    description: "این صفحه یک تست واقعی برای استقرار فرانت‌اند و ارتباط آن با بک‌اند است. هنوز امکانات اصلی Company-OS پیاده‌سازی نشده‌اند.",
    frontend: "فرانت‌اند",
    backend: "بک‌اند",
    online: "متصل و فعال",
    offline: "در دسترس نیست",
    loading: "در حال بررسی ارتباط",
    frontendDetail: "Next.js روی Vercel",
    backendDetail: "Python FastAPI روی Vercel",
    foundation: "نسخه پایه",
    foundationDetail: "گام اول زیرساخت آماده است، انتقال امکانات اصلی هنوز انجام نشده است.",
    apiCheck: "بررسی مجدد API",
    apiDocs: "مشاهده API Health",
    github: "مخزن GitHub",
    foot: "Company-OS · Deployment Foundation"
  },
  en: {
    kicker: "Deployment foundation",
    title: "Company-OS",
    subtitle: "The starting point for a smart platform, powered by Next.js and Python FastAPI",
    description: "This is a real deployment and backend connectivity check. The full Company-OS features have not been implemented yet.",
    frontend: "Frontend",
    backend: "Backend",
    online: "Connected and healthy",
    offline: "Unavailable",
    loading: "Checking connection",
    frontendDetail: "Next.js on Vercel",
    backendDetail: "Python FastAPI on Vercel",
    foundation: "Foundation release",
    foundationDetail: "The deployable scaffold is in place; original application features still need migrating.",
    apiCheck: "Retry API check",
    apiDocs: "Open API health",
    github: "GitHub repository",
    foot: "Company-OS · Deployment Foundation"
  }
};

export default function HomePage() {
  const [lang, setLang] = useState<Lang>("fa");
  const [health, setHealth] = useState<Health>("loading");
  const t = translations[lang];

  async function checkHealth() {
    setHealth("loading");
    try {
      const response = await fetch("/api/backend-health", { cache: "no-store" });
      const data: { connected?: boolean } = await response.json();
      setHealth(response.ok && data.connected ? "online" : "offline");
    } catch {
      setHealth("offline");
    }
  }

  useEffect(() => {
    void checkHealth();
  }, []);

  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === "fa" ? "rtl" : "ltr";
  }, [lang]);

  return (
    <main className="shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="Company-OS home"><span className="brand-icon">C</span><span>Company<span className="brand-accent">OS</span></span></a>
        <button className="lang-switch" onClick={() => setLang(lang === "fa" ? "en" : "fa")} aria-label="Switch language">{lang === "fa" ? "EN" : "فا"}</button>
      </header>

      <section className="hero" aria-labelledby="headline">
        <p className="eyebrow"><span className="dot" /> {t.kicker}</p>
        <h1 id="headline">{t.title}<span className="headline-star">✳</span></h1>
        <p className="subhead">{t.subtitle}</p>
        <p className="description">{t.description}</p>
      </section>

      <section className="status-grid" aria-label="Deployment status">
        <article className="status-card">
          <div className="card-top"><span className="card-icon">◈</span><span className="pill success">ONLINE</span></div>
          <h2>{t.frontend}</h2>
          <p className="card-value">{t.online}</p>
          <p className="card-detail">{t.frontendDetail}</p>
        </article>
        <article className="status-card">
          <div className="card-top"><span className="card-icon">⌘</span><span className={`pill ${health === "online" ? "success" : health === "loading" ? "checking" : "error"}`}>{health === "online" ? "ONLINE" : health === "loading" ? "CHECKING" : "OFFLINE"}</span></div>
          <h2>{t.backend}</h2>
          <p className="card-value">{health === "online" ? t.online : health === "loading" ? t.loading : t.offline}</p>
          <p className="card-detail">{t.backendDetail}</p>
        </article>
      </section>

      <section className="foundation-panel">
        <div><span className="panel-label">{t.foundation}</span><p>{t.foundationDetail}</p></div>
        <div className="actions">
          <button type="button" onClick={() => void checkHealth()} className="primary-button">{t.apiCheck}</button>
          <a href="/api/backend-health" target="_blank" rel="noreferrer" className="secondary-button">{t.apiDocs}</a>
        </div>
      </section>

      <footer><span>{t.foot}</span><a href="https://github.com/MxWorking/company-os" target="_blank" rel="noreferrer">{t.github} ↗</a></footer>
    </main>
  );
}
