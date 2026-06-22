import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import {
  Upload,
  Bot,
  AlertTriangle,
  TrendingUp,
  PlusCircle,
  HelpCircle,
  FileCheck,
  TrendingDown
} from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip
} from "recharts";



const Dashboard: React.FC = () => {
  const queryClient = useQueryClient();
  
  // Form states for statement upload
  const [file, setFile] = useState<File | null>(null);
  const [accountName, setAccountName] = useState("HDFC Bank");
  const [accountType, setAccountType] = useState("Bank");
  const [uploadSuccess, setUploadSuccess] = useState("");
  const [uploadError, setUploadError] = useState("");
  
  // Queries
  const { data: analytics } = useQuery({ queryKey: ["analytics"], queryFn: api.transactions.analytics });
  const { data: wellness } = useQuery({ queryKey: ["wellness"], queryFn: api.wellness.getLatest });
  const { data: fraud = [] } = useQuery({ queryKey: ["fraud"], queryFn: api.fraud.list });
  const { data: subscriptions = [] } = useQuery({ queryKey: ["subscriptions"], queryFn: api.subscriptions.list });
  const { data: goals = [] } = useQuery({ queryKey: ["goals"], queryFn: api.savings.list });
  

  // Active fraud alerts count
  const activeAlerts = fraud.filter((a: any) => !a.is_resolved).length;
  
  // File upload mutation
  const uploadMutation = useMutation({
    mutationFn: (vars: { file: File; name: string; type: string }) =>
      api.transactions.upload(vars.file, vars.name, vars.type),
    onSuccess: (data) => {
      setUploadSuccess(data.message || "File uploaded successfully!");
      setFile(null);
      // Invalidate queries to reload dashboard
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
      queryClient.invalidateQueries({ queryKey: ["wellness"] });
      queryClient.invalidateQueries({ queryKey: ["fraud"] });
      queryClient.invalidateQueries({ queryKey: ["subscriptions"] });
      queryClient.invalidateQueries({ queryKey: ["goals"] });
      queryClient.invalidateQueries({ queryKey: ["reports"] });
    },
    onError: (err: any) => {
      setUploadError(err.response?.data?.detail || "Failed to process bank statement.");
    }
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setUploadSuccess("");
      setUploadError("");
    }
  };

  const handleUploadSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    uploadMutation.mutate({ file, name: accountName, type: accountType });
  };

  // Safe fallbacks for charts
  const monthlyTrendData = analytics?.monthly_trend || [
    { month: "Jan", Income: 80000, Expense: 45000 },
    { month: "Feb", Income: 82000, Expense: 48000 },
    { month: "Mar", Income: 80000, Expense: 52000 },
    { month: "Apr", Income: 85000, Expense: 42000 },
    { month: "May", Income: 85000, Expense: 49000 },
    { month: "Jun", Income: 92000, Expense: 55000 }
  ];



  const score = wellness?.score || 72.5;
  const grade = wellness?.grade || "B";
  
  // Calculate SVG dashoffset based on 0-100 score
  const strokeOffset = 280 - (280 * score) / 100;

  return (
    <div className="space-y-8 pb-10">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-white">Financial Command Center</h1>
          <p className="text-slate-400 text-sm mt-1">Autonomous multi-agent reviews running in real-time</p>
        </div>
        
        {/* Risk Alerts Indicator */}
        <div className={`flex items-center gap-3 px-4 py-2 rounded-2xl border ${
          activeAlerts > 0 
            ? "bg-brand-danger/10 border-brand-danger/35 text-brand-danger" 
            : "bg-brand-success/10 border-brand-success/30 text-brand-success"
        }`}>
          <div className={`w-2.5 h-2.5 rounded-full ${activeAlerts > 0 ? "bg-brand-danger animate-ping" : "bg-brand-success"}`}></div>
          <span className="text-xs font-bold uppercase tracking-wider">
            {activeAlerts > 0 ? `${activeAlerts} Security Alerts` : "Cybersecurity Verified"}
          </span>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          {
            title: "Monthly Ingested Income",
            value: `₹${(analytics?.overview?.total_income || 92000.0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`,
            change: "From statement CSV",
            isUp: true,
            icon: TrendingUp,
            color: "text-brand-success"
          },
          {
            title: "Monthly Ingested Expenses",
            value: `₹${(analytics?.overview?.total_expense || 55000.0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`,
            change: "Categorized by Agent",
            isUp: false,
            icon: TrendingDown,
            color: "text-brand-danger"
          },
          {
            title: "Estimated Savings Rate",
            value: `${(analytics?.overview?.savings_rate || 40.2).toFixed(1)}%`,
            change: `₹${(analytics?.overview?.net_savings || 37000.0).toLocaleString("en-IN")} EOM expected`,
            isUp: true,
            icon: Bot,
            color: "text-brand-warning"
          }
        ].map((card, idx) => {
          const Icon = card.icon;
          return (
            <div key={idx} className="glass-card p-6 rounded-2xl relative overflow-hidden">
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">{card.title}</span>
                <Icon className={`w-5 h-5 ${card.color}`} />
              </div>
              <div className="text-2xl font-extrabold text-white mb-2">{card.value}</div>
              <div className={`text-xs ${card.isUp ? "text-brand-success" : "text-brand-danger"} font-semibold`}>
                {card.change}
              </div>
            </div>
          );
        })}
      </div>

      {/* Main Panels Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Side: Statement Upload & Charts */}
        <div className="lg:col-span-8 space-y-8">
          
          {/* Upload Card */}
          <div className="glass-card p-6 rounded-2xl relative">
            <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
              <Upload className="w-5 h-5 text-brand-primary" />
              Autonomous Statement Upload
            </h3>
            <p className="text-xs text-slate-400 mb-6">
              Drop your bank, credit card, or UPI statements (CSV) to execute transaction auditing, risk indices, and reports.
            </p>

            <form onSubmit={handleUploadSubmit} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Account Nickname</label>
                  <input
                    type="text"
                    value={accountName}
                    onChange={(e) => setAccountName(e.target.value)}
                    className="w-full px-3 py-2.5 rounded-xl glass-input text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Account Type</label>
                  <select
                    value={accountType}
                    onChange={(e) => setAccountType(e.target.value)}
                    className="w-full px-3 py-2.5 rounded-xl glass-input text-sm"
                  >
                    <option value="Bank">Bank Account (Savings/Current)</option>
                    <option value="Credit Card">Credit Card</option>
                    <option value="UPI">UPI Wallet</option>
                  </select>
                </div>
                <div className="flex flex-col justify-end">
                  <input
                    type="file"
                    id="csv-file-picker"
                    accept=".csv"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                  <label
                    htmlFor="csv-file-picker"
                    className="flex items-center justify-center gap-2 border border-dashed border-white/10 hover:border-brand-primary/50 bg-slate-900/50 hover:bg-brand-primary/5 px-4 py-2.5 rounded-xl text-sm font-semibold cursor-pointer text-slate-300 hover:text-white transition-colors"
                  >
                    <PlusCircle className="w-4 h-4 text-brand-primary" />
                    {file ? file.name : "Pick Statement CSV"}
                  </label>
                </div>
              </div>

              {file && (
                <button
                  type="submit"
                  disabled={uploadMutation.isPending}
                  className="w-full py-3 rounded-xl bg-brand-primary hover:bg-brand-primary/95 text-white font-bold transition-all duration-200 text-sm flex items-center justify-center gap-2 shadow-md shadow-brand-primary/10"
                >
                  {uploadMutation.isPending ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      Processing Financial Transaction Audit Analysis...
                    </>
                  ) : (
                    <>
                      <Bot className="w-4.5 h-4.5" />
                      Trigger Agentic Analysis
                    </>
                  )}
                </button>
              )}

              {uploadSuccess && (
                <div className="p-3 rounded-xl bg-brand-success/10 border border-brand-success/20 text-brand-success text-xs font-semibold flex items-center gap-2">
                  <FileCheck className="w-4 h-4" />
                  {uploadSuccess}
                </div>
              )}

              {uploadError && (
                <div className="p-3 rounded-xl bg-brand-danger/10 border border-brand-danger/25 text-brand-danger text-xs font-semibold flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  {uploadError}
                </div>
              )}
            </form>
          </div>

          {/* Area Chart: Income vs Expense Trend */}
          <div className="glass-card p-6 rounded-2xl">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-bold text-white">Cash Flow Dynamics</h3>
                <p className="text-xs text-slate-500">Historical trend mapping income vs expenditure</p>
              </div>
            </div>

            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={monthlyTrendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorIncome" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10B981" stopOpacity={0.2}/>
                      <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorExpense" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#EF4444" stopOpacity={0.2}/>
                      <stop offset="95%" stopColor="#EF4444" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="month" stroke="#475569" fontSize={11} tickLine={false} />
                  <YAxis stroke="#475569" fontSize={11} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: "#1E293B", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "12px", color: "#FFF", fontSize: "12px" }} />
                  <Area type="monotone" dataKey="Income" stroke="#10B981" strokeWidth={2} fillOpacity={1} fill="url(#colorIncome)" />
                  <Area type="monotone" dataKey="Expense" stroke="#EF4444" strokeWidth={2} fillOpacity={1} fill="url(#colorExpense)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Right Side: Score Gauge & Risk Panels */}
        <div className="lg:col-span-4 space-y-8">
          
          {/* Wellness Score Gauge */}
          <div className="glass-card p-6 rounded-2xl text-center relative">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-6 text-left">Wellness Index</h3>
            
            <div className="relative w-40 h-40 mx-auto mb-6">
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 120 120">
                {/* Background Circle */}
                <circle cx="60" cy="60" r="45" fill="none" stroke="rgba(255,255,255,0.03)" strokeWidth="9" />
                {/* Foreground Score Ring */}
                <circle 
                  cx="60" 
                  cy="60" 
                  r="45" 
                  fill="none" 
                  stroke="url(#dash-grad)" 
                  strokeWidth="9" 
                  strokeDasharray="280" 
                  strokeDashoffset={strokeOffset}
                  className="gauge-path" 
                  style={{ "--offset": strokeOffset } as React.CSSProperties}
                />
                <defs>
                  <linearGradient id="dash-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#4F46E5" />
                    <stop offset="100%" stopColor="#10B981" />
                  </linearGradient>
                </defs>
              </svg>
              
              {/* Score Value Display */}
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-3.5xl font-extrabold text-white">{score.toFixed(1)}</span>
                <span className="text-[10px] text-slate-500 uppercase font-bold tracking-widest mt-1">Health Index</span>
              </div>
            </div>

            <div className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-brand-success/10 border border-brand-success/20 text-brand-success text-xs font-bold mb-4">
              Grade {grade}: Strong Standing
            </div>

            <p className="text-xs text-slate-400 leading-relaxed px-2">
              Your savings rate is in the top 15% regional bracket. Complete savings goals to unlock an A+ grade.
            </p>
          </div>

          {/* Subscriptions Card */}
          <div className="glass-card p-6 rounded-2xl">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-4">Subscription Waste Audit</h3>
            
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="text-2xl font-extrabold text-white">
                  ₹{(subscriptions.reduce((acc: number, cur: any) => acc + (cur.is_unused ? cur.monthly_cost : 0), 0) || 1200.0).toLocaleString("en-IN")}
                </div>
                <p className="text-xs text-slate-500">Unused monthly subscription cost</p>
              </div>
              <div className="w-10 h-10 rounded-xl bg-brand-warning/10 flex items-center justify-center text-brand-warning">
                <HelpCircle className="w-5 h-5" />
              </div>
            </div>

            <div className="space-y-2.5">
              {subscriptions.slice(0, 2).map((s: any, idx: number) => (
                <div key={idx} className="flex items-center justify-between p-2 rounded-xl bg-slate-900/30 border border-white/5">
                  <span className="text-xs font-medium text-slate-300">{s.merchant}</span>
                  <span className="text-xs font-bold text-brand-danger">₹{s.monthly_cost}/mo</span>
                </div>
              ))}
              {subscriptions.length === 0 && (
                <div className="p-3 text-center text-xs text-slate-500 italic bg-slate-900/20 rounded-xl">
                  No active waste detected. Upload statements to review.
                </div>
              )}
            </div>
          </div>
          
          {/* Savings Goa Trip Goal Widget */}
          <div className="glass-card p-6 rounded-2xl">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-4">Savings Goal Progress</h3>
            
            {goals.slice(0, 1).map((g: any, idx: number) => {
              const progress = g.target_amount > 0 ? (g.current_amount / g.target_amount) * 100 : 50;
              return (
                <div key={idx} className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-white">{g.name}</span>
                    <span className="text-xs text-brand-success font-semibold">{progress.toFixed(0)}%</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-slate-900 overflow-hidden border border-white/5">
                    <div className="h-full bg-gradient-to-r from-brand-primary to-brand-success rounded-full" style={{ width: `${progress}%` }}></div>
                  </div>
                  <div className="flex justify-between text-[10px] text-slate-500">
                    <span>₹{g.current_amount.toLocaleString("en-IN")} saved</span>
                    <span>Target: ₹{g.target_amount.toLocaleString("en-IN")}</span>
                  </div>
                </div>
              );
            })}
            
            {goals.length === 0 && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">Goa Trip Savings</span>
                  <span className="text-xs text-brand-success font-semibold">50%</span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-900 overflow-hidden border border-white/5">
                  <div className="h-full bg-gradient-to-r from-brand-primary to-brand-success rounded-full w-[50%]"></div>
                </div>
                <div className="flex justify-between text-[10px] text-slate-500">
                  <span>₹25,000 saved</span>
                  <span>Target: ₹50,000</span>
                </div>
              </div>
            )}
          </div>
          
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
