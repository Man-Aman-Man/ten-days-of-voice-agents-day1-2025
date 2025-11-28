'use client';

import React from "react";
import { Button } from "@/components/livekit/button";

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({ startButtonText, onStartCall }: WelcomeViewProps) => {
  return (
    <section className="min-h-screen flex flex-col items-center justify-center px-6 text-center bg-slate-950">
      <div className="max-w-xl space-y-3">
        <p className="text-xs tracking-[0.28em] uppercase text-emerald-400">
          SwiftCart · Voice Groceries
        </p>

        <h1 className="text-3xl md:text-4xl font-semibold tracking-tight text-slate-50">
          Hands-free Food & Grocery Ordering
        </h1>

        <p className="text-sm md:text-base text-slate-300">
          I’m the SwiftCart voice assistant. Tell me what you’d like — specific items, quantities,
          or even just “ingredients for pasta for two” — and I’ll build your cart step by step.
        </p>
      </div>

      <div className="mt-8 flex flex-col md:flex-row gap-4 max-w-3xl w-full text-left">
        <div className="flex-1 rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
          <h2 className="text-sm font-semibold text-slate-50 mb-1">Cart Control</h2>
          <p className="text-xs text-slate-300">
            Add, remove, or update quantities with simple voice commands and I’ll keep your cart in sync.
          </p>
        </div>
        <div className="flex-1 rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
          <h2 className="text-sm font-semibold text-slate-50 mb-1">Recipe Bundles</h2>
          <p className="text-xs text-slate-300">
            High-level requests like “ingredients for a sandwich” automatically add multiple items together.
          </p>
        </div>
      </div>

      <Button
        size="lg"
        className="mt-8 px-10 py-4 rounded-2xl bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-semibold shadow-lg"
        onClick={onStartCall}
      >
        {startButtonText || "Start Voice Session"}
      </Button>

      <p className="text-[11px] text-slate-400 mt-3">
        Sandbox only · Uses a small demo catalog powered by JSON
      </p>
    </section>
  );
};

export default WelcomeView;
