import './globals.css';
import React from 'react';

export const metadata = {
  title: 'Private AI Face Studio',
  description: 'Zero-Cost Personal AI Media Studio',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-studio-950 text-gray-100 min-h-screen antialiased">
        {children}
      </body>
    </html>
  );
}
