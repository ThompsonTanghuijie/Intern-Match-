import { FormEvent, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/Card";
import { Input, Label, Select, Textarea } from "../components/ui/Form";
import { EmptyState, ErrorState } from "../components/ui/State";
import { Skeleton } from "../components/ui/Skeleton";
import { useToast } from "../components/ui/Toast";
import { getMatches, type MatchRequest } from "../lib/api";

function splitCsv(value: string) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function normalizeInputList(items: string[]) {
  const aliases: Record<string, string> = {
    远程: "Remote",
    纽约: "New York",
    旧金山: "San Francisco",
    后端: "backend",
    数据工程: "data engineering",
    实习: "internship",
    无薪: "unpaid"
  };
  return items.map((item) => aliases[item] ?? item);
}

export function Match() {
  const { toast } = useToast();
  const [form, setForm] = useState({
    skills: "Python, SQL, FastAPI, Docker",
    target_locations: "远程, 纽约, 旧金山",
    target_directions: "后端, 数据工程, 实习",
    remote_preference: "prefer_remote",
    blacklist_keywords: "无薪",
    min_score: 0.35,
    limit: 30
  });

  const matchMutation = useMutation({
    mutationFn: (payload: MatchRequest) => getMatches(payload),
    onSuccess: (data) => {
      toast({
        title: "匹配已生成",
        description: `返回了 ${data.items.length} 个推荐岗位。`,
        variant: "success"
      });
    },
    onError: () => {
      toast({
        title: "匹配失败",
        description: "后端暂时无法为岗位打分。",
        variant: "error"
      });
    }
  });

  function submit(event: FormEvent) {
    event.preventDefault();
    matchMutation.mutate({
      name: "default",
      skills: splitCsv(form.skills),
      target_locations: normalizeInputList(splitCsv(form.target_locations)),
      target_directions: normalizeInputList(splitCsv(form.target_directions)),
      remote_preference: form.remote_preference || null,
      blacklist_keywords: normalizeInputList(splitCsv(form.blacklist_keywords)),
      min_score: Number(form.min_score),
      limit: Number(form.limit)
    });
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[420px_1fr]">
      <Card className="h-fit">
        <CardHeader>
          <CardTitle>个人偏好</CardTitle>
          <CardDescription>多个值请用英文逗号分隔，提交后会直接发送到匹配接口。</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="space-y-4">
            <Label>
              技能
              <Textarea
                className="mt-1"
                value={form.skills}
                onChange={(event) => setForm((current) => ({ ...current, skills: event.target.value }))}
              />
            </Label>
            <Label>
              目标地点
              <Input
                className="mt-1"
                value={form.target_locations}
                onChange={(event) => setForm((current) => ({ ...current, target_locations: event.target.value }))}
              />
            </Label>
            <Label>
              求职方向
              <Input
                className="mt-1"
                value={form.target_directions}
                onChange={(event) => setForm((current) => ({ ...current, target_directions: event.target.value }))}
              />
            </Label>
            <Label>
              远程偏好
              <Select
                className="mt-1"
                value={form.remote_preference}
                onChange={(event) => setForm((current) => ({ ...current, remote_preference: event.target.value }))}
              >
                <option value="prefer_remote">优先远程</option>
                <option value="remote">只看远程</option>
                <option value="hybrid">混合办公</option>
                <option value="onsite">现场办公</option>
                <option value="">无偏好</option>
              </Select>
            </Label>
            <Label>
              排除关键词
              <Input
                className="mt-1"
                value={form.blacklist_keywords}
                onChange={(event) => setForm((current) => ({ ...current, blacklist_keywords: event.target.value }))}
              />
            </Label>
            <div className="grid grid-cols-2 gap-3">
              <Label>
                最低分数
                <Input
                  className="mt-1"
                  type="number"
                  min="0"
                  max="1"
                  step="0.05"
                  value={form.min_score}
                  onChange={(event) => setForm((current) => ({ ...current, min_score: Number(event.target.value) }))}
                />
              </Label>
              <Label>
                返回数量
                <Input
                  className="mt-1"
                  type="number"
                  min="1"
                  max="200"
                  value={form.limit}
                  onChange={(event) => setForm((current) => ({ ...current, limit: Number(event.target.value) }))}
                />
              </Label>
            </div>
            <Button className="w-full" disabled={matchMutation.isPending}>
              {matchMutation.isPending ? "正在为岗位打分..." : "生成匹配结果"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card className="overflow-hidden">
        <CardHeader>
          <div className="flex items-center justify-between gap-4">
            <div>
              <CardTitle>推荐结果</CardTitle>
              <CardDescription>根据技能、地点、方向和更新时间综合排序。</CardDescription>
            </div>
            {matchMutation.data && <Badge variant="secondary">{matchMutation.data.items.length} 条结果</Badge>}
          </div>
        </CardHeader>

        <CardContent className="p-0">
          {!matchMutation.data && !matchMutation.isPending && !matchMutation.isError && (
            <div className="p-5">
              <EmptyState title="还没有生成匹配" description="调整左侧偏好并生成匹配后，这里会显示排序后的岗位。" />
            </div>
          )}

          {matchMutation.isPending && (
            <div className="space-y-4 p-5">
              {Array.from({ length: 5 }).map((_, index) => (
                <div key={index} className="rounded-lg border border-slate-100 p-4">
                  <Skeleton className="h-5 w-2/3" />
                  <Skeleton className="mt-3 h-4 w-1/2" />
                  <div className="mt-4 flex gap-2">
                    <Skeleton className="h-6 w-24 rounded-full" />
                    <Skeleton className="h-6 w-28 rounded-full" />
                  </div>
                </div>
              ))}
            </div>
          )}

          {matchMutation.isError && (
            <div className="p-5">
              <ErrorState description="匹配接口返回错误。请调整条件后重试。" />
            </div>
          )}

          {matchMutation.data?.items.length === 0 && (
            <div className="p-5">
              <EmptyState title="没有找到推荐岗位" description="可以降低最低分数，或放宽技能和地点条件。" />
            </div>
          )}

          {matchMutation.data && matchMutation.data.items.length > 0 && (
            <div className="divide-y divide-slate-100">
              {matchMutation.data.items.map((item) => (
                <article key={item.job.id} className="p-5 transition hover:bg-slate-50/70">
                  <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                    <div>
                      <h2 className="font-semibold text-slate-950">{item.job.title}</h2>
                      <div className="mt-1 text-sm text-slate-500">
                        {item.job.company} {item.job.location ? `- ${item.job.location}` : ""}
                      </div>
                    </div>
                    <Badge variant={item.score >= 0.6 ? "success" : "warning"}>匹配度 {(item.score * 100).toFixed(0)}%</Badge>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {item.reasons.length > 0 ? (
                      item.reasons.map((reason) => (
                        <Badge key={reason} variant="default">
                          {reason}
                        </Badge>
                      ))
                    ) : (
                      <span className="text-sm text-slate-500">接口没有返回明确的推荐理由。</span>
                    )}
                  </div>
                </article>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
