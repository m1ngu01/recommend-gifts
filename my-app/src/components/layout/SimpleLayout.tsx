import React from "react";

export default function SimpleLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-bg text-text">
      <header className="border-b border-border bg-surface-1">
        <div className="container mx-auto max-w-6xl px-4 py-3">
          <h1 className="text-lg font-semibold">서비스</h1>
        </div>
      </header>
      <main className="container mx-auto max-w-6xl px-4 py-8 sm:py-12">{children}</main>
      <footer className="border-t border-border bg-surface-1">
        <div className="container mx-auto max-w-6xl px-4 py-6 text-sm text-text-muted">© 2025</div>
      </footer>
    </div>
  );
}

