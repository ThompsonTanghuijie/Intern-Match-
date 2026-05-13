import { ReactNode } from "react";
import { Button } from "./Button";

export function EmptyState({
  title,
  description,
  action
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex min-h-64 flex-col items-center justify-center rounded-lg border border-dashed border-slate-300 bg-slate-50/70 p-8 text-center">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-white text-lg shadow-sm">+</div>
      <h3 className="text-base font-semibold text-slate-950">{title}</h3>
      <p className="mt-2 max-w-md text-sm text-slate-500">{description}</p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function ErrorState({
  title = "出错了",
  description,
  onRetry
}: {
  title?: string;
  description: string;
  onRetry?: () => void;
}) {
  return (
    <div className="rounded-lg border border-rose-200 bg-rose-50 p-5">
      <div className="text-sm font-semibold text-rose-900">{title}</div>
      <p className="mt-1 text-sm text-rose-700">{description}</p>
      {onRetry && (
        <Button className="mt-4" variant="secondary" onClick={onRetry}>
          重试
        </Button>
      )}
    </div>
  );
}
