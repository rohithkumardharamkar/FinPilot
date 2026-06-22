import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import { FileText, RefreshCw, Sparkles } from "lucide-react";

const Reports: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedReportId, setSelectedReportId] = useState<number | null>(null);

  // Queries
  const { data: reports = [], isLoading, refetch } = useQuery({
    queryKey: ["reports"],
    queryFn: api.reports.list
  });

  const { data: activeReportContent } = useQuery({
    queryKey: ["reportContent", selectedReportId],
    queryFn: () => (selectedReportId ? api.reports.get(selectedReportId) : null),
    enabled: !!selectedReportId
  });

  // Manual generation trigger mutation
  const generateMutation = useMutation({
    mutationFn: api.reports.generate,
    onSuccess: (data) => {
      alert("New Financial Health Report compiled successfully by the agent team!");
      setSelectedReportId(data.id);
      queryClient.invalidateQueries({ queryKey: ["reports"] });
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || "Make sure you have uploaded statement CSVs before triggering review.");
    }
  });

  // Auto-select first report if none selected
  React.useEffect(() => {
    if (reports.length > 0 && !selectedReportId) {
      setSelectedReportId(reports[0].id);
    }
  }, [reports, selectedReportId]);

  return (
    <div className="space-y-8 pb-10">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold text-white">Financial Reports</h1>
          <p className="text-slate-400 text-sm mt-1">Multi-agent executive summaries compiling wellness indices and risks</p>
        </div>
        
        <div className="flex items-center gap-3">
          <button
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-tr from-brand-primary to-indigo-500 hover:from-brand-primary/90 hover:to-indigo-500/90 text-sm font-bold text-white shadow-lg shadow-brand-primary/20 transition-all"
          >
            <Sparkles className="w-4 h-4" />
            {generateMutation.isPending ? "Compiling..." : "Trigger Manual Review"}
          </button>
          
          <button
            onClick={() => refetch()}
            className="p-2.5 rounded-xl border border-white/5 bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white transition-all"
          >
            <RefreshCw className="w-5 h-5" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Side: Report History List */}
        <div className="lg:col-span-4 glass-card p-6 rounded-2xl h-fit space-y-4">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500">Report Archive</h3>
          
          {isLoading ? (
            <div className="text-center py-8 text-slate-400 font-semibold text-xs">Loading logs...</div>
          ) : reports.length === 0 ? (
            <div className="text-center py-10 text-slate-500 italic text-xs">
              No reports compiled. Tap "Trigger Manual Review" to start your first assessment.
            </div>
          ) : (
            <div className="space-y-2">
              {reports.map((r: any) => {
                const isSelected = selectedReportId === r.id;
                return (
                  <button
                    key={r.id}
                    onClick={() => setSelectedReportId(r.id)}
                    className={`w-full flex items-start gap-3 p-3.5 rounded-xl text-left border transition-all duration-150 ${
                      isSelected
                        ? "bg-brand-primary/10 border-brand-primary/30 text-white font-semibold"
                        : "border-transparent text-slate-400 hover:text-white hover:bg-white/5"
                    }`}
                  >
                    <FileText className={`w-5 h-5 mt-0.5 ${isSelected ? "text-brand-primary" : "text-slate-400"}`} />
                    <div className="min-w-0">
                      <div className="text-sm truncate font-bold text-white">{r.title}</div>
                      <span className="text-[10px] text-slate-500 font-mono">
                        {new Date(r.generated_at).toLocaleDateString("en-IN", {
                          month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit"
                        })}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Side: Report Markdown Viewer */}
        <div className="lg:col-span-8 glass-card p-8 rounded-2xl min-h-[500px]">
          {selectedReportId ? (
            activeReportContent ? (
              <div className="prose prose-invert max-w-none space-y-6">
                <h2 className="text-2xl font-extrabold text-white border-b border-white/5 pb-4">
                  {activeReportContent.title}
                </h2>
                
                {/* Renders basic markdown spacing and typography */}
                <div className="text-sm leading-relaxed text-slate-300 font-normal whitespace-pre-wrap">
                  {activeReportContent.content_markdown}
                </div>
              </div>
            ) : (
              <div className="p-16 text-center text-slate-400 font-semibold">Retrieving report content...</div>
            )
          ) : (
            <div className="flex flex-col items-center justify-center h-96 text-center text-slate-500 italic">
              <FileText className="w-12 h-12 text-slate-700 mb-4" />
              <span>Select a report from the archive to view details or click "Trigger Manual Review" above.</span>
            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default Reports;
