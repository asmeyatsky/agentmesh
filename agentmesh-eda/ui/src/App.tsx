import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { toast, Toaster } from 'react-hot-toast'
import {
  Activity,
  BarChart2,
  Bell,
  Box,
  Briefcase,
  Cpu,
  Home,
  LayoutDashboard,
  LogOut,
  Menu,
  MessageSquare,
  PieChart,
  Plus,
  RefreshCw,
  Search,
  Settings,
  Users,
  Zap,
  Shield,
  AlertTriangle,
  TrendingUp,
  Clock,
  CheckCircle,
  XCircle,
  Loader2
  ChevronDown,
  ChevronUp,
  MoreVertical,
  Eye,
  Edit,
  Trash2,
  Download
  Upload,
  Filter
  Calendar,
  User,
  Building,
  Cloud,
  Database,
  Globe,
  Lock,
  Unlock,
  Wifi,
  Server
  Monitor,
  Smartphone
  Tablet
  Code,
  Terminal
  Package,
  FileText,
  GitBranch,
  Layers,
  HelpCircle,
  AlertCircle
} from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, PieChart as RechartsPieChart } from 'recharts'
import { format, formatDistanceToNow, formatDistanceToNowStrict } from 'date-fns'

// Types
interface Agent {
  id: string
  name: string
  type: string
  status: 'AVAILABLE' | 'BUSY' | 'PAUSED' | 'UNHEALTHY' | 'TERMINATED'
  capabilities: Array<{
    name: string
    level: number
  }>
  tenant_id: string
  created_at: string
  last_heartbeat?: string
  performance_metrics?: {
    success_rate: number
    response_time: number
    tasks_completed: number
  }
}

interface Tenant {
  id: string
  name: string
  agent_count: number
  created_at: string
  status: 'active' | 'inactive'
}

interface Task {
  id: string
  name: string
  type: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  assigned_agent?: string
  created_at: string
  completed_at?: string
  priority: 'low' | 'medium' | 'high' | 'urgent'
}

interface SystemMetrics {
  agent_count: number
  active_agents: number
  tasks_completed: number
  tasks_failed: number
  message_throughput: number
  error_rate: number
  uptime: number
  resource_usage: {
    cpu: number
    memory: number
    storage: number
  }
}

interface ApiResponse<T> {
  data: T
  error?: string
  message?: string
}

// API service
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
      staleTime: 10000,
    },
  },
});

// API hooks
export const useAgents = () => {
  return useQuery<ApiResponse<Agent[]>, Error>({
    queryKey: ['agents'],
    query: async () => {
      const response = await fetch(`${API_BASE_URL}/v1/agents`);
      if (!response.ok) {
        throw new Error(`Failed to fetch agents: ${response.statusText}`);
      }
      return response.json();
    },
  });
};

export const useTenants = () => {
  return useQuery<ApiResponse<Tenant[]>, Error>({
    queryKey: ['tenants'],
    query: async () => {
      const response = await fetch(`${API_BASE_URL}/v1/tenants`);
      if (!response.ok) {
        throw new Error(`Failed to fetch tenants: ${response.statusText}`);
      }
      return response.json();
    },
  });
};

export const useMetrics = () => {
  return useQuery<ApiResponse<SystemMetrics>, Error>({
    queryKey: ['metrics'],
    query: async () => {
      const response = await fetch(`${API_BASE_URL}/v1/metrics`);
      if (!response.ok) {
        throw new Error(`Failed to fetch metrics: ${response.statusText}`);
      }
      return response.json();
    },
  });
};

