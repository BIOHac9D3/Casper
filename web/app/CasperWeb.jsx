/**
 * Casper Node - Web Frontend
 * Next.js application for monitoring and controlling Casper
 */

'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import {
  LayoutDashboard,
  MessageSquare,
  Settings,
  PlayCircle,
  StopCircle,
  List,
  Search,
  Filter,
  Tag,
  User,
  Cpu,
  Database,
  Code,
  Bot,
  CheckCircle,
  XCircle,
  Loader2
} from 'lucide-react';

// API client
const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
});

// Fetch environment info
const fetchEnvironment = async () => {
  const response = await api.get('/environment');
  return response.data;
};

// Fetch skills list
const fetchSkills = async () => {
  const response = await api.get('/skills');
  return response.data;
};

// Fetch skill stats
const fetchStats = async () => {
  const response = await api.get('/skills/stats');
  return response.data;
};

// Execute skill
const executeSkill = async ({ skill_id, prompt, provider = 'openai' }) => {
  const response = await api.post(`/skills/${skill_id}/execute`, {
    prompt,
    provider,
    use_skills: true
  });
  return response.data;
};

// Generate with skills
const generateWithSkills = async ({ prompt, provider = 'openai' }) => {
  const response = await api.post('/generate', {
    prompt,
    provider,
    use_skills: true
  });
  return response.data;
};

// Enable/disable skill
const toggleSkill = async ({ skill_id, enabled }) => {
  const response = await api.post(`/skills/${skill_id}/enable`, { enabled });
  return response.data;
};

