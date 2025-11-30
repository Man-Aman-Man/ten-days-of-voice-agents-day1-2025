"use client";

import React, { useState } from "react";
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
  const [name, setName] = useState("");

  const handleStart = () => {
    // For challenge requirements we show a Name field in UI,
    // but the backend will still learn the name from what the user says.
    // You can also encourage them to say their name in the first line.
    onStartCall();
  };

  return (
    <div
      {...divProps}
      className="min-h-screen w-full flex flex-col items-center justify-center px-6 py-10
                 bg-gradient-to-b from-slate-950 via-slate-900 to-black text-slate-50"
    >
      {/* Header */}
      <div className="max-w-2xl text-center space-y-3 mb-8">
        <p className="text-[11px] tracking-[0.35em] uppercase text-amber-400">
          Live from the Studio · Improv Battle
        </p>
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
          Step into the Voice Improv Arena
        </h1>
        <p className="text-sm md:text-base text-slate-300">
          You are the contestant. The AI is the high-energy host. Act out absurd scenes,
          get live reactions, and see what kind of improviser you are.
        </p>
      </div>

      {/* Join card */}
      <div className="w-full max-w-md bg-slate-900/70 border border-slate-800 rounded-3xl p-6 shadow-lg">
        <h2 className="text-lg font-semibold mb-3">Join as a contestant</h2>

        <label className="flex flex-col gap-2 text-left mb-4">
          <span className="text-xs font-medium text-slate-300">
            Name (what should the host call you?)
          </span>
          <input
            type="text"
            placeholder="Aman, Disha, The Chaos Wizard..."
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-2xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm
                       outline-none focus:border-amber-400 focus:ring-1 focus:ring-amber-400"
          />
          <span className="text-[11px] text-slate-500">
            Tip: even if you type it here, say your name once after the call starts so the host can lock it in.
          </span>
        </label>

        <Button
          onClick={handleStart}
          className="w-full mt-1 py-3 rounded-2xl bg-amber-500 hover:bg-amber-600 text-slate-950 font-semibold"
        >
          {startButtonText || "Start Improv Battle"}
        </Button>
      </div>

      {/* Footer tips */}
      <div className="mt-6 max-w-xl text-center text-[11px] md:text-xs text-slate-400 space-y-1">
        <p>
          Say things like: “Okay, end scene” when you’re done with a scenario.
        </p>
        <p>
          You can also say “stop game” or “end show” at any time to wrap up early.
        </p>
      </div>
    </div>
  );
};

export default WelcomeView;
