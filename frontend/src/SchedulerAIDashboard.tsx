import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  Download,
  FileJson,
  Search,
  Sparkles,
  Wand2,
} from "lucide-react";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";

type ApiStatus = "idle" | "loading" | "success" | "error";

type ParseResponse = {
  status: string;
  extracted_data: Record<string, unknown>;
};

type ScheduleResponse = {
  status: string;
  job_id?: string;
  graph_summary: {
    node_count?: number;
    edge_count?: number;
    color_count?: number;
  };
  validation: {
    is_valid?: boolean;
    error_count?: number;
    warning_count?: number;
    errors?: Array<Record<string, unknown>>;
    warnings?: Array<Record<string, unknown>>;
  };
  final_schedule: {
    days?: Record<string, Array<Record<string, unknown>>>;
    total_assignments?: number;
  };
  extracted_data?: Record<string, unknown>;
  normalized_data?: Record<string, unknown>;
  schedule_result?: Record<string, unknown>;
  is_valid: boolean;
};

type JobResponse = {
  status: string;
  job_id: string;
  job: ScheduleResponse;
};

type HealthResponse = {
  status: string;
  services: Record<string, { status?: string; [key: string]: unknown }>;
};

const DEFAULT_RAW_TEXT = "";
const STRATEGIES = ["largest_first", "saturation_largest_first", "DSATUR"] as const;

function prettyJson(value: unknown) {
  return JSON.stringify(value, null, 2);
}

function StatusDot({ status }: { status: ApiStatus | string }) {
  const tone =
    status === "success"
      ? "bg-emerald-400 shadow-[0_0_12px_rgba(52,211,153,0.5)]"
      : status === "error"
        ? "bg-rose-500 shadow-[0_0_12px_rgba(244,63,94,0.5)]"
        : status === "loading"
          ? "bg-indigo-400 shadow-[0_0_12px_rgba(129,140,248,0.5)] animate-pulse"
          : "bg-slate-300";

  return <span className={`h-2.5 w-2.5 rounded-full ${tone}`} />;
}

function LoadingTime({ startedAt }: { startedAt: number | null }) {
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    if (!startedAt) return;

    setNow(Date.now());
    const intervalId = window.setInterval(() => setNow(Date.now()), 500);
    return () => window.clearInterval(intervalId);
  }, [startedAt]);

  if (!startedAt) return null;

  const elapsedSeconds = Math.max(0, Math.floor((now - startedAt) / 1000));
  return <span className="tabular-nums text-slate-500">{elapsedSeconds}s</span>;
}

function Metric({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="relative overflow-hidden rounded-xl border border-white/60 bg-white/70 shadow-sm p-5 backdrop-blur-md transition-all hover:bg-white/90">
      <div className="absolute -right-4 -top-4 h-24 w-24 rounded-full bg-indigo-500/10 blur-2xl pointer-events-none" />
      <p className="text-[11px] font-bold uppercase tracking-widest text-slate-500">{label}</p>
      <p className="mt-3 text-3xl font-bold tracking-tight text-slate-800">{value}</p>
    </div>
  );
}

function JsonBlock({ data }: { data: unknown }) {
  return (
    <pre className="max-h-[460px] overflow-auto rounded-xl border border-slate-200 bg-slate-50/50 p-6 text-xs leading-6 text-slate-700 shadow-inner custom-scrollbar">
      {prettyJson(data)}
    </pre>
  );
}

function getScheduleRows(schedule?: ScheduleResponse["final_schedule"]) {
  const days = schedule?.days ?? {};
  return Object.entries(days).flatMap(([day, items]) =>
    items.map((item) => ({
      day,
      employee_name: String(item.employee_name ?? "-"),
      shift_id: String(item.shift_id ?? "-"),
      start_time: String(item.start_time ?? "-"),
      end_time: String(item.end_time ?? "-"),
      location: String(item.location ?? "-"),
    })),
  );
}

