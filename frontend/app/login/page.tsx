'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { LockKeyhole, Sparkles, Loader2 } from 'lucide-react';
import { apiClient } from '../../lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const body = new URLSearchParams();
      body.set('username', username);
      body.set('password', password);
      const res = await apiClient.post('/api/auth/login', body, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      localStorage.setItem('studio_token', res.data.access_token);
      router.replace('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Unable to connect to the studio API. Check the Vercel API URL and Render service.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-studio-950 text-gray-100 flex items-center justify-center p-6">
      <form onSubmit={submit} className="w-full max-w-md bg-studio-900 border border-studio-700/70 rounded-3xl p-8 shadow-2xl">
        <div className="w-14 h-14 rounded-2xl bg-studio-accent/20 text-studio-accent flex items-center justify-center mx-auto mb-5 border border-studio-accent/30">
          <Sparkles className="w-7 h-7" />
        </div>
        <h1 className="text-2xl font-bold text-white text-center">AI Face Studio</h1>
        <p className="text-sm text-gray-400 text-center mt-2 mb-7">Private administrator access</p>
        <label className="block text-xs font-semibold text-gray-300 mb-2">Username</label>
        <input value={username} onChange={e => setUsername(e.target.value)} required autoComplete="username" className="w-full mb-4 px-4 py-3 rounded-xl bg-studio-850 border border-studio-700 text-white outline-none focus:border-studio-accent" />
        <label className="block text-xs font-semibold text-gray-300 mb-2">Password</label>
        <div className="relative mb-5">
          <LockKeyhole className="absolute left-3 top-3.5 w-4 h-4 text-gray-500" />
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} required autoComplete="current-password" className="w-full pl-10 pr-4 py-3 rounded-xl bg-studio-850 border border-studio-700 text-white outline-none focus:border-studio-accent" />
        </div>
        {error && <div className="mb-4 p-3 rounded-xl bg-rose-950/50 border border-rose-800 text-rose-300 text-xs">{error}</div>}
        <button disabled={loading} className="w-full py-3.5 rounded-xl bg-gradient-to-r from-studio-accent to-indigo-600 text-white font-bold disabled:opacity-60 flex items-center justify-center gap-2">
          {loading && <Loader2 className="w-4 h-4 animate-spin" />}
          Sign in
        </button>
      </form>
    </main>
  );
}
