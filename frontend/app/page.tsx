'use client';
import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import Navigation from '../components/Navigation';
import { Sparkles, Wand2, Cpu, ShieldCheck, Zap, ArrowRight, Play, CheckCircle2, Film, Image as ImageIcon, Activity } from 'lucide-react';
import { apiClient } from '../lib/api';

export default function DashboardPage() {
  const [worker, setWorker] = useState<any>({ online: false });
  const [stats, setStats] = useState({ totalJobs: 1, completed: 1, vram: '15.3 GB', durationAvg: '14.2s' });

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
    <div className="flex bg-studio-950 text-gray-100 min-h-screen overflow-x-hidden font-sans">
      <Navigation />

      <main className="flex-1 p-10 overflow-y-auto">
        {/* Top Header Banner */}
        <div className="relative rounded-3xl bg-gradient-to-r from-studio-900 via-studio-850 to-indigo-950/40 border border-studio-700/60 p-8 mb-10 overflow-hidden shadow-2xl">
          <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
          <div className="relative z-10 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-studio-accent/15 border border-studio-accent/30 text-xs font-semibold text-indigo-300 mb-4">
              <Zap className="w-3.5 h-3.5 text-studio-accent" /> Zero-Cost Distributed Neural Studio
            </div>
            <h2 className="text-3xl font-extrabold text-white tracking-tight sm:text-4xl mb-3">
              Transform Media with <span className="bg-gradient-to-r from-indigo-400 via-studio-cyan to-cyan-300 bg-clip-text text-transparent">Multi-Reference Precision</span>
            </h2>
            <p className="text-gray-400 text-sm leading-relaxed mb-6">
              Full consent-based video and image identity transformation. Powered by temporal ArcFace aggregation, Reinhard LAB color adaptation, and GFPGAN face restoration.
            </p>
            <div className="flex items-center gap-4">
              <Link
                href="/generate"
                className="flex items-center gap-2.5 bg-gradient-to-r from-studio-accent to-indigo-600 hover:from-indigo-500 hover:to-indigo-600 text-white px-6 py-3.5 rounded-xl font-semibold shadow-lg shadow-indigo-500/25 transition transform hover:-translate-y-0.5"
              >
                <Wand2 className="w-4 h-4" /> Launch Studio Pipeline <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                href="/worker"
                className="flex items-center gap-2 bg-studio-800/80 hover:bg-studio-750 text-gray-200 border border-studio-700 px-5 py-3.5 rounded-xl font-medium text-sm transition"
              >
                <Cpu className="w-4 h-4 text-studio-cyan" /> Worker Telemetry
              </Link>
            </div>
          </div>
        </div>

        {/* Real-time Telemetry Metric Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-5 mb-10">
          <div className="p-5 rounded-2xl bg-studio-900/80 border border-studio-700/60 backdrop-blur">
            <div className="flex items-center justify-between text-gray-400 text-xs font-medium mb-3">
              <span>GPU Session Status</span>
              <span className={`w-2.5 h-2.5 rounded-full ${worker.online ? 'bg-emerald-400 animate-ping' : 'bg-rose-500'}`} />
            </div>
            <div className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
              {worker.online ? 'NVIDIA T4' : 'OFFLINE'}
            </div>
            <p className="text-xs text-emerald-400 mt-1">Kaggle Free Node Connected</p>
          </div>

          <div className="p-5 rounded-2xl bg-studio-900/80 border border-studio-700/60 backdrop-blur">
            <div className="flex items-center justify-between text-gray-400 text-xs font-medium mb-3">
              <span>Total Transformations</span>
              <Film className="w-4 h-4 text-studio-accent" />
            </div>
            <div className="text-2xl font-bold text-white tracking-tight">Ready</div>
            <p className="text-xs text-gray-400 mt-1">Up to 30s 1080p Video</p>
          </div>

          <div className="p-5 rounded-2xl bg-studio-900/80 border border-studio-700/60 backdrop-blur">
            <div className="flex items-center justify-between text-gray-400 text-xs font-medium mb-3">
              <span>Color / Occlusion Engine</span>
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold text-white tracking-tight">Active</div>
            <p className="text-xs text-indigo-400 mt-1">Reinhard LAB + Soft Feather</p>
          </div>

          <div className="p-5 rounded-2xl bg-studio-900/80 border border-studio-700/60 backdrop-blur">
            <div className="flex items-center justify-between text-gray-400 text-xs font-medium mb-3">
              <span>Infrastructure Cost</span>
              <Zap className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-bold text-emerald-400 tracking-tight">$0.00 / day</div>
            <p className="text-xs text-gray-400 mt-1">100% Free Resources</p>
          </div>
        </div>

        {/* Feature Highlights Grid */}
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-studio-accent" /> Studio Pipeline Capabilities
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 rounded-2xl bg-studio-900/60 border border-studio-700/50 hover:border-studio-accent/40 transition">
            <div className="w-10 h-10 rounded-xl bg-indigo-950 text-indigo-400 flex items-center justify-center mb-4 border border-indigo-800/40">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <h4 className="font-semibold text-white text-base mb-1">Target Face Isolation</h4>
            <p className="text-sm text-gray-400 leading-relaxed">
              Detects all faces in target images/videos. Allows user to select strictly one face; all other people remain 100% unchanged.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-studio-900/60 border border-studio-700/50 hover:border-studio-accent/40 transition">
            <div className="w-10 h-10 rounded-xl bg-cyan-950 text-cyan-400 flex items-center justify-center mb-4 border border-cyan-800/40">
              <Activity className="w-5 h-5" />
            </div>
            <h4 className="font-semibold text-white text-base mb-1">Multi-Angle Identity Aggregator</h4>
            <p className="text-sm text-gray-400 leading-relaxed">
              Upload 3–8 references. Features are combined with quality scoring and pose weighting to maintain consistency across rotations.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-studio-900/60 border border-studio-700/50 hover:border-studio-accent/40 transition">
            <div className="w-10 h-10 rounded-xl bg-emerald-950 text-emerald-400 flex items-center justify-center mb-4 border border-emerald-800/40">
              <Film className="w-5 h-5" />
            </div>
            <h4 className="font-semibold text-white text-base mb-1">Temporal Smoothing & Audio Mux</h4>
            <p className="text-sm text-gray-400 leading-relaxed">
              Eliminates frame-to-frame jitter using exponential landmark moving averages and automatically preserves original audio via FFmpeg.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