function ScheduleView({ schedule }: { schedule?: ScheduleResponse["final_schedule"] }) {
  const rows = getScheduleRows(schedule);

  if (!rows.length) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 bg-white/50 p-16 text-center text-sm text-slate-500 shadow-inner">
        <Sparkles className="mb-4 h-8 w-8 text-slate-300" />
        <p>No valid schedule generated yet. Awaiting extraction engine.</p>
      </div>
    );
  }

  return (
    <Card className="overflow-hidden border-white/60 bg-white/80 shadow-[0_8px_30px_rgb(0,0,0,0.04)] backdrop-blur-xl">
      <CardHeader className="border-b border-slate-100 bg-white/50 pb-5">
        <CardTitle className="text-xl font-bold tracking-tight text-slate-800">Generated Schedule Flow</CardTitle>
        <CardDescription className="text-slate-500">Assignments mapped against dynamic validity constraints.</CardDescription>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50/80">
              <tr className="border-b border-slate-200 text-left text-slate-500">
                <th className="px-6 py-4 font-semibold tracking-wide">Day</th>
                <th className="px-6 py-4 font-semibold tracking-wide">Employee</th>
                <th className="px-6 py-4 font-semibold tracking-wide">Shift</th>
                <th className="px-6 py-4 font-semibold tracking-wide">Time</th>
                <th className="px-6 py-4 font-semibold tracking-wide">Location</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {rows.map((row, index) => (
                <tr
                  key={`${row.day}-${row.shift_id}-${index}`}
                  className="transition-colors hover:bg-white"
                >
                  <td className="px-6 py-5 font-medium capitalize text-slate-700">{row.day}</td>
                  <td className="px-6 py-5 font-semibold text-indigo-600">{row.employee_name}</td>
                  <td className="px-6 py-5 text-slate-500">{row.shift_id}</td>
                  <td className="px-6 py-5 text-slate-600">
                    <span className="inline-flex items-center rounded-md bg-slate-100 px-2 py-1 text-xs font-mono border border-slate-200 shadow-sm">
                      {row.start_time} - {row.end_time}
                    </span>
                  </td>
                  <td className="px-6 py-5 text-slate-500">{row.location}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

export default function SchedulerAIDashboard() {
  const [apiBaseUrl, setApiBaseUrl] = useState("http://127.0.0.1:8000/api/v1");
  const [rawText, setRawText] = useState(DEFAULT_RAW_TEXT);
  const [strategy, setStrategy] = useState<string>("largest_first");
  const [jobIdInput, setJobIdInput] = useState("");

  const [healthStatus, setHealthStatus] = useState<ApiStatus>("idle");
  const [parseStatus, setParseStatus] = useState<ApiStatus>("idle");
  const [scheduleStatus, setScheduleStatus] = useState<ApiStatus>("idle");
  const [jobStatus, setJobStatus] = useState<ApiStatus>("idle");
  const [healthStartedAt, setHealthStartedAt] = useState<number | null>(null);
  const [parseStartedAt, setParseStartedAt] = useState<number | null>(null);
  const [scheduleStartedAt, setScheduleStartedAt] = useState<number | null>(null);
  const [jobStartedAt, setJobStartedAt] = useState<number | null>(null);

  const [healthData, setHealthData] = useState<HealthResponse | null>(null);
  const [parseData, setParseData] = useState<ParseResponse | null>(null);
  const [scheduleData, setScheduleData] = useState<ScheduleResponse | null>(null);
  const [jobData, setJobData] = useState<JobResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

  const normalizedBaseUrl = useMemo(() => apiBaseUrl.replace(/\/$/, ""), [apiBaseUrl]);
  const scheduleRows = useMemo(
    () => getScheduleRows(scheduleData?.final_schedule),
    [scheduleData?.final_schedule],
  );

  async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${normalizedBaseUrl}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers || {}),
      },
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = typeof data?.detail === "string" ? data.detail : "Request failed";
      throw new Error(detail);
    }

    return data as T;
  }

  async function handleHealthCheck() {
    setErrorMessage("");
    setHealthStatus("loading");
    setHealthStartedAt(Date.now());
    try {
      const data = await requestJson<HealthResponse>("/health", { method: "GET" });
      setHealthData(data);
      setHealthStatus("success");
    } catch (error) {
      setHealthStatus("error");
      setErrorMessage(error instanceof Error ? error.message : "Health check failed");
    } finally {
      setHealthStartedAt(null);
    }
  }

  async function handleParse() {
    setErrorMessage("");
    setParseStatus("loading");
    setParseStartedAt(Date.now());
    try {
      const data = await requestJson<ParseResponse>("/parse", {
        method: "POST",
        body: JSON.stringify({
          raw_text: rawText,
          domain: "workforce_schedule",
          metadata: {},
        }),
      });
      setParseData(data);
      setParseStatus("success");
    } catch (error) {
      setParseStatus("error");
      setErrorMessage(error instanceof Error ? error.message : "Parse request failed");
    } finally {
      setParseStartedAt(null);
    }
  }

  async function handleSchedule() {
    setErrorMessage("");
    setScheduleStatus("loading");
    setScheduleStartedAt(Date.now());
    try {
      const data = await requestJson<ScheduleResponse>("/schedule", {
        method: "POST",
        body: JSON.stringify({
          raw_text: rawText,
          strategy,
          metadata: {},
        }),
      });
      setScheduleData(data);
      setScheduleStatus("success");
      if (data.job_id) setJobIdInput(data.job_id);
    } catch (error) {
      setScheduleStatus("error");
      setErrorMessage(error instanceof Error ? error.message : "Schedule request failed");
    } finally {
      setScheduleStartedAt(null);
    }
  }

  function handleDownloadPdf() {
    if (!scheduleRows.length) {
      setErrorMessage("No schedule available to export.");
      return;
    }

    const doc = new jsPDF({ orientation: "portrait", unit: "pt", format: "a4" });
    doc.setFontSize(18);
    doc.text("Scheduler AI Schedule", 40, 40);
    doc.setFontSize(10);
    doc.text(`Strategy: ${strategy}`, 40, 58);
    doc.text(
      `Total assignments: ${String(scheduleData?.final_schedule?.total_assignments ?? scheduleRows.length)}`,
      40,
      72,
    );

    autoTable(doc, {
      startY: 90,
      head: [["Day", "Employee", "Shift", "Time", "Location"]],
      body: scheduleRows.map((row) => [
        row.day,
        row.employee_name,
        row.shift_id,
        `${row.start_time} - ${row.end_time}`,
        row.location,
      ]),
      styles: {
        fontSize: 10,
        cellPadding: 6,
      },
      headStyles: {
        fillColor: [15, 23, 42],
      },
      alternateRowStyles: {
        fillColor: [248, 250, 252],
      },
      margin: { left: 40, right: 40 },
    });

    doc.save("schedule.pdf");
  }

  async function handleJobLookup() {
    if (!jobIdInput.trim()) return;
    setErrorMessage("");
    setJobStatus("loading");
    setJobStartedAt(Date.now());
    try {
      const data = await requestJson<JobResponse>(`/jobs/${jobIdInput.trim()}`, {
        method: "GET",
      });
      setJobData(data);
      setJobStatus("success");
    } catch (error) {
      setJobStatus("error");
      setErrorMessage(error instanceof Error ? error.message : "Job lookup failed");
    } finally {
      setJobStartedAt(null);
    }
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-50/50 via-white to-slate-50 px-4 py-12 text-slate-800 selection:bg-indigo-500/10 font-sans">
      <div className="mx-auto max-w-6xl space-y-8">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-3xl border border-white bg-white/60 p-8 shadow-[0_8px_30px_rgb(0,0,0,0.06)] backdrop-blur-3xl"
        >
          <div className="flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
            <div className="space-y-4">
              <div className="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-indigo-50 px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-indigo-700 shadow-sm">
                <Sparkles className="h-4 w-4" />
                Scheduler AI Engine
              </div>
              <h1 className="max-w-3xl text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl">
                Algorithmic Workforce Routing
              </h1>
              <p className="max-w-2xl text-base leading-relaxed text-slate-500">
                A premium intelligence dashboard for evaluating spatial, temporal, and logic constraints against autonomous AI staffing models.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-4 rounded-2xl border border-slate-100 bg-white/50 p-3 text-sm font-semibold text-slate-600 shadow-sm backdrop-blur-md">
              <div className="flex items-center gap-3 rounded-lg px-3 py-2 transition-colors hover:bg-white hover:shadow-sm">
                <StatusDot status={healthStatus} />
                <span>Health Bridge</span>
              </div>
              <div className="flex items-center gap-3 rounded-lg px-3 py-2 transition-colors hover:bg-white hover:shadow-sm">
                <StatusDot status={parseStatus} />
                <span>Extracted</span>
              </div>
              <div className="flex items-center gap-3 rounded-lg px-3 py-2 transition-colors hover:bg-white hover:shadow-sm">
                <StatusDot status={scheduleStatus} />
                <span>Computed</span>
              </div>
              <div className="flex items-center gap-3 rounded-lg px-3 py-2 transition-colors hover:bg-white hover:shadow-sm">
                <StatusDot status={jobStatus} />
                <span>Cached Data</span>
              </div>
            </div>
          </div>
        </motion.div>

        <div className="grid gap-8 lg:grid-cols-[1.15fr_0.85fr]">
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 }}
          >
            <Card className="border-white/60 bg-white/80 backdrop-blur-xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] h-full">
              <CardHeader className="border-b border-slate-100 bg-white/50 pb-5">
                <CardTitle className="text-xl font-bold tracking-tight text-slate-800">Execution Telemetry</CardTitle>
                <CardDescription className="text-slate-500">Configure LLM extraction and solver heuristics.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6 pt-6">
                <div className="space-y-3">
                  <label className="text-[10px] font-bold uppercase tracking-widest text-slate-500">API Context Layer</label>
                  <div className="flex flex-col gap-3 sm:flex-row">
                    <Input 
                      className="border-slate-200 bg-white/80 text-slate-800 focus-visible:ring-indigo-500/50 shadow-sm"
                      value={apiBaseUrl} 
                      onChange={(event) => setApiBaseUrl(event.target.value)} 
                    />
                    <Button
                      onClick={handleHealthCheck}
                      variant="outline"
                      className="border-slate-200 bg-white text-slate-700 hover:bg-slate-50 hover:text-indigo-600 transition-all shadow-sm"
                      disabled={healthStatus === "loading"}
                    >
                      <Activity className="mr-2 h-4 w-4" />
                      {healthStatus === "loading" ? "Probing..." : "Ping Endpoint"}
                      <LoadingTime startedAt={healthStartedAt} />
                    </Button>
                  </div>
                </div>

                <div className="space-y-3">
                  <label className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Natural Language Schema</label>
                  <Textarea
                    value={rawText}
                    onChange={(event) => setRawText(event.target.value)}
                    className="min-h-[280px] border-slate-200 bg-white/80 text-sm leading-relaxed text-slate-700 placeholder:text-slate-400 focus-visible:ring-indigo-500/50 resize-y custom-scrollbar shadow-inner"
                    placeholder="Provide explicit operational parameters here..."
                  />
                </div>

                <div className="grid gap-3 sm:grid-cols-[1fr_auto_auto]">
                  <Select value={strategy} onValueChange={setStrategy}>
                    <SelectTrigger className="border-slate-200 bg-white/80 text-slate-700 focus:ring-indigo-500/50 shadow-sm">
                      <SelectValue placeholder="Select heuristic" />
                    </SelectTrigger>
                    <SelectContent className="border-slate-100 bg-white text-slate-700">
                      {STRATEGIES.map((item) => (
                        <SelectItem key={item} value={item} className="focus:bg-indigo-50 focus:text-indigo-700 cursor-pointer">
                          {item}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  <Button
                    onClick={handleParse}
                    variant="outline"
                    className="border-slate-200 bg-white text-slate-700 hover:bg-slate-50 hover:text-indigo-600 transition-all shadow-sm"
                    disabled={parseStatus === "loading"}
                  >
                    <FileJson className="mr-2 h-4 w-4" />
                    {parseStatus === "loading" ? "Parsing..." : "Extract Node Map"}
                    <LoadingTime startedAt={parseStartedAt} />
                  </Button>

                  <Button 
                    onClick={handleSchedule} 
                    className="bg-indigo-600 text-white font-bold tracking-wide hover:bg-indigo-500 shadow-[0_4px_14px_0_rgba(99,102,241,0.39)] transition-all hover:shadow-[0_6px_20px_rgba(99,102,241,0.23)] hover:-translate-y-0.5"
                    disabled={scheduleStatus === "loading"}
                  >
                    <Wand2 className="mr-2 h-4 w-4" />
                    {scheduleStatus === "loading" ? "Computing Constraints..." : "Initialize Engine"}
                    <LoadingTime startedAt={scheduleStartedAt} />
                  </Button>
                </div>

                {errorMessage ? (
                  <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-4 text-sm text-red-800 shadow-sm">
                    <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-600" />
                    <span className="font-medium leading-relaxed">{errorMessage}</span>
                  </div>
                ) : null}
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card className="border-white/60 bg-white/80 backdrop-blur-xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] h-full">
              <CardHeader className="border-b border-slate-100 bg-white/50 pb-5">
                <CardTitle className="text-xl font-bold tracking-tight text-slate-800">Graph Diagnostics</CardTitle>
                <CardDescription className="text-slate-500">Node generation & solver validation context.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6 pt-6">
                <div className="grid gap-4 sm:grid-cols-2">
                  <Metric label="Graph Nodes" value={scheduleData?.graph_summary?.node_count ?? "-"} />
                  <Metric label="Conflicts Map" value={scheduleData?.graph_summary?.edge_count ?? "-"} />
                  <Metric label="Colors (Shifts)" value={scheduleData?.graph_summary?.color_count ?? "-"} />
                  <Metric label="Is Fully Valid" value={scheduleData?.is_valid ? "Yes" : scheduleData ? "No" : "-"} />
                </div>

                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-6 shadow-inner relative overflow-hidden">
                  <div className="absolute top-0 right-0 h-40 w-40 bg-zinc-200 blur-3xl pointer-events-none rounded-full" />
                  <div className="flex items-center gap-3 text-sm font-bold uppercase tracking-widest text-slate-500">
                    {scheduleData?.is_valid ? (
                      <CheckCircle2 className="h-5 w-5 text-emerald-500 drop-shadow-sm" />
                    ) : (
                      <AlertCircle className="h-5 w-5 text-slate-400" />
                    )}
                    Validation Matrix
                  </div>
                  <div className="mt-5 grid gap-4 sm:grid-cols-2">
                    <div className="rounded-xl border border-white bg-white/80 p-4 shadow-sm backdrop-blur-sm">
                      <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Strict Errors</p>
                      <p className="mt-2 text-3xl font-extrabold text-slate-800">{scheduleData?.validation?.error_count ?? 0}</p>
                    </div>
                    <div className="rounded-xl border border-white bg-white/80 p-4 shadow-sm backdrop-blur-sm">
                      <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Soft Warnings</p>
                      <p className="mt-2 text-3xl font-extrabold text-slate-800">{scheduleData?.validation?.warning_count ?? 0}</p>
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  <label className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Cache Fetching</label>
                  <div className="flex gap-3">
                    <Input
                      value={jobIdInput}
                      onChange={(event) => setJobIdInput(event.target.value)}
                      placeholder="Input memory UUID..."
                      className="border-slate-200 bg-white/80 text-slate-800 focus-visible:ring-indigo-500/50 shadow-sm"
                    />
                    <Button
                      onClick={handleJobLookup}
                      variant="outline"
                      className="border-slate-200 bg-white text-slate-700 hover:bg-slate-50 transition-colors shadow-sm"
                      disabled={jobStatus === "loading"}
                    >
                      <Search className="mr-2 h-4 w-4" />
                      {jobStatus === "loading" ? "Retrieving..." : "Query Cache"}
                      <LoadingTime startedAt={jobStartedAt} />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        <Tabs defaultValue="schedule" className="w-full">
          <TabsList className="grid w-full grid-cols-4 border border-white/60 bg-white/80 p-1.5 shadow-sm rounded-2xl backdrop-blur-md">
            <TabsTrigger value="schedule" className="data-[state=active]:bg-indigo-50 data-[state=active]:text-indigo-700 data-[state=active]:shadow-sm text-slate-500 rounded-xl transition-all py-2 font-medium tracking-wide">Operation Matrix</TabsTrigger>
            <TabsTrigger value="parse" className="data-[state=active]:bg-white data-[state=active]:text-slate-900 data-[state=active]:shadow-sm text-slate-500 rounded-xl transition-all py-2 font-medium tracking-wide">Abstract Nodes</TabsTrigger>
            <TabsTrigger value="health" className="data-[state=active]:bg-white data-[state=active]:text-slate-900 data-[state=active]:shadow-sm text-slate-500 rounded-xl transition-all py-2 font-medium tracking-wide">Infrastructure</TabsTrigger>
            <TabsTrigger value="job" className="data-[state=active]:bg-white data-[state=active]:text-slate-900 data-[state=active]:shadow-sm text-slate-500 rounded-xl transition-all py-2 font-medium tracking-wide">Cache Buffer</TabsTrigger>
          </TabsList>

          <TabsContent value="schedule" className="mt-8 space-y-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between px-2">
              <div className="space-y-1">
                <h2 className="text-2xl font-extrabold tracking-tight text-slate-800">Operational Schedule</h2>
                <p className="text-sm text-slate-500">Chronological mapping of resources and assignments.</p>
              </div>
              <Button onClick={handleDownloadPdf} variant="outline" className="border-slate-200 bg-white text-slate-700 hover:bg-slate-50 hover:text-indigo-600 transition-all shadow-sm">
                <Download className="mr-2 h-4 w-4" /> Export Ledger
              </Button>
            </div>
            <ScheduleView schedule={scheduleData?.final_schedule} />
          </TabsContent>

          <TabsContent value="parse" className="mt-8">
            <Card className="border-white/60 bg-white/80 shadow-[0_8px_30px_rgb(0,0,0,0.04)] backdrop-blur-xl">
              <CardHeader className="border-b border-slate-100 bg-white/50 pb-5">
                <CardTitle className="text-slate-800 text-xl font-bold">Node Extraction Context</CardTitle>
                <CardDescription className="text-slate-500">Raw LLM inference payload output.</CardDescription>
              </CardHeader>
              <CardContent className="pt-6">
                <JsonBlock data={parseData?.extracted_data ?? parseData ?? {}} />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="health" className="mt-8">
            <Card className="border-white/60 bg-white/80 shadow-[0_8px_30px_rgb(0,0,0,0.04)] backdrop-blur-xl">
              <CardHeader className="border-b border-slate-100 bg-white/50 pb-5">
                <CardTitle className="text-slate-800 text-xl font-bold">Diagnostics Output</CardTitle>
                <CardDescription className="text-slate-500">Server instance bindings.</CardDescription>
              </CardHeader>
              <CardContent className="pt-6">
                <JsonBlock data={healthData ?? {}} />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="job" className="mt-8">
            <Card className="border-white/60 bg-white/80 shadow-[0_8px_30px_rgb(0,0,0,0.04)] backdrop-blur-xl">
              <CardHeader className="border-b border-slate-100 bg-white/50 pb-5">
                <CardTitle className="text-slate-800 text-xl font-bold">Persistent Blob</CardTitle>
                <CardDescription className="text-slate-500">Memory address trace output.</CardDescription>
              </CardHeader>
              <CardContent className="pt-6">
                <JsonBlock data={jobData ?? {}} />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
