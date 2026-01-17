import React from "react";
import { cn } from "../../lib/cn";

export interface TabsProps {
  value: string;
  onChange: (value: string) => void;
  children: React.ReactNode;
}

export function Tabs({ value, onChange, children }: TabsProps) {
  return <div data-value={value}>{children}</div>;
}

export interface TabsListProps extends React.HTMLAttributes<HTMLDivElement> {}
export function TabsList({ className, ...props }: TabsListProps) {
  return (
    <div className={cn("inline-flex items-center gap-1 rounded-md bg-surface-2 p-1", className)} {...props} />
  );
}

export interface TabsTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  value: string;
  active?: boolean;
}

export function TabsTrigger({ className, value, active, onClick, ...props }: TabsTriggerProps) {
  return (
    <button
      type="button"
      data-value={value}
      aria-selected={active}
      className={cn(
        "rounded-md px-3 py-2 text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]",
        active ? "bg-white shadow-sm" : "text-text hover:bg-white/60",
        className
      )}
      onClick={(e) => {
        props.onClick?.(e);
      }}
      {...props}
    />
  );
}

export interface TabsContentProps extends React.HTMLAttributes<HTMLDivElement> {
  value: string;
  active?: boolean;
}

export function TabsContent({ className, value, active, ...props }: TabsContentProps) {
  if (!active) return null;
  return <div data-value={value} className={cn(className)} {...props} />;
}

export default Tabs;

