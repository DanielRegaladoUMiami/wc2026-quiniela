"use client";

import { useEffect, useState } from "react";

export default function LangToggle() {
  const [lang, setLang] = useState<"en" | "es">("en");

  useEffect(() => {
    const stored = (localStorage.getItem("wc-lang") as "en" | "es") || "en";
    setLang(stored);
  }, []);

  function toggle() {
    const next = lang === "en" ? "es" : "en";
    setLang(next);
    try {
      localStorage.setItem("wc-lang", next);
    } catch {
      /* ignore */
    }
    const d = document.documentElement;
    d.classList.remove("lang-en", "lang-es");
    d.classList.add("lang-" + next);
  }

  return (
    <button
      onClick={toggle}
      aria-label="Toggle language"
      className="display shrink-0 px-2 py-1 text-sm leading-none text-[color:var(--color-card)] border-2 border-[color:var(--color-card)] hover:bg-[color:var(--color-card)] hover:text-[color:var(--color-red)] transition-colors"
    >
      {/* show the language you'd switch TO */}
      {lang === "en" ? "ES" : "EN"}
    </button>
  );
}
