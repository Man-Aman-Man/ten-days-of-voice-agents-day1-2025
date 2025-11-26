'use client';

import React from "react";
import { Button } from "@/components/livekit/button";

interface WelcomeViewProps {
  onStartCall: () => void;
}

export const WelcomeView = ({ onStartCall }: WelcomeViewProps) => {
  return (
    <section className="min-h-screen flex flex-col items-center justify-center px-6 text-center bg-gradient-to-b from-white via-slate-50 to-slate-100">
      <img
        src="/freshworks.png"
        alt="Freshworks hero"
        className="w-48 h-48 object-contain mb-6"
      />

      <h1 className="text-4xl font-bold text-foreground mb-2">Freshworks Voice SDR</h1>
      <p className="text-lg text-muted-foreground max-w-2xl mb-6">
        Welcome! I’m Alex from Freshworks. I can answer basic product questions, discuss pricing, and capture lead details so our sales team can follow up.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-4xl w-full mb-6">
        <div className="p-4 rounded-xl border bg-white/80 shadow-sm">
          <h3 className="text-sm font-semibold mb-2">Product</h3>
          <p className="text-xs text-muted-foreground">Customer engagement, ITSM, CRM — simple, integrated SaaS apps.</p>
        </div>
        <div className="p-4 rounded-xl border bg-white/80 shadow-sm">
          <h3 className="text-sm font-semibold mb-2">Pricing</h3>
          <p className="text-xs text-muted-foreground">Tiered pricing and trials — exact plans vary by product.</p>
        </div>
        <div className="p-4 rounded-xl border bg-white/80 shadow-sm">
          <h3 className="text-sm font-semibold mb-2">Lead Capture</h3>
          <p className="text-xs text-muted-foreground">I’ll collect name, email, company, role, use case, team size, and timeline.</p>
        </div>
      </div>

      <Button
        size="lg"
        className="px-10 py-4 rounded-2xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold"
        onClick={onStartCall}
      >
        Talk to Alex (Start Call)
      </Button>

      <p className="text-[12px] mt-4 text-muted-foreground">Powered by Murf Falcon TTS • LiveKit Agents</p>
    </section>
  );
};

export default WelcomeView;
