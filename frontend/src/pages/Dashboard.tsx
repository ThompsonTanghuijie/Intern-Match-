import { useQuery } from "@tanstack/react-query";
import { Badge } from "../components/ui/Badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/Card";
import { ErrorState } from "../components/ui/State";
import { Skeleton } from "../components/ui/Skeleton";
import { getTrends, type TrendPoint } from "../lib/api";

function MetricCard({ label, value, hint }: { label: string; value: number; hint: string }) {
  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-slate-500">{label}</p>
            <div className="mt-2 text-3xl font-semibold tracking-tight">{value.toLocaleString()}</div>
          </div>
          <Badge variant="secondary">{hint}</Badge>
        </div>
      </CardContent>
    </Card>
  );
}

function translateTrendLabel(label: string) {
  const labels: Record<string, string> = {
    internship: "实习",
    new_grad: "应届",
    coop: "合作教育",
    unknown: "未知",
    active: "招聘中",
    inactive: "已关闭",
    saved: "已收藏",
    interested: "感兴趣",
    applied: "已投递",
    interview: "面试中",
    offer: "已录用",
    rejected: "已拒绝",
    archived: "已归档"
  };
  return labels[label] ?? label;
}

function ChartCard({ title, description, points }: { title: string; description: string; points: TrendPoint[] }) {
  const max = Math.max(...points.map((point) => point.count), 1);

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {points.length === 0 ? (
          <div className="rounded-md border border-dashed border-slate-300 bg-slate-50 p-6 text-center text-sm text-slate-500">
            暂无趋势数据。
          </div>
        ) : (
          points.map((point) => (
            <div key={point.label}>
              <div className="mb-2 flex items-center justify-between gap-4 text-sm">
                <span className="truncate font-medium text-slate-700">{translateTrendLabel(point.label)}</span>
                <span className="tabular-nums text-slate-500">{point.count}</span>
              </div>
              <div className="h-2.5 overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-teal-600 to-cyan-500"
                  style={{ width: `${Math.max((point.count / max) * 100, 5)}%` }}
                />
              </div>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <Card key={index}>
            <CardContent className="space-y-3 p-5">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-9 w-32" />
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        {Array.from({ length: 4 }).map((_, index) => (
          <Card key={index}>
            <CardHeader>
              <Skeleton className="h-5 w-32" />
              <Skeleton className="mt-2 h-4 w-56" />
            </CardHeader>
            <CardContent className="space-y-4">
              {Array.from({ length: 5 }).map((__, row) => (
                <Skeleton key={row} className="h-8" />
              ))}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

export function Dashboard() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["trends"],
    queryFn: () => getTrends(10)
  });

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  if (error || !data) {
    return <ErrorState description="数据分析接口没有响应。" onRetry={() => void refetch()} />;
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="岗位总数" value={data.total_jobs} hint="全部时间" />
        <MetricCard label="活跃岗位" value={data.active_jobs} hint="正在招聘" />
        <MetricCard label="跟踪状态" value={data.application_status.length} hint="求职流程" />
        <MetricCard label="识别技能" value={data.top_skills.length} hint="热门列表" />
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <ChartCard title="岗位类型" description="当前岗位类别分布。" points={data.by_job_type} />
        <ChartCard title="热门技能" description="最常被识别出的技术关键词。" points={data.top_skills} />
        <ChartCard title="热门地点" description="标准化后出现频率最高的地点。" points={data.top_locations} />
        <ChartCard title="数据源覆盖" description="按上游数据源统计的岗位数量。" points={data.by_source} />
      </div>
    </div>
  );
}
