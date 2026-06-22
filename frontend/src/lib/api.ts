import axios from "axios";

const API_BASE_URL = "http://localhost:8000/api/v1";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Interceptor to inject JWT Token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("finpilot_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

export const api = {
  // Auth
  auth: {
    signup: async (data: any) => {
      const resp = await apiClient.post("/auth/signup", data);
      return resp.data;
    },
    login: async (formData: URLSearchParams) => {
      const resp = await apiClient.post("/auth/login", formData, {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      });
      return resp.data;
    },
    googleLogin: async (payload: any) => {
      const resp = await apiClient.post("/auth/google-login", payload);
      return resp.data;
    },
    otpLogin: async (data: { email: string; otp: string }) => {
      const resp = await apiClient.post("/auth/otp-login", data);
      return resp.data;
    },
    forgotPassword: async (email: string) => {
      const resp = await apiClient.post("/auth/forgot-password", { email });
      return resp.data;
    },
  },
  
  // Transactions
  transactions: {
    list: async () => {
      const resp = await apiClient.get("/transactions");
      return resp.data;
    },
    listAccounts: async () => {
      const resp = await apiClient.get("/transactions/accounts");
      return resp.data;
    },
    upload: async (file: File, accountName: string, accountType: string) => {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("account_name", accountName);
      formData.append("account_type", accountType);
      
      const resp = await apiClient.post("/transactions/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      return resp.data;
    },
    analytics: async () => {
      const resp = await apiClient.get("/transactions/analytics");
      return resp.data;
    },
  },
  
  // Budgets
  budgets: {
    list: async () => {
      const resp = await apiClient.get("/budgets");
      return resp.data;
    },
    create: async (data: any) => {
      const resp = await apiClient.post("/budgets", data);
      return resp.data;
    },
    generateAI: async () => {
      const resp = await apiClient.post("/budgets/generate");
      return resp.data;
    },
  },
  
  // Subscriptions
  subscriptions: {
    list: async () => {
      const resp = await apiClient.get("/subscriptions");
      return resp.data;
    },
  },
  
  // Savings Goals
  savings: {
    list: async () => {
      const resp = await apiClient.get("/savings");
      return resp.data;
    },
    create: async (data: any) => {
      const resp = await apiClient.post("/savings", data);
      return resp.data;
    },
    generateRoadmap: async (targetAmount: number, monthsHorizon: number, goalName: string) => {
      const resp = await apiClient.post(`/savings/roadmap?target_amount=${targetAmount}&months_horizon=${monthsHorizon}&goal_name=${encodeURIComponent(goalName)}`);
      return resp.data;
    },
  },
  
  // Fraud
  fraud: {
    list: async () => {
      const resp = await apiClient.get("/fraud");
      return resp.data;
    },
    resolve: async (alertId: number) => {
      const resp = await apiClient.post(`/fraud/resolve/${alertId}`);
      return resp.data;
    },
  },
  
  // Wellness
  wellness: {
    getLatest: async () => {
      const resp = await apiClient.get("/wellness");
      return resp.data;
    },
    history: async () => {
      const resp = await apiClient.get("/wellness/history");
      return resp.data;
    },
  },
  
  // Reports
  reports: {
    list: async () => {
      const resp = await apiClient.get("/reports");
      return resp.data;
    },
    get: async (id: number) => {
      const resp = await apiClient.get(`/reports/${id}`);
      return resp.data;
    },
    generate: async () => {
      const resp = await apiClient.post("/reports/generate");
      return resp.data;
    },
  },
  
  // Copilot
  copilot: {
    history: async () => {
      const resp = await apiClient.get("/copilot/history");
      return resp.data;
    },
    chat: async (message: string) => {
      const resp = await apiClient.post("/copilot/chat", { message });
      return resp.data;
    },
    approve: async (approve: boolean) => {
      const resp = await apiClient.post("/copilot/approve", { approve });
      return resp.data;
    },
    status: async () => {
      const resp = await apiClient.get("/copilot/status");
      return resp.data;
    },
  },
};
export default apiClient;


