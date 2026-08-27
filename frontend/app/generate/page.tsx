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
  const [workerOnline, setWorkerOnline] = useState(false);

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
      const res = await apiClient.post('/api/jobs', {
        media_type: targetMedia?.analysis?.media_type || 'image',
        target_media_id: targetMedia?.media_id,
        selected_face_id: selectedFaceId,
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
    <div className="flex bg-studio-950 text-gray-100 min-h-screen">
      <Navigation />

      <main className="flex-1 p-10 overflow-y-auto">
        {/* Wizard Header Progress Bar */}
        <div className="max-w-4xl mx-auto mb-10">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-3xl font-extrabold text-white tracking-tight">AI Studio Generator</h2>
              <p className="text-sm text-gray-400 mt-0.5">Step-by-Step Multi-Reference Face Transformation</p>
            </div>
            <div className={`px-4 py-2 rounded-xl text-xs font-bold border flex items-center gap-2 ${
              workerOnline ? 'bg-emerald-950/80 text-emerald-300 border-emerald-700' : 'bg-rose-950/80 text-rose-300 border-rose-800'
            }`}>
              <span className={`w-2 h-2 rounded-full ${workerOnline ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
              {workerOnline ? 'GPU WORKER ONLINE' : 'GPU WORKER OFFLINE'}
            </div>
          </div>

          {/* Stepper Indicator */}
          <div className="grid grid-cols-4 gap-2 bg-studio-900 p-2 rounded-2xl border border-studio-700/60">
            {[
              { num: 1, label: 'Upload Target' },
              { num: 2, label: 'Select Target Face' },
              { num: 3, label: 'References (3-8)' },
              { num: 4, label: 'Studio Settings' },
            ].map(s => (
              <div
                key={s.num}
                className={`py-2 px-3 rounded-xl text-center text-xs font-semibold transition ${
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
          {/* STEP 1: Upload Target */}
          {step === 1 && (
            <div className="bg-studio-900/90 border border-studio-700/70 rounded-3xl p-10 text-center shadow-2xl backdrop-blur">
              <div className="w-16 h-16 rounded-2xl bg-studio-accent/20 text-studio-accent flex items-center justify-center mx-auto mb-5 border border-studio-accent/30 shadow-lg">
                <Upload className="w-8 h-8" />
              </div>
              <h3 className="text-2xl font-bold text-white mb-2">Upload Target Media</h3>
              <p className="text-sm text-gray-400 max-w-md mx-auto mb-8">
                Upload the video (up to 30s) or image containing the face you wish to transform. Other people in the scene will remain unchanged.
              </p>

              <label className="bg-gradient-to-r from-studio-accent to-indigo-600 hover:from-indigo-500 hover:to-indigo-600 text-white px-8 py-4 rounded-xl cursor-pointer font-semibold shadow-xl shadow-indigo-500/25 transition transform hover:-translate-y-0.5 inline-flex items-center gap-3">
                {isUploading ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Film className="w-5 h-5" />}
                {isUploading ? 'Analyzing Video & Detecting Faces...' : 'Select Target Video or Image'}
                <input type="file" onChange={handleTargetUpload} className="hidden" accept="image/*,video/*" />
              </label>
            </div>
          )}

          {/* STEP 2: Select Target Face */}
          {step === 2 && (
            <div className="bg-studio-900/90 border border-studio-700/70 rounded-3xl p-8 shadow-2xl">
              <h3 className="text-xl font-bold text-white mb-2">Step 2: Select Exact Target Face</h3>
              <p className="text-sm text-gray-400 mb-6">
                Multiple faces detected. Select strictly <strong className="text-white">one</strong> face. Other people will stay completely untouched.
              </p>

              <div className="grid grid-cols-2 gap-4 mb-8">
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
                  className="bg-studio-accent hover:bg-indigo-600 disabled:opacity-50 text-white px-7 py-3 rounded-xl font-semibold transition"
                >
                  Confirm Face & Continue
                </button>
              </div>
            </div>
          )}

          {/* STEP 3: Multi-Reference Upload */}
          {step === 3 && (
            <div className="bg-studio-900/90 border border-studio-700/70 rounded-3xl p-8 shadow-2xl">
              <h3 className="text-xl font-bold text-white mb-2">Step 3: Reference Photos (3–8 Recommended)</h3>
              <p className="text-sm text-gray-400 mb-6">
                Upload clear photos of the new identity (Front, 3/4 angles, profile) for best multi-angle consistency.
              </p>

              <div className="grid grid-cols-2 gap-4 mb-6">
                {references.map((ref, idx) => (
                  <div key={idx} className="p-4 bg-studio-800/80 rounded-xl border border-studio-700 flex items-center justify-between">
                    <div>
                      <p className="text-sm font-semibold text-white">{ref.filename}</p>
                      <p className="text-xs text-emerald-400 font-mono">Score: {ref.analysis.quality_score}% • {ref.analysis.estimated_angle}</p>
                    </div>
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  </div>
                ))}
              </div>

              <label className="bg-studio-800 hover:bg-studio-750 text-gray-200 border border-studio-700 px-5 py-3 rounded-xl cursor-pointer text-sm font-semibold transition inline-flex items-center gap-2 mb-8">
                + Upload Reference Photos
                <input type="file" multiple onChange={handleReferenceUpload} className="hidden" accept="image/*" />
              </label>

              <div className="flex justify-between items-center pt-4 border-t border-studio-800">
                <button onClick={() => setStep(2)} className="text-sm text-gray-400 hover:text-white">Back</button>
                <button
                  onClick={() => setStep(4)}
                  className="bg-studio-accent hover:bg-indigo-600 text-white px-7 py-3 rounded-xl font-semibold transition"
                >
                  Proceed to Settings
                </button>
              </div>
            </div>
          )}

          {/* STEP 4: Review Settings */}
          {step === 4 && (
            <div className="bg-studio-900/90 border border-studio-700/70 rounded-3xl p-8 shadow-2xl">
              <h3 className="text-xl font-bold text-white mb-4">Step 4: Quality & Pipeline Settings</h3>

              <div className="space-y-3 bg-studio-850 p-6 rounded-2xl border border-studio-700/60 mb-8 text-sm">
                <div className="flex justify-between py-1 border-b border-studio-800"><span>Quality Preset:</span><span className="font-bold text-white">Maximum (Quality &gt; Speed)</span></div>
                <div className="flex justify-between py-1 border-b border-studio-800"><span>GFPGAN Face Detail Restoration:</span><span className="font-semibold text-emerald-400">ENABLED</span></div>
                <div className="flex justify-between py-1 border-b border-studio-800"><span>Temporal Stabilization (EMA Filter):</span><span className="font-semibold text-emerald-400">ENABLED</span></div>
                <div className="flex justify-between py-1 border-b border-studio-800"><span>Reinhard LAB Color & Lighting Matching:</span><span className="font-semibold text-emerald-400">ENABLED</span></div>
                <div className="flex justify-between py-1"><span>FFmpeg Audio Track Sync:</span><span className="font-semibold text-emerald-400">ENABLED</span></div>
              </div>

              <button
                onClick={handleStartGeneration}
                className="w-full flex items-center justify-center gap-3 bg-gradient-to-r from-studio-accent to-indigo-600 hover:from-indigo-500 hover:to-indigo-600 text-white py-4 rounded-xl font-bold shadow-xl shadow-indigo-500/25 transition text-base"
              >
                <Sparkles className="w-5 h-5" /> Start GPU Transformation
              </button>
            </div>
          )}

          {/* STEP 5: Active Processing Monitor */}
          {step === 5 && (
            <div className="bg-studio-900/90 border border-studio-700/70 rounded-3xl p-10 text-center shadow-2xl">
              <div className="animate-spin w-14 h-14 border-4 border-studio-accent border-t-transparent rounded-full mx-auto mb-6 shadow-lg" />
              <h3 className="text-2xl font-bold text-white mb-2">GPU Transformation in Progress</h3>
              <p className="text-sm text-gray-400 mb-6">Processing on Kaggle NVIDIA T4 GPU node...</p>
              <div className="w-full bg-studio-800 rounded-full h-3 mb-3 overflow-hidden">
                <div className="bg-gradient-to-r from-studio-accent to-cyan-400 h-full rounded-full animate-pulse" style={{ width: '65%' }} />
              </div>
              <p className="text-xs text-indigo-400 font-mono">Job ID: {activeJob?.job_id}</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
