import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Mail, Lock, Key, AlertCircle, ArrowRight } from "lucide-react";

const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login, otpLogin, googleLogin } = useAuth();
  
  // Tab control: 'password' or 'otp'
  const [authMethod, setAuthMethod] = useState<"password" | "otp">("password");
  
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    
    try {
      if (authMethod === "password") {
        await login(email, password);
      } else {
        if (!otpSent) {
          // Trigger OTP delivery
          setOtpSent(true);
          setLoading(false);
          return;
        }
        await otpLogin(email, otp);
      }
      navigate("/dashboard");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Authentication failed. Please verify credentials.");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setError("");
    try {
      // Mock Google SSO sign-in
      await googleLogin("google.judge@hackathon.com", "Hackathon Judge");
      navigate("/dashboard");
    } catch (err: any) {
      setError("Google Sign-In failed.");
    }
  };

  return (
    <div className="min-h-screen bg-brand-bg flex items-center justify-center p-6 relative overflow-hidden text-white">
      <div className="glow-bg top-[-100px] left-[-100px]"></div>
      <div className="glow-bg-secondary bottom-[-100px] right-[-100px]"></div>

      <div className="w-full max-w-md relative z-10">
        {/* Brand Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-tr from-brand-primary to-brand-success font-bold text-white text-xl mb-4 shadow-lg shadow-brand-primary/20">
            FP
          </div>
          <h2 className="text-3xl font-extrabold tracking-tight">Welcome Back</h2>
          <p className="text-sm text-slate-400 mt-2">Access your AI financial dashboard</p>
        </div>

        {/* Card Panel */}
        <div className="glass-card p-8 rounded-3xl border border-white/10 shadow-2xl">
          {error && (
            <div className="mb-6 p-4 rounded-xl bg-brand-danger/10 border border-brand-danger/25 text-brand-danger text-sm flex items-center gap-3">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Toggle Tabs */}
          <div className="flex border-b border-white/5 mb-6.5">
            <button
              onClick={() => { setAuthMethod("password"); setError(""); setOtpSent(false); }}
              className={`flex-1 pb-3 text-sm font-semibold border-b-2 transition-colors ${
                authMethod === "password" ? "border-brand-primary text-white" : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              Password
            </button>
            <button
              onClick={() => { setAuthMethod("otp"); setError(""); }}
              className={`flex-1 pb-3 text-sm font-semibold border-b-2 transition-colors ${
                authMethod === "otp" ? "border-brand-primary text-white" : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              One-Time OTP
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Email Field */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Email Address</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-slate-500">
                  <Mail className="w-4.5 h-4.5" />
                </span>
                <input
                  type="email"
                  required
                  placeholder="name@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={otpSent}
                  className="w-full pl-10 pr-4 py-3 rounded-xl glass-input text-sm"
                />
              </div>
            </div>

            {/* Password Field */}
            {authMethod === "password" && (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400">Password</label>
                  <a href="#forgot" onClick={() => alert("Mock password reset sent.")} className="text-xs text-brand-primary hover:underline">Forgot password?</a>
                </div>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-slate-500">
                    <Lock className="w-4.5 h-4.5" />
                  </span>
                  <input
                    type="password"
                    required
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 rounded-xl glass-input text-sm"
                  />
                </div>
              </div>
            )}

            {/* OTP Verification Field */}
            {authMethod === "otp" && otpSent && (
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Verification OTP</label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-slate-500">
                    <Key className="w-4.5 h-4.5" />
                  </span>
                  <input
                    type="text"
                    required
                    placeholder="Enter 6-digit OTP code (e.g. 666888)"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 rounded-xl glass-input text-sm"
                  />
                </div>
                <p className="text-xs text-slate-500 mt-2">
                  Tip: Use <code className="text-brand-success font-bold">666888</code> as a bypass key code for quick login.
                </p>
              </div>
            )}

            {/* Submit CTA */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 rounded-xl bg-brand-primary hover:bg-brand-primary/95 font-bold transition-all duration-200 shadow-md shadow-brand-primary/10 flex items-center justify-center gap-2"
            >
              {loading ? (
                "Processing..."
              ) : authMethod === "otp" && !otpSent ? (
                <>Send Verification OTP <ArrowRight className="w-4 h-4" /></>
              ) : (
                "Sign In"
              )}
            </button>
          </form>

          {/* Social Divider */}
          <div className="flex items-center my-6">
            <div className="flex-1 border-t border-white/5"></div>
            <span className="px-3 text-xs text-slate-500 uppercase font-bold tracking-widest">or continue with</span>
            <div className="flex-1 border-t border-white/5"></div>
          </div>

          {/* Google SSO Button */}
          <button
            onClick={handleGoogleSignIn}
            className="w-full py-3 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 font-semibold transition-all duration-200 flex items-center justify-center gap-2 text-sm"
          >
            <svg className="w-4.5 h-4.5" viewBox="0 0 24 24">
              <path
                fill="currentColor"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="currentColor"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="currentColor"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
              />
              <path
                fill="currentColor"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
              />
            </svg>
            Google Workspace
          </button>
        </div>

        {/* Footer Link */}
        <p className="text-center text-sm text-slate-400 mt-6">
          Don't have an account?{" "}
          <Link to="/signup" className="text-brand-primary font-semibold hover:underline">
            Create an Account
          </Link>
        </p>
      </div>
    </div>
  );
};

export default Login;
