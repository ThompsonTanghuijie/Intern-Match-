import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/Card";
import { EmptyState, ErrorState } from "../components/ui/State";
import { TableSkeleton } from "../components/ui/Skeleton";
import { Table, TableBody, TableHead, Td, Th } from "../components/ui/Table";
import { useToast } from "../components/ui/Toast";
import { getSources, runCrawl } from "../lib/api";

function statusVariant(status: string | null) {
  if (status === "ok") return "success" as const;
  if (status === "failed") return "danger" as const;
  if (status === "not_modified") return "secondary" as const;
  return "default" as const;
}

function formatSourceStatus(status: string | null) {
  const labels: Record<string, string> = {
    ok: "正常",
    failed: "失败",
    not_modified: "无更新",
    success: "成功"
  };
  return status ? labels[status] ?? status : "未抓取";
}

function formatSourceType(type: string) {
  const labels: Record<string, string> = {
    github_markdown: "代码仓库文本",
    markdown: "文本",
    html: "网页",
    api: "接口"
  };
  return labels[type] ?? type;
}

export function Sources() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["sources"],
    queryFn: getSources
  });

  const crawlMutation = useMutation({
    mutationFn: () => runCrawl(true),
    onSuccess: (runs) => {
      void queryClient.invalidateQueries({ queryKey: ["sources"] });
      void queryClient.invalidateQueries({ queryKey: ["trends"] });
      void queryClient.invalidateQueries({ queryKey: ["jobs"] });
      toast({
        title: "抓取完成",
        description: `从 ${runs.length} 个数据源中发现了 ${runs.reduce((sum, run) => sum + run.jobs_found, 0)} 个岗位。`,
        variant: "success"
      });
    },
    onError: () => {
      toast({
        title: "抓取失败",
        description: "后端抓取任务返回了错误。",
        variant: "error"
      });
    }
  });

  return (
    <div className="space-y-5">
      <Card>
        <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle>数据源操作</CardTitle>
            <CardDescription>手动触发抓取，并刷新已配置数据源中的看板数据。</CardDescription>
          </div>
          <Button disabled={crawlMutation.isPending} onClick={() => crawlMutation.mutate()}>
            {crawlMutation.isPending ? "正在抓取..." : "开始抓取"}
          </Button>
        </CardHeader>
      </Card>

      {crawlMutation.data && (
        <Card>
          <CardHeader>
            <CardTitle>最新抓取结果</CardTitle>
            <CardDescription>当前抓取请求返回的摘要。</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            {crawlMutation.data.map((run) => (
              <div key={run.id} className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <div className="flex items-center justify-between gap-2">
                  <div className="text-sm font-semibold">数据源 #{run.source_id ?? "无"}</div>
                  <Badge variant={run.status === "success" ? "success" : "danger"}>{formatSourceStatus(run.status)}</Badge>
                </div>
                <div className="mt-3 grid grid-cols-3 gap-2 text-center text-xs text-slate-500">
                  <div>
                    <div className="text-lg font-semibold text-slate-950">{run.jobs_found}</div>
                    发现
                  </div>
                  <div>
                    <div className="text-lg font-semibold text-slate-950">{run.jobs_created}</div>
                    新增
                  </div>
                  <div>
                    <div className="text-lg font-semibold text-slate-950">{run.jobs_updated}</div>
                    更新
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      <Card className="overflow-hidden">
        <CardHeader>
          <div className="flex items-center justify-between gap-4">
            <div>
              <CardTitle>已配置数据源</CardTitle>
              <CardDescription>后端预置的公开文本数据源。</CardDescription>
            </div>
            <Badge>{data?.length ?? 0} 个数据源</Badge>
          </div>
        </CardHeader>

        {isLoading && <TableSkeleton rows={5} />}
        {error && <div className="p-5"><ErrorState description="数据源接口没有响应。" onRetry={() => void refetch()} /></div>}
        {data && data.length === 0 && (
          <div className="p-5">
            <EmptyState title="没有配置数据源" description="后端还没有预置任何数据源。" />
          </div>
        )}
        {data && data.length > 0 && (
          <div className="overflow-x-auto">
            <Table>
              <TableHead>
                <tr>
                  <Th>名称</Th>
                  <Th>类型</Th>
                  <Th>状态</Th>
                  <Th>最近抓取</Th>
                </tr>
              </TableHead>
              <TableBody>
                {data.map((source) => (
                  <tr key={source.id} className="hover:bg-slate-50/70">
                    <Td className="min-w-80">
                      <a href={source.url} target="_blank" rel="noreferrer" className="font-medium text-slate-950 hover:text-teal-700">
                        {source.name}
                      </a>
                      <div className="mt-1 max-w-xl truncate text-xs text-slate-500">{source.url}</div>
                    </Td>
                    <Td className="text-slate-500">{formatSourceType(source.source_type)}</Td>
                    <Td>
                      <Badge variant={statusVariant(source.last_status)}>{formatSourceStatus(source.last_status)}</Badge>
                    </Td>
                    <Td className="text-slate-500">
                      {source.last_crawled_at ? new Date(source.last_crawled_at).toLocaleString("zh-CN") : "从未抓取"}
                    </Td>
                  </tr>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </Card>
    </div>
  );
}
