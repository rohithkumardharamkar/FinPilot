import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { 
  ArrowRight, 
  Bot, 
  TrendingUp, 
  ShieldAlert, 
  CalendarDays, 
  Sparkles,
  FileCheck,
  Zap,
  Users
} from "lucide-react";

const Landing: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated, login } = useAuth();
  
  const handleTryDemo = async () => {
    try {
      // Mock login for demo evaluation
      await login("demo@finpilot.ai", "demopassword123");
      navigate("/dashboard");
    } catch (err) {
      navigate("/login");
    }
  };

  const features = [
    {
      title: "Autonomous Financial Review",
      desc: "Upload standard bank, credit card, or UPI statements and let the agent team categorize and audit your accounts instantly.",
      icon: Bot,
      color: "from-indigo-500 to-purple-500"
    },
    {
      title: "Smart Subscription Audit",
      desc: "Autodetect recurring Netflix, Spotify, or SaaS payments. Identify double charges, price hikes, and cancel unused accounts.",
      icon: CalendarDays,
      color: "from-emerald-500 to-teal-500"
    },
    {
      title: "Cybersecurity Fraud Monitor",
      desc: "Z-Score and Isolation Forest anomaly models scanning for duplicate charges, unknown merchants, or midnight spikes.",
      icon: ShieldAlert,
      color: "from-red-500 to-rose-500"
    },
    {
      title: "Month-End Trend Forecast",
      desc: "Predict savings rates and budget breaches weeks before they happen, with linear run-rate trend regressions.",
      icon: TrendingUp,
      color: "from-amber-500 to-orange-500"
    }
  ];

  return (
    <div className="min-h-screen bg-brand-bg relative overflow-hidden text-white selection:bg-brand-primary/30">
      <div className="glow-bg top-[-200px] left-[-150px]"></div>
      <div className="glow-bg-secondary bottom-[-100px] right-[-100px]"></div>

      {/* Header */}
      <header className="h-20 max-w-7xl mx-auto px-6 flex items-center justify-between border-b border-white/5 relative z-10">
        <div className="flex items-center gap-2.5">
          <div className="w-9.5 h-9.5 rounded-xl bg-gradient-to-tr from-brand-primary to-brand-success flex items-center justify-center font-bold text-white shadow-lg shadow-brand-primary/20">
            FP
          </div>
          <span className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
            FinPilot <span className="text-brand-success font-semibold text-sm">AI</span>
          </span>
        </div>

        <div className="flex items-center gap-4">
          {isAuthenticated ? (
            <Link
              to="/dashboard"
              className="px-5 py-2 rounded-xl bg-brand-primary hover:bg-brand-primary/90 text-sm font-semibold transition-all duration-200 shadow-md shadow-brand-primary/20"
            >
              Go to Dashboard
            </Link>
          ) : (
            <>
              <Link to="/login" className="text-sm font-medium text-slate-300 hover:text-white transition-colors">
                Sign In
              </Link>
              <Link
                to="/signup"
                className="px-5 py-2.5 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 text-sm font-semibold transition-all duration-200"
              >
                Get Started
              </Link>
            </>
          )}
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-6 pt-24 pb-16 text-center relative z-10">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-brand-primary/10 border border-brand-primary/20 text-brand-primary text-xs font-semibold mb-6 animate-pulse">
          <Sparkles className="w-3.5 h-3.5" />
          Multi-Agent Agentic Financial Audit is Here
        </div>
        
        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight leading-[1.1] mb-6 max-w-4xl mx-auto">
          Your AI <span className="bg-gradient-to-r from-brand-primary via-indigo-400 to-brand-success bg-clip-text text-transparent">Financial Copilot</span>
        </h1>
        
        <p className="text-lg md:text-xl text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
          Automatically track spending, detect hidden subscriptions, forecast budgets, monitor savings goals, and improve your financial health.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <button
            onClick={handleTryDemo}
            className="w-full sm:w-auto flex items-center justify-center gap-2 px-8 py-4 rounded-xl bg-brand-primary hover:bg-brand-primary/95 text-base font-bold shadow-lg shadow-brand-primary/20 hover:shadow-brand-primary/30 transition-all duration-200"
          >
            Try Free Demo
            <ArrowRight className="w-5 h-5" />
          </button>
          <Link
            to="/login"
            className="w-full sm:w-auto flex items-center justify-center gap-2 px-8 py-4 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 text-base font-semibold transition-all duration-200"
          >
            Upload Statement
          </Link>
        </div>
      </section>

      {/* Feature Grid */}
      <section className="max-w-7xl mx-auto px-6 py-20 relative z-10">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-extrabold mb-4">Autonomous Agent Operations</h2>
          <p className="text-slate-400 max-w-xl mx-auto">
            Powered by LangGraph multi-agent systems, FinPilot assigns specific specialists to manage every dimension of your cash flow.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((f, idx) => {
            const Icon = f.icon;
            return (
              <div key={idx} className="glass-card p-6.5 rounded-2xl relative overflow-hidden group">
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-tr ${f.color} flex items-center justify-center mb-6`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-lg font-bold mb-2.5 text-white group-hover:text-brand-success transition-colors">
                  {f.title}
                </h3>
                <p className="text-sm text-slate-400 leading-relaxed">
                  {f.desc}
                </p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Wellness score teaser */}
      <section className="max-w-7xl mx-auto px-6 py-16 relative z-10 border-t border-white/5">
        <div className="grid lg:grid-cols-12 gap-12 items-center">
          <div className="lg:col-span-7">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-success/10 border border-brand-success/20 text-brand-success text-xs font-semibold mb-4">
              <Zap className="w-3.5 h-3.5" />
              Weighted Wellness Index
            </div>
            <h2 className="text-3.5xl md:text-4.5xl font-extrabold mb-6 leading-tight">
              Get an overall Wellness Score & Grade from A+ to D
            </h2>
            <p className="text-slate-400 text-base mb-6 leading-relaxed">
              We compile your spending history along five weighted pillars: Savings Rate (30%), Budget Adherence (25%), Income Stability (20%), Debt EMIs (15%), and Emergency Reserve (10%).
            </p>
            <div className="space-y-3.5">
              {[
                "Get actionable suggestions targeting specific low sub-metrics",
                "Compare scores with regional benchmarks and peer brackets",
                "Track score improvements dynamically as you clear debts"
              ].map((item, idx) => (
                <div key={idx} className="flex items-center gap-3">
                  <div className="w-5 h-5 rounded-full bg-brand-success/10 border border-brand-success/30 flex items-center justify-center">
                    <FileCheck className="w-3 h-3 text-brand-success" />
                  </div>
                  <span className="text-sm text-slate-300">{item}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="lg:col-span-5 flex justify-center">
            <div className="glass-card p-8 rounded-3xl w-full max-w-md border border-white/10 relative">
              <div className="absolute top-4 right-4 text-xs font-bold text-slate-500 uppercase tracking-widest">
                Wellness Gauge
              </div>
              <div className="text-center py-6">
                <svg className="w-40 h-40 mx-auto" viewBox="0 0 120 120">
                  <circle cx="60" cy="60" r="45" fill="none" stroke="rgba(255,255,255,0.03)" strokeWidth="8" />
                  <circle 
                    cx="60" 
                    cy="60" 
                    r="45" 
                    fill="none" 
                    stroke="url(#wellness-grad)" 
                    strokeWidth="8" 
                    strokeDasharray="280" 
                    strokeDashoffset="70"
                    className="gauge-path" 
                  />
                  <defs>
                    <linearGradient id="wellness-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#4F46E5" />
                      <stop offset="100%" stopColor="#10B981" />
                    </linearGradient>
                  </defs>
                </svg>
                <div className="mt-[-90px] mb-8">
                  <span className="text-4xl font-extrabold text-white">82.5</span>
                  <p className="text-xs text-slate-500 uppercase font-bold tracking-wider mt-1">Score</p>
                </div>
                <div className="px-3 py-1.5 rounded-xl bg-brand-success/10 border border-brand-success/20 text-brand-success text-sm font-bold inline-block">
                  Grade A: Financial Health Strong
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="max-w-7xl mx-auto px-6 py-20 relative z-10 border-t border-white/5 text-center">
        <h2 className="text-3xl md:text-4xl font-extrabold mb-12">Loved by Smart Investors</h2>
        <div className="grid md:grid-cols-3 gap-6 text-left">
          {[
            { name: "Risika Andeti", role: "Software Architect", comment: "The subscription auditing tool saved me ₹8,400 in 10 minutes. It flagged duplicate premium accounts instantly." },
            { name: "Varun Mehta", role: "Venture Capitalist", comment: "This isn't a chatbot. It's a true autonomous orchestrator that structures budget limits based on daily rate forecasts." },
            { name: "Neha Sharma", role: "Product Manager", comment: "The Vacation Affordability check is genius. It checks EOM expected savings and cash buffers to decide conditionally." }
          ].map((t, idx) => (
            <div key={idx} className="glass-card p-6 rounded-2xl border border-white/5">
              <div className="flex items-center gap-3.5 mb-4">
                <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center text-slate-300">
                  <Users className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-bold text-sm text-white">{t.name}</h4>
                  <p className="text-xs text-slate-400">{t.role}</p>
                </div>
              </div>
              <p className="text-sm text-slate-300 leading-relaxed italic">"{t.comment}"</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-12 text-center text-sm text-slate-500 relative z-10 bg-slate-950/20">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-gradient-to-tr from-brand-primary to-brand-success flex items-center justify-center font-bold text-xs text-white">
              FP
            </div>
            <span className="font-bold text-white tracking-tight">FinPilot AI</span>
          </div>
          <p>© 2026 FinPilot AI. All rights reserved. Hackathon Special Edition.</p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
