'use client';

import React, { useState } from 'react';
import { Sparkles, ArrowRight, ArrowLeft, RotateCcw, CheckCircle2, Loader2 } from 'lucide-react';
import { scoreRecommendations } from '@/lib/api';
import StepCategory from '@/components/wizard/StepCategory';
import StepBudget from '@/components/wizard/StepBudget';
import StepScenario from '@/components/wizard/StepScenario';
import StepPriority from '@/components/wizard/StepPriority';
import WizardResults from '@/components/wizard/WizardResults';

export default function WizardPage() {
  const [currentStep, setCurrentStep] = useState(1);
  const [category, setCategory] = useState('smartphone');
  const [budgetMin, setBudgetMin] = useState(3000000);
  const [budgetMax, setBudgetMax] = useState(12000000);
  const [scenarios, setScenarios] = useState(['gaming', 'productivity']);
  const [priorities, setPriorities] = useState({
    performance: 4,
    camera: 3,
    battery: 4,
    display: 3,
    build_quality: 3,
    value: 4,
  });

  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);

  // Toggle scenario selection
  const handleToggleScenario = (id) => {
    if (scenarios.includes(id)) {
      setScenarios(scenarios.filter((s) => s !== id));
    } else {
      setScenarios([...scenarios, id]);
    }
  };

  // Change priority weight (1-5)
  const handleChangePriority = (key, val) => {
    setPriorities((prev) => ({ ...prev, [key]: val }));
  };

  // Next / Prev Navigation
  const handleNext = () => {
    if (currentStep < 4) {
      setCurrentStep(currentStep + 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
      handleSubmit();
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  // Submit preferences to Scoring Engine
  const handleSubmit = async () => {
    setLoading(true);
    try {
      const payload = {
        category,
        budget_min: budgetMin,
        budget_max: budgetMax,
        scenarios,
        priorities,
      };

      const res = await scoreRecommendations(payload);
      setResults(res.results || []);
      setCurrentStep(5); // Show results
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      console.error('Failed to calculate scores:', err);
      alert('Gagal menghitung skor rekomendasi. Silakan coba lagi.');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setResults(null);
    setCurrentStep(1);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const stepLabels = [
    'Pilih Kategori',
    'Atur Budget',
    'Skenario Pakai',
    'Prioritas Trade-off',
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 space-y-8">
      {/* Step Progress Stepper (Only show in steps 1-4) */}
      {currentStep <= 4 && (
        <div className="max-w-2xl mx-auto">
          <div className="flex items-center justify-between relative">
            {/* Connecting line */}
            <div className="absolute left-0 top-1/2 -translate-y-1/2 h-1 bg-slate-200 dark:bg-slate-800 w-full -z-0" />
            <div
              className="absolute left-0 top-1/2 -translate-y-1/2 h-1 bg-indigo-600 transition-all duration-300 -z-0"
              style={{ width: `${((currentStep - 1) / 3) * 100}%` }}
            />

            {stepLabels.map((label, idx) => {
              const stepNum = idx + 1;
              const isCompleted = stepNum < currentStep;
              const isCurrent = stepNum === currentStep;

              return (
                <div key={idx} className="flex flex-col items-center relative z-10">
                  <div
                    className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs transition-all ${
                      isCompleted
                        ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                        : isCurrent
                        ? 'bg-white dark:bg-slate-900 border-2 border-indigo-600 text-indigo-600 dark:text-indigo-400 ring-4 ring-indigo-100 dark:ring-indigo-950 font-black'
                        : 'bg-slate-200 dark:bg-slate-800 text-slate-500'
                    }`}
                  >
                    {isCompleted ? <CheckCircle2 className="w-5 h-5" /> : stepNum}
                  </div>
                  <span
                    className={`text-[11px] mt-1.5 font-semibold hidden sm:block ${
                      isCurrent
                        ? 'text-indigo-600 dark:text-indigo-400 font-bold'
                        : 'text-slate-400'
                    }`}
                  >
                    {label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Main Step Body */}
      <div className="min-h-[420px]">
        {loading ? (
          <div className="text-center py-24 space-y-4">
            <Loader2 className="w-12 h-12 text-indigo-600 animate-spin mx-auto" />
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">
              Menghitung Algoritma Dynamic Scoring Engine...
            </h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Memproses normalisasi multi-kriteria dan menyesuaikan pembobotan skenario Anda.
            </p>
          </div>
        ) : (
          <>
            {currentStep === 1 && (
              <StepCategory
                selectedCategory={category}
                onSelect={(cat) => setCategory(cat)}
              />
            )}

            {currentStep === 2 && (
              <StepBudget
                category={category}
                budgetMin={budgetMin}
                budgetMax={budgetMax}
                onChangeMin={setBudgetMin}
                onChangeMax={setBudgetMax}
              />
            )}

            {currentStep === 3 && (
              <StepScenario
                selectedScenarios={scenarios}
                onToggleScenario={handleToggleScenario}
              />
            )}

            {currentStep === 4 && (
              <StepPriority
                priorities={priorities}
                onChangePriority={handleChangePriority}
              />
            )}

            {currentStep === 5 && results && (
              <WizardResults
                results={results}
                onReset={handleReset}
                wizardInput={{ category, budget_min: budgetMin, budget_max: budgetMax, scenarios, priorities }}
              />
            )}
          </>
        )}
      </div>

      {/* Navigation Buttons (Only in steps 1-4) */}
      {currentStep <= 4 && !loading && (
        <div className="max-w-2xl mx-auto flex items-center justify-between pt-6 border-t border-slate-200 dark:border-slate-800">
          <button
            type="button"
            onClick={handleBack}
            disabled={currentStep === 1}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 text-xs font-bold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-30 disabled:pointer-events-none transition-all"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Kembali</span>
          </button>

          <button
            type="button"
            onClick={handleNext}
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-xs sm:text-sm font-bold shadow-lg shadow-indigo-600/25 transition-all active:scale-95"
          >
            <span>{currentStep === 4 ? 'Hitung Skor Rekomendasi' : 'Lanjutkan'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
}
