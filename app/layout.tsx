import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'DineScope | Food Marketplace Intelligence',
  description: 'See demand. Understand customers. Prioritize growth.',
  icons: {
    icon: [{ url: '/favicon.png', type: 'image/png' }],
    shortcut: '/favicon.png',
    apple: '/favicon.png',
  },
  openGraph: {
    title: 'DineScope | Food Marketplace Intelligence',
    description: 'An interactive decision-intelligence platform for Product and Growth teams.',
    images: [{ url: '/og.png', width: 1200, height: 630, alt: 'DineScope food marketplace intelligence platform' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'DineScope | Food Marketplace Intelligence',
    description: 'See demand. Understand customers. Prioritize growth.',
    images: ['/og.png'],
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
