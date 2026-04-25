import {
  createContext,
  type ButtonHTMLAttributes,
  type HTMLAttributes,
  type ReactNode,
  useContext,
  useMemo,
  useState,
} from "react";

import { cn } from "@/lib/utils";

type TabsContextValue = {
  value: string;
  setValue: (value: string) => void;
};

const TabsContext = createContext<TabsContextValue | null>(null);

function useTabsContext() {
  const context = useContext(TabsContext);
  if (!context) throw new Error("Tabs components must be used within Tabs");
  return context;
}

export function Tabs({
  defaultValue,
  className,
  children,
}: HTMLAttributes<HTMLDivElement> & { defaultValue: string }) {
  const [value, setValue] = useState(defaultValue);
  const contextValue = useMemo(() => ({ value, setValue }), [value]);

  return (
    <TabsContext.Provider value={contextValue}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  );
}

export function TabsList({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex gap-1 rounded-lg bg-slate-100 p-1", className)} {...props} />;
}

export function TabsTrigger({
  value,
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { value: string }) {
  const context = useTabsContext();
  return (
    <button
      type="button"
      className={cn(
        "rounded-md px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:text-slate-950",
        context.value === value && "bg-white text-slate-950 shadow-sm",
        className,
      )}
      onClick={() => context.setValue(value)}
      {...props}
    />
  );
}

export function TabsContent({
  value,
  className,
  children,
}: HTMLAttributes<HTMLDivElement> & { value: string; children: ReactNode }) {
  const context = useTabsContext();
  if (context.value !== value) return null;
  return <div className={className}>{children}</div>;
}
