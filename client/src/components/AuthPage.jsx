import React, { useState } from 'react';
import api from '../utils/api';

const AuthPage = ({ onAuthSuccess }) => {
  const [mode, setMode] = useState('login');
  const [loginRole, setLoginRole] = useState('user');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!email.trim() || !password) {
      setError('Email and password are required.');
      return;
    }

    if (mode === 'register' && password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    try {
      const endpoint = mode === 'register' ? '/auth/register' : '/auth/login';
      const response = await api.post(endpoint, { email, password });
      onAuthSuccess(response.data.user, response.data.token);
    } catch (err) {
      const message = err?.response?.data?.error || 'Authentication failed.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-prime text-white px-4">
      <div className="w-full max-w-md rounded-2xl border border-white/10 bg-white/5 p-8 shadow-xl">
        <div className="mb-6 text-center">
          <h1 className="text-3xl font-bold">Autonotex</h1>
          <p className="text-sm text-gray-400 mt-2">
            {mode === 'login' ? 'Sign in to continue' : 'Create your account'}
          </p>
        </div>

        <div className="flex gap-2 mb-6">
          <button
            type="button"
            onClick={() => setMode('login')}
            className={`flex-1 py-2 rounded-lg text-sm border transition-colors ${
              mode === 'login'
                ? 'bg-accent/20 text-accent border-accent/40'
                : 'bg-white/5 text-gray-300 border-white/10 hover:bg-white/10'
            }`}
          >
            Login
          </button>
          <button
            type="button"
            onClick={() => setMode('register')}
            className={`flex-1 py-2 rounded-lg text-sm border transition-colors ${
              mode === 'register'
                ? 'bg-accent/20 text-accent border-accent/40'
                : 'bg-white/5 text-gray-300 border-white/10 hover:bg-white/10'
            }`}
          >
            Register
          </button>
        </div>

        {mode === 'login' && (
          <div className="mb-4">
            <label className="block text-xs text-gray-400 mb-1">Login as</label>
            <div className="flex gap-2">
              {['user', 'admin'].map((role) => (
                <button
                  key={role}
                  type="button"
                  onClick={() => setLoginRole(role)}
                  className={`flex-1 py-2 rounded-lg text-xs border transition-colors ${
                    loginRole === role
                      ? 'bg-accent/20 text-accent border-accent/40'
                      : 'bg-white/5 text-gray-300 border-white/10 hover:bg-white/10'
                  }`}
                >
                  {role === 'admin' ? 'Admin' : 'User'}
                </button>
              ))}
            </div>
            <p className="mt-2 text-xs text-gray-400">
              {loginRole === 'admin'
                ? 'Use the admin email and password configured on the server.'
                : 'Use your registered email and password.'}
            </p>
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg bg-slate-900/70 border border-white/10 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-accent/40"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg bg-slate-900/70 border border-white/10 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-accent/40"
              placeholder="••••••••"
            />
          </div>
          {mode === 'register' && (
            <div>
              <label className="block text-xs text-gray-400 mb-1">Confirm Password</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full rounded-lg bg-slate-900/70 border border-white/10 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-accent/40"
                placeholder="••••••••"
              />
            </div>
          )}

          {error && (
            <div className="text-sm text-red-300 bg-red-900/30 border border-red-700 rounded-lg p-2">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 rounded-lg bg-accent hover:bg-accent/80 text-white text-sm font-semibold transition-colors disabled:opacity-60"
          >
            {loading ? 'Please wait...' : mode === 'login' ? 'Login' : 'Create Account'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default AuthPage;
