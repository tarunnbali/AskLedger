"use client";

import { useEffect, useState } from "react";
import { warmUpBackend } from "@/lib/api";
import ChatWidget from "../components/ChatWidget";
import Hero from "../components/landing/Hero";
import { FeatureCards, Pipeline, StackMarquee } from "../components/landing/Sections";
import { DemoTenants, QuestionCards, TrustAndCta } from "../components/landing/QuestionsAndMore";

export default function Home() {
  const [chatOpen, setChatOpen] = useState(false);
  const [demoUser, setDemoUser] = useState<string | null>(null);
  const [pendingQuestion, setPendingQuestion] = useState<string | null>(null);

  // Start waking the free-tier backend as soon as someone lands on the page
  useEffect(() => {
    warmUpBackend();
  }, []);

  const openChat = () => setChatOpen(true);

  const openAsDemoUser = (username: string) => {
    setDemoUser(username);
    setChatOpen(true);
  };

  const askQuestion = (question: string) => {
    setPendingQuestion(question);
    setChatOpen(true);
  };

  return (
    <main className="relative min-h-screen overflow-x-hidden bg-paper">
      <Hero onTryDemo={openChat} />
      <StackMarquee />
      <FeatureCards />
      <Pipeline />
      <QuestionCards onAsk={askQuestion} />
      <DemoTenants onPick={openAsDemoUser} />
      <TrustAndCta onTryDemo={openChat} />

      <ChatWidget
        isOpen={chatOpen}
        onOpenChange={setChatOpen}
        autoLoginUsername={demoUser}
        onAutoLoginConsumed={() => setDemoUser(null)}
        pendingQuestion={pendingQuestion}
        onPendingQuestionSent={() => setPendingQuestion(null)}
      />
    </main>
  );
}
