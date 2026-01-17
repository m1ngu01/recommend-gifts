import React, { createContext, useCallback, useContext, useMemo, useState } from "react";
import { cn } from "../../lib/cn";

type ToastType = "info" | "success" | "warning" | "error";
export interface ToastItem {
  id: string;
  type: ToastType;
  title?: string;
  message: string;
  duration?: number;
}

interface ToastContextValue {
  push: (item: Omit<ToastItem, "id">) => void;
  remove: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const remove = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const push = useCallback(
    (item: Omit<ToastItem, "id">) => {
      const id = crypto.randomUUID();
      const toast: ToastItem = { id, duration: 3000, ...item };
      setToasts((prev) => [...prev, toast]);
      if (toast.duration && toast.duration > 0) {
        setTimeout(() => remove(id), toast.duration);
      }
    },
    [remove]
  );

  const value = useMemo(() => ({ push, remove }), [push, remove]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div aria-live="polite" aria-atomic="true" className="pointer-events-none fixed inset-x-0 top-4 z-[60] flex w-full justify-center px-4">
        <div className="flex w-full max-w-lg flex-col gap-2">
          {toasts.map((t) => (
            <div
              key={t.id}
              role="status"
              className={cn(
                "pointer-events-auto rounded-lg border p-3 shadow-md bg-white",
                t.type === "success" && "border-green-200",
                t.type === "info" && "border-blue-200",
                t.type === "warning" && "border-yellow-200",
                t.type === "error" && "border-red-200"
              )}
            >
              {t.title && <div className="text-sm font-semibold">{t.title}</div>}
              <div className="text-sm text-text-muted">{t.message}</div>
            </div>
          ))}
        </div>
      </div>
    </ToastContext.Provider>
  );
}

export function useToastContext() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("ToastProvider 내에서 사용해야 합니다.");
  return ctx;
}

export default ToastProvider;

