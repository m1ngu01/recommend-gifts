import React from "react";
import { cn } from "../../lib/cn";

type ButtonVariant = "primary" | "secondary" | "ghost" | "destructive";
type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
}

const base =
  "inline-flex items-center justify-center font-medium transition-colors duration-200 select-none focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 rounded-md disabled:cursor-not-allowed disabled:opacity-50";
const variants: Record<ButtonVariant, string> = {
  primary:
    "bg-[var(--color-primary)] text-white hover:bg-[var(--color-primary-600)] focus-visible:ring-[var(--color-primary)]",
  secondary:
    "bg-surface-2 text-text hover:bg-surface-3 border border-border focus-visible:ring-[var(--color-primary)]",
  ghost:
    "bg-transparent text-text hover:bg-surface-2 focus-visible:ring-[var(--color-primary)]",
  destructive:
    "bg-danger text-white hover:bg-danger-600 focus-visible:ring-danger",
};
const sizes: Record<ButtonSize, string> = {
  sm: "h-9 px-3 text-sm",
  md: "h-10 px-4 text-sm",
  lg: "h-11 px-5 text-base",
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", isLoading = false, disabled, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(base, variants[variant], sizes[size], className)}
        aria-busy={isLoading || undefined}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading && (
          <svg className="mr-2 h-4 w-4 animate-spin text-current" viewBox="0 0 24 24" role="status" aria-label="로딩 중">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
          </svg>
        )}
        {children}
      </button>
    );
  }
);
Button.displayName = "Button";

export default Button;

