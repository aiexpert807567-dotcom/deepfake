'use client';
import React, { useState, useEffect } from 'react';
import Navigation from '../../components/Navigation';
import { Upload, Sparkles, CheckCircle2, Film, Image as ImageIcon, Sliders, ShieldCheck, AlertCircle, ArrowRight, RefreshCw, Cpu, Layers } from 'lucide-react';
import { apiClient } from '../../lib/api';

export default function GenerateStudioPage() {
  const [step, setStep] = useState(1);
  const [targetFile, setTargetFile] = useState<File | null>(null);
  const [targetMedia, setTargetMedia] = useState<any>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [detectedFaces, setDetectedFaces] = useState<any[]>([]);
  const [selectedFaceId, setSelectedFaceId] = useState('');
  const [references, setReferences] = useState<any[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [activeJob, setActiveJob] = useState<any>(null);
  const [jobStatus, setJobStatus] = useState<any>(null);
  const [workerOnline, setWorkerOnline] = useState(false);

  useEffect(() => {
    if (!activeJob?.job_id) return;
    const pollJob = async () => {
      try {
        const res = await apiClient.get(`/api/jobs/${activeJob.job_id}`);
        setJobStatus(res.data);
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
        setWorkerOnline(res.data.online);
      } catch {}
    };
    checkWorker();
    const interval = setInterval(checkWorker, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleTargetUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.[0]) return;
    const file = e.target.files[0];
    setTargetFile(file);
    setIsUploading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await apiClient.post('/api/media/upload-target', formData);
      setTargetMedia(res.data);

      const faceRes = await apiClient.get(`/api/media/${res.data.media_id}/detect-faces`);
      setDetectedFaces(faceRes.data.faces);
      setStep(2);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Target upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleReferenceUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return;
    const files = Array.from(e.target.files);

    for (const file of files) {
      const formData = new FormData();
      formData.append('file', file);
      try {
        const res = await apiClient.post('/api/media/upload-reference', formData);
        setReferences(prev => [...prev, res.data]);
      } catch (err) {
        console.error(err);
      }
    }
  };

  const handleStartGeneration = async () => {
    setIsGenerating(true);
    try {
      const chosenFace = detectedFaces.find(f => f.id === selectedFaceId);
      const res = await apiClient.post('/api/jobs', {
        media_type: targetMedia?.analysis?.media_type || 'image',
        target_media_id: targetMedia?.media_id,
        selected_face_id: selectedFaceId,
        target_face_bbox: chosenFace?.bbox || null,
        reference_ids: references.map(r => r.reference_id),
        quality: 'maximum',
        face_restoration: true,
        temporal_stabilization: true,
        color_matching: true,
        lighting_matching: true,
        occlusion_handling: true,
        super_resolution: true,
      });
      setActiveJob(res.data);
      setStep(5);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Job initialization failed');
      setIsGenerating(false);
    }
  };

  return (
    <div className="flex flex-col md:flex-row bg-studio-950 text-gray-100 min-h-screen">
      <Navigation />

      <main className="flex-1 p-4 sm:p-6 lg:p-10 overflow-y-auto">
        <div className="max-w-4xl mx-auto mb-6 sm:mb-10">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
            <div>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">AI Studio Generator</h2>
              <p className="text-sm text-gray-400 mt-0.5">Step-by-Step Multi-Reference Face Transformation</p>
            </div>
            <div className={`self-start sm:self-auto px-4 py-2 rounded-xl text-xs font-bold border flex items-center gap-2 ${
              workerOnline ? 'bg-emerald-950/80 text-emerald-300 border-emerald-700' : 'bg-rose-950/80 text-rose-300 border-rose-800'
            }`}>
              <span className={`w-2 h-2 rounded-full ${workerOnline ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
              {workerOnline ? 'GPU WORKER ONLINE' : 'GPU WORKER OFFLINE'}
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 bg-studio-900 p-2 rounded-2xl border border-studio-700/60">
            {[
              { num: 1, label: 'Upload Target' },
              { num: 2, label: 'Select Target Face' },
              { num: 3, label: 'References (3-8)' },
              { num: 4, label: 'Studio Settings' },
            ].map(s => (
              <div
                key={s.num}
                className={`py-2 px-2 sm:px-3 rounded-xl text-center text-[11px] sm:text-xs font-semibold transition ${
                  step === s.num
                    ? 'bg-studio-accent text-white shadow-md shadow-indigo-600/30'
                    : step > s.num
                    ? 'text-emerald-400 bg-studio-850'
                    : 'text-gray-500'
                }`}
              >
                Step {s.num}: {s.label}
              </div>
            ))}
          </div>
        </div>

        <div className="max-w-4xl mx-auto">
          {step === 1 && (
            <div className="bg-studio-900/90 border border-studio-700/70 rounded-3xl p-6 sm:p-10 text-center shadow-2xl backdrop-blur">
              <div className="w-16 h-16 rounded-2xl bg-studio-accent/20 text-studio-accent flex items-center justify-center mx-auto mb-5 border border-studio-accent/30 shadow-lg">
                <Upload className="w-8 h-8" />
              </div>
              <h3 className="text-xl sm:text-2xl font-bold text-white mb-2">Upload Target Media</h3>
              <p className="text-sm text-gray-400 max-w-md mx-auto mb-8">
                Upload the video (up to 30s) or image containing the face you wish to transform. Other people in the scene will remain unchanged.
              </p>

              <label className="w-full sm:w-auto justify-center bg-gradient-to-r from-studio-accent to-indigo-600 hover:from-indigo-500 hover:to-indigo-600 text-white px-6 sm:px-8 py-4 rounded-xl cursor-pointer font-semibold shadow-xl shadow-indigo-500/25 transition transform hover:-translate-y-0.5 inline-flex items-center gap-3">
                {isUploading ? <RefreshCw className="w-5 h-5 animate-spin shrink-0" /> : <Film className="w-5 h-5 shrink-0" />}
                <span className="text-sm sm:text-base">{isUploading ? 'Analyzing Video & Detecting Faces...' : 'Select Target Video or Image'}</span>
                <input type="file" onChange={handleTargetUpload} className="hidden" accept="image/*,video/*" />
              </label>
            </div>
          )}

          {step === 2 && (
            <div className="bg-studio-900/90 border border-studio-700/70 rounded-3xl p-5 sm:p-8 shadow-2xl">
              <h3 className="text-lg sm:text-xl font-bold text-white mb-2">Step 2: Select Exact Target Face</h3>
              <p className="text-sm text-gray-400 mb-6">
                Multiple faces detected. Select strictly <strong className="text-white">one</strong> face. Other people will stay completely untouched.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
                {detectedFaces.map(face => (
                  <div
                    key={face.id}
                    onClick={() => setSelectedFaceId(face.id)}
                    className={`p-5 rounded-2xl border cursor-pointer transition-all duration-200 ${
                      selectedFaceId === face.id
                        ? 'border-studio-accent bg-studio-accent/15 shadow-lg shadow-indigo-500/20'
                        : 'border-studio-700 bg-studio-800/80 hover:border-gray-500'
                    }`}
                  >
                    <div className="flex items-center gap-4">
                      {face.thumbnail && (
                        <img
                          src={`data:image/jpeg;base64,${face.thumbnail}`}
                          alt={face.label}
                          className="w-16 h-16 rounded-xl object-cover border border-studio-700 shrink-0"
                        />
                      )}
                      <div className="min-w-0">
                        <div className="flex items-center justify-between mb-1 gap-2">
                          <span className="font-bold text-white text-base">{face.label}</span>
                          {selectedFaceId === face.id && <CheckCircle2 className="w-5 h-5 text-studio-accent shrink-0" />}
                        </div>
                        <p className="text-xs text-gray-400">Detection Confidence: {(face.confidence * 100).toFixed(0)}%</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex justify-between items-center pt-4 border-t border-studio-800">
                <button onClick={() => setStep(1)} className="text-sm text-gray-400 hover:text-white">Back</button>
                <button
                  disabled={!selectedFaceId}
                  onClick={() => setStep(3)}
                  className="bg-studio-accent hover:bg-indigo-600 disabled:opacity-50 text-white px-5 sm:px-7 py-3 rounded-xl font-semibold transition text-sm sm:text-base"
                >
                  Confirm Face & Continue
                </button>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="bg-studio-900/90 border border-studio-700/70 rounded-3xl p-5 sm:p-8 shadow-2xl">
              <h3 className="text-lg sm:text-xl font-bold text-white mb-2">Step 3: Reference Photos (3–8 Recommended)</h3>
              <p className="text-sm text-gray-400 mb-6">
                Upload clear photos of the new identity (Front, 3/4 angles, profile) for best multi-angle consistency.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
                {references.map((ref, idx) => (
                  <div key={idx} className="p-4 bg-studio-800/80 rounded-xl border border-studio-700 flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-white truncate">{ref.filename}</p>
                      <p className="text-xs text-emerald-400 font-mono">Score: {ref.analysis.quality_score}% • {ref.analysis.estimated_angle}</p>
                    </div>
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  </div>
                ))}
              </div>

              <label className="w-full sm:w-auto justify-center bg-studio-800 hover:bg-studio-750 text-gray-200 border border-studio-700 px-5 py-3 rounded-xl cursor-pointer text-sm font-semibold transition inline-flex items-center gap-2 mb-8">
                + Upload Reference Photos
                <input type="file" multiple onChange={handleReferenceUpload} className="hidden" accept="image/*" />
              </label>

              <div className="flex justify-between items-center pt-4 border-t border-studio-800">
                <button onClick={() => setStep(2)} className="text-sm text-gray-400 hover:text-white">Back</button>
                <button
                  onClick={() => setStep(4)}
                  className="bg-studio-accent hover:bg-indigo-600 text-white px-5 sm:px-7 py-3 rounded-xl font-semibold transition text-sm sm:text-base"
                >
                  Proceed to Settings
                </button>
              </div>
            </div>
          )}

          {step === 4 && (
            <div className="bg-studio-900/90 border border-studio-700/70 rounded-3xl p-5 sm:p-8 shadow-2xl">
              <h3 className="text-lg sm:text-xl font-bold text-white mb-4">Step 4: Quality & Pipeline Settings</h3>

              <div className="space-y-3 bg-studio-850 p-5 sm:p-6 rounded-2xl border border-studio-700/60 mb-8 text-sm">
                <div className="flex justify-between py-1 border-b border-studio-800 gap-2"><span>Quality Preset:</span><span className="font-bold text-white text-right">Maximum (Quality &gt; Speed)</span></div>
                <div className="flex justify-between py-1 border-b border-studio-800 gap-2"><span>GFPGAN Face Detail Restoration:</span><span className="font-semibold text-emerald-400 shrink-0">ENABLED</span></div>
                <div className="flex justify-between py-1 border-b border-studio-800 gap-2"><span>Temporal Stabilization (EMA Filter):</span><span className="font-semibold text-emerald-400 shrink-0">ENABLED</span></div>
                <div className="flex justify-between py-1 border-b border-studio-800 gap-2"><span>Reinhard LAB Color & Lighting Matching:</span><span className="font-semibold text-emerald-400 shrink-0">ENABLED</span></div>
                <div className="flex justify-between py-1 gap-2"><span>FFmpeg Audio Track Sync:</span><span className="font-semibold text-emerald-400 shrink-0">ENABLED</span></div>
              </div>

              <button
                onClick={handleStartGeneration}
                className="w-full flex items-center justify-center gap-3 bg-gradient-to-r from-studio-accent to-indigo-600 hover:from-indigo-500 hover:to-indigo-600 text-white py-4 rounded-xl font-bold shadow-xl shadow-indigo-500/25 transition text-sm sm:text-base"
              >
                <Sparkles className="w-5 h-5" /> Start GPU Transformation
              </button>
            </div>
          )}

          {step === 5 && (
            <div className="bg-studio-900/90 border border-studio-700/70 rounded-3xl p-6 sm:p-10 text-center shadow-2xl">
              {jobStatus?.status === 'COMPLETED' ? (
                <>
                  <div className="w-16 h-16 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto mb-6">
                    <CheckCircle2 className="w-9 h-9" />
                  </div>
                  <h3 className="text-xl sm:text-2xl font-bold text-white mb-2">Transformation Complete</h3>
                  <p className="text-sm text-gray-400 mb-6">Your result is ready.</p>
                  {jobStatus.result_url && (
                    <a
                      href={`${apiClient.defaults.baseURL}${jobStatus.result_url}`}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-2 bg-studio-accent hover:bg-indigo-600 text-white px-6 py-3 rounded-xl font-semibold transition"
                    >
                      View / Download Result
                    </a>
                  )}
                </>
              ) : jobStatus?.status === 'FAILED' ? (
                <>
                  <div className="w-16 h-16 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center mx-auto mb-6">
                    <AlertCircle className="w-9 h-9" />
                  </div>
                  <h3 className="text-xl sm:text-2xl font-bold text-white mb-2">Transformation Failed</h3>
                  <p className="text-sm text-rose-400 mb-6 break-words">{jobStatus.error_message || 'An unknown error occurred.'}</p>
                </>
              ) : (
                <>
                  <div className="animate-spin w-14 h-14 border-4 border-studio-accent border-t-transparent rounded-full mx-auto mb-6 shadow-lg" />
                  <h3 className="text-xl sm:text-2xl font-bold text-white mb-2">GPU Transformation in Progress</h3>
                  <p className="text-sm text-gray-400 mb-6">{jobStatus?.current_stage || 'Processing on Kaggle NVIDIA T4 GPU node...'}</p>
                  <div className="w-full bg-studio-800 rounded-full h-3 mb-3 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-studio-accent to-cyan-400 h-full rounded-full transition-all duration-500"
                      style={{ width: `${jobStatus?.progress_percent ?? 5}%` }}
                    />
                  </div>
                </>
              )}
              <p className="text-xs text-indigo-400 font-mono mt-4 break-all">Job ID: {activeJob?.job_id}</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
