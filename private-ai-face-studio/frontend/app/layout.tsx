import React from 'react';
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-studio-950 text-gray-100 min-h-screen">{children}</body>
    </html>
  );
}
