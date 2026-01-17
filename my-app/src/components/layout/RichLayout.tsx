import React from "react";

export default function RichLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-surface-2 text-text">
      <header className="border-b border-border bg-white/80 backdrop-blur">
        <div className="container mx-auto max-w-6xl px-4 py-4 flex items-center justify-between">
          <div className="text-lg font-semibold">브랜드</div>
          <nav className="flex items-center gap-4 text-sm">
            <a className="text-text hover:opacity-80" href="/">홈</a>
            <a className="text-text hover:opacity-80" href="/ui-demo">컴포넌트</a>
          </nav>
        </div>
      </header>
      <main className="container mx-auto max-w-6xl px-4 py-10">{children}</main>
      <footer className="border-t border-border bg-surface-1">
        <div className="container mx-auto max-w-6xl px-4 py-8 grid gap-4 text-sm text-text-muted">
          <div>문의: support@example.com</div>
          <div>© 2025 Brand, Inc.</div>
        </div>
      </footer>
    </div>
  );
}

