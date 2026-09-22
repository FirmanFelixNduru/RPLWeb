import './globals.css';
import { ThemeProvider } from '@/context/ThemeContext';
import { CompareProvider } from '@/context/CompareContext';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import FloatingDock from '@/components/layout/FloatingDock';
import ProductModal from '@/components/product/ProductModal';

export const viewport = {
  width: 'device-width',
  initialScale: 1,
};

export const metadata = {
  title: 'CompareBuy — Platform Cerdas Perbandingan & Rekomendasi Gadget Teknologi',
  description:
    'Temukan gadget paling worth it dengan Smart Recommendation Wizard, Weighted Dynamic Scoring Engine, dan perbandingan harga live marketplace Tokopedia, Shopee, serta Lazada.',
  keywords: [
    'perbandingan gadget',
    'rekomendasi smartphone',
    'laptop terbaik mahasiswa',
    'fastapi microservice',
    'spesifikasi hp indonesia',
    'harga live tokopedia shopee',
  ],
  authors: [{ name: 'CompareBuy Engineering Team' }],
};

export default function RootLayout({ children }) {
  return (
    <html lang="id" suppressHydrationWarning>
      <body className="min-h-screen flex flex-col antialiased selection:bg-indigo-500 selection:text-white">
        <ThemeProvider>
          <CompareProvider>
            {/* Global Navigation */}
            <Navbar />

            {/* Main Page Content */}
            <main className="flex-1">{children}</main>

            {/* Floating Comparison Dock */}
            <FloatingDock />

            {/* Product Detail Modal */}
            <ProductModal />

            {/* Global Footer */}
            <Footer />
          </CompareProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
