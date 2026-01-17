import React from "react";
import { cn } from "../../lib/cn";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helpText?: string;
}

export function Input({ id, label, error, helpText, className, ...props }: InputProps) {
  const inputId = id || React.useId();
  const describedBy = [helpText ? `${inputId}-help` : undefined, error ? `${inputId}-error` : undefined]
    .filter(Boolean)
    .join(" ");

  return (
    <div className="w-full">
      {label && (
        <label htmlFor={inputId} className="mb-1 block text-sm font-medium text-text">
          {label}
        </label>
      )}
      <input
        id={inputId}
        className={cn(
          "h-11 w-full rounded-md border bg-white px-3 text-sm outline-none transition-colors",
          "border-border placeholder:text-text/60 focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]",
          error && "border-danger focus-visible:ring-danger",
          className
        )}
        aria-invalid={!!error || undefined}
        aria-describedby={describedBy || undefined}
        {...props}
      />
      {helpText && (
        <p id={`${inputId}-help`} className="mt-1 text-xs text-text/70">
          {helpText}
        </p>
      )}
      {error && (
        <p id={`${inputId}-error`} className="mt-1 text-xs text-danger">
          {error}
        </p>
      )}
    </div>
  );
}

export default Input;

