'use client';
import React, { useState } from 'react';
import Navigation from '../../components/Navigation';
import { Upload, Sparkles } from 'lucide-react';
import { apiClient } from '../../lib/api';

export default function GeneratePage() {
  const [step, setStep] = useState(1);
  const [targetMedia, setTargetMedia] = useState<any>(null);
  const [detectedFaces, setDetectedFaces] = useState<any[]>([]);
  const [selectedFaceId, setSelectedFaceId] = useState('');
  const [activeJob, setActiveJob] = useState<any>(null);

  const handleUploadTarget = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.[0]) return;
    const fd = new FormData();
    fd.append('file', e.target.files[0]);
    try {
      const res = await apiClient.post('/api/media/upload-target', fd);
      setTargetMedia(res.data);
      const faceRes = await apiClient.get(`/api/media/${res.data.media_id}/detect-faces`);
      setDetectedFaces(faceRes.data.faces);
      setStep(2);
    } catch (err) { alert('Upload failed'); }
  };

  const handleStart = async () => {
    try {
      const res = await apiClient.post('/api/jobs', {
        media_type: targetMedia?.analysis?.media_type || 'image',
        target_media_id: targetMedia?.media_id,
        selected_face_id: selectedFaceId,
        reference_ids: [],
      });
      setActiveJob(res.data);
      setStep(4);
    } catch (e) { alert('Job initialization failed'); }
  };

  return (
    <div className="flex min-h-screen bg-studio-950 text-gray-100">
      <Navigation />
      <main className="flex-1 p-8">
        <h2 className="text-2xl font-bold text-white mb-2">Transform Media</h2>
        <p className="text-sm text-gray-400 mb-8">11-Step Face Studio Pipeline</p>

        {step === 1 && (
          <div className="max-w-2xl bg-studio-900 border border-studio-700/60 p-8 rounded-xl text-center">
            <Upload className="w-12 h-12 text-studio-accent mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Upload Target Media</h3>
            <label className="bg-studio-accent hover:bg-studio-accentHover text-white px-6 py-2.5 rounded-lg cursor-pointer inline-block font-medium">
              Select Video or Photo
              <input type="file" onChange={handleUploadTarget} className="hidden" accept="image/*,video/*" />
            </label>
          </div>
        )}

        {step === 2 && (
          <div className="max-w-2xl bg-studio-900 border border-studio-700/60 p-8 rounded-xl">
            <h3 className="text-lg font-semibold mb-4">Select Target Face</h3>
            <div className="grid grid-cols-2 gap-4 mb-6">
              {detectedFaces.map(f => (
                <div key={f.id} onClick={() => setSelectedFaceId(f.id)} className={`p-4 rounded-lg border cursor-pointer ${selectedFaceId === f.id ? 'border-studio-accent bg-studio-accent/10' : 'border-studio-700 bg-studio-800'}`}>
                  <p className="font-semibold text-white">{f.label}</p>
                  <p className="text-xs text-gray-400">Confidence: {(f.confidence * 100).toFixed(0)}%</p>
                </div>
              ))}
            </div>
            <button disabled={!selectedFaceId} onClick={() => setStep(3)} className="bg-studio-accent text-white px-6 py-2 rounded-lg">Confirm Face</button>
          </div>
        )}

        {step === 3 && (
          <div className="max-w-2xl bg-studio-900 border border-studio-700/60 p-8 rounded-xl">
            <h3 className="text-lg font-semibold mb-4">Review Pipeline Settings</h3>
            <button onClick={handleStart} className="w-full flex items-center justify-center gap-2 bg-studio-accent text-white py-3 rounded-lg font-semibold">
              <Sparkles className="w-5 h-5" /> Start GPU Transformation
            </button>
          </div>
        )}

        {step === 4 && (
          <div className="max-w-2xl bg-studio-900 border border-studio-700/60 p-8 rounded-xl text-center">
            <div className="animate-spin w-10 h-10 border-4 border-studio-accent border-t-transparent rounded-full mx-auto mb-4" />
            <h3 className="text-lg font-semibold">Processing on Free GPU Worker</h3>
            <p className="text-xs text-gray-400 mt-2">Job ID: {activeJob?.job_id}</p>
          </div>
        )}
      </main>
    </div>
  );
}
