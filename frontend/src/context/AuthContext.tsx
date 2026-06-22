import React, { createContext, useContext, useState } from "react";
import { api } from "../lib/api";

interface AuthContextType {
  token: string | null;
  isAuthenticated: boolean;
  userEmail: string | null;
  login: (email: string, pass: string) => Promise<void>;
  otpLogin: (email: string, otp: string) => Promise<void>;
  googleLogin: (email: string, name: string) => Promise<void>;
  signup: (email: string, pass: string, name: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem("finpilot_token"));
  const [userEmail, setUserEmail] = useState<string | null>(localStorage.getItem("finpilot_email"));

  const login = async (email: string, pass: string) => {
    const params = new URLSearchParams();
    params.append("username", email);
    params.append("password", pass);
    
    const data = await api.auth.login(params);
    localStorage.setItem("finpilot_token", data.access_token);
    localStorage.setItem("finpilot_email", email);
    setToken(data.access_token);
    setUserEmail(email);
  };

  const otpLogin = async (email: string, otp: string) => {
    const data = await api.auth.otpLogin({ email, otp });
    localStorage.setItem("finpilot_token", data.access_token);
    localStorage.setItem("finpilot_email", email);
    setToken(data.access_token);
    setUserEmail(email);
  };

  const googleLogin = async (email: string, name: string) => {
    const data = await api.auth.googleLogin({ email, name });
    localStorage.setItem("finpilot_token", data.access_token);
    localStorage.setItem("finpilot_email", email);
    setToken(data.access_token);
    setUserEmail(email);
  };

  const signup = async (email: string, pass: string, name: string) => {
    await api.auth.signup({ email, password: pass, full_name: name });
    await login(email, pass);
  };

  const logout = () => {
    localStorage.removeItem("finpilot_token");
    localStorage.removeItem("finpilot_email");
    setToken(null);
    setUserEmail(null);
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        isAuthenticated: !!token,
        userEmail,
        login,
        otpLogin,
        googleLogin,
        signup,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
