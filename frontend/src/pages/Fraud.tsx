import React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import { ShieldAlert, ShieldCheck, RefreshCw, Check, AlertTriangle } from "lucide-react";

const Fraud: React.FC = () => {
  const queryClient = useQueryClient();

  const { data: alerts = [], isLoading, refetch } = useQuery({
    queryKey: ["fraud"],
    queryFn: api.fraud.list
  });

  const resolveMutation = useMutation({
    mutationFn: (id: number) => api.fraud.resolve(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["fraud"] });
    }
  });

  const activeAlerts = alerts.filter((a: any) => !a.is_resolved);
  
  // Calculate average risk score
  const avgRisk = alerts.length > 0 
    ? alerts.reduce((acc: number, cur: any) => acc + cur.risk_score, 0) / alerts.length
    : 15.0;

  return (
    <div className="space-y-8 pb-10">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold text-white">Cybersecurity Monitor</h1>
          <p className="text-slate-400 text-sm mt-1">Z-Score & Isolation Forest outlier transaction detection models</p>
        </div>
        <button
          onClick={() => refetch()}
          className="p-2.5 rounded-xl border border-white/5 bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white transition-all duration-200"
        >
          <RefreshCw className="w-5 h-5" />
        </button>
      </div>

      {/* Cyber stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className={`glass-card p-6 rounded-2xl border ${
          activeAlerts.length > 0 ? "border-brand-danger/35 bg-brand-danger/5 text-brand-danger" : "border-white/5 text-white"
        }`}>
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Active Threats</span>
          <div className="text-3xl font-extrabold mt-2">{activeAlerts.length} Warnings</div>
          <p className="text-xs text-slate-400 mt-1">Requires manual audit confirmation</p>
        </div>
        <div className="glass-card p-6 rounded-2xl">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500">System Risk Index</span>
          <div className="text-3xl font-extrabold text-white mt-2">{(avgRisk * 10).toFixed(0)} / 1000</div>
          <p className="text-xs text-slate-400 mt-1">Weighted transaction variance rating</p>
        </div>
        <div className="glass-card p-6 rounded-2xl border-brand-success/30 bg-brand-success/5">
          <span className="text-xs font-bold uppercase tracking-wider text-brand-success">Outlier Algorithms</span>
          <div className="text-3xl font-extrabold text-brand-success mt-2">Active</div>
          <p className="text-xs text-slate-300 mt-1">Z-Score threshold &gt; 2.5</p>
        </div>
      </div>

      {/* Fraud alerts list */}
      <div className="space-y-4">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-brand-danger" />
          Flagged Anomalous Outliers
        </h3>

        {isLoading ? (
          <div className="p-16 text-center text-slate-400 font-semibold">Scanning transaction variance...</div>
        ) : alerts.length === 0 ? (
          <div className="p-16 text-center text-slate-500 italic bg-slate-900/10 rounded-2xl border border-white/5">
            Clean scan. No transaction outliers or anomalous activity detected.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {alerts.map((a: any) => (
              <div key={a.id} className={`glass-card p-6 rounded-2xl border ${
                a.is_resolved 
                  ? "border-white/5 opacity-65 bg-slate-950/20" 
                  : "border-brand-danger/30 bg-brand-danger/[0.01]"
              } flex flex-col sm:flex-row sm:items-center justify-between gap-6`}>
                
                {/* Details */}
                <div className="flex items-start gap-4">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${
                    a.is_resolved ? "bg-slate-800 text-slate-400" : "bg-brand-danger/10 text-brand-danger"
                  }`}>
                    {a.is_resolved ? <ShieldCheck className="w-6 h-6" /> : <AlertTriangle className="w-6 h-6" />}
                  </div>
                  <div>
                    <div className="flex items-center gap-2.5">
                      <span className="font-bold text-white text-base">
                        {a.transaction?.merchant || "Unknown Merchant"}
                      </span>
                      <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider ${
                        a.severity === "High" 
                          ? "bg-brand-danger/15 text-brand-danger border border-brand-danger/30" 
                          : "bg-brand-warning/15 text-brand-warning border border-brand-warning/30"
                      }`}>
                        {a.severity} Severity
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">Reason: {a.reason}</p>
                    <p className="text-[10px] text-slate-500 font-mono mt-1">
                      Detected at: {new Date(a.detected_at).toLocaleString("en-IN")} | Z-Score Index: {a.risk_score.toFixed(2)}
                    </p>
                  </div>
                </div>

                {/* Amount and actions */}
                <div className="flex items-center justify-between sm:text-right gap-6">
                  <div>
                    <div className="text-lg font-extrabold text-white">
                      ₹{a.transaction?.amount ? a.transaction.amount.toLocaleString("en-IN") : "0"}
                    </div>
                    <span className="text-[10px] text-slate-500">Transaction Value</span>
                  </div>

                  {!a.is_resolved ? (
                    <button
                      onClick={() => resolveMutation.mutate(a.id)}
                      disabled={resolveMutation.isPending}
                      className="px-4 py-2 rounded-xl bg-brand-success hover:bg-brand-success/90 text-white text-xs font-bold transition-all flex items-center gap-1.5 shadow-md shadow-brand-success/15"
                    >
                      <Check className="w-3.5 h-3.5" />
                      Approve & Resolve
                    </button>
                  ) : (
                    <span className="px-3.5 py-1.5 rounded-xl border border-white/5 text-slate-500 text-xs font-bold">
                      Resolved
                    </span>
                  )}
                </div>

              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Fraud;
