'use client';

import { Button } from "@/components/livekit/button";

interface WelcomeViewProps {
  onStartCall: () => void;
}

export const WelcomeView = ({ onStartCall }: WelcomeViewProps) => {
  return (
    <section className="min-h-screen flex flex-col items-center justify-center px-6 text-center bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950">
      <div className="max-w-xl space-y-4">
        <p className="text-xs tracking-[0.3em] uppercase text-slate-400">
          SafeBank · Fraud Alert
        </p>

        <h1 className="text-3xl md:text-4xl font-semibold tracking-tight text-slate-50">
          Fraud Alert Voice Assistant
        </h1>

        <p className="text-sm md:text-base text-slate-300">
          This is a demo-only SafeBank fraud department agent. It walks through a suspicious
          transaction, verifies identity using safe questions, and marks the case as safe or
          fraudulent in a sample database.
        </p>
      </div>

      <div className="mt-8 flex flex-col md:flex-row gap-4 max-w-3xl w-full text-left">
        <div className="flex-1 rounded-xl border border-slate-700/70 bg-slate-900/70 p-4">
          <h2 className="text-sm font-semibold text-slate-50 mb-1">Safe Verification</h2>
          <p className="text-xs text-slate-300">
            Uses only non-sensitive info from the case file. Never asks for full card number, PIN,
            passwords, or OTPs.
          </p>
        </div>
        <div className="flex-1 rounded-xl border border-slate-700/70 bg-slate-900/70 p-4">
          <h2 className="text-sm font-semibold text-slate-50 mb-1">Case Review</h2>
          <p className="text-xs text-slate-300">
            Reads out merchant, amount, masked card, time, and location from a fake fraud database.
          </p>
        </div>
        <div className="flex-1 rounded-xl border border-slate-700/70 bg-slate-900/70 p-4">
          <h2 className="text-sm font-semibold text-slate-50 mb-1">Status Update</h2>
          <p className="text-xs text-slate-300">
            Marks the case as confirmed safe, fraudulent, or verification failed and writes back to JSON.
          </p>
        </div>
      </div>

      <Button
        size="lg"
        className="mt-8 px-10 py-4 rounded-2xl bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-semibold shadow-lg"
        onClick={onStartCall}
      >
        Start Fraud Alert Demo
      </Button>

      <p className="text-[11px] text-slate-400 mt-3">
        Demo only · No real banking data · Powered by Murf Falcon TTS & LiveKit
      </p>
    </section>
  );
};

export default WelcomeView;
