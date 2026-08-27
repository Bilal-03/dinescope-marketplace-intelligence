import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'PlateLens | Food Delivery Marketplace Intelligence',
  description: 'An independent decision-support workspace for food-delivery Product and Growth teams.',
  openGraph: {
    title: 'PlateLens | Food Delivery Marketplace Intelligence',
    description: 'Audited customer growth, retention and marketplace decision intelligence.',
    images: [{ url: '/og.png', width: 1731, height: 909, alt: 'PlateLens food delivery marketplace intelligence' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'PlateLens | Food Delivery Marketplace Intelligence',
    description: 'Audited customer growth, retention and marketplace decision intelligence.',
    images: ['/og.png'],
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
