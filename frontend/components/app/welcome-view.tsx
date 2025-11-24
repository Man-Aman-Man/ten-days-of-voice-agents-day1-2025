"use client";

import React from "react";
import { Button } from "@/components/livekit/button";

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({ startButtonText, onStartCall }: WelcomeViewProps) => {
  return (
    <div className="flex min-h-[calc(100vh-80px)] flex-col items-center justify-center px-8 py-10 bg-[#F6F7FB] bg-gradient-to-br from-[#B4F288] via-[#E4ECF4] to-[#88F2E6] text-[#10212B]">
      <div className="max-w-xl text-center space-y-6">
        <p className="text-xs tracking-[0.3em] uppercase text-[#4B6A88]/80">
          SteadyMind · Daily Check-In
        </p>

        <h1 className="text-3xl md:text-4xl font-semibold tracking-tight">
          Your Everyday Wellness Voice Companion
        </h1>

        <p className="text-sm md:text-base text-[#10212B]/75">
          I am a calm, grounded companion that checks in with you about your mood, energy
          and simple goals for the day. I&apos;m not a doctor or therapist; I just help you
          reflect, set small intentions, and remember how things have been going over time.
        </p>

        <div className="rounded-xl border border-[#4B6A88]/20 bg-white/80 px-4 py-3 text-xs md:text-sm text-left text-[#10212B]/80 shadow-sm">
          Try saying:
          <br />
          “I’m feeling a bit overwhelmed but I want to finish two tasks and take a break.
          How should I plan my day?”
        </div>

        <div className="pt-2">
          <Button
            variant="primary"
            size="lg"
            onClick={onStartCall}
            className="mt-3 w-72 rounded-full font-medium bg-[#4B6A88] text-white hover:bg-[#3b556d]"
          >
            {startButtonText || "Start today’s wellness check-in"}
          </Button>
        </div>

        <p className="text-[11px] text-[#10212B]/55">
          Built for the Murf AI Voice Agent Challenge · Powered by Murf Falcon TTS
        </p>
      </div>
    </div>
  );
};

export default WelcomeView;
