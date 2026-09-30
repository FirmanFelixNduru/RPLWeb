'use client';

import React from 'react';
import {
  Check,
  Flame,
  Camera,
  Smartphone,
  Briefcase,
  Gamepad,
  Palette,
  Code,
  Coffee,
  PenTool,
  BookOpen,
  Monitor,
  Activity,
  Mic,
  Headphones,
  Crosshair,
  Map,
  Heart,
  MessageSquare,
  Watch,
  Compass,
} from 'lucide-react';

export const SCENARIO_MAPPING = {
  smartphone: [
    { id: 'sp_game', scenarioKey: 'gaming', title: 'Gaming Berat', desc: 'Performa GPU tinggi & refresh rate mulus', icon: Flame },
    { id: 'sp_foto', scenarioKey: 'photography', title: 'Fotografi & Kamera', desc: 'Sensor jernih, zoom optik, & akurasi warna', icon: Camera },
    { id: 'sp_sosmed', scenarioKey: 'social_media', title: 'Sosmed & Hiburan', desc: 'Layar cerah, baterai awet, navigasi lancar', icon: Smartphone },
    { id: 'sp_bisnis', scenarioKey: 'business', title: 'Bisnis & Multitasking', desc: 'Keamanan data, memori besar, & performa stabil', icon: Briefcase },
  ],
  laptop: [
    { id: 'lp_game', scenarioKey: 'gaming', title: 'Gaming & 3D Render', desc: 'Kartu grafis diskrit & sistem pendingin maksimal', icon: Gamepad },
    { id: 'lp_kreatif', scenarioKey: 'content_creation', title: 'Video & Desain Grafis', desc: 'Akurasi warna sRGB tinggi & RAM besar', icon: Palette },
    { id: 'lp_coding', scenarioKey: 'productivity', title: 'Programming / IT', desc: 'Prosesor multi-core kuat & keyboard nyaman', icon: Code },
    { id: 'lp_office', scenarioKey: 'business', title: 'Office & Mobilitas', desc: 'Desain tipis, ringan, & baterai tahan seharian', icon: Coffee },
  ],
  tablet: [
    { id: 'tb_gambar', scenarioKey: 'content_creation', title: 'Ilustrasi & Desain', desc: 'Dukungan stylus presisi & layar resolusi tinggi', icon: PenTool },
    { id: 'tb_catatan', scenarioKey: 'student', title: 'Kuliah & Catatan', desc: 'Ringan untuk dibawa, baterai awet untuk kelas', icon: BookOpen },
    { id: 'tb_nonton', scenarioKey: 'multimedia', title: 'Nonton & Hiburan', desc: 'Speaker stereo mantap & layar OLED/AMOLED', icon: Monitor },
    { id: 'tb_kerja', scenarioKey: 'productivity', title: 'Pengganti Laptop', desc: 'Dukungan keyboard eksternal & mode desktop', icon: Briefcase },
  ],
  tws: [
    { id: 'au_olahraga', scenarioKey: 'fitness', title: 'Olahraga & Gym', desc: 'Tahan air/keringat (IP Rating) & fitting aman di telinga', icon: Activity },
    { id: 'au_rapat', scenarioKey: 'business', title: 'Kerja & Rapat Online', desc: 'Mikrofon jernih dengan peredam bising (ANC/ENC)', icon: Mic },
    { id: 'au_musik', scenarioKey: 'multimedia', title: 'Musik / Audiophile', desc: 'Kualitas audio Hi-Res & soundstage luas', icon: Headphones },
    { id: 'au_game', scenarioKey: 'gaming', title: 'Mobile Gaming', desc: 'Mode latensi sangat rendah (low latency)', icon: Crosshair },
  ],
  smartwatch: [
    { id: 'sw_olahraga', scenarioKey: 'fitness', title: 'Lari & Olahraga Outdoor', desc: 'GPS presisi & pelacakan rute akurat', icon: Map },
    { id: 'sw_sehat', scenarioKey: 'fitness', title: 'Pantau Kesehatan', desc: 'Sensor detak jantung, SpO2, & pemantauan tidur', icon: Heart },
    { id: 'sw_notif', scenarioKey: 'casual', title: 'Ekstensi Smartphone', desc: 'Balas pesan cepat & terima telepon dari pergelangan', icon: MessageSquare },
    { id: 'sw_gaya', scenarioKey: 'casual', title: 'Fashion & Gaya Hidup', desc: 'Desain premium & kustomisasi watch face beragam', icon: Watch },
  ],
};

export default function StepScenario({ category = 'smartphone', selectedScenarios = [], onToggleScenario }) {
  const normalizedCategory = category?.toLowerCase();
  const currentScenarios = SCENARIO_MAPPING[normalizedCategory] || SCENARIO_MAPPING.smartphone;

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div className="text-center">
        <span className="text-xs font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
          Langkah 3 dari 4
        </span>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white mt-1">
          Bagaimana Skenario Penggunaan Utama Anda?
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
          Pilihan skenario berikut disesuaikan khusus untuk kategori{' '}
          <strong className="capitalize text-indigo-600 dark:text-indigo-400">{category}</strong>.
          Pilih 1 atau lebih skenario harian Anda.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {currentScenarios.map((sc) => {
          const Icon = sc.icon || Compass;
          const isSelected = selectedScenarios.includes(sc.id) || selectedScenarios.includes(sc.scenarioKey);

          return (
            <button
              type="button"
              key={sc.id}
              onClick={() => onToggleScenario(sc.id)}
              aria-pressed={isSelected}
              className={`relative w-full p-5 rounded-2xl border-2 text-left cursor-pointer transition-all duration-200 flex flex-col justify-between group ${
                isSelected
                  ? 'border-indigo-600 dark:border-indigo-400 bg-indigo-50/70 dark:bg-indigo-950/40 shadow-md shadow-indigo-500/10'
                  : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-indigo-300'
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div
                  className={`w-10 h-10 rounded-xl flex items-center justify-center transition-colors ${
                    isSelected
                      ? 'bg-indigo-600 text-white'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 group-hover:bg-indigo-50'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                </div>

                <div
                  className={`w-5 h-5 rounded-full border flex items-center justify-center transition-colors ${
                    isSelected
                      ? 'bg-indigo-600 border-indigo-600 text-white'
                      : 'border-slate-300 dark:border-slate-700'
                  }`}
                >
                  {isSelected && <Check className="w-3 h-3" />}
                </div>
              </div>

              <div className="mt-3">
                <h3 className="text-sm sm:text-base font-bold text-slate-900 dark:text-white">
                  {sc.title}
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                  {sc.desc}
                </p>
              </div>
            </button>
          );
        })}
      </div>

      {selectedScenarios.length > 0 && (
        <div className="text-center text-xs font-semibold text-indigo-600 dark:text-indigo-400">
          ✓ {selectedScenarios.length} skenario terpilih untuk penyesuaian bobot scoring
        </div>
      )}
    </div>
  );
}
