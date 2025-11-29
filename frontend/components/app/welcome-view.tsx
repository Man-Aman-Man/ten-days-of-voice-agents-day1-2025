'use client';

import React from "react";
import { Button } from "@/components/livekit/button";

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({ startButtonText, onStartCall }: WelcomeViewProps) => {
  return (
    <section className="min-h-screen flex flex-col items-center justify-center px-6 text-center bg-gradient-to-b from-slate-950 via-slate-900 to-black">
      <div className="max-w-xl space-y-3">
        <p className="text-xs tracking-[0.32em] uppercase text-emerald-400">
          Greyford Outbreak · Voice Adventure
        </p>

        <h1 className="text-3xl md:text-4xl font-semibold tracking-tight text-slate-50">
          The Last Cure in Greyford
        </h1>

        <p className="text-sm md:text-base text-slate-300">
          The city has fallen to the infected. You’re one of the last survivors with a lead on a possible cure
          hidden in an abandoned hospital lab. The Game Master will narrate the world. You answer with your voice.
        </p>
      </div>

      <div className="mt-8 flex flex-col md:flex-row gap-4 max-w-3xl w-full text-left">
        <div className="flex-1 rounded-2xl border border-slate-800 bg-slate-900/80 p-4">
          <h2 className="text-sm font-semibold text-slate-50 mb-1">Survive</h2>
          <p className="text-xs text-slate-300">
            Move through alleys, rooftops, and ruins while avoiding the infected and scavenging supplies.
          </p>
        </div>
        <div className="flex-1 rounded-2xl border border-slate-800 bg-slate-900/80 p-4">
          <h2 className="text-sm font-semibold text-slate-50 mb-1">Decide</h2>
          <p className="text-xs text-slate-300">
            Every choice matters: who to trust, where to hide, when to run. The GM reacts to your decisions.
          </p>
        </div>
        <div className="flex-1 rounded-2xl border border-slate-800 bg-slate-900/80 p-4">
          <h2 className="text-sm font-semibold text-slate-50 mb-1">Find the Cure</h2>
          <p className="text-xs text-slate-300">
            Your goal: reach the old hospital lab and uncover any clue that might help humanity fight back.
          </p>
        </div>
      </div>

      <Button
        size="lg"
        className="mt-8 px-10 py-4 rounded-2xl bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-semibold shadow-lg"
        onClick={onStartCall}
      >
        {startButtonText || "Enter the Wasteland"}
      </Button>

      <p className="text-[11px] text-slate-500 mt-3">
        Voice-only story · Say things like “look around”, “search the room”, or “sneak past them”.
      </p>
    </section>
  );
};

export default WelcomeView;
