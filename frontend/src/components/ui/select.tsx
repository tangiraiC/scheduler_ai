import { createContext, type HTMLAttributes, type ReactNode, useContext } from "react";

import { cn } from "@/lib/utils";

type SelectContextValue = {
  value: string;
  onValueChange: (value: string) => void;
};

const SelectContext = createContext<SelectContextValue | null>(null);

function useSelectContext() {
  const context = useContext(SelectContext);
  if (!context) throw new Error("Select components must be used within Select");
  return context;
}

export function Select({
  value,
  onValueChange,
  children,
}: {
  value: string;
  onValueChange: (value: string) => void;
  children: ReactNode;
}) {
  return (
    <SelectContext.Provider value={{ value, onValueChange }}>
      <div className="relative">{children}</div>
    </SelectContext.Provider>
  );
}

export function SelectTrigger({ className, children }: HTMLAttributes<HTMLDivElement>) {
  const { value, onValueChange } = useSelectContext();
  return (
    <select
      value={value}
      onChange={(event) => onValueChange(event.target.value)}
      className={cn(
        "h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-900 outline-none focus:border-slate-400",
        className,
      )}
      aria-label="Coloring strategy"
    >
      {children}
    </select>
  );
}

export function SelectValue({ placeholder }: { placeholder?: string }) {
  return <option value="">{placeholder ?? "Select"}</option>;
}

export function SelectContent({ children }: { children: ReactNode }) {
  return <>{children}</>;
}

export function SelectItem({ value, children }: { value: string; children: ReactNode }) {
  return <option value={value}>{children}</option>;
}
