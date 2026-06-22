import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import { Wallet, Sparkles, RefreshCw, PlusCircle, AlertCircle, FileCheck } from "lucide-react";

const Budgets: React.FC = () => {
  const queryClient = useQueryClient();
  
  // Local form state
  const [category, setCategory] = useState("Shopping");
  const [amount, setAmount] = useState("");
  const [formSuccess, setFormSuccess] = useState("");
  const [formError, setFormError] = useState("");
  
  // Queries
  const { data: budgets = [], isLoading, refetch } = useQuery({
    queryKey: ["budgets"],
    queryFn: api.budgets.list
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: (vars: { category: string; amount: number; start: string; end: string }) =>
      api.budgets.create({
        category: vars.category,
        amount: vars.amount,
        start_date: vars.start,
        end_date: vars.end
      }),
    onSuccess: () => {
      setFormSuccess("Budget ceiling created successfully!");
      setAmount("");
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
    },
    onError: (err: any) => {
      setFormError(err.response?.data?.detail || "Failed to save budget.");
    }
  });

  const generateAIMutation = useMutation({
    mutationFn: api.budgets.generateAI,
    onSuccess: (data) => {
      alert(data.message || "AI Budgets generated successfully!");
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || "AI Ingestion requires historical transactions.");
    }
  });

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormSuccess("");
    setFormError("");
    if (!amount || parseFloat(amount) <= 0) return;
    
    // Set active monthly bounds
    const today = new Date();
    const start = new Date(today.getFullYear(), today.getMonth(), 1).toISOString();
    const end = new Date(today.getFullYear(), today.getMonth() + 1, 0, 23, 59, 59).toISOString();
    
    createMutation.mutate({
      category,
      amount: parseFloat(amount),
      start,
      end
    });
  };

  return (
    <div className="space-y-8 pb-10">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold text-white">Budget Settings</h1>
          <p className="text-slate-400 text-sm mt-1">Configure limits and track allocation usage</p>
        </div>
        
        <div className="flex items-center gap-3">
          <button
            onClick={() => generateAIMutation.mutate()}
            disabled={generateAIMutation.isPending}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-tr from-brand-primary to-indigo-500 hover:from-brand-primary/90 hover:to-indigo-500/90 text-sm font-bold text-white shadow-lg shadow-brand-primary/20 transition-all duration-200"
          >
            <Sparkles className="w-4 h-4" />
            {generateAIMutation.isPending ? "Configuring..." : "Generate AI Budgets"}
          </button>
          
          <button
            onClick={() => refetch()}
            className="p-2.5 rounded-xl border border-white/5 bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white transition-all"
          >
            <RefreshCw className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Main Budget Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Side: Create Budget Form */}
        <div className="lg:col-span-4 glass-card p-6 rounded-2xl h-fit">
          <h3 className="text-lg font-bold text-white mb-4.5 flex items-center gap-2">
            <PlusCircle className="w-5 h-5 text-brand-primary" />
            Set Category Cap
          </h3>

          <form onSubmit={handleCreateSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Category</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3 py-2.5 rounded-xl glass-input text-sm"
              >
                <option value="Shopping">Shopping</option>
                <option value="Food & Dining">Food & Dining</option>
                <option value="Utilities">Utilities</option>
                <option value="Entertainment">Entertainment</option>
                <option value="Travel">Travel</option>
                <option value="Rent">Rent</option>
                <option value="Investment">Investment</option>
                <option value="Others">Others</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Monthly Budget Limit (₹)</label>
              <input
                type="number"
                required
                placeholder="e.g. 15000"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="w-full px-3 py-2.5 rounded-xl glass-input text-sm"
              />
            </div>

            <button
              type="submit"
              disabled={createMutation.isPending}
              className="w-full py-3 rounded-xl bg-brand-primary hover:bg-brand-primary/95 text-white font-bold transition-all text-sm"
            >
              {createMutation.isPending ? "Saving..." : "Save Budget Limit"}
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

        {/* Right Side: Active Budget List */}
        <div className="lg:col-span-8 space-y-4">
          <h3 className="text-lg font-bold text-white">Current Trackers</h3>

          {isLoading ? (
            <div className="p-16 text-center text-slate-400 font-semibold">Loading budget targets...</div>
          ) : budgets.length === 0 ? (
            <div className="p-16 text-center text-slate-500 italic bg-slate-900/10 rounded-2xl border border-white/5">
              No budget limits defined. Tap "Generate AI Budgets" to automatically create personalized thresholds based on your statement history.
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {budgets.map((b: any) => {
                const percentage = b.amount > 0 ? (b.spent / b.amount) * 100 : 0;
                const isBreached = percentage > 100;
                const isWarning = percentage > 80 && percentage <= 100;
                
                return (
                  <div key={b.id} className="glass-card p-6 rounded-2xl border border-white/5 space-y-4">
                    {/* Top Row */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-brand-primary/10 border border-brand-primary/20 flex items-center justify-center text-brand-primary">
                          <Wallet className="w-5 h-5" />
                        </div>
                        <div>
                          <span className="font-bold text-white text-base">{b.category}</span>
                          <p className="text-[10px] text-slate-500 font-medium">Valid until EOM</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-extrabold text-sm text-white">
                          ₹{b.spent.toLocaleString("en-IN")} / ₹{b.amount.toLocaleString("en-IN")}
                        </div>
                        <span className={`text-[10px] font-bold uppercase tracking-wider ${
                          isBreached ? "text-brand-danger" : isWarning ? "text-brand-warning" : "text-brand-success"
                        }`}>
                          {percentage.toFixed(0)}% Used
                        </span>
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="w-full h-2.5 rounded-full bg-slate-950 border border-white/5 overflow-hidden">
                      <div 
                        className={`h-full rounded-full transition-all duration-500 ${
                          isBreached ? "bg-brand-danger" : isWarning ? "bg-brand-warning" : "bg-gradient-to-r from-brand-primary to-brand-success"
                        }`}
                        style={{ width: `${Math.min(100, percentage)}%` }}
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

export default Budgets;
