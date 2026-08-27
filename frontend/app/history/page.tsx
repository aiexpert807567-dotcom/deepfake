'use client';
import React, { useEffect, useState } from 'react';
import Navigation from '../../components/Navigation';
import { History, RefreshCw, Download, CheckCircle2, XCircle, Clock3 } from 'lucide-react';
import { apiClient } from '../../lib/api';

export default function HistoryPage() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true); setError('');
    try { const res = await apiClient.get('/api/jobs'); setJobs(res.data || []); }
    catch (err: any) { setError(err.response?.data?.detail || 'Unable to load history. Check your Render API URL.'); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); const timer = setInterval(load, 5000); return () => clearInterval(timer); }, []);

  const resultUrl = (job: any) => {
    if (!job.result_url) return '#';
    const base = (process.env.NEXT_PUBLIC_API_URL || '').replace(/\/$/, '');
    return `${base}${job.result_url}`;
  };

  return <div className="flex bg-studio-950 text-gray-100 min-h-screen"><Navigation /><main className="flex-1 p-10 overflow-y-auto"><div className="max-w-5xl mx-auto">
    <div className="flex items-center justify-between mb-8"><div><h2 className="text-3xl font-extrabold text-white flex items-center gap-3"><History className="w-7 h-7 text-studio-accent" /> Media History</h2><p className="text-sm text-gray-400 mt-1">Jobs submitted to the GPU processing queue.</p></div><button onClick={load} className="px-4 py-2 rounded-xl border border-studio-700 bg-studio-900 hover:bg-studio-800 text-sm flex items-center gap-2"><RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Refresh</button></div>
    {error && <div className="mb-5 p-4 rounded-xl border border-rose-800 bg-rose-950/40 text-rose-300 text-sm">{error}</div>}
    {!loading && !error && jobs.length === 0 && <div className="p-12 rounded-2xl border border-studio-700 bg-studio-900/70 text-center"><Clock3 className="w-10 h-10 text-gray-500 mx-auto mb-3" /><p className="text-white font-semibold">No transformations yet</p><p className="text-gray-500 text-sm mt-1">Completed and queued jobs will appear here.</p></div>}
    <div className="space-y-4">{jobs.map(job => <div key={job.job_id} className="p-5 rounded-2xl border border-studio-700/70 bg-studio-900/80 flex items-center justify-between gap-5"><div className="min-w-0"><div className="flex items-center gap-3"><span className="font-mono text-xs text-indigo-300">{job.job_id}</span><span className={`text-[10px] font-bold px-2 py-1 rounded-full ${job.status === 'COMPLETED' ? 'bg-emerald-950 text-emerald-300' : job.status === 'FAILED' ? 'bg-rose-950 text-rose-300' : 'bg-amber-950 text-amber-300'}`}>{job.status}</span></div><p className="text-sm text-gray-300 mt-2">{job.current_stage}</p><p className="text-xs text-gray-500 mt-1">{job.target_media_type} • {job.duration_sec ? `${job.duration_sec.toFixed(1)}s` : '—'} • {new Date(job.created_at).toLocaleString()}</p>{job.error_message && <p className="text-xs text-rose-400 mt-2">{job.error_message}</p>}</div>{job.status === 'COMPLETED' && job.result_url && <a href={resultUrl(job)} target="_blank" rel="noreferrer" className="shrink-0 px-4 py-2 rounded-xl bg-studio-accent hover:bg-indigo-600 text-white text-sm font-semibold flex items-center gap-2"><Download className="w-4 h-4" /> Result</a>}{job.status === 'COMPLETED' && !job.result_url && <CheckCircle2 className="w-5 h-5 text-emerald-400" />}{job.status === 'FAILED' && <XCircle className="w-5 h-5 text-rose-400" />}</div>)}</div>
  </div></main></div>;
}
