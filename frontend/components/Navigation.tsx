'use client';
import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Sparkles, LayoutDashboard, Wand2, History, Cpu, Activity, ShieldCheck, Power } from 'lucide-react';
import { apiClient } from '../lib/api';

export default function Navigation() {
  const pathname = usePathname();
  const [worker, setWorker] = useState<any>({ online: false, enabled: true, status: 'OFFLINE', gpu_name: 'Scanning...' });
  const [isToggling, setIsToggling] = useState(false);

  const fetchStatus = async () => {
    try {
      const res = await apiClient.get('/api/worker/status');
      setWorker(res.data);
    } catch {
      setWorker({ online: false, enabled: true, status: 'OFFLINE' });
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  const toggleWorker = async () => {
    if (isToggling) return;
    setIsToggling(true);
    try {
      const nextEnabled = worker.enabled === false;
      const res = await apiClient.post('/api/worker/power', { enabled: nextEnabled });
      setWorker(res.data);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Unable to change GPU worker state');
    } finally {
      setIsToggling(false);
    }
  };

  const navItems = [
    { label: 'Studio Dashboard', href: '/', icon: LayoutDashboard },
    { label: 'AI Generator', href: '/generate', icon: Wand2 },
    { label: 'GPU Command Center', href: '/worker', icon: Cpu },
    { label: 'Media History', href: '/history', icon: History },
  ];

  const enabled = worker.enabled !== false;

  return (
    <aside className="w-72 bg-studio-900/90 backdrop-blur-2xl border-r border-studio-700/60 flex flex-col justify-between p-5 min-h-screen z-30 select-none">
      <div>
        <div className="flex items-center gap-3.5 px-2 py-3 mb-8">
          <div className="relative">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-studio-accent to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/25"><Sparkles className="w-5 h-5 text-white" /></div>
            <span className="absolute -bottom-1 -right-1 w-3.5 h-3.5 bg-studio-900 rounded-full flex items-center justify-center"><span className={`w-2 h-2 rounded-full ${worker.online ? 'bg-emerald-400 animate-ping' : enabled ? 'bg-amber-400' : 'bg-rose-500'}`} /></span>
          </div>
          <div><div className="flex items-center gap-2"><h1 className="font-bold text-white text-base tracking-tight">AI Face Studio</h1><span className="text-[10px] bg-studio-accent/20 text-studio-accent border border-studio-accent/30 font-semibold px-1.5 py-0.5 rounded">v2.5</span></div><p className="text-xs text-gray-400 flex items-center gap-1 mt-0.5"><ShieldCheck className="w-3 h-3 text-emerald-400" /> Private Zero-Cost Node</p></div>
        </div>
        <div className="space-y-1.5">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-gray-500 px-3 mb-2">Studio Navigation</p>
          {navItems.map((item) => { const Icon = item.icon; const active = pathname === item.href; return <Link key={item.href} href={item.href} className={`flex items-center justify-between px-3.5 py-3 rounded-xl text-sm font-medium transition-all duration-200 group ${active ? 'bg-gradient-to-r from-studio-accent to-indigo-700 text-white shadow-lg shadow-indigo-600/30' : 'text-gray-400 hover:text-gray-100 hover:bg-studio-800/80 border border-transparent hover:border-studio-700/50'}`}><div className="flex items-center gap-3"><Icon className={`w-4 h-4 ${active ? 'text-white' : 'text-gray-400 group-hover:text-studio-accent'}`} /><span>{item.label}</span></div>{item.badge && <span className="text-[10px] uppercase font-bold bg-studio-cyan/20 text-cyan-300 border border-cyan-500/30 px-2 py-0.5 rounded-full">{item.badge}</span>}{item.count && <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${worker.online ? 'bg-emerald-950 text-emerald-300 border border-emerald-800/60' : 'bg-rose-950 text-rose-300 border border-rose-800/60'}`}>{item.count}</span>}</Link>; })}
        </div>
      </div>
      <div className="pt-4 border-t border-studio-700/60 space-y-3">
        <div className={`p-4 rounded-2xl border transition-all duration-300 ${worker.online ? 'bg-gradient-to-b from-studio-850 to-studio-900 border-emerald-500/30 shadow-lg shadow-emerald-950/20' : 'bg-studio-850 border-studio-700/50'}`}>
          <div className="flex items-center justify-between mb-3"><div className="flex items-center gap-2"><Activity className={`w-4 h-4 ${worker.online ? 'text-emerald-400 animate-pulse' : enabled ? 'text-amber-400' : 'text-gray-500'}`} /><span className="text-xs font-semibold text-gray-200">GPU Hardware Node</span></div>
            <button onClick={toggleWorker} disabled={isToggling} title={enabled ? 'Disable GPU worker' : 'Enable GPU worker'} className={`p-1.5 rounded-lg border transition-all disabled:opacity-50 ${enabled ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40 hover:bg-emerald-500/30' : 'bg-rose-500/20 text-rose-400 border-rose-500/40 hover:bg-rose-500/30'}`}><Power className={`w-3.5 h-3.5 ${isToggling ? 'animate-spin' : ''}`} /></button>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs"><span className="text-gray-400">Status:</span><span className={`font-bold flex items-center gap-1.5 ${worker.online ? 'text-emerald-400' : enabled ? 'text-amber-400' : 'text-rose-400'}`}><span className={`w-2 h-2 rounded-full ${worker.online ? 'bg-emerald-400 shadow-md shadow-emerald-500' : enabled ? 'bg-amber-400' : 'bg-rose-500'}`} />{worker.online ? 'CONNECTED' : enabled ? 'WAITING' : 'GPU OFF'}</span></div>
            <div className="flex items-center justify-between text-xs"><span className="text-gray-400">Accelerator:</span><span className="text-gray-200 font-mono text-[11px] truncate max-w-[120px]">{worker.gpu_name || (worker.online ? 'NVIDIA T4' : 'None')}</span></div>
            <div className="flex items-center justify-between text-xs"><span className="text-gray-400">VRAM Allocation:</span><span className="text-indigo-400 font-mono text-[11px]">{worker.vram_total_mb ? `${worker.vram_total_mb} MB` : worker.online ? '15,360 MB' : '0 MB'}</span></div>
          </div>
        </div>
        <p className="text-[11px] text-center text-gray-500">Kaggle Free GPU Session • $0 Cost</p>
      </div>
    </aside>
  );
}
