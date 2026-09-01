'use client';
import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import Navigation from '../components/Navigation';
import { Sparkles, Wand2, ShieldCheck, Zap, ArrowRight, CheckCircle2, Film, Activity } from 'lucide-react';
import { apiClient } from '../lib/api';

export default function DashboardPage() {
  const [worker, setWorker] = useState<any>({ online: false });

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await apiClient.get('/api/worker/status');
        setWorker(res.data);
      } catch {}
    };
    fetchStatus();
  }, []);

  return (
    <div className="flex flex-col md:flex-row bg-studio-950 text-gray-100 min-h-screen overflow-x-hidden font-sans">
      <Navigation />
      <main className="flex-1 p-4 sm:p-6 lg:p-10 overflow-y-auto">
        <div className="relative rounded-3xl bg-gradient-to-r from-white via-slate-50 to-indigo-50 border border-studio-700/60 p-6 sm:p-8 mb-8 sm:mb-10 overflow-hidden shadow-xl">
          <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
          <div className="relative z-10 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-studio-accent/15 border border-studio-accent/30 text-xs font-semibold text-indigo-600 mb-4"><Zap className="w-3.5 h-3.5 text-studio-accent" /> Zero-Cost Distributed Neural Studio</div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight sm:text-4xl mb-3">Transform Media with <span className="bg-gradient-to-r from-indigo-600 via-studio-cyan to-cyan-500 bg-clip-text text-transparent">Multi-Reference Precision</span></h2>
            <p className="text-gray-400 text-sm leading-relaxed mb-6">Full consent-based video and image identity transformation. Powered by temporal ArcFace aggregation, Reinhard LAB color adaptation, and GFPGAN face restoration.</p>
            <Link href="/generate" className="inline-flex items-center justify-center gap-2.5 bg-gradient-to-r from-studio-accent to-indigo-600 hover:from-indigo-500 hover:to-indigo-700 text-white px-6 py-3.5 rounded-xl font-semibold shadow-lg shadow-indigo-500/25 transition transform hover:-translate-y-0.5"><Wand2 className="w-4 h-4" /> Launch Studio Pipeline <ArrowRight className="w-4 h-4" /></Link>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5 mb-8 sm:mb-10">
          <div className="p-5 rounded-2xl bg-white border border-studio-700/60 shadow-sm"><div className="flex items-center justify-between text-gray-400 text-xs font-medium mb-3"><span>GPU Session Status</span><span className={`w-2.5 h-2.5 rounded-full ${worker.online ? 'bg-emerald-400 animate-ping' : 'bg-rose-500'}`} /></div><div className="text-2xl font-bold text-white tracking-tight">{worker.online ? 'NVIDIA T4' : 'OFFLINE'}</div><p className="text-xs text-emerald-500 mt-1">{worker.online ? 'Kaggle Free Node Connected' : 'Turn on GPU from the sidebar'}</p></div>
          <div className="p-5 rounded-2xl bg-white border border-studio-700/60 shadow-sm"><div className="flex items-center justify-between text-gray-400 text-xs font-medium mb-3"><span>Total Transformations</span><Film className="w-4 h-4 text-studio-accent" /></div><div className="text-2xl font-bold text-white tracking-tight">Ready</div><p className="text-xs text-gray-400 mt-1">Up to 30s 1080p Video</p></div>
          <div className="p-5 rounded-2xl bg-white border border-studio-700/60 shadow-sm"><div className="flex items-center justify-between text-gray-400 text-xs font-medium mb-3"><span>Infrastructure Cost</span><Zap className="w-4 h-4 text-amber-400" /></div><div className="text-2xl font-bold text-emerald-500 tracking-tight">$0.00 / day</div><p className="text-xs text-gray-400 mt-1">100% Free Resources</p></div>
        </div>

        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2"><Sparkles className="w-4 h-4 text-studio-accent" /> Studio Pipeline Capabilities</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 sm:gap-6">
          <div className="p-6 rounded-2xl bg-white border border-studio-700/50 shadow-sm hover:border-studio-accent/40 transition"><div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-500 flex items-center justify-center mb-4 border border-indigo-100"><CheckCircle2 className="w-5 h-5" /></div><h4 className="font-semibold text-white text-base mb-1">Target Face Isolation</h4><p className="text-sm text-gray-400 leading-relaxed">Detects all faces in target images/videos. Allows user to select strictly one face; all other people remain unchanged.</p></div>
          <div className="p-6 rounded-2xl bg-white border border-studio-700/50 shadow-sm hover:border-studio-accent/40 transition"><div className="w-10 h-10 rounded-xl bg-cyan-50 text-cyan-500 flex items-center justify-center mb-4 border border-cyan-100"><Activity className="w-5 h-5" /></div><h4 className="font-semibold text-white text-base mb-1">Multi-Angle Identity Aggregator</h4><p className="text-sm text-gray-400 leading-relaxed">Upload 3–8 references. Features are combined with quality scoring and pose weighting to maintain consistency across rotations.</p></div>
          <div className="p-6 rounded-2xl bg-white border border-studio-700/50 shadow-sm hover:border-studio-accent/40 transition"><div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-500 flex items-center justify-center mb-4 border border-emerald-100"><Film className="w-5 h-5" /></div><h4 className="font-semibold text-white text-base mb-1">Temporal Smoothing & Audio Mux</h4><p className="text-sm text-gray-400 leading-relaxed">Reduces frame-to-frame jitter and automatically preserves original audio via FFmpeg.</p></div>
        </div>
      </main>
    </div>
  );
}
