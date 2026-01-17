import React, { useEffect, useRef } from "react";
import { cn } from "../../lib/cn";
import Button from "./Button";

export interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  children?: React.ReactNode;
  footer?: React.ReactNode;
}

export function Modal({ open, onClose, title, description, children, footer }: ModalProps) {
  const ref = useRef<HTMLDivElement | null>(null);

  // ESC close + scroll lock
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    if (open) {
      document.addEventListener("keydown", onKey);
      const prev = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      return () => {
        document.body.style.overflow = prev;
        document.removeEventListener("keydown", onKey);
      };
    }
  }, [open, onClose]);

  // Focus trap
  useEffect(() => {
    if (!open) return;
    const root = ref.current;
    if (!root) return;
    const focusable = root.querySelectorAll<HTMLElement>(
      'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])'
    );
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    function onTab(e: KeyboardEvent) {
      if (e.key !== "Tab") return;
      if (focusable.length === 0) return;
      if (e.shiftKey) {
        if (document.activeElement === first) {
          (last || first).focus();
          e.preventDefault();
        }
      } else {
        if (document.activeElement === last) {
          (first || last).focus();
          e.preventDefault();
        }
      }
    }
    document.addEventListener("keydown", onTab);
    first?.focus();
    return () => document.removeEventListener("keydown", onTab);
  }, [open]);

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? "modal-title" : undefined}
      aria-describedby={description ? "modal-desc" : undefined}
      className="fixed inset-0 z-50 grid place-items-center"
    >
      <div className="absolute inset-0 bg-black/50" onClick={onClose} aria-hidden="true" />
      <div ref={ref} className={cn("relative w-full max-w-lg rounded-xl bg-white p-5 shadow-lg outline-none")}
        role="document">
        <div className="flex items-start justify-between gap-4">
          <div>
            {title && (
              <h2 id="modal-title" className="text-lg font-semibold text-text-strong">
                {title}
              </h2>
            )}
            {description && (
              <p id="modal-desc" className="mt-1 text-sm text-text-muted">
                {description}
              </p>
            )}
          </div>
          <Button variant="ghost" size="sm" aria-label="닫기" onClick={onClose}>
            ✕
          </Button>
        </div>
        <div className="mt-4">{children}</div>
        {footer && <div className="mt-6">{footer}</div>}
      </div>
    </div>
  );
}

export default Modal;

