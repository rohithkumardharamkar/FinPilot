import React from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { CalendarDays, RefreshCw, Trash2 } from "lucide-react";

const Subscriptions: React.FC = () => {
  const { data: subscriptions = [], isLoading, refetch } = useQuery({
    queryKey: ["subscriptions"],
    queryFn: api.subscriptions.list
  });

  // Calculate stats
  const totalCost = subscriptions.reduce((acc: number, cur: any) => acc + cur.monthly_cost, 0);
  const annualCost = subscriptions.reduce((acc: number, cur: any) => acc + cur.annual_cost, 0);
  const potentialSavings = subscriptions.reduce((acc: number, cur: any) => acc + cur.savings_opportunity, 0);

  return (
    <div className="space-y-8 pb-10">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold text-white">Subscription Audit</h1>
          <p className="text-slate-400 text-sm mt-1">Autonomous identification of recurring charges and cash leaks</p>
        </div>
        <button
          onClick={() => refetch()}
          className="p-2.5 rounded-xl border border-white/5 bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white transition-all duration-200"
        >
          <RefreshCw className="w-5 h-5" />
        </button>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-6 rounded-2xl">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Monthly Run Rate</span>
          <div className="text-3xl font-extrabold text-white mt-2">₹{totalCost.toLocaleString("en-IN")}/mo</div>
          <p className="text-xs text-slate-400 mt-1">Across all detected accounts</p>
        </div>
        <div className="glass-card p-6 rounded-2xl">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Annual Run Rate</span>
          <div className="text-3xl font-extrabold text-white mt-2">₹{annualCost.toLocaleString("en-IN")}/yr</div>
          <p className="text-xs text-slate-400 mt-1">Compounded subscription overhead</p>
        </div>
        <div className="glass-card p-6 rounded-2xl border-brand-warning/30 bg-brand-warning/5">
          <span className="text-xs font-bold uppercase tracking-wider text-brand-warning">Potential Annual Savings</span>
          <div className="text-3xl font-extrabold text-brand-warning mt-2">₹{potentialSavings.toLocaleString("en-IN")}/yr</div>
          <p className="text-xs text-slate-300 mt-1">Identified double charges & idle accounts</p>
        </div>
      </div>

      {/* Subscription List */}
      <div className="space-y-4">
        <h3 className="text-lg font-bold text-white">Detailed Account Breakdown</h3>
        
        {isLoading ? (
          <div className="p-16 text-center text-slate-400 font-semibold">Loading subscription database...</div>
        ) : subscriptions.length === 0 ? (
          <div className="p-16 text-center text-slate-500 italic bg-slate-900/10 rounded-2xl border border-white/5">
            No active subscriptions detected. Please ensure statements are uploaded.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {subscriptions.map((sub: any) => {
              const hasAlert = sub.is_unused || sub.duplicate_service;
              return (
                <div key={sub.id} className={`glass-card p-6 rounded-2xl border ${
                  hasAlert ? "border-brand-warning/30 bg-brand-warning/[0.02]" : "border-white/5"
                } flex flex-col md:flex-row md:items-center justify-between gap-6`}>
                  
                  {/* Left info */}
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 rounded-xl bg-slate-800 flex items-center justify-center text-slate-300 flex-shrink-0">
                      <CalendarDays className="w-6 h-6" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white text-base">{sub.merchant}</span>
                        {sub.is_unused && (
                          <span className="px-2 py-0.5 rounded-md bg-brand-danger/10 border border-brand-danger/25 text-brand-danger text-[10px] font-bold uppercase tracking-wider">
                            Idle Account
                          </span>
                        )}
                        {sub.duplicate_service && (
                          <span className="px-2 py-0.5 rounded-md bg-brand-warning/10 border border-brand-warning/25 text-brand-warning text-[10px] font-bold uppercase tracking-wider">
                            Duplicate Service
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-500 mt-1">Classification Confidence: {(sub.confidence_score * 100).toFixed(0)}%</p>
                      
                      {/* Cancel advice */}
                      {hasAlert && (
                        <div className="mt-3 text-xs text-slate-300 bg-slate-950/30 p-3 rounded-xl border border-white/5 max-w-xl">
                          💡 **Cancel Guide:** Go to `{sub.merchant.toLowerCase()}.com` &gt; Account Settings &gt; Billing. Cancel before your next statement date to prevent the ₹{sub.monthly_cost} charge.
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Right cost info */}
                  <div className="flex items-center justify-between md:text-right gap-6">
                    <div>
                      <div className="text-lg font-extrabold text-white">₹{sub.monthly_cost.toLocaleString("en-IN")}/mo</div>
                      <div className="text-xs text-slate-500">₹{sub.annual_cost.toLocaleString("en-IN")}/yr</div>
                    </div>

                    <button
                      onClick={() => alert(`Cancel prompt triggered for ${sub.merchant}. Instructions are logged.`)}
                      className={`px-4 py-2 rounded-xl text-xs font-bold transition-all duration-150 flex items-center gap-1.5 ${
                        hasAlert
                          ? "bg-brand-danger text-white hover:bg-brand-danger/90"
                          : "border border-white/10 hover:bg-white/5 text-slate-300 hover:text-white"
                      }`}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      {hasAlert ? "Flag to Cancel" : "Review billing"}
                    </button>
                  </div>

                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default Subscriptions;
