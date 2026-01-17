import React, { useEffect, useRef, useState } from "react";
import { cn } from "../../lib/cn";

export interface TooltipProps extends React.HTMLAttributes<HTMLDivElement> {
  content: React.ReactNode;
  placement?: "top" | "bottom" | "left" | "right";
}

export function Tooltip({ children, content, placement = "top", className }: TooltipProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    if (open) document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <div
      ref={ref}
      className="relative inline-flex"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onFocus={() => setOpen(true)}
      onBlur={() => setOpen(false)}
    >
      {children}
      <div
        role="tooltip"
        className={cn(
          "pointer-events-none absolute z-40 whitespace-pre rounded-md bg-black/80 px-2 py-1 text-xs text-white opacity-0 transition-opacity",
          open && "opacity-100",
          placement === "top" && "-top-1 translate-y-[-100%] left-1/2 -translate-x-1/2",
          placement === "bottom" && "-bottom-1 translate-y-[100%] left-1/2 -translate-x-1/2",
          placement === "left" && "left-0 -translate-x-full top-1/2 -translate-y-1/2",
          placement === "right" && "right-0 translate-x-full top-1/2 -translate-y-1/2",
          className
        )}
      >
        {content}
      </div>
    </div>
  );
}

export default Tooltip;

