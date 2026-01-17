import React from "react";
import { cn } from "../../lib/cn";

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helpText?: string;
}

export function Textarea({ id, label, error, helpText, className, rows = 4, ...props }: TextareaProps) {
  const taId = id || React.useId();
  const describedBy = [helpText ? `${taId}-help` : undefined, error ? `${taId}-error` : undefined]
    .filter(Boolean)
    .join(" ");

  return (
    <div className="w-full">
      {label && (
        <label htmlFor={taId} className="mb-1 block text-sm font-medium text-text">
          {label}
        </label>
      )}
      <textarea
        id={taId}
        rows={rows}
        className={cn(
          "w-full rounded-md border bg-white px-3 py-2 text-sm outline-none transition-colors",
          "border-border placeholder:text-text/60 focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]",
          error && "border-danger focus-visible:ring-danger",
          className
        )}
        aria-invalid={!!error || undefined}
        aria-describedby={describedBy || undefined}
        {...props}
      />
      {helpText && (
        <p id={`${taId}-help`} className="mt-1 text-xs text-text/70">
          {helpText}
        </p>
      )}
      {error && (
        <p id={`${taId}-error`} className="mt-1 text-xs text-danger">
          {error}
        </p>
      )}
    </div>
  );
}

export default Textarea;