// Navigation
const Sidebar = ({ isOpen }: { isOpen: boolean }) => {
  return (
    <motion.div
      initial={{ opacity: 0, x: -250 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -250 }}
      className={`fixed left-0 top-0 h-full w-64 bg-gray-900 transform transition-transform duration-300 ease-in-out ${isOpen ? 'translate-x-0' : ''}`}
    >
      <div className="flex items-center justify-between h-16 px-6 bg-gray-800 border-b border-gray-700">
        <div className="flex items-center">
          <LayoutDashboard className="w-5 h-5 text-indigo-500" />
          <span className="ml-3 text-white text-sm font-medium">AgentMesh</span>
        </div>
        <button
          onClick={() => window.location.reload()}
          className="text-gray-400 hover:text-gray-200 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white focus:ring-offset-2 focus:ring-offset-gray-800 rounded-md p-1"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      <nav className="flex-1 px-2 space-y-1">
        <Routes>
          <Route
            path="/"
            element={
              <NavLink
                icon={<Home className="w-5 h-5" />}
                label="Dashboard"
                to="/"
              />
            }
          />
          <Route
            path="/agents"
            element={
              <NavLink
                icon={<Users className="w-5 h-5" />}
                label="Agents"
                to="/agents"
              />
            }
          />
          <Route
            path="/tasks"
            element={
              <NavLink
                icon={<Briefcase className="w-5 h-5" />}
                label="Tasks"
                to="/tasks"
              />
            }
          />
          <Route
            path="/metrics"
            element={
              <NavLink
                icon={<BarChart2 className="w-5 h-5" />}
                label="Metrics"
                to="/metrics"
              />
            }
          />
          <Route
            path="/settings"
            element={
              <NavLink
                icon={<Settings className="w-5 h-5" />}
                label="Settings"
                to="/settings"
              />
            }
          />
          <Route
            path="/tenants"
            element={
              <NavLink
                icon={<Building className="w-5 h-5" />}
                label="Tenants"
                to="/tenants"
              />
            }
          />
        </Routes>
      </nav>

      <div className="absolute bottom-0 w-full p-4 border-t border-gray-700">
        <div className="flex items-center text-gray-400">
          <User className="w-4 h-4" />
          <span className="ml-2 text-sm">System User</span>
        </div>
      </div>
    </motion.div>
  );
};

const NavLink = ({ icon, label, to }: { icon: React.ReactNode; label: string; to: string }) => {
  const location = window.location.pathname;
  const isActive = location.pathname === to;

  return (
    <Link
      to={to}
      className={`flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors duration-200 ${
        isActive
          ? 'bg-gray-900 text-white'
          : 'text-gray-300 hover:bg-gray-700 hover:text-white'
      }`}
    >
      {icon}
      <span className="ml-3">{label}</span>
    </Link>
  );
};

