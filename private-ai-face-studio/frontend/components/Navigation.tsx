'use client';
import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { Sparkles, LayoutDashboard, Wand2, History, Cpu } from 'lucide-react';
import { apiClient } from '../lib/api';

export default function Navigation() {
  const [workerOnline, setWorkerOnline] = useState(false);

  useEffect(() => {
    const checkWorker = async () => {
      try {
        const res = await apiClient.get('/api/worker/status');
        setWorkerOnline(res.data.online);
      } catch {
        setWorkerOnline(false);
      }
    };
    checkWorker();
    const interval = setInterval(checkWorker, 8000);
    return () => clearInterval(interval);
  }, []);

  return (
    <nav className="w-64 bg-studio-900 border-r border-studio-700/50 flex flex-col justify-between p-4 min-h-screen">
      <div>
        <div className="flex items-center gap-3 px-3 py-4 mb-6">
          <div className="p-2 bg-studio-accent rounded-lg">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-semibold text-white text-sm">AI Face Studio</h1>
            <p className="text-xs text-gray-400">Private Studio Edition</p>
          </div>
        </div>
        <div className="space-y-1">
          <Link href="/" className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-300 hover:bg-studio-800"><LayoutDashboard className="w-4 h-4" />Dashboard</Link>
          <Link href="/generate" className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm bg-studio-accent text-white"><Wand2 className="w-4 h-4" />Studio Generate</Link>
        </div>
      </div>
      <div className="p-3 bg-studio-800 rounded-lg flex items-center justify-between">
        <span className="text-xs text-gray-300 flex items-center gap-1.5"><Cpu className="w-3.5 h-3.5" />GPU Worker</span>
        <span className={`text-xs font-bold ${workerOnline ? 'text-emerald-400' : 'text-rose-400'}`}>{workerOnline ? 'ONLINE' : 'OFFLINE'}</span>
      </div>
    </nav>
  );
}
