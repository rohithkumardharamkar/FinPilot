import React, { useState, useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import { Bot, Send, User, Sparkles, RefreshCw, AlertTriangle, Check } from "lucide-react";

const Copilot: React.FC = () => {
  const queryClient = useQueryClient();
  const [message, setMessage] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Queries
  const { data: chatHistory = [], isLoading, refetch } = useQuery({
    queryKey: ["chatHistory"],
    queryFn: api.copilot.history
  });

  const { data: statusData } = useQuery({
    queryKey: ["copilotStatus"],
    queryFn: api.copilot.status,
    refetchInterval: 3000 // Poll status every 3s
  });

  const currentStatus = statusData?.status || "COMPLETED";

  // Mutation to send a message
  const chatMutation = useMutation({
    mutationFn: (msg: string) => api.copilot.chat(msg),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chatHistory"] });
      queryClient.invalidateQueries({ queryKey: ["copilotStatus"] });
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
      queryClient.invalidateQueries({ queryKey: ["goals"] });
    }
  });

  // Mutation to approve/reject
  const approveMutation = useMutation({
    mutationFn: (approve: boolean) => api.copilot.approve(approve),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chatHistory"] });
      queryClient.invalidateQueries({ queryKey: ["copilotStatus"] });
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
      queryClient.invalidateQueries({ queryKey: ["goals"] });
    }
  });


  const handleSend = (e?: React.FormEvent, customMsg?: string) => {
    if (e) e.preventDefault();
    const queryToSend = customMsg || message;
    if (!queryToSend.trim() || chatMutation.isPending || currentStatus === "PAUSED_FOR_APPROVAL") return;

    chatMutation.mutate(queryToSend);
    if (!customMsg) setMessage("");
  };

  // Scroll to bottom whenever history updates
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory, chatMutation.isPending]);

  const quickPrompts = [
    "Can I afford a Goa trip?",
    "Generate a savings roadmap for ₹5 lakh in 18 months",
    "Create a monthly budget for me",
    "Show me potential subscription savings"
  ];

  return (
    <div className="space-y-6 pb-10 flex flex-col h-[calc(100vh-6rem)]">
      {/* Header */}
      <div className="flex items-center justify-between flex-shrink-0">
        <div>
          <h1 className="text-3xl font-extrabold text-white">AI Copilot</h1>
          <p className="text-slate-400 text-sm mt-1">Chat statefully with your agent team</p>
        </div>
        <button
          onClick={() => refetch()}
          className="p-2.5 rounded-xl border border-white/5 bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white transition-all duration-200"
        >
          <RefreshCw className="w-5 h-5" />
        </button>
      </div>

      {/* Chat Area Panel */}
      <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Side: Message logs */}
        <div className="lg:col-span-8 glass-card rounded-2xl flex flex-col justify-between overflow-hidden border border-white/5">
          {/* Scrollable logs */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {isLoading ? (
              <div className="text-center py-10 text-slate-400 font-semibold text-xs">Connecting to copilot session...</div>
            ) : chatHistory.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center text-slate-500 py-10">
                <Bot className="w-12 h-12 text-slate-700 mb-4 animate-bounce" />
                <span className="font-medium text-sm">FinPilot AI is online and ready.</span>
                <p className="text-xs text-slate-600 max-w-sm mt-1.5 leading-relaxed">
                  Ask details about your expenses, affordability thresholds, savings goals, or budgets.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {chatHistory.map((m: any, idx: number) => {
                  const isAgent = m.role === "assistant";
                  return (
                    <div key={idx} className={`flex items-start gap-3.5 ${isAgent ? "justify-start" : "justify-end"}`}>
                      {/* Avatar */}
                      {isAgent && (
                        <div className="w-8 h-8 rounded-lg bg-brand-primary/15 border border-brand-primary/25 text-brand-primary flex items-center justify-center flex-shrink-0">
                          <Bot className="w-4.5 h-4.5" />
                        </div>
                      )}
                      
                      {/* Bubble */}
                      <div className={`p-4 rounded-2xl text-sm leading-relaxed max-w-xl whitespace-pre-wrap ${
                        isAgent
                          ? "bg-slate-800/60 border border-white/5 text-slate-200"
                          : "bg-brand-primary text-white font-medium"
                      }`}>
                        {m.content}
                      </div>

                      {/* User Avatar */}
                      {!isAgent && (
                        <div className="w-8 h-8 rounded-lg bg-slate-700 flex items-center justify-center text-slate-300 flex-shrink-0">
                          <User className="w-4.5 h-4.5" />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
            
            {/* Typing Indicator */}
            {chatMutation.isPending && (
              <div className="flex items-start gap-3.5 justify-start">
                <div className="w-8 h-8 rounded-lg bg-brand-primary/15 border border-brand-primary/25 text-brand-primary flex items-center justify-center flex-shrink-0">
                  <Bot className="w-4.5 h-4.5" />
                </div>
                <div className="px-5 py-4.5 rounded-2xl bg-slate-800/60 border border-white/5 flex gap-1.5 items-center justify-center">
                  <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></div>
                  <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:0.2s]"></div>
                  <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:0.4s]"></div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Approval Gate Banner */}
          {currentStatus === "PAUSED_FOR_APPROVAL" && (
            <div className="p-4 border-t border-white/5 bg-amber-500/10 text-amber-500 flex flex-col sm:flex-row sm:items-center justify-between gap-4 flex-shrink-0">
              <div className="flex items-start gap-3">
                <div className="w-9 h-9 rounded-lg bg-amber-500/15 border border-amber-500/25 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <AlertTriangle className="w-5 h-5 text-amber-500 animate-pulse" />
                </div>
                <div>
                  <span className="font-bold text-white text-sm">Human Approval Requested</span>
                  <p className="text-xs text-slate-400 mt-1 max-w-md">
                    The AI agent has paused and is awaiting confirmation for this action. Please approve or reject below.
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => approveMutation.mutate(false)}
                  disabled={approveMutation.isPending}
                  className="px-3.5 py-2 rounded-xl border border-brand-danger/30 hover:bg-brand-danger/5 text-brand-danger text-xs font-bold transition-all"
                >
                  Reject Action
                </button>
                <button
                  type="button"
                  onClick={() => approveMutation.mutate(true)}
                  disabled={approveMutation.isPending}
                  className="px-3.5 py-2 rounded-xl bg-brand-success hover:bg-brand-success/90 text-white text-xs font-bold transition-all shadow-md shadow-brand-success/15 flex items-center gap-1.5"
                >
                  {approveMutation.isPending ? (
                    <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  ) : (
                    <Check className="w-3.5 h-3.5" />
                  )}
                  Approve Action
                </button>
              </div>
            </div>
          )}

          {/* Form input */}
          <form onSubmit={(e) => handleSend(e)} className="p-4 border-t border-white/5 bg-slate-900/30 flex gap-3 flex-shrink-0">
            <input
              type="text"
              required
              disabled={chatMutation.isPending || currentStatus === "PAUSED_FOR_APPROVAL"}
              placeholder={currentStatus === "PAUSED_FOR_APPROVAL" ? "Awaiting human verification response..." : "Ask FinPilot a question..."}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              className="flex-1 px-4 py-3 rounded-xl glass-input text-sm focus:outline-none"
            />
            <button
              type="submit"
              disabled={chatMutation.isPending || currentStatus === "PAUSED_FOR_APPROVAL" || !message.trim()}
              className="p-3.5 rounded-xl bg-brand-primary hover:bg-brand-primary/90 text-white font-bold transition-all flex items-center justify-center shadow-md shadow-brand-primary/10"
            >
              <Send className="w-4.5 h-4.5" />
            </button>
          </form>
        </div>

        {/* Right Side: Quick Prompt chips */}
        <div className="lg:col-span-4 space-y-4 flex-shrink-0">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500">Suggested Inquiries</h3>
          
          <div className="flex flex-col gap-2.5">
            {quickPrompts.map((prompt) => (
              <button
                key={prompt}
                onClick={() => handleSend(undefined, prompt)}
                disabled={chatMutation.isPending || currentStatus === "PAUSED_FOR_APPROVAL"}
                className="w-full flex items-center gap-3 p-3.5 rounded-xl border border-white/5 bg-white/5 hover:bg-white/10 text-left text-xs font-semibold text-slate-300 hover:text-white transition-all duration-150"
              >
                <Sparkles className="w-4 h-4 text-brand-success flex-shrink-0" />
                <span>{prompt}</span>
              </button>
            ))}
          </div>
        </div>


      </div>
    </div>
  );
};

export default Copilot;