// Dashboard Page
const Dashboard = () => {
  const { data: agentsData, isLoading: agentsError } = useAgents();
  const { data: metricsData, isLoading: metricsError } = useMetrics();

  return (
    <div className="p-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center">
            <Users className="w-8 h-8 text-indigo-500" />
            <div className="ml-4">
              <h3 className="text-2xl font-bold text-white">{agentsData?.data?.length || 0}</h3>
              <p className="text-gray-400">Total Agents</p>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center">
            <Activity className="w-8 h-8 text-green-500" />
            <div className="ml-4">
              <h3 className="text-2xl font-bold text-white">{metricsData?.data?.active_agents || 0}</h3>
              <p className="text-gray-400">Active Now</p>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center">
            <CheckCircle className="w-8 h-8 text-blue-500" />
            <div className="ml-4">
              <h3 className="text-2xl font-bold text-white">{metricsData?.data?.tasks_completed || 0}</h3>
              <p className="text-gray-400">Tasks Completed</p>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center">
            <TrendingUp className="w-8 h-8 text-purple-500" />
            <div className="ml-4">
              <h3 className="text-2xl font-bold text-white">{Math.round(metricsData?.data?.message_throughput || 0)}</h3>
              <p className="text-gray-400">Msg/sec</p>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-6">
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">System Health</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400">API Status</span>
              <span className="text-green-400">Healthy</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Database</span>
              <span className="text-green-400">Connected</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Message Queue</span>
              <span className="text-green-400">Operational</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Agents Page
const AgentsPage = () => {
  const { data, isLoading, error } = useAgents();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <XCircle className="w-5 h-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-lg font-medium text-red-800">Error loading agents</h3>
              <p>{error.message}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-white">Agents</h1>
        <div className="flex items-center space-x-4">
          <div className="relative">
            <Search className="w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search agents..."
              className="ml-3 bg-gray-700 text-white rounded-md py-2 px-4 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white focus:ring-offset-2 focus:ring-offset-gray-800"
            />
          </div>
          <button className="bg-indigo-600 text-white rounded-md px-4 py-2 text-sm font-medium hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-inset focus:ring-white focus:ring-offset-2 focus:ring-offset-indigo-600">
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {data?.data?.map((agent: Agent) => (
          <div key={agent.id} className="bg-gray-800 rounded-lg p-6 border border border-gray-700">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-medium text-white">{agent.name}</h3>
                <p className="text-sm text-gray-400">{agent.type}</p>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded text-xs font-medium ${
                  agent.status === 'AVAILABLE' ? 'bg-green-100 text-green-800' :
                  agent.status === 'BUSY' ? 'bg-yellow-100 text-yellow-800' :
                  agent.status === 'PAUSED' ? 'bg-blue-100 text-blue-800' :
                  agent.status === 'UNHEALTHY' ? 'bg-red-100 text-red-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {agent.status}
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-400">{agent.tenant_id}</span>
                <button className="text-gray-400 hover:text-gray-200">
                  <MoreVertical className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="text-sm text-gray-400 space-y-2">
              <div className="flex items-center">
                <Calendar className="w-4 h-4 text-gray-400" />
                <span>Created: {format(new Date(agent.created_at), 'MMM d, yyyy')}</span>
              </div>
              <div className="flex items-center">
                <Clock className="w-4 h-4 text-gray-400" />
                <span>Last seen: {agent.last_heartbeat ? formatDistanceToNow(new Date(agent.last_heartbeat)) : 'Never'}</span>
              </div>
            </div>

            <div className="mt-4">
              <h4 className="text-white font-medium mb-2">Capabilities</h4>
              <div className="flex flex-wrap gap-2">
                {agent.capabilities.map((cap, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-2.5 py-1 rounded-md text-sm font-medium bg-gray-700 text-gray-300"
                  >
                    {cap.name}
                    <span className="ml-2 bg-gray-600 text-gray-200 px-2 py-1 rounded">{cap.level}</span>
                  </span>
                ))}
              </div>
            </div>

            {agent.performance_metrics && (
              <div className="mt-4 pt-4 border-t border-gray-700">
                <h4 className="text-white font-medium mb-2">Performance</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Success Rate</span>
                    <span className="text-green-400">{agent.performance_metrics.success_rate}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Avg Response Time</span>
                    <span className="text-blue-400">{agent.performance_metrics.response_time}ms</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Tasks Completed</span>
                    <span className="text-purple-400">{agent.performance_metrics.tasks_completed}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

// Main App
const App = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="flex h-screen bg-gray-900">
      <Sidebar isOpen={sidebarOpen} />
      
      <main className="flex-1 flex overflow-hidden">
        <div className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/agents" element={<AgentsPage />} />
            <Route path="/tasks" element={<div>Tasks page coming soon...</div>} />
            <Route path="/metrics" element={<div>Metrics page coming soon...</div>} />
            <Route path="/settings" element={<div>Settings page coming soon...</div>} />
            <Route path="/tenants" element={<div>Tenants page coming soon...</div>} />
          </Routes>
        </div>
      </main>

      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="fixed top-4 right-4 z-10 p-2 bg-gray-800 text-gray-400 hover:bg-gray-700 rounded-md"
      >
        {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>
    </div>
  );
};

export default App;