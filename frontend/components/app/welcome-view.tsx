"use client";

import { Button } from "@/components/livekit/button";

interface WelcomeViewProps {
  onStartCall: () => void;
}

export const WelcomeView = ({ onStartCall }: WelcomeViewProps) => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] p-6 text-center space-y-8">

      <h1 className="text-4xl font-bold text-foreground tracking-tight">
        Your Personal Study Coach
      </h1>

      <p className="text-lg text-muted-foreground max-w-lg">
        Learn smarter. Test your knowledge. Teach back to master any subject.
      </p>

      <Button
        size="lg"
        className="px-10 py-6 rounded-xl font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-lg transition"
        onClick={onStartCall}
      >
        Start Learning
      </Button>
    </div>
  );
};

export default WelcomeView;
