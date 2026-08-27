import React from 'react';
import Navigation from '../components/Navigation';

export default function HomePage() {
  return (
    <div className="flex bg-studio-950 text-gray-100 min-h-screen">
      <Navigation />
      <main className="flex-1 p-8 flex flex-col justify-center items-center text-center">
        <h1 className="text-4xl font-bold text-white mb-3">Private AI Face Studio</h1>
        <p className="text-gray-400 mb-8 max-w-md">Private, consent-based, zero-cost AI video and image transformation studio.</p>
        <a href="/generate" className="bg-indigo-600 hover:bg-indigo-500 text-white px-8 py-3 rounded-lg font-semibold transition">
          Launch Studio Pipeline
        </a>
      </main>
    </div>
  );
}