// Main App Component
export default function CasperWeb() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedSkill, setSelectedSkill] = useState(null);
  const [prompt, setPrompt] = useState('');
  const [provider, setProvider] = useState('openai');
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState(null);
  const [filterDomain, setFilterDomain] = useState('');
  const [filterEnabled, setFilterEnabled] = useState(null);

  // Queries
  const { data: environment, isLoading: envLoading } = useQuery({
    queryKey: ['environment'],
    queryFn: fetchEnvironment,
  });

  const { data: skills, isLoading: skillsLoading } = useQuery({
    queryKey: ['skills', filterDomain, filterEnabled],
    queryFn: fetchSkills,
  });

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: fetchStats,
  });

  // Mutations
  const executeMutation = useMutation({
    mutationFn: generateWithSkills,
    onSuccess: (data) => {
      setExecutionResult(data);
      setIsExecuting(false);
    },
    onError: (error) => {
      setExecutionResult({ status: 'error', message: error.message });
      setIsExecuting(false);
    },
  });

  const skillExecuteMutation = useMutation({
    mutationFn: executeSkill,
    onSuccess: (data) => {
      setExecutionResult(data);
      setIsExecuting(false);
    },
    onError: (error) => {
      setExecutionResult({ status: 'error', message: error.message });
      setIsExecuting(false);
    },
  });

  const toggleMutation = useMutation({
    mutationFn: toggleSkill,
    onSuccess: () => {
      queryClient.invalidateQueries(['skills']);
      queryClient.invalidateQueries(['stats']);
    },
  });

  // Handle execution
  const handleExecute = () => {
    if (!prompt.trim()) return;
    setIsExecuting(true);
    setExecutionResult(null);
    
    if (selectedSkill) {
      skillExecuteMutation.mutate({
        skill_id: selectedSkill,
        prompt,
        provider
      });
    } else {
      executeMutation.mutate({ prompt, provider });
    }
  };

  // Handle skill toggle
  const handleToggleSkill = (skillId, enabled) => {
    toggleMutation.mutate({ skill_id: skillId, enabled });
  };

  // Get domain color
  const getDomainColor = (domain) => {
    const colors = {
      web: 'bg-blue-100 text-blue-800',
      data: 'bg-green-100 text-green-800',
      automation: 'bg-purple-100 text-purple-800',
      analysis: 'bg-yellow-100 text-yellow-800',
      development: 'bg-indigo-100 text-indigo-800',
      security: 'bg-red-100 text-red-800',
      other: 'bg-gray-100 text-gray-800'
    };
    return colors[domain?.toLowerCase()] || 'bg-gray-100 text-gray-800';
  };

  // Render skill card
  const SkillCard = ({ skill }) => (
    <div className="border rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-lg">{skill.name}</h3>
            <span className={`px-2 py-1 text-xs rounded-full ${getDomainColor(skill.domain)}`}>
              {skill.domain}
            </span>
          </div>
          <p className="text-sm text-gray-600 mb-2">{skill.id}</p>
          <p className="text-sm text-gray-700 line-clamp-2">{skill.description}</p>
          <div className="mt-2 flex flex-wrap gap-1">
            {skill.tags?.slice(0, 3).map(tag => (
              <span key={tag} className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">
                {tag}
              </span>
            ))}
          </div>
        </div>
        <div className="flex flex-col items-end gap-2">
          <button
            onClick={() => handleToggleSkill(skill.id, !skill.enabled)}
            className={`p-1.5 rounded-full ${skill.enabled ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'}`}
            title={skill.enabled ? 'Disable' : 'Enable'}
          >
            {skill.enabled ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
          </button>
          <button
            onClick={() => {
              setSelectedSkill(skill.id);
              setPrompt(skill.triggers?.[0]?.phrase || '');
            }}
            className="p-1.5 bg-blue-100 text-blue-600 rounded-full hover:bg-blue-200"
            title="Use this skill"
          >
            <PlayCircle className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );

  // Render loading state
  if (envLoading || skillsLoading || statsLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center gap-2">
          <Loader2 className="w-6 h-6 animate-spin" />
          <span>Loading Casper...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Casper Node</h1>
                <p className="text-sm text-gray-500">AI Orchestration Platform</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500">
                {environment?.platform || 'Unknown'} | Python {environment?.python_version} | Node {environment?.node_version || 'N/A'}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex gap-6">
          {/* Sidebar */}
          <aside className="w-64 flex-shrink-0">
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h2 className="text-lg font-semibold mb-4">Navigation</h2>
              <nav className="space-y-1">
                {[
                  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
                  { id: 'skills', label: 'Skills', icon: List },
                  { id: 'generate', label: 'Generate', icon: MessageSquare },
                  { id: 'settings', label: 'Settings', icon: Settings },
                ].map((item) => (
                  <button
                    key={item.id}
                    onClick={() => setActiveTab(item.id)}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                      activeTab === item.id
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    <item.icon className="w-5 h-5" />
                    <span>{item.label}</span>
                  </button>
                ))}
              </nav>
            </div>

            {/* Stats Card */}
            <div className="bg-white rounded-lg border border-gray-200 p-4 mt-4">
              <h2 className="text-lg font-semibold mb-4">Statistics</h2>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Total Skills</span>
                  <span className="font-medium">{stats?.total_skills || 0}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Enabled</span>
                  <span className="font-medium text-green-600">{stats?.enabled_skills || 0}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Disabled</span>
                  <span className="font-medium text-red-600">{stats?.disabled_skills || 0}</span>
                </div>
              </div>
            </div>
          </aside>

          {/* Main Panel */}
          <div className="flex-1">
            {/* Dashboard Tab */}
            {activeTab === 'dashboard' && (
              <div>
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
                </div>

                {/* Quick Actions */}
                <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
                  <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
                  <div className="flex gap-4">
                    <button
                      onClick={() => {
                        setActiveTab('generate');
                        setPrompt('');
                        setSelectedSkill(null);
                      }}
                      className="flex-1 flex items-center justify-center gap-2 py-3 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      <MessageSquare className="w-5 h-5" />
                      <span>New Generation</span>
                    </button>
                    <button
                      onClick={() => setActiveTab('skills')}
                      className="flex-1 flex items-center justify-center gap-2 py-3 px-4 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                    >
                      <List className="w-5 h-5" />
                      <span>View Skills</span>
                    </button>
                  </div>
                </div>

                {/* Environment Info */}
                <div className="bg-white rounded-lg border border-gray-200 p-6">
                  <h3 className="text-lg font-semibold mb-4">Environment</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-600">Platform</p>
                      <p className="font-medium">{environment?.platform || 'Unknown'}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Python</p>
                      <p className="font-medium">{environment?.python_version || 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Termux</p>
                      <p className="font-medium">{environment?.is_termux ? 'Yes' : 'No'}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Node.js</p>
                      <p className="font-medium">{environment?.node_version || 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Docker</p>
                      <p className="font-medium">{environment?.is_docker ? 'Yes' : 'No'}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Architecture</p>
                      <p className="font-medium">{environment?.architecture || 'N/A'}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Skills Tab */}
            {activeTab === 'skills' && (
              <div>
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-bold text-gray-900">Skills</h2>
                  <div className="flex gap-2">
                    <select
                      value={filterDomain}
                      onChange={(e) => setFilterDomain(e.target.value)}
                      className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
                    >
                      <option value="">All Domains</option>
                      <option value="web">Web</option>
                      <option value="data">Data</option>
                      <option value="automation">Automation</option>
                      <option value="analysis">Analysis</option>
                      <option value="development">Development</option>
                      <option value="security">Security</option>
                    </select>
                    <select
                      value={filterEnabled}
                      onChange={(e) => setFilterEnabled(e.target.value === 'true' ? true : e.target.value === 'false' ? false : null)}
                      className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
                    >
                      <option value="">All Status</option>
                      <option value="true">Enabled</option>
                      <option value="false">Disabled</option>
                    </select>
                    <button
                      onClick={() => {
                        setFilterDomain('');
                        setFilterEnabled(null);
                      }}
                      className="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm hover:bg-gray-200"
                    >
                      Clear
                    </button>
                  </div>
                </div>

                {skills?.length ? (
                  <div className="grid gap-4">
                    {skills.map(skill => (
                      <SkillCard key={skill.id} skill={skill} />
                    ))}
                  </div>
                ) : (
                  <div className="bg-white rounded-lg border border-gray-200 p-6 text-center">
                    <p className="text-gray-500">No skills found</p>
                  </div>
                )}
              </div>
            )}

            {/* Generate Tab */}
            {activeTab === 'generate' && (
              <div>
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-bold text-gray-900">Generate</h2>
                </div>

                <div className="bg-white rounded-lg border border-gray-200 p-6">
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      AI Provider
                    </label>
                    <select
                      value={provider}
                      onChange={(e) => setProvider(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    >
                      <option value="openai">OpenAI</option>
                      <option value="claude">Anthropic Claude</option>
                      <option value="local">Local (Ollama)</option>
                    </select>
                  </div>

                  {selectedSkill && (
                    <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Bot className="w-4 h-4 text-blue-600" />
                          <span className="font-medium">
                            Using skill: {skills?.find(s => s.id === selectedSkill)?.name || selectedSkill}
                          </span>
                        </div>
                        <button
                          onClick={() => setSelectedSkill(null)}
                          className="text-sm text-blue-600 hover:underline"
                        >
                          Clear
                        </button>
                      </div>
                    </div>
                  )}

                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Prompt
                    </label>
                    <textarea
                      value={prompt}
                      onChange={(e) => setPrompt(e.target.value)}
                      placeholder="Enter your prompt here..."
                      rows={6}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <button
                    onClick={handleExecute}
                    disabled={isExecuting || !prompt.trim()}
                    className="flex items-center justify-center gap-2 py-3 px-6 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-300 transition-colors"
                  >
                    {isExecuting ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        <span>Generating...</span>
                      </>
                    ) : (
                      <>
                        <PlayCircle className="w-5 h-5" />
                        <span>Generate</span>
                      </>
                    )}
                  </button>

                  {/* Results */}
                  {executionResult && (
                    <div className="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-semibold">Result</h3>
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          executionResult.status === 'error' 
                            ? 'bg-red-100 text-red-800' 
                            : 'bg-green-100 text-green-800'
                        }`}>
                          {executionResult.status}
                        </span>
                      </div>
                      {executionResult.skill && (
                        <div className="mb-2 p-2 bg-blue-50 rounded">
                          <span className="text-sm text-blue-700">
                            Skill: {executionResult.skill.name || executionResult.skill.id}
                          </span>
                        </div>
                      )}
                      <pre className="text-sm whitespace-pre-wrap">{executionResult.message || JSON.stringify(executionResult, null, 2)}</pre>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Settings Tab */}
            {activeTab === 'settings' && (
              <div>
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-bold text-gray-900">Settings</h2>
                </div>

                <div className="bg-white rounded-lg border border-gray-200 p-6">
                  <h3 className="text-lg font-semibold mb-4">API Configuration</h3>
                  <p className="text-sm text-gray-600">
                    Configure your API keys in the .env file
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-4 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p className="text-sm text-gray-500">
            Casper Node v0.1.0 | AI Orchestration Platform
          </p>
        </div>
      </footer>
    </div>
  );
}