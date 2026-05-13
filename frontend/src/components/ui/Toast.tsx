import { createContext, ReactNode, useContext, useMemo, useState } from "react";
import { cn } from "../../lib/utils";

type ToastVariant = "success" | "error" | "info";
type Toast = {
  id: number;
  title: string;
  description?: string;
  variant: ToastVariant;
};

type ToastContextValue = {
  toast: (input: Omit<Toast, "id">) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

const variantClass: Record<ToastVariant, string> = {
  success: "border-emerald-200 bg-emerald-50 text-emerald-950",
  error: "border-rose-200 bg-rose-50 text-rose-950",
  info: "border-slate-200 bg-white text-slate-950"
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<Toast[]>([]);

  const value = useMemo(
    () => ({
      toast: (input: Omit<Toast, "id">) => {
        const id = Date.now();
        setItems((current) => [...current, { ...input, id }]);
        window.setTimeout(() => {
          setItems((current) => current.filter((item) => item.id !== id));
        }, 4200);
      }
    }),
    []
  );

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex w-[calc(100%-2rem)] max-w-sm flex-col gap-3">
        {items.map((item) => (
          <div key={item.id} className={cn("rounded-lg border p-4 shadow-lg", variantClass[item.variant])}>
            <div className="text-sm font-semibold">{item.title}</div>
            {item.description && <div className="mt-1 text-sm opacity-80">{item.description}</div>}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return context;
}
