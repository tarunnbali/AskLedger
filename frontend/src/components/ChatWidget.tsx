"use client";

import { useState } from "react";
import { MessageSquare, X, Maximize2, Minimize2 } from "lucide-react";
import ChatInterface from "@/components/ChatInterface";
import Login from "@/components/Login";

interface ChatWidgetProps {
  // Optional external control so a landing-page CTA can open the widget.
  isOpen?: boolean;
  onOpenChange?: (open: boolean) => void;
  // Optional: pre-fill and auto-submit a demo login when opened from the
  // landing page's demo account cards.
  autoLoginUsername?: string | null;
  onAutoLoginConsumed?: () => void;
  // Optional: a question to ask as soon as the user is signed in. If nobody is
  // signed in yet, the widget signs in as the first demo tenant.
  pendingQuestion?: string | null;
  onPendingQuestionSent?: () => void;
}

const DEFAULT_DEMO_USER = "alice";

export default function ChatWidget({
  isOpen: isOpenProp,
  onOpenChange,
  autoLoginUsername,
  onAutoLoginConsumed,
  pendingQuestion,
  onPendingQuestionSent,
}: ChatWidgetProps) {
  const [internalOpen, setInternalOpen] = useState(false);
  const isOpen = isOpenProp ?? internalOpen;
  const setIsOpen = (open: boolean) => {
    setInternalOpen(open);
    onOpenChange?.(open);
  };

  const [isFullscreen, setIsFullscreen] = useState(false);
  const [sessionToken, setSessionToken] = useState<string | null>(null);
  const [currentUser, setCurrentUser] = useState<string | null>(null);

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-50 flex cursor-pointer items-center justify-center rounded-full bg-ink p-4 text-paper shadow-[0_12px_30px_-10px_rgba(22,24,29,0.6)] transition-colors hover:bg-ledger animate-fade-in group"
        aria-label="Open AskLedger chat"
      >
        <MessageSquare size={28} className="transition-transform group-hover:scale-110" />
      </button>
    );
  }

  const containerClasses = isFullscreen
    ? "fixed inset-0 w-full h-full z-50 bg-paper flex flex-col transition-all duration-300"
    : "fixed bottom-6 right-6 w-[90vw] sm:w-[450px] h-[600px] max-h-[85vh] z-50 flex flex-col rounded-2xl overflow-hidden border border-rule bg-paper shadow-[0_24px_60px_-16px_rgba(22,24,29,0.35)] transition-all duration-300 animate-fade-in";

  return (
    <div className={containerClasses}>
      {/* Widget Header */}
      <div className="flex items-center justify-between border-b border-rule p-4">
        <div className="flex items-center gap-2">
          <div className="flex flex-col leading-tight">
            <span className="text-lg font-semibold text-ink">Ask<span className="text-ledger">Ledger</span></span>
            <span className="-mt-0.5 font-mono text-[10px] text-graphite">Billing analytics assistant</span>
          </div>
          <div className={`w-2 h-2 rounded-full ml-1 ${sessionToken ? 'bg-ledger' : 'bg-graphite/40'}`}></div>
          {sessionToken && (
            <span className="ml-1 max-w-[100px] truncate font-mono text-xs text-graphite">
              {currentUser}
            </span>
          )}
        </div>

        <div className="flex items-center gap-1">
          {sessionToken && (
            <button
              onClick={() => { setSessionToken(null); setCurrentUser(null); }}
              className="mr-1 rounded px-2 py-1 text-xs text-graphite transition-colors hover:bg-paper-2 hover:text-ink"
              title="Sign out"
            >
              Sign out
            </button>
          )}
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="rounded-md p-1.5 text-graphite transition-colors hover:bg-paper-2 hover:text-ink"
            title={isFullscreen ? "Minimize" : "Maximize"}
          >
            {isFullscreen ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
          </button>
          <button
            onClick={() => setIsOpen(false)}
            className="rounded-md p-1.5 text-graphite transition-colors hover:bg-paper-2 hover:text-ink"
            title="Close"
          >
            <X size={18} />
          </button>
        </div>
      </div>

      {/* Widget Body */}
      <div className="flex-1 overflow-hidden relative">
        {!sessionToken ? (
          <div className="h-full overflow-y-auto px-4 pb-4">
             {pendingQuestion && (
               <div className="mx-auto mt-4 max-w-sm rounded-lg border border-ledger/25 bg-ledger-soft px-3 py-2 text-xs text-ledger">
                 Signing you in as a demo tenant to ask: &ldquo;{pendingQuestion}&rdquo;
               </div>
             )}
             <Login
               onLoginSuccess={(token, user) => {
                 setSessionToken(token);
                 setCurrentUser(user);
               }}
               autoLogin={autoLoginUsername ?? (pendingQuestion ? DEFAULT_DEMO_USER : null)}
               onAutoLoginConsumed={onAutoLoginConsumed}
             />
          </div>
        ) : (
          <div className="h-full animate-fade-in px-4 pb-4 flex flex-col">
            <ChatInterface
              token={sessionToken}
              initialQuestion={pendingQuestion}
              onInitialQuestionSent={onPendingQuestionSent}
            />
          </div>
        )}
      </div>
    </div>
  );
}
