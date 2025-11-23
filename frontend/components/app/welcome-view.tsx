"use client";

import React from "react";
import { Button } from "@/components/livekit/button";

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({ startButtonText, onStartCall }: WelcomeViewProps) => {
  return (
    <div className="flex min-h-[calc(100vh-80px)] flex-col items-center justify-center px-6 py-10 bg-[#0F1714] bg-gradient-to-br from-[#0F1714] via-[#143A2D] to-black text-[#F5F0E6]">
      <div className="max-w-xl text-center space-y-6">
        <p className="text-xs tracking-[0.3em] uppercase text-[#C59D5F]/80">
          BLUE TOKAI · MURF FALCON
        </p>

        <h1 className="text-3xl md:text-4xl font-semibold tracking-tight">
          Your Blue Tokai AI Barista
        </h1>

        <p className="text-sm md:text-base text-[#F5F0E6]/80">
          Welcome to your virtual Blue Tokai café, powered by the fastest TTS API, Murf Falcon.
          Just talk to place your coffee order by voice, and I will ask follow-up questions,
          confirm every detail, and save your order.
        </p>

        <div className="rounded-xl border border-[#C59D5F]/30 bg-black/30 px-4 py-3 text-xs md:text-sm text-left text-[#F5F0E6]/80">
          Try saying:
          <br />
          “I&apos;d like a medium latte with oat milk and an extra shot. My name is Aman.”
        </div>

        <div className="pt-2">
          <Button
            variant="primary"
            size="lg"
            onClick={onStartCall}
            className="mt-3 w-64 rounded-full font-mono bg-[#C59D5F] text-black hover:bg-[#d2ad6a]"
          >
            {startButtonText || "Start order with AI Barista"}
          </Button>
        </div>

        <p className="text-[11px] text-[#F5F0E6]/50">
          Built for the Murf AI Voice Agent Challenge · #MurfAIVoiceAgentsChallenge
        </p>
      </div>
    </div>
  );
};

export default WelcomeView;
