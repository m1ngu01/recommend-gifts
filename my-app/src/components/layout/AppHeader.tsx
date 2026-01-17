import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { logout as apiLogout } from "../../api/auth";
import logoLight from "../../assets/logo-light.png";
import logoDark from "../../assets/logo-dark.png";

type ThemeMode = "dark" | "light";

function getStoredTheme(): ThemeMode | null {
  try {
    const v = localStorage.getItem("theme-mode");
    if (v === "dark" || v === "light") return v;
    return null;
  } catch {
    return null;
  }
}

function applyTheme(mode: ThemeMode) {
  const root = document.documentElement;
  if (mode === "light") {
    root.classList.add("theme-light");
  } else {
    root.classList.remove("theme-light");
  }
}

export default function AppHeader() {
  const [mode, setMode] = useState<ThemeMode>(() => getStoredTheme() ?? "dark");
  const [user, setUser] = useState<any | null>(null);

  useEffect(() => {
    applyTheme(mode);
    try {
      localStorage.setItem("theme-mode", mode);
    } catch {}
  }, [mode]);

  const isLight = mode === "light";
  const toggle = () => setMode(isLight ? "dark" : "light");

  const headerGradient = isLight
    ? "linear-gradient(to right, rgba(255,255,255,0.95), rgba(224,231,255,0.95))"
    : "linear-gradient(to right, #6a11cb, #913ac4ff)";

  const primaryLinkClass = isLight
    ? "text-slate-800 hover:text-slate-900 transition-colors"
    : "text-white/90 hover:text-white transition-colors";

  const secondaryLinkClass = isLight
    ? "text-slate-500 hover:text-slate-700 transition-colors"
    : "text-white/60 hover:text-white transition-colors";

  const logoutButtonClass = isLight
    ? "px-3 py-1.5 rounded-md border border-slate-300 text-slate-800 hover:text-slate-900 hover:bg-slate-200/60 transition-colors"
    : "px-3 py-1.5 rounded-md border border-white/40 text-white/90 hover:text-white hover:bg-white/10 transition-colors";

  const controlButtonClass = isLight
    ? "inline-flex h-9 w-9 items-center justify-center rounded-md border border-slate-300 text-slate-700 hover:text-slate-900 hover:bg-slate-200/60 transition-colors"
    : "inline-flex h-9 w-9 items-center justify-center rounded-md border border-white/40 text-white/90 hover:text-white hover:bg-white/10 transition-colors";

  const displayName = useMemo(() => {
    if (user && typeof user.name === "string" && user.name.trim()) {
      return user.name.trim();
    }
    if (user && typeof user.email === "string" && user.email.trim()) {
      return user.email.trim();
    }
    return "";
  }, [user]);

  useEffect(() => {
    const readStoredUser = () => {
      try {
        const saved = localStorage.getItem("user");
        setUser(saved ? JSON.parse(saved) : null);
      } catch {
        setUser(null);
      }
    };

    readStoredUser();

    const onStorage = (e: StorageEvent) => {
      if (e.key === "user") {
        readStoredUser();
      }
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const handleLogout = async () => {
    try {
      await apiLogout();
    } catch {}
    try {
      localStorage.removeItem("user");
    } catch {}
    window.location.href = "/";
  };

  const Icon = useMemo(() => {
    return isLight ? (
      // Sun icon
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-5 w-5">
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
      </svg>
    ) : (
      // Moon icon
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-5 w-5">
        <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" />
      </svg>
    );
  }, [isLight]);

  return (
    <header
      className={`sticky top-0 z-30 border-b ${
        isLight ? "border-slate-200 text-slate-900" : "border-white/20 text-white"
      }`}
      style={{ background: headerGradient }}
    >
      <div className="container mx-auto max-w-6xl px-4 py-3 flex items-center justify-between">
        <Link to="/" className="flex items-center" aria-label="대학생 선물 추천 홈">
          <img
            src={isLight ? logoDark : logoLight}
            alt="대학생 선물 추천"
            className="h-10 w-auto"
            loading="lazy"
          />
        </Link>

        <nav className="flex items-center gap-2 sm:gap-4 text-sm">
          {user ? (
            <>
              <Link to="/mypage" className={primaryLinkClass}>
                마이페이지
              </Link>
              {user?.role === "admin" && (
                <Link to="/admin" className={primaryLinkClass}>
                  Admin
                </Link>
              )}
              {displayName && (
                <span className={`${secondaryLinkClass} hidden sm:inline-block`}>{displayName}님</span>
              )}
              <button
                type="button"
                onClick={handleLogout}
                className={logoutButtonClass}
              >
                로그아웃
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className={primaryLinkClass}>
                로그인
              </Link>
              <Link to="/register" className={secondaryLinkClass}>
                회원가입
              </Link>
            </>
          )}
          <button
            type="button"
            aria-label={isLight ? "다크 모드로 변경" : "라이트 모드로 변경"}
            onClick={toggle}
            className={controlButtonClass}
            title={isLight ? "다크 모드" : "라이트 모드"}
          >
            {Icon}
          </button>
        </nav>
      </div>
    </header>
  );
}





