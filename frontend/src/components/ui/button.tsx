import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "outline";
};

export function Button({ className, variant = "default", ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex h-10 items-center justify-center rounded-lg px-4 text-sm font-medium transition-colors disabled:pointer-events-none disabled:opacity-50",
        variant === "default"
          ? "bg-slate-900 text-white hover:bg-slate-800"
          : "border border-slate-200 bg-white text-slate-900 hover:bg-slate-50",
        className,
      )}
      {...props}
    />
  );
}
