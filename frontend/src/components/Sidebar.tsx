import React from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  LayoutDashboard,
  Receipt,
  BarChart3,
  CalendarDays,
  LineChart,
  Wallet,
  ShieldAlert,
  Target,
  FileText,
  MessageSquareCode,
  LogOut,
  User
} from "lucide-react";

const Sidebar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout, userEmail } = useAuth();
  
  const navItems = [
    { name: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
    { name: "Transactions", path: "/transactions", icon: Receipt },
    { name: "Analytics", path: "/analytics", icon: BarChart3 },
    { name: "Subscriptions", path: "/subscriptions", icon: CalendarDays },
    { name: "Forecast", path: "/forecast", icon: LineChart },
    { name: "Budgets", path: "/budgets", icon: Wallet },
    { name: "Fraud Monitor", path: "/fraud", icon: ShieldAlert },
    { name: "Savings Goals", path: "/savings", icon: Target },
    { name: "AI Reports", path: "/reports", icon: FileText },
    { name: "AI Copilot", path: "/copilot", icon: MessageSquareCode },
  ];

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <aside className="fixed inset-y-0 left-0 w-64 glass-panel flex flex-col z-20">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 border-b border-white/5 gap-2.5">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-brand-primary to-brand-success flex items-center justify-center font-bold text-white shadow-lg shadow-brand-primary/20">
          FP
        </div>
        <span className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
          FinPilot <span className="text-brand-success font-semibold text-sm">AI</span>
        </span>
      </div>

      {/* Navigation Items */}
      <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              to={item.path}
              className={`flex items-center gap-3.5 px-4 py-3 rounded-xl transition-all duration-200 group ${
                isActive
                  ? "bg-brand-primary/10 border border-brand-primary/30 text-white font-medium shadow-md shadow-brand-primary/5"
                  : "text-slate-400 hover:text-white hover:bg-white/5 border border-transparent"
              }`}
            >
              <Icon className={`w-5 h-5 transition-transform duration-200 group-hover:scale-110 ${
                isActive ? "text-brand-primary" : "text-slate-400 group-hover:text-slate-200"
              }`} />
              <span className="text-sm">{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer Info */}
      <div className="p-4 border-t border-white/5 bg-slate-950/20">
        <div className="flex items-center gap-3 p-2 rounded-xl bg-white/5 mb-3">
          <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-slate-300 border border-white/5">
            <User className="w-4 h-4" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs text-slate-400 truncate">Logged in as</p>
            <p className="text-xs font-semibold text-slate-200 truncate">{userEmail || "user@finpilot.ai"}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl border border-brand-danger/20 text-brand-danger bg-brand-danger/5 hover:bg-brand-danger/10 transition-colors duration-200 text-sm font-semibold"
        >
          <LogOut className="w-4 h-4" />
          Log Out
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
