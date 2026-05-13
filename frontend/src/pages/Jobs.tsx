import { FormEvent, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/Card";
import { Input, Select } from "../components/ui/Form";
import { EmptyState, ErrorState } from "../components/ui/State";
import { Table, TableBody, TableHead, Td, Th } from "../components/ui/Table";
import { Skeleton, TableSkeleton } from "../components/ui/Skeleton";
import { getJob, getJobs, type Job } from "../lib/api";

const PAGE_SIZES = [25, 50, 100, 200];

function jobTypeVariant(type: string | null) {
  if (type === "internship") return "success" as const;
  if (type === "new_grad") return "secondary" as const;
  if (type === "coop") return "warning" as const;
  return "default" as const;
}

function formatDate(value: string | null | undefined) {
  if (!value) return "未知";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "未知";
  return date.toLocaleDateString("zh-CN");
}

function safeText(value: string | null | undefined, fallback = "未知") {
  return value && value.trim() ? value : fallback;
}

function formatJobType(type: string | null | undefined) {
  const labels: Record<string, string> = {
    internship: "实习",
    new_grad: "应届",
    coop: "合作实习",
    unknown: "未知"
  };
  return type ? labels[type] ?? type : "未知";
}

function formatStatus(status: string | null | undefined) {
  const labels: Record<string, string> = {
    active: "招聘中",
    inactive: "已关闭",
    open: "开放中",
    closed: "已关闭",
    unknown: "未知"
  };
  return status ? labels[status] ?? status : "未知";
}

function parseSkills(job: Job | undefined) {
  if (!job?.skills_json) return [];
  try {
    const parsed = JSON.parse(job.skills_json);
    return Array.isArray(parsed) ? parsed.filter((item): item is string => typeof item === "string") : [];
  } catch {
    return [];
  }
}

function JobDetailPanel({ jobId }: { jobId: number | null }) {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["job", jobId],
    queryFn: () => getJob(jobId as number),
    enabled: jobId !== null
  });
  const skills = useMemo(() => parseSkills(data), [data]);

  if (jobId === null) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>岗位详情</CardTitle>
          <CardDescription>从表格中选择一个岗位，查看完整的后端返回信息。</CardDescription>
        </CardHeader>
        <CardContent>
          <EmptyState title="尚未选择岗位" description="点击一行岗位后，这里会展示完整详情。" />
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-40" />
          <Skeleton className="mt-2 h-4 w-64" />
        </CardHeader>
        <CardContent className="space-y-3">
          {Array.from({ length: 7 }).map((_, index) => (
            <Skeleton key={index} className="h-8" />
          ))}
        </CardContent>
      </Card>
    );
  }

  if (error || !data) {
    return (
      <Card>
        <CardContent>
          <ErrorState description="岗位详情接口没有响应。" onRetry={() => void refetch()} />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div>
            <CardTitle>{safeText(data.title, "未命名岗位")}</CardTitle>
            <CardDescription>{safeText(data.company)} · {safeText(data.location)}</CardDescription>
          </div>
          <Badge variant={jobTypeVariant(data.job_type)}>{formatJobType(data.job_type)}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="grid gap-3 text-sm sm:grid-cols-2">
          <div>
            <div className="text-slate-500">状态</div>
            <div className="mt-1 font-medium">{formatStatus(data.status)}</div>
          </div>
          <div>
            <div className="text-slate-500">招聘季</div>
            <div className="mt-1 font-medium">{safeText(data.season)}</div>
          </div>
          <div>
            <div className="text-slate-500">首次发现</div>
            <div className="mt-1 font-medium">{formatDate(data.first_seen_at)}</div>
          </div>
          <div>
            <div className="text-slate-500">最近发现</div>
            <div className="mt-1 font-medium">{formatDate(data.last_seen_at)}</div>
          </div>
        </div>

        <div>
          <div className="mb-2 text-sm font-medium text-slate-700">技能</div>
          {skills.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {skills.map((skill) => (
                <Badge key={skill}>{skill}</Badge>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500">接口没有返回可解析的技能。</p>
          )}
        </div>

        <div>
          <div className="mb-2 text-sm font-medium text-slate-700">描述</div>
          <p className="max-h-56 overflow-auto rounded-md border border-slate-200 bg-slate-50 p-3 text-sm leading-6 text-slate-600">
            {safeText(data.raw_text, "接口没有返回原始描述。")}
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          {data.apply_url && (
            <a className="rounded-md bg-slate-950 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800" href={data.apply_url} target="_blank" rel="noreferrer">
              申请
            </a>
          )}
          <a className="rounded-md border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50" href={data.source_url} target="_blank" rel="noreferrer">
            来源
          </a>
        </div>
      </CardContent>
    </Card>
  );
}

export function Jobs() {
  const [filters, setFilters] = useState({ q: "", location: "", job_type: "" });
  const [draft, setDraft] = useState(filters);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(50);
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null);

  const { data, isLoading, isFetching, error, refetch } = useQuery({
    queryKey: ["jobs", filters, page, pageSize],
    queryFn: () => getJobs({ ...filters, skip: page * pageSize, limit: pageSize }),
    placeholderData: (previous) => previous
  });

  const total = data?.total ?? 0;
  const pageCount = Math.max(Math.ceil(total / pageSize), 1);
  const currentStart = total === 0 ? 0 : page * pageSize + 1;
  const currentEnd = Math.min((page + 1) * pageSize, total);

  function submit(event: FormEvent) {
    event.preventDefault();
    setPage(0);
    setSelectedJobId(null);
    setFilters(draft);
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_420px]">
      <div className="space-y-5">
        <Card>
          <CardHeader>
            <CardTitle>筛选条件</CardTitle>
            <CardDescription>通过岗位接口按关键词、地点和岗位类型筛选结果。</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={submit} className="grid gap-3 md:grid-cols-[1fr_220px_180px_auto]">
              <Input
                placeholder="搜索公司、岗位或描述"
                value={draft.q}
                onChange={(event) => setDraft((current) => ({ ...current, q: event.target.value }))}
              />
              <Input
                placeholder="地点"
                value={draft.location}
                onChange={(event) => setDraft((current) => ({ ...current, location: event.target.value }))}
              />
              <Select
                value={draft.job_type}
                onChange={(event) => setDraft((current) => ({ ...current, job_type: event.target.value }))}
              >
                <option value="">全部类型</option>
                <option value="internship">实习</option>
                <option value="new_grad">应届</option>
                <option value="coop">合作实习</option>
                <option value="unknown">未知</option>
              </Select>
              <Button>搜索</Button>
            </form>
          </CardContent>
        </Card>

        <Card className="overflow-hidden">
          <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <CardTitle>活跃岗位</CardTitle>
              <p className="mt-1 text-sm text-slate-500">
                {data ? `第 ${currentStart}-${currentEnd} 条，共 ${total.toLocaleString()} 条结果` : "搜索结果"}
                {isFetching && !isLoading ? " · 正在刷新" : ""}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Select
                className="h-9 w-28"
                value={pageSize}
                onChange={(event) => {
                  setPage(0);
                  setPageSize(Number(event.target.value));
                }}
              >
                {PAGE_SIZES.map((size) => (
                  <option key={size} value={size}>
                    每页 {size} 条
                  </option>
                ))}
              </Select>
              <Badge>已显示 {data?.items.length ?? 0} 条</Badge>
            </div>
          </CardHeader>

          {isLoading && <TableSkeleton rows={8} />}
          {error && <div className="p-5"><ErrorState description="岗位接口没有响应。" onRetry={() => void refetch()} /></div>}
          {data && data.items.length === 0 && (
            <div className="p-5">
              <EmptyState title="没有找到岗位" description="可以尝试减少筛选条件，扩大搜索范围。" />
            </div>
          )}
          {data && data.items.length > 0 && (
            <>
              <div className="overflow-x-auto">
                <Table>
                  <TableHead>
                    <tr>
                      <Th>岗位</Th>
                      <Th>公司</Th>
                      <Th>地点</Th>
                      <Th>类型</Th>
                      <Th>链接</Th>
                      <Th>详情</Th>
                    </tr>
                  </TableHead>
                  <TableBody>
                    {data.items.map((job) => (
                      <tr key={job.id} className={selectedJobId === job.id ? "bg-teal-50/70" : "hover:bg-slate-50/70"}>
                        <Td className="min-w-72">
                          <div className="font-medium text-slate-950">{safeText(job.title, "未命名岗位")}</div>
                          <div className="mt-1 text-xs text-slate-500">最近发现：{formatDate(job.last_seen_at)}</div>
                        </Td>
                        <Td className="min-w-44 text-slate-700">{safeText(job.company)}</Td>
                        <Td className="min-w-44 text-slate-500">{safeText(job.location)}</Td>
                        <Td>
                          <Badge variant={jobTypeVariant(job.job_type)}>{formatJobType(job.job_type)}</Badge>
                        </Td>
                        <Td>
                          <div className="flex gap-3">
                            {job.apply_url && (
                              <a className="font-medium text-teal-700 hover:text-teal-900" href={job.apply_url} target="_blank" rel="noreferrer">
                                申请
                              </a>
                            )}
                            <a className="text-slate-500 hover:text-slate-950" href={job.source_url} target="_blank" rel="noreferrer">
                              来源
                            </a>
                          </div>
                        </Td>
                        <Td>
                          <Button type="button" variant="secondary" className="h-8 px-3" onClick={() => setSelectedJobId(job.id)}>
                            查看
                          </Button>
                        </Td>
                      </tr>
                    ))}
                  </TableBody>
                </Table>
              </div>
              <div className="flex flex-col gap-3 border-t border-slate-100 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="text-sm text-slate-500">
                  第 {page + 1} 页，共 {pageCount} 页
                </div>
                <div className="flex gap-2">
                  <Button type="button" variant="secondary" disabled={page === 0} onClick={() => setPage((current) => Math.max(current - 1, 0))}>
                    上一页
                  </Button>
                  <Button type="button" variant="secondary" disabled={page + 1 >= pageCount} onClick={() => setPage((current) => current + 1)}>
                    下一页
                  </Button>
                </div>
              </div>
            </>
          )}
        </Card>
      </div>

      <JobDetailPanel jobId={selectedJobId} />
    </div>
  );
}
