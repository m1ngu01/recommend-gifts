import React from "react";
import { cn } from "../../lib/cn";

type BadgeVariant = "solid" | "soft" | "outline";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  color?: "primary" | "neutral" | "danger";
}

export function Badge({ className, variant = "soft", color = "primary", ...props }: BadgeProps) {
  const colorBase =
    color === "danger"
      ? { bg: "bg-red-50", text: "text-red-700", ring: "ring-red-200" }
      : color === "neutral"
      ? { bg: "bg-surface-2", text: "text-text", ring: "ring-border" }
      : { bg: "bg-blue-50", text: "text-blue-700", ring: "ring-blue-200" };

  const style =
    variant === "solid"
      ? "bg-[var(--color-primary)] text-white"
      : variant === "outline"
      ? cn("border", colorBase.ring, "bg-transparent", colorBase.text)
      : cn(colorBase.bg, colorBase.text);

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium",
        style,
        className
      )}
      {...props}
    />
  );
}

export default Badge;

