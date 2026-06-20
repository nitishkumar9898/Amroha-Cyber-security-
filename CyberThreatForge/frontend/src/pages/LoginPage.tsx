import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield } from 'lucide-react';
import api from '../services/api';
import { useAuthStore } from '../store/authStore';

export function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [mfaCode, setMfaCode] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const setTokens = useAuthStore((s) => s.setTokens);
  const setUser = useAuthStore((s) => s.setUser);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      const { data } = await api.post('/auth/login', { email, password, mfaCode: mfaCode || undefined });
      setTokens(data.accessToken, data.refreshToken);
      const userData = JSON.parse(atob(data.accessToken.split('.')[1]));
      setUser({ id: userData.sub, email, name: userData.name, role: userData.role, department: userData.department });
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.error ?? err.message ?? 'Login failed');
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-6 p-8">
        <div className="text-center">
          <Shield className="w-12 h-12 text-cyan-400 mx-auto mb-2" />
          <h1 className="text-2xl font-bold text-gray-100">CyberThreatForge</h1>
          <p className="text-sm text-gray-500">Law Enforcement Cyber Investigation Platform</p>
        </div>
        {error && <div className="bg-red-900/30 border border-red-800 text-red-400 text-sm p-3 rounded">{error}</div>}
        <input
          type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)}
          className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-100"
          required
        />
        <input
          type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)}
          className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-100"
          required
        />
        <input
          type="text" placeholder="MFA Code (if enabled)" value={mfaCode} onChange={(e) => setMfaCode(e.target.value)}
          className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-100"
          maxLength={6}
        />
        <button type="submit" className="w-full bg-cyan-600 hover:bg-cyan-500 text-white font-medium py-2 rounded transition-colors">
          Sign In
        </button>
      </form>
    </div>
  );
}
