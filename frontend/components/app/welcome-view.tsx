"use client";

import React from "react";
import { Button } from "@/components/livekit/button";

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ...divProps
}: React.ComponentProps<"div"> & WelcomeViewProps) => {
  return (
    <div
      {...divProps}
      className="min-h-screen w-full flex flex-col items-center justify-center px-6 py-10 bg-gradient-to-b from-slate-950 via-slate-900 to-black"
    >
      {/* Hero */}
      <div className="max-w-3xl text-center space-y-3">
        <p className="text-[11px] tracking-[0.3em] uppercase text-emerald-400">
          ACP-Lite · Voice Commerce
        </p>

        <h1 className="text-3xl md:text-4xl font-semibold tracking-tight text-slate-50">
          Talk to Your E-Commerce Agent
        </h1>

        <p className="text-sm md:text-base text-slate-300">
          Browse products, compare options, and place demo orders using only your voice.
          I’ll handle the catalog, pricing, and order creation behind the scenes.
        </p>
      </div>

      {/* Feature cards */}
      <div className="mt-8 grid gap-4 w-full max-w-4xl md:grid-cols-3">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 text-left shadow-sm">
          <h2 className="text-sm font-semibold text-slate-50 mb-1">
            Browse with your voice
          </h2>
          <p className="text-xs text-slate-300">
            Ask for mugs, t-shirts, hoodies, or accessories. Filter by price or color
            and I’ll list matching items with names and prices.
          </p>
          <p className="text-[11px] text-emerald-400 mt-2">
            Try: “Show me black hoodies under 1600.”
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 text-left shadow-sm">
          <h2 className="text-sm font-semibold text-slate-50 mb-1">
            Order like a pro
          </h2>
          <p className="text-xs text-slate-300">
            Pick items by number and size. I’ll create an ACP-style order object
            with product IDs, quantity, and total in INR.
          </p>
          <p className="text-[11px] text-emerald-400 mt-2">
            Try: “I’ll buy the second hoodie in size L.”
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 text-left shadow-sm">
          <h2 className="text-sm font-semibold text-slate-50 mb-1">
            Check your last order
          </h2>
          <p className="text-xs text-slate-300">
            I store orders in a simple backend structure, so you can ask what you
            just bought and I’ll read back the latest summary.
          </p>
          <p className="text-[11px] text-emerald-400 mt-2">
            Try: “What did I just buy?”
          </p>
        </div>
      </div>

      {/* Start button */}
      <Button
        size="lg"
        className="mt-8 px-10 py-4 rounded-2xl bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-semibold shadow-lg"
        onClick={onStartCall}
      >
        {startButtonText || "Start Voice Shopping"}
      </Button>

      <p className="mt-3 text-[11px] text-slate-500">
        Demo only · No real payments or deliveries · JSON orders on the backend
      </p>
    </div>
  );
};

// Also provide default export to be extra safe
export default WelcomeView;
