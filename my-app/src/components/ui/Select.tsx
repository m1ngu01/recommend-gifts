import React from "react";
import { cn } from "../../lib/cn";

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  helpText?: string;
}

export function Select({ id, label, error, helpText, className, children, ...props }: SelectProps) {
  const selId = id || React.useId();
  const describedBy = [helpText ? `${selId}-help` : undefined, error ? `${selId}-error` : undefined]
    .filter(Boolean)
    .join(" ");

  return (
    <div className="w-full">
      {label && (
        <label htmlFor={selId} className="mb-1 block text-sm font-medium text-text">
          {label}
        </label>
      )}
      <select
        id={selId}
        className={cn(
          "h-11 w-full rounded-md border bg-white px-3 text-sm outline-none transition-colors",
          "border-border focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]",
          error && "border-danger focus-visible:ring-danger",
          className
        )}
        aria-invalid={!!error || undefined}
        aria-describedby={describedBy || undefined}
        {...props}
      >
        {children}
      </select>
      {helpText && (
        <p id={`${selId}-help`} className="mt-1 text-xs text-text/70">
          {helpText}
        </p>
      )}
      {error && (
        <p id={`${selId}-error`} className="mt-1 text-xs text-danger">
          {error}
        </p>
      )}
    </div>
  );
}

export default Select;

