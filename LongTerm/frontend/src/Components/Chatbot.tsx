import React, { useState, useRef, useEffect } from 'react';
import { Send, User, Bot, Database, Clock, Plus, Settings, RefreshCw, ChevronRight, Menu, X } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  storedMemory?: Record<string, string> | null;
}

interface ChatRequest {
  user_id: string;
  session_id: string;
  user_input: string;
}

interface ChatResponse {
  answer: string;
  stored_memory: Record<string, string> | null;
}

interface SessionData {
  sessionId: string;
  userID: string;
  memories: Record<string, string>[];
  messages: Message[];
  createdAt: Date;
}

// Generate 6 character random session ID
const generateSessionId = (): string => {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  let result = '';
  for (let i = 0; i < 6; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
};

const Chatbot: React.FC = () => {
  const [userId, setUserId] = useState(() => localStorage.getItem('chatbot_user_id') || `user_${Date.now()}`);
  const [sessions, setSessions] = useState<SessionData[]>(() => {
    const saved = localStorage.getItem('chatbot_sessions');
    if (saved) {
      const parsed = JSON.parse(saved);
      return parsed.map((s: any) => ({
        ...s,
        createdAt: new Date(s.createdAt),
        messages: s.messages.map((m: any) => ({
          ...m,
          timestamp: new Date(m.timestamp)
        }))
      }));
    }
    const initialSessionId = generateSessionId();
    return [{
      sessionId: initialSessionId,
      userID: userId,
      memories: [],
      messages: [],
      createdAt: new Date()
    }];
  });
  
  const [currentSessionId, setCurrentSessionId] = useState<string>(() => localStorage.getItem('current_session_id') || '');
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [tempUserId, setTempUserId] = useState(userId);
  const [apiUrl, setApiUrl] = useState(() => localStorage.getItem('chatbot_api_url') || 'http://127.0.0.1:8000');
  const [tempApiUrl, setTempApiUrl] = useState(apiUrl);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const userSessions = sessions.filter(s => s.userID === userId);
  const currentSession = sessions.find(s => s.sessionId === currentSessionId) || userSessions[0] || {sessionId: '', userID: '', memories: [], messages: [], createdAt: new Date()};
  const messages = currentSession.messages;
  const memories = currentSession.memories;
  const sessionId = currentSession.sessionId;

  // Save sessions to localStorage
  useEffect(() => {
    localStorage.setItem('chatbot_sessions', JSON.stringify(sessions));
  }, [sessions]);

  // Save userId and apiUrl to localStorage
  useEffect(() => {
    localStorage.setItem('chatbot_user_id', userId);
    localStorage.setItem('chatbot_api_url', apiUrl);
  }, [userId, apiUrl]);

  // Initialize currentSessionId
  useEffect(() => {
    if (sessions.length > 0 && !currentSessionId) {
      const userSess = sessions.filter(s => s.userID === userId);
      setCurrentSessionId(userSess[0]?.sessionId || '');
    }
  }, [sessions, currentSessionId, userId]);

  // Save currentSessionId to localStorage
  useEffect(() => {
    if (currentSessionId) {
      localStorage.setItem('current_session_id', currentSessionId);
    }
  }, [currentSessionId]);

  // Ensure currentSessionId is valid for current user
  useEffect(() => {
    if (currentSessionId && !userSessions.find(s => s.sessionId === currentSessionId)) {
      setCurrentSessionId(userSessions[0]?.sessionId || '');
    }
  }, [userId, sessions, currentSessionId, userSessions]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const currentIndex = sessions.findIndex(s => s.sessionId === currentSessionId);
    if (currentIndex === -1) return; // safety check

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    // Update current session with new message
    setSessions(prev => {
      const updated = [...prev];
      updated[currentIndex] = {
        ...updated[currentIndex],
        messages: [...updated[currentIndex].messages, userMessage]
      };
      return updated;
    });

    setInput('');
    setLoading(true);

    try {
      const payload: ChatRequest = {
        user_id: userId,
        session_id: sessionId,
        user_input: userMessage.content,
      };

      const response = await fetch(`${apiUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const data: ChatResponse = await response.json();

      const assistantMessage: Message = {
        role: 'assistant',
        content: data.answer,
        timestamp: new Date(),
        storedMemory: data.stored_memory,
      };

      // Update session with assistant response and memory
      setSessions(prev => {
        const updated = [...prev];
        const currentMessages = [...updated[currentIndex].messages, assistantMessage];
        const currentMemories = data.stored_memory 
          ? [...updated[currentIndex].memories, data.stored_memory]
          : updated[currentIndex].memories;
        
        updated[currentIndex] = {
          ...updated[currentIndex],
          messages: currentMessages,
          memories: currentMemories
        };
        return updated;
      });

    } catch (error) {
      console.error('Error:', error);
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please check if the backend is running and the API URL is correct.',
        timestamp: new Date(),
      };
      
      setSessions(prev => {
        const updated = [...prev];
        updated[currentIndex] = {
          ...updated[currentIndex],
          messages: [...updated[currentIndex].messages, errorMessage]
        };
        return updated;
      });
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const createNewSession = () => {
    const newSessionId = generateSessionId();
    const newSession: SessionData = {
      sessionId: newSessionId,
      userID: userId,
      memories: [],
      messages: [],
      createdAt: new Date()
    };
    setSessions(prev => [newSession, ...prev]);
    setCurrentSessionId(newSessionId);
  };

  const switchSession = (sessionId: string) => {
    setCurrentSessionId(sessionId);
  };

  const saveSettings = () => {
    setUserId(tempUserId);
    setApiUrl(tempApiUrl);
    setShowSettings(false);
  };

  const cancelSettings = () => {
    setTempUserId(userId);
    setTempApiUrl(apiUrl);
    setShowSettings(false);
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      {/* Settings Modal */}
      {showSettings && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md border border-gray-200 shadow-2xl">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                <Settings className="w-5 h-5 text-blue-600" />
                Settings
              </h3>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  User ID
                </label>
                <input
                  type="text"
                  value={tempUserId}
                  onChange={(e) => setTempUserId(e.target.value)}
                  placeholder="Enter your user ID"
                  className="w-full bg-gray-50 border border-gray-300 rounded-lg px-4 py-2 text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">This identifies you across sessions</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  API URL
                </label>
                <input
                  type="text"
                  value={tempApiUrl}
                  onChange={(e) => setTempApiUrl(e.target.value)}
                  placeholder="http://127.0.0.1:8000"
                  className="w-full bg-gray-50 border border-gray-300 rounded-lg px-4 py-2 text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">Backend API endpoint</p>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={cancelSettings}
                className="flex-1 px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={saveSettings}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Sidebar - Sessions List */}
      {sidebarOpen && (
        <div className="w-80 bg-white/90 backdrop-blur-lg border-r border-gray-200 flex flex-col shadow-lg">
          <div className="p-4 border-b border-gray-200">
            <button
              onClick={createNewSession}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
            >
              <Plus className="w-4 h-4" />
              New Session
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {userSessions.map((session) => (
              <div
                key={session.sessionId}
                onClick={() => switchSession(session.sessionId)}
                className={`rounded-lg p-3 cursor-pointer transition-all ${
                  session.sessionId === currentSessionId
                    ? 'bg-blue-50 border-2 border-blue-300'
                    : 'bg-gray-50 border border-gray-200 hover:bg-gray-100'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Database className="w-4 h-4 text-blue-600" />
                    <span className="font-mono text-sm font-semibold text-gray-900">
                      {session.userID}
                    </span>
                  </div>
                  {session.sessionId === currentSessionId && (
                    <ChevronRight className="w-4 h-4 text-blue-600" />
                  )}
                </div>

                <div className="space-y-1">
                  <div className="flex items-center gap-1 text-xs text-gray-500">
                    <Clock className="w-3 h-3" />
                    <span>{session.createdAt.toLocaleDateString()}</span>
                  </div>
                  
                  {session.memories.length > 0 ? (
                    <div className="mt-2 space-y-1">
                      {session.memories.slice(0, 2).map((memory, idx) => (
                        <div key={idx} className="text-xs text-blue-700 truncate">
                          • {typeof memory === 'object' ? JSON.stringify(memory) : memory}
                        </div>
                      ))}
                      {session.memories.length > 2 && (
                        <div className="text-xs text-gray-500">
                          +{session.memories.length - 2} more
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-xs text-gray-500 mt-1">No memories yet</div>
                  )}

                  <div className="text-xs text-gray-500 mt-1">
                    {session.messages.length} messages
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="p-4 border-t border-gray-200 space-y-3">
            <div className="bg-gray-50 rounded-lg p-3 text-xs text-gray-600 space-y-1">
              <div className="flex justify-between items-center">
                <span>User ID:</span>
                <span className="text-blue-600 font-mono">{userId.slice(0, 15)}{userId.length > 15 ? '...' : ''}</span>
              </div>
              <div className="flex justify-between items-center">
                <span>Active Session:</span>
                <span className="text-blue-600 font-mono">{sessionId}</span>
              </div>
              <div className="flex justify-between items-center">
                <span>Total Sessions:</span>
                <span className="text-green-600">{userSessions.length}</span>
              </div>
            </div>

            <button
              onClick={() => setShowSettings(true)}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors text-sm"
            >
              <Settings className="w-4 h-4" />
              Settings
            </button>
          </div>
        </div>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white/90 backdrop-blur-lg border-b border-gray-200 px-6 py-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                title={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
              >
                {sidebarOpen ? <X className="w-5 h-5 text-gray-600" /> : <Menu className="w-5 h-5 text-gray-600" />}
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">AI Assistant</h1>
                <p className="text-sm text-gray-600">
                  Session: <span className="font-mono text-blue-600">{sessionId}</span> • {memories.length} memories stored
                </p>
              </div>
            </div>
            <button
              onClick={createNewSession}
              className="flex items-center gap-2 px-4 py-2 bg-blue-50 hover:bg-blue-100 text-blue-600 rounded-lg transition-colors border border-blue-200"
            >
              <RefreshCw className="w-4 h-4" />
              New Session
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-md">
                <Bot className="w-16 h-16 text-blue-600 mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-gray-900 mb-2">Welcome {userId.split("@")[0]}!</h2>
                <p className="text-gray-600 mb-4">
                  {/* I'm an AI assistant with long-term memory. Share your name, location, profession, or other personal details, and I'll remember them for our future conversations. */}
                </p>
                <div className="bg-gray-50 rounded-lg p-4 text-left text-sm text-gray-700">
                  <p className="font-semibold mb-2 flex justify-center text-xl">How can I help you?</p>
                  <ul className="space-y-1 text-gray-600">
                    <li></li>
                  </ul>
                </div>
              </div>
            </div>
          ) : (
            messages.map((message, idx) => (
              <div
                key={idx}
                className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {message.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                )}
                
                <div className={`flex flex-col ${message.role === 'user' ? 'items-end' : 'items-start'} max-w-2xl`}>
                  <div
                    className={`rounded-2xl px-4 py-3 ${
                      message.role === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-900 border border-gray-200'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  </div>
                  
                  {message.storedMemory && (
                    <div className="mt-2 bg-green-50 border border-green-200 rounded-lg px-3 py-2 text-xs text-green-700 flex items-start gap-2">
                      <Database className="w-3 h-3 mt-0.5 " />
                      <span><strong>Stored:</strong> {typeof message.storedMemory === 'object' ? JSON.stringify(message.storedMemory) : message.storedMemory}</span>
                    </div>
                  )}
                  
                  <span className="text-xs text-gray-500 mt-1">
                    {message.timestamp.toLocaleTimeString()}
                  </span>
                </div>

                {message.role === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center flex-shrink-0">
                    <User className="w-5 h-5 text-gray-700" />
                  </div>
                )}
              </div>
            ))
          )}
          
          {loading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="bg-gray-100 rounded-2xl px-4 py-3 border border-gray-200">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-200 bg-white/90 backdrop-blur-lg p-4">
          <div className="max-w-4xl mx-auto flex gap-3">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message..."
              disabled={loading}
              className="flex-1 bg-gray-50 border border-gray-300 rounded-lg px-4 py-3 text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
            />
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-lg transition-colors flex items-center gap-2 font-medium"
            >
              <Send className="w-4 h-4" />
              Send
            </button>
          </div>
          {/* <p className="text-xs text-gray-500 text-center mt-2">
            Share personal info like your name, location, or profession to build long-term memory
          </p> */}
        </div>
      </div>
    </div>
  );
};

export default Chatbot;