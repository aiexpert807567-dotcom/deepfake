'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Navigation from '../../components/Navigation';
import { Upload, Sparkles, CheckCircle2, Film, Image as ImageIcon, ArrowLeft, ArrowRight, RefreshCw, Download, RotateCcw, Loader2 } from 'lucide-react';
import { apiClient, getBaseUrl } from '../../lib/api';

type Face = { id: string; label: string; confidence: number; bbox?: number[]; thumbnail?: string };
type Reference = { reference_id: string; filename: string; analysis: { quality_score: number; estimated_angle: string } };

export default function GenerateStudioPage() {
  const [step, setStep] = useState(1);
  const [targetFile, setTargetFile] = useState<File | null>(null);
  const [targetMedia, setTargetMedia] = useState<any>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [detectedFaces, setDetectedFaces] = useState<Face[]>([]);
  const [selectedFaceId, setSelectedFaceId] = useState('');
  const [references, setReferences] = useState<Reference[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [activeJob, setActiveJob] = useState<any>(null);
  const [jobStatus, setJobStatus] = useState<any>(null);
  const [workerOnline, setWorkerOnline] = useState(false);

  const resetStudio = () => {
    setStep(1); setTargetFile(null); setTargetMedia(null); setIsUploading(false);
    setDetectedFaces([]); setSelectedFaceId(''); setReferences([]);
    setIsGenerating(false); setActiveJob(null); setJobStatus(null);
  };

  useEffect(() => {
    if (!activeJob?.job_id) return;
    const pollJob = async () => {
      try {
        const res = await apiClient.get(`/api/jobs/${activeJob.job_id}`);
        setJobStatus(res.data);
        if (res.data.status === 'COMPLETED' || res.data.status === 'FAILED') setIsGenerating(false);
      } catch {}
    };
    pollJob();
    const interval = setInterval(pollJob, 3000);
    return () => clearInterval(interval);
  }, [activeJob]);

  useEffect(() => {
    const checkWorker = async () => {
      try {
        const res = await apiClient.get('/api/worker/status');
        setWorkerOnline(Boolean(res.data.online));
      } catch { setWorkerOnline(false); }
    };
    checkWorker();
    const interval = setInterval(checkWorker, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleTargetUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setTargetFile(file); setIsUploading(true);
    const formData = new FormData(); formData.append('file', file);
    try {
      const res = await apiClient.post('/api/media/upload-target', formData);
      setTargetMedia(res.data);
      const faceRes = await apiClient.get(`/api/media/${res.data.media_id}/detect-faces`);
      setDetectedFaces(faceRes.data.faces || []); setStep(2);
    } catch (err: any) {
      setTargetFile(null); alert(err.response?.data?.detail || 'Target upload failed');
    } finally { setIsUploading(false); }
  };

  const handleReferenceUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return;
    for (const file of Array.from(e.target.files)) {
      const formData = new FormData(); formData.append('file', file);
      try {
        const res = await apiClient.post('/api/media/upload-reference', formData);
        setReferences(prev => [...prev, res.data]);
      } catch (err: any) {
        alert(err.response?.data?.detail || `Reference upload failed: ${file.name}`);
      }
    }
    e.target.value = '';
  };

  const handleStartGeneration = async () => {
    if (!targetMedia || !selectedFaceId || references.length === 0) return;
    setIsGenerating(true); setJobStatus(null);
    try {
      const chosenFace = detectedFaces.find(f => f.id === selectedFaceId);
      const res = await apiClient.post('/api/jobs', {
        media_type: targetMedia?.analysis?.media_type || 'image',
        target_media_id: targetMedia.media_id,
        selected_face_id: selectedFaceId,
        target_face_bbox: chosenFace?.bbox || null,
        reference_ids: references.map(r => r.reference_id),
        quality: 'maximum', face_restoration: true, temporal_stabilization: true,
        color_matching: true, lighting_matching: true, occlusion_handling: true, super_resolution: true,
      });
      setActiveJob(res.data); setStep(5);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Job initialization failed'); setIsGenerating(false);
    }
  };

  const resultUrl = useMemo(() => jobStatus?.result_url ? `${getBaseUrl()}${jobStatus.result_url}` : '', [jobStatus?.result_url]);
  const resultIsVideo = useMemo(() => targetMedia?.analysis?.media_type === 'video' || /\.(mp4|webm|mov|m4v)(\?|$)/i.test(resultUrl), [targetMedia?.analysis?.media_type, resultUrl]);

  return (
    <div className="flex flex-col md:flex-row bg-studio-950 text-gray-100 min-h-screen">
      <Navigation />
      <main className="flex-1 p-4 sm:p-6 lg:p-10 overflow-y-auto">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-start justify-between gap-4 mb-6 sm:mb-10">
            <div><h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">AI Studio Generator</h2><p className="text-sm text-gray-400 mt-1">Multi-reference face transformation studio</p></div>
            {step > 1 && <button onClick={resetStudio} disabled={isGenerating} className="shrink-0 px-3 sm:px-4 py-2 rounded-xl border border-studio-700 bg-studio-900 hover:bg-studio-800 disabled:opacity-50 text-sm font-semibold flex items-center gap-2"><RotateCcw className="w-4 h-4" /><span className="hidden sm:inline">Reset</span></button>}
          </div>

          <div className="flex items-center gap-2 mb-6">
            {[1,2,3,4,5].map(n => <React.Fragment key={n}><div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${step >= n ? 'bg-studio-accent text-white' : 'bg-studio-800 text-gray-500'}`}>{n}</div>{n < 5 && <div className={`h-px flex-1 ${step > n ? 'bg-studio-accent' : 'bg-studio-700'}`} />}</React.Fragment>)}
          </div>

          {step === 1 && <section className="bg-studio-900/90 border border-studio-700/70 rounded-3xl p-6 sm:p-10 text-center shadow-2xl">
            <div className="w-16 h-16 rounded-2xl bg-studio-accent/20 text-studio-accent flex items-center justify-center mx-auto mb-5"><Upload className="w-8 h-8" /></div>
            <h3 className="text-xl sm:text-2xl font-bold text-white mb-2">Upload Target Media</h3><p className="text-sm text-gray-400 max-w-md mx-auto mb-8">Choose an image or video containing the face you want to transform.</p>
            <label className="w-full sm:w-auto justify-center bg-gradient-to-r from-studio-accent to-indigo-600 text-white px-6 sm:px-8 py-4 rounded-xl cursor-pointer font-semibold shadow-xl inline-flex items-center gap-3">{isUploading ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Film className="w-5 h-5" />}{isUploading ? 'Analyzing & Detecting Faces...' : 'Select Video or Image'}<input type="file" onChange={handleTargetUpload} className="hidden" accept="image/*,video/*" disabled={isUploading} /></label>
          </section>}

          {step === 2 && <section className="bg-studio-900/90 border border-studio-700/70 rounded-3xl p-5 sm:p-8 shadow-2xl">
            <h3 className="text-xl font-bold text-white mb-2">Select Target Face</h3><p className="text-sm text-gray-400 mb-6">Select exactly one face to transform.</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">{detectedFaces.map(face => <button key={face.id} onClick={() => setSelectedFaceId(face.id)} className={`text-left p-5 rounded-2xl border transition ${selectedFaceId === face.id ? 'border-studio-accent bg-studio-accent/10' : 'border-studio-700 bg-studio-800 hover:border-gray-500'}`}><div className="flex items-center gap-4">{face.thumbnail ? <img src={`data:image/jpeg;base64,${face.thumbnail}`} alt={face.label} className="w-16 h-16 rounded-xl object-cover" /> : <div className="w-16 h-16 rounded-xl bg-studio-700 flex items-center justify-center"><ImageIcon className="w-6 h-6" /></div>}<div className="flex-1"><div className="flex items-center justify-between gap-2"><span className="font-bold text-white">{face.label}</span>{selectedFaceId === face.id && <CheckCircle2 className="w-5 h-5 text-studio-accent" />}</div><p className="text-xs text-gray-400 mt-1">Confidence: {(face.confidence * 100).toFixed(0)}%</p></div></div></button>)}</div>
            <div className="flex justify-between pt-4 border-t border-studio-800"><button onClick={() => setStep(1)} className="px-4 py-2 text-sm text-gray-400 flex items-center gap-2"><ArrowLeft className="w-4 h-4" /> Back</button><button disabled={!selectedFaceId} onClick={() => setStep(3)} className="px-5 py-3 rounded-xl bg-studio-accent text-white font-semibold disabled:opacity-50 flex items-center gap-2">Continue <ArrowRight className="w-4 h-4" /></button></div>
          </section>}

          {step === 3 && <section className="bg-studio-900/90 border border-studio-700/70 rounded-3xl p-5 sm:p-8 shadow-2xl">
            <h3 className="text-xl font-bold text-white mb-2">Reference Photos</h3><p className="text-sm text-gray-400 mb-6">Use multiple angles for the best identity consistency. 3–8 photos are recommended.</p>
            {references.length > 0 && <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">{references.map((ref, idx) => <div key={`${ref.reference_id}-${idx}`} className="p-4 bg-studio-800 rounded-xl border border-studio-700 flex items-center justify-between gap-3"><div className="min-w-0"><p className="text-sm font-semibold text-white truncate">{ref.filename}</p><p className="text-xs text-emerald-400 mt-1">Score: {ref.analysis.quality_score}% • {ref.analysis.estimated_angle}</p></div><CheckCircle2 className="w-4 h-4 text-emerald-400" /></div>)}</div>}
            <label className="w-full sm:w-auto justify-center bg-studio-800 hover:bg-studio-750 text-gray-200 border border-studio-700 px-5 py-3 rounded-xl cursor-pointer text-sm font-semibold inline-flex items-center gap-2 mb-8">+ Upload Reference Photos<input type="file" multiple onChange={handleReferenceUpload} className="hidden" accept="image/*" /></label>
            <div className="flex justify-between pt-4 border-t border-studio-800"><button onClick={() => setStep(2)} className="px-4 py-2 text-sm text-gray-400 flex items-center gap-2"><ArrowLeft className="w-4 h-4" /> Back</button><button disabled={references.length === 0} onClick={() => setStep(4)} className="px-5 py-3 rounded-xl bg-studio-accent text-white font-semibold disabled:opacity-50 flex items-center gap-2">Continue <ArrowRight className="w-4 h-4" /></button></div>
          </section>}

          {step === 4 && <section className="bg-studio-900/90 border border-studio-700/70 rounded-3xl p-5 sm:p-8 shadow-2xl">
            <h3 className="text-xl font-bold text-white mb-4">Quality & Pipeline</h3>
            <div className="space-y-3 bg-studio-850 p-5 rounded-2xl border border-studio-700/60 mb-8 text-sm"><div className="flex justify-between py-2 border-b border-studio-800"><span>Quality Preset</span><strong className="text-white">Maximum</strong></div><div className="flex justify-between py-2 border-b border-studio-800"><span>GFPGAN Restoration</span><span className="text-emerald-400 font-semibold">ENABLED</span></div><div className="flex justify-between py-2 border-b border-studio-800"><span>Temporal Stabilization</span><span className="text-emerald-400 font-semibold">ENABLED</span></div><div className="flex justify-between py-2 border-b border-studio-800"><span>Color & Lighting Matching</span><span className="text-emerald-400 font-semibold">ENABLED</span></div><div className="flex justify-between py-2"><span>Audio Track Sync</span><span className="text-emerald-400 font-semibold">ENABLED</span></div></div>
            <div className="mb-6 p-4 rounded-xl border border-studio-700 bg-studio-800 text-sm flex items-center justify-between"><span>GPU Worker</span><span className={workerOnline ? 'text-emerald-400 font-semibold' : 'text-rose-400 font-semibold'}>{workerOnline ? 'ONLINE' : 'OFFLINE'}</span></div>
            <button onClick={handleStartGeneration} disabled={isGenerating || !workerOnline} className="w-full flex items-center justify-center gap-3 bg-gradient-to-r from-studio-accent to-indigo-600 text-white py-4 rounded-xl font-bold disabled:opacity-50">{isGenerating ? <Loader2 className="w-5 h-5 animate-spin" /> : <Sparkles className="w-5 h-5" />}{isGenerating ? 'Starting Transformation...' : 'Start GPU Transformation'}</button>
          </section>}

          {step === 5 && <section className="bg-studio-900/90 border border-studio-700/70 rounded-3xl p-5 sm:p-8 shadow-2xl">
            {jobStatus?.status === 'COMPLETED' && resultUrl ? <div><div className="text-center mb-6"><div className="w-16 h-16 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto mb-4"><CheckCircle2 className="w-9 h-9" /></div><h3 className="text-2xl font-bold text-white">Transformation Complete</h3><p className="text-sm text-gray-400 mt-1">Preview your result here. Download it only if you want a local copy.</p></div><div className="rounded-2xl overflow-hidden border border-studio-700 bg-black mb-6">{resultIsVideo ? <video src={resultUrl} controls playsInline className="w-full max-h-[70vh] object-contain" /> : <img src={resultUrl} alt="Generated result" className="w-full max-h-[70vh] object-contain" />}</div><div className="flex flex-col sm:flex-row gap-3 justify-center"><a href={resultUrl} download className="px-6 py-3 rounded-xl bg-studio-accent hover:bg-indigo-600 text-white font-semibold flex items-center justify-center gap-2"><Download className="w-4 h-4" /> Download Result</a><button onClick={resetStudio} className="px-6 py-3 rounded-xl border border-studio-700 bg-studio-800 hover:bg-studio-750 text-white font-semibold flex items-center justify-center gap-2"><RotateCcw className="w-4 h-4" /> Reset & Start New</button></div></div> : jobStatus?.status === 'FAILED' ? <div className="text-center py-8"><h3 className="text-xl font-bold text-rose-400">Transformation Failed</h3><p className="text-sm text-gray-400 mt-2 mb-6">{jobStatus.error_message || 'The GPU worker could not complete the job.'}</p><button onClick={resetStudio} className="px-6 py-3 rounded-xl bg-studio-accent text-white font-semibold">Reset & Try Again</button></div> : <div className="text-center py-10"><Loader2 className="w-10 h-10 animate-spin text-studio-accent mx-auto mb-5" /><h3 className="text-xl font-bold text-white">Processing Your {targetMedia?.analysis?.media_type === 'video' ? 'Video' : 'Image'}</h3><p className="text-sm text-gray-400 mt-2">{jobStatus?.current_stage || 'Waiting for the GPU worker...'}</p><div className="max-w-md mx-auto mt-6 h-2 rounded-full bg-studio-800 overflow-hidden"><div className="h-full bg-studio-accent transition-all" style={{ width: `${Math.min(100, Math.max(0, Number(jobStatus?.progress_percent || 0)))}%` }} /></div><p className="text-xs text-gray-500 mt-2">{Number(jobStatus?.progress_percent || 0).toFixed(0)}%</p></div>}
          </section>}
        </div>
      </main>
    </div>
  );
}
