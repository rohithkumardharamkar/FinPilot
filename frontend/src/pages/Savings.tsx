import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import { Target, RefreshCw, Sparkles, PlusCircle, AlertCircle, FileCheck } from "lucide-react";

const Savings: React.FC = () => {
  const queryClient = useQueryClient();

  // Standard Form State
  const [goalName, setGoalName] = useState("");
  const [targetAmount, setTargetAmount] = useState("");
  const [currentAmount, setCurrentAmount] = useState("");
  const [monthsHorizon, setMonthsHorizon] = useState("12");
  const [formSuccess, setFormSuccess] = useState("");
  const [formError, setFormError] = useState("");

  // AI Roadmap Form State
  const [aiName, setAiName] = useState("Goa Trip Fund");
  const [aiTarget, setAiTarget] = useState("35000");
  const [aiMonths, setAiMonths] = useState("6");
  const [roadmapOutput, setRoadmapOutput] = useState<any>(null);

  // Queries
  const { data: goals = [], isLoading, refetch } = useQuery({
    queryKey: ["goals"],
    queryFn: api.savings.list
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: (vars: { name: string; target: number; current: number; months: number }) => {
      const today = new Date();
      const targetDate = new Date(today.getFullYear(), today.getMonth() + vars.months, today.getDate()).toISOString();
      return api.savings.create({
        name: vars.name,
        target_amount: vars.target,
        current_amount: vars.current,
        start_date: today.toISOString(),
        target_date: targetDate,
        category: "Savings"
      });
    },
    onSuccess: () => {
      setFormSuccess("Savings goal established!");
      setGoalName("");
      setTargetAmount("");
      setCurrentAmount("");
      queryClient.invalidateQueries({ queryKey: ["goals"] });
    },
    onError: (err: any) => {
      setFormError(err.response?.data?.detail || "Failed to create savings goal.");
    }
  });

  const roadmapMutation = useMutation({
    mutationFn: (vars: { target: number; months: number; name: string }) =>
      api.savings.generateRoadmap(vars.target, vars.months, vars.name),
    onSuccess: (data) => {
      setRoadmapOutput(data);
      queryClient.invalidateQueries({ queryKey: ["goals"] });
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || "Roadmap generation failed. Please verify amounts.");
    }
  });

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormSuccess("");
    setFormError("");
    if (!goalName || !targetAmount) return;

    createMutation.mutate({
      name: goalName,
      target: parseFloat(targetAmount),
      current: parseFloat(currentAmount || "0"),
      months: parseInt(monthsHorizon)
    });
  };

  const handleRoadmapSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!aiTarget || !aiMonths) return;
    roadmapMutation.mutate({
      target: parseFloat(aiTarget),
      months: parseInt(aiMonths),
      name: aiName
    });
  };

  return (
    <div className="space-y-8 pb-10">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold text-white">Savings Hub</h1>
          <p className="text-slate-400 text-sm mt-1">Define milestones and optimize timelines with savings plans</p>
        </div>
        <button
          onClick={() => refetch()}
          className="p-2.5 rounded-xl border border-white/5 bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white transition-all duration-200"
        >
          <RefreshCw className="w-5 h-5" />
        </button>
      </div>

      {/* Main Grid Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Side: Create / Roadmaps */}
        <div className="lg:col-span-5 space-y-8">
          
          {/* Goal Achievement Agent Card */}
          <div className="glass-card p-6 rounded-2xl border-brand-primary/20 bg-brand-primary/[0.01]">
            <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-brand-primary" />
              AI Goal Achievement Agent
            </h3>
            <p className="text-xs text-slate-400 mb-6">
              Input targets (e.g. ₹5 Lakh in 18 months) to establish goals and generate savings roadmaps.
            </p>

            <form onSubmit={handleRoadmapSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Roadmap Objective</label>
                <input
                  type="text"
                  placeholder="e.g. European Tour, New Laptop"
                  value={aiName}
                  onChange={(e) => setAiName(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-xl glass-input text-sm"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Target Sum (₹)</label>
                  <input
                    type="number"
                    placeholder="e.g. 500000"
                    value={aiTarget}
                    onChange={(e) => setAiTarget(e.target.value)}
                    className="w-full px-3 py-2.5 rounded-xl glass-input text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Horizon (Months)</label>
                  <input
                    type="number"
                    placeholder="e.g. 18"
                    value={aiMonths}
                    onChange={(e) => setAiMonths(e.target.value)}
                    className="w-full px-3 py-2.5 rounded-xl glass-input text-sm"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={roadmapMutation.isPending}
                className="w-full py-3 rounded-xl bg-gradient-to-tr from-brand-primary to-indigo-500 hover:from-brand-primary/95 text-white font-bold transition-all text-sm flex items-center justify-center gap-2"
              >
                <Sparkles className="w-4 h-4" />
                {roadmapMutation.isPending ? "Analyzing budgets..." : "Calculate Savings Roadmap"}
              </button>
            </form>
          </div>

          {/* Standard Goal Setup */}
          <div className="glass-card p-6 rounded-2xl">
            <h3 className="text-lg font-bold text-white mb-4.5 flex items-center gap-2">
              <PlusCircle className="w-5 h-5 text-brand-success" />
              Manual Goal Setup
            </h3>

            <form onSubmit={handleCreateSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Goal Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Emergency Fund"
                  value={goalName}
                  onChange={(e) => setGoalName(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-xl glass-input text-sm"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Target (₹)</label>
                  <input
                    type="number"
                    required
                    placeholder="e.g. 100000"
                    value={targetAmount}
                    onChange={(e) => setTargetAmount(e.target.value)}
                    className="w-full px-3 py-2.5 rounded-xl glass-input text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Initial Saved (₹)</label>
                  <input
                    type="number"
                    placeholder="0"
                    value={currentAmount}
                    onChange={(e) => setCurrentAmount(e.target.value)}
                    className="w-full px-3 py-2.5 rounded-xl glass-input text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Timeline</label>
                <select
                  value={monthsHorizon}
                  onChange={(e) => setMonthsHorizon(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-xl glass-input text-sm"
                >
                  <option value="3">3 Months</option>
                  <option value="6">6 Months</option>
                  <option value="12">12 Months</option>
                  <option value="18">18 Months</option>
                  <option value="24">24 Months</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={createMutation.isPending}
                className="w-full py-3 rounded-xl bg-brand-primary hover:bg-brand-primary/95 text-white font-bold transition-all text-sm"
              >
                Create Savings Goal
              </button>

              {formSuccess && (
                <div className="p-3 rounded-xl bg-brand-success/10 border border-brand-success/20 text-brand-success text-xs font-semibold flex items-center gap-2">
                  <FileCheck className="w-4.5 h-4.5" />
                  {formSuccess}
                </div>
              )}

              {formError && (
                <div className="p-3 rounded-xl bg-brand-danger/10 border border-brand-danger/25 text-brand-danger text-xs font-semibold flex items-center gap-2">
                  <AlertCircle className="w-4.5 h-4.5" />
                  {formError}
                </div>
              )}
            </form>
          </div>

        </div>

        {/* Right Side: Goals & Roadmap display */}
        <div className="lg:col-span-7 space-y-6">
          
          {/* AI Roadmap Output */}
          {roadmapOutput && (
            <div className="glass-card p-6 rounded-2xl border border-brand-success/30 bg-brand-success/[0.01] space-y-4">
              <div className="flex items-center justify-between">
                <span className="font-extrabold text-sm text-brand-success uppercase tracking-wider">AI Roadmap Generated</span>
                <span className="text-xs text-slate-400">{roadmapOutput.months} Month Horizon</span>
              </div>

              <h4 className="text-xl font-bold text-white">Roadmap for {roadmapOutput.goal_name}</h4>
              
              <div className="grid grid-cols-3 gap-4 py-2 border-y border-white/5 text-center">
                <div>
                  <div className="text-xs text-slate-500 uppercase tracking-wider">Required /mo</div>
                  <div className="text-lg font-extrabold text-white">₹{roadmapOutput.required_monthly_savings.toLocaleString("en-IN")}</div>
                </div>
                <div>
                  <div className="text-xs text-slate-500 uppercase tracking-wider">Current /mo</div>
                  <div className="text-lg font-extrabold text-slate-400">₹{roadmapOutput.current_monthly_savings.toLocaleString("en-IN")}</div>
                </div>
                <div>
                  <div className="text-xs text-slate-500 uppercase tracking-wider">Monthly Gap</div>
                  <div className="text-lg font-extrabold text-brand-danger">₹{roadmapOutput.gap.toLocaleString("en-IN")}</div>
                </div>
              </div>

              <div className="space-y-3.5">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Actionable Savings Roadmap:</span>
                <ul className="space-y-2.5 text-xs text-slate-300">
                  {roadmapOutput.roadmap.map((line: string, idx: number) => (
                    <li key={idx} className="flex gap-2.5 items-start">
                      <div className="w-1.5 h-1.5 rounded-full bg-brand-success mt-1.5 flex-shrink-0"></div>
                      <span>{line}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          <h3 className="text-lg font-bold text-white">Monitored Savings Targets</h3>
          
          {isLoading ? (
            <div className="p-16 text-center text-slate-400 font-semibold">Loading goal profiles...</div>
          ) : goals.length === 0 ? (
            <div className="p-16 text-center text-slate-500 italic bg-slate-900/10 rounded-2xl border border-white/5">
              No active goals. Define manual targets or generate roadmaps above.
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {goals.map((g: any) => {
                const progress = g.target_amount > 0 ? (g.current_amount / g.target_amount) * 100 : 0;
                return (
                  <div key={g.id} className="glass-card p-6 rounded-2xl border border-white/5 space-y-4">
                    {/* Header */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-brand-success/15 border border-brand-success/20 flex items-center justify-center text-brand-success">
                          <Target className="w-5 h-5" />
                        </div>
                        <div>
                          <span className="font-bold text-white text-base">{g.name}</span>
                          <p className="text-[10px] text-slate-500 font-medium">
                            Target Date: {new Date(g.target_date).toLocaleDateString("en-IN")}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-extrabold text-sm text-white">
                          ₹{g.current_amount.toLocaleString("en-IN")} / ₹{g.target_amount.toLocaleString("en-IN")}
                        </div>
                        <span className={`text-[10px] font-extrabold uppercase tracking-wider ${
                          g.health_score > 75 ? "text-brand-success" : g.health_score > 40 ? "text-brand-warning" : "text-brand-danger"
                        }`}>
                          Health: {g.health_score}%
                        </span>
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="w-full h-2 rounded-full bg-slate-950 overflow-hidden border border-white/5">
                      <div 
                        className="h-full bg-gradient-to-r from-brand-primary to-brand-success rounded-full"
                        style={{ width: `${progress}%` }}
                      ></div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default Savings;
