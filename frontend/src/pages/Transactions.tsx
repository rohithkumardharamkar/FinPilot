import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { Search, RefreshCw } from "lucide-react";

const Transactions: React.FC = () => {
  const { data: transactions = [], isLoading, refetch } = useQuery({
    queryKey: ["transactions"],
    queryFn: api.transactions.list
  });

  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [categoryFilter, setCategoryFilter] = useState("all");

  const filtered = transactions.filter((t: any) => {
    const matchesSearch =
      (t.merchant || "").toLowerCase().includes(search.toLowerCase()) ||
      (t.description || "").toLowerCase().includes(search.toLowerCase());
    const matchesType = typeFilter === "all" || t.transaction_type === typeFilter;
    const matchesCategory = categoryFilter === "all" || t.category === categoryFilter;
    return matchesSearch && matchesType && matchesCategory;
  });

  // Get unique categories for dropdown filter
  const categories = Array.from(new Set(transactions.map((t: any) => t.category)));

  return (
    <div className="space-y-8 pb-10">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold text-white">Transaction Logs</h1>
          <p className="text-slate-400 text-sm mt-1">Classification and recurring audits verified by AI</p>
        </div>
        <button
          onClick={() => refetch()}
          className="p-2.5 rounded-xl border border-white/5 bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white transition-all duration-200"
        >
          <RefreshCw className="w-5 h-5" />
        </button>
      </div>

      {/* Filters Card */}
      <div className="glass-card p-5 rounded-2xl flex flex-col md:flex-row gap-4">
        {/* Search */}
        <div className="flex-1 relative">
          <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-slate-500">
            <Search className="w-4.5 h-4.5" />
          </span>
          <input
            type="text"
            placeholder="Search merchant or description..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 rounded-xl glass-input text-sm"
          />
        </div>

        {/* Type Filter */}
        <div className="w-full md:w-48">
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="w-full px-3 py-2.5 rounded-xl glass-input text-sm"
          >
            <option value="all">All Types</option>
            <option value="credit">Credits (Income)</option>
            <option value="debit">Debits (Expenses)</option>
          </select>
        </div>

        {/* Category Filter */}
        <div className="w-full md:w-48">
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="w-full px-3 py-2.5 rounded-xl glass-input text-sm"
          >
            <option value="all">All Categories</option>
            {categories.map((c: any) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Transactions Table Card */}
      <div className="glass-card rounded-2xl overflow-hidden">
        {isLoading ? (
          <div className="p-16 text-center text-slate-400 font-semibold">Loading transactions...</div>
        ) : filtered.length === 0 ? (
          <div className="p-16 text-center text-slate-500 italic">No transactions found. Make sure to upload statement CSVs in the dashboard.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/5 bg-slate-900/40 text-xs font-bold uppercase tracking-widest text-slate-400">
                  <th className="py-4 px-6">Date</th>
                  <th className="py-4 px-6">Merchant / Description</th>
                  <th className="py-4 px-6">Category</th>
                  <th className="py-4 px-6 text-center">Confidence</th>
                  <th className="py-4 px-6 text-center">Recurrence</th>
                  <th className="py-4 px-6 text-right">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-sm">
                {filtered.map((t: any) => {
                  const isCredit = t.transaction_type === "credit";
                  return (
                    <tr key={t.id} className="hover:bg-white/[0.02] transition-colors duration-150">
                      <td className="py-4.5 px-6 text-slate-300 font-mono">
                        {new Date(t.date).toLocaleDateString("en-IN", {
                          year: "numeric",
                          month: "short",
                          day: "numeric"
                        })}
                      </td>
                      <td className="py-4.5 px-6">
                        <div className="font-bold text-white">{t.merchant || "Generic"}</div>
                        <div className="text-xs text-slate-500 max-w-sm truncate">{t.description || "N/A"}</div>
                      </td>
                      <td className="py-4.5 px-6">
                        <span className="inline-block px-3 py-1 rounded-full bg-brand-primary/10 border border-brand-primary/20 text-brand-primary text-xs font-semibold">
                          {t.category}
                        </span>
                      </td>
                      <td className="py-4.5 px-6 text-center">
                        <span className={`text-xs font-bold ${
                          t.confidence_score > 0.8 ? "text-brand-success" : "text-brand-warning"
                        }`}>
                          {(t.confidence_score * 100).toFixed(0)}%
                        </span>
                      </td>
                      <td className="py-4.5 px-6 text-center">
                        {t.is_recurring ? (
                          <span className="inline-block px-2.5 py-0.5 rounded-full bg-brand-warning/10 border border-brand-warning/20 text-brand-warning text-xxs font-bold uppercase tracking-wider">
                            Recurring
                          </span>
                        ) : (
                          <span className="text-slate-500 text-xs">-</span>
                        )}
                      </td>
                      <td className={`py-4.5 px-6 text-right font-extrabold ${
                        isCredit ? "text-brand-success" : "text-white"
                      }`}>
                        <span className="mr-1">{isCredit ? "+" : "-"}</span>
                        ₹{t.amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default Transactions;
