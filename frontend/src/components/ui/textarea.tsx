import type { TextareaHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Textarea({ className, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={cn(
        "w-full resize-y rounded-lg border border-slate-200 bg-white px-3 py-3 text-sm leading-6 text-slate-900 outline-none transition-colors placeholder:text-slate-400 focus:border-slate-400",
        className,
      )}
      {...props}
    />
  );
}
