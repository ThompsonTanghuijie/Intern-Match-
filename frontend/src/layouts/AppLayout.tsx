import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Badge } from "../components/ui/Badge";
import { API_BASE_URL, getHealth } from "../lib/api";
import { cn } from "../lib/utils";

const navItems = [
  { to: "/dashboard", label: "概览", icon: "概" },
  { to: "/jobs", label: "岗位", icon: "岗" },
  { to: "/match", label: "匹配", icon: "配" },
  { to: "/sources", label: "数据源", icon: "源" }
];

const pageMeta: Record<string, { title: string; description: string }> = {
  "/dashboard": {
    title: "市场概览",
    description: "快速查看岗位供给、数据源状态和职位趋势。"
  },
  "/jobs": {
    title: "岗位搜索",
    description: "搜索、筛选并查看正在招聘的实习和应届岗位。"
  },
  "/match": {
    title: "推荐生成器",
    description: "根据你的技能、目标地点和求职方向为岗位打分。"
  },
  "/sources": {
    title: "数据源管理",
    description: "监控已配置的数据源，并在需要时手动触发新的抓取。"
  }
};

export function AppLayout() {
  const location = useLocation();
  const meta = pageMeta[location.pathname] ?? { title: "实习匹配平台", description: "招聘信息分析工作台。" };
  const { data: health, isLoading: healthLoading, isError: healthError } = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 30_000,
    retry: 1
  });

  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <aside className="fixed inset-y-0 left-0 hidden w-72 border-r border-slate-200 bg-white px-4 py-5 lg:block">
        <div className="mb-7 flex items-center gap-3 px-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-950 text-sm font-semibold text-white shadow-sm">
            习
          </div>
          <div>
            <div className="text-base font-semibold">实习匹配平台</div>
            <div className="text-sm text-slate-500">岗位采集看板</div>
          </div>
        </div>
        <nav className="space-y-1.5">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition",
                  isActive ? "bg-slate-950 text-white shadow-sm" : "text-slate-600 hover:bg-slate-100 hover:text-slate-950"
                )
              }
            >
              <span className="flex h-6 w-6 items-center justify-center rounded bg-white/10 text-xs">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="absolute bottom-5 left-4 right-4 rounded-lg border border-slate-200 bg-slate-50 p-4">
          <div className="text-sm font-medium">接口地址</div>
          <div className="mt-1 truncate text-xs text-slate-500">{API_BASE_URL}</div>
        </div>
      </aside>

      <div className="lg:pl-72">
        <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/90 px-4 py-4 backdrop-blur sm:px-6 lg:px-8">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-2xl font-semibold tracking-tight">{meta.title}</h1>
              <p className="mt-1 text-sm text-slate-500">{meta.description}</p>
            </div>
            <div className="flex items-center gap-3">
              <Badge variant={healthError ? "danger" : health?.status === "ok" ? "success" : "default"}>
                {healthLoading ? "正在检查接口" : healthError ? "接口离线" : `${health?.app ?? "接口"}：${health?.status === "ok" ? "正常" : health?.status ?? "未知"}`}
              </Badge>
            </div>
            <nav className="flex gap-2 overflow-x-auto lg:hidden">
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    cn(
                      "whitespace-nowrap rounded-md px-3 py-2 text-sm font-medium",
                      isActive ? "bg-slate-950 text-white" : "border border-slate-200 bg-white text-slate-600"
                    )
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </nav>
          </div>
        </header>

        <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
