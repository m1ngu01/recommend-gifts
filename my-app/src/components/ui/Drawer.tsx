import React, { useEffect } from "react";
import { cn } from "../../lib/cn";

export interface DrawerProps {
  open: boolean;
  onClose: () => void;
  side?: "left" | "right";
  children?: React.ReactNode;
  width?: number; // px
}

export function Drawer({ open, onClose, side = "right", width = 360, children }: DrawerProps) {
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

  return (
    <div className={cn("fixed inset-0 z-50", open ? "pointer-events-auto" : "pointer-events-none")} aria-hidden={!open}>
      <div
        className={cn(
          "absolute inset-0 bg-black/50 transition-opacity",
          open ? "opacity-100" : "opacity-0"
        )}
        onClick={onClose}
      />
      <div
        className={cn(
          "absolute top-0 h-full bg-white shadow-lg transition-transform will-change-transform",
          side === "right" ? "right-0" : "left-0",
          open ? "translate-x-0" : side === "right" ? "translate-x-full" : "-translate-x-full"
        )}
        style={{ width }}
        role="dialog"
        aria-modal="true"
      >
        {children}
      </div>
    </div>
  );
}

export default Drawer;

