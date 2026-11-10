/**
 * ⚡ FLOWORK OS — NEXT.JS 14/15 AGENTIC SEO & SCHEMA CONFIGURATION
 * Example drop-in metadata and JSON-LD script for Next.js App Router (layout.tsx or page.tsx)
 */

import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Flowork OS — The Sovereign AI Desktop Operating System',
  description: 'Flowork OS is an AI-native desktop operating system with autonomous subagents, Landlock LSM security, and sub-millisecond reflex routing.',
  alternates: {
    canonical: 'https://floworkos.org',
  },
  openGraph: {
    title: 'Flowork OS — Sovereign AI Desktop',
    description: 'Empowering autonomous development and sub-millisecond agent swarms.',
    url: 'https://floworkos.org',
    siteName: 'Flowork OS',
    images: [
      {
        url: 'https://floworkos.org/og-image.png',
        width: 1200,
        height: 630,
        alt: 'Flowork OS Sovereign Desktop Interface',
      },
    ],
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Flowork OS — Sovereign AI Desktop',
    description: 'Autonomous AI Operating System with 0.60 Glass HUD and Landlock LSM security.',
    images: ['https://floworkos.org/og-image.png'],
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: 'Flowork OS',
    operatingSystem: 'Linux (Kernel 7.3.0 Rust)',
    applicationCategory: 'OperatingSystem',
    description: 'Sovereign AI-native desktop operating system.',
    offers: {
      '@type': 'Offer',
      price: '0',
      priceCurrency: 'USD',
    },
  };

  return (
    <html lang="en">
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
