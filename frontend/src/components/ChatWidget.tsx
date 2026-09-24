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
}

export default function ChatWidget({
  isOpen: isOpenProp,
  onOpenChange,
  autoLoginUsername,
  onAutoLoginConsumed,
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
        className="fixed bottom-6 right-6 p-4 rounded-full bg-blue-600 text-white shadow-[0_0_20px_rgba(37,99,235,0.4)] hover:shadow-[0_0_30px_rgba(37,99,235,0.6)] hover:bg-blue-500 hover:scale-105 transition-all z-50 flex items-center justify-center cursor-pointer animate-fade-in group"
        aria-label="Open AskLedger chat"
      >
        <MessageSquare size={28} className="transition-transform group-hover:scale-110" />
      </button>
    );
  }

  const containerClasses = isFullscreen
    ? "fixed inset-0 w-full h-full z-50 bg-[#121212] flex flex-col transition-all duration-300"
    : "fixed bottom-6 right-6 w-[90vw] sm:w-[450px] h-[600px] max-h-[85vh] z-50 flex flex-col rounded-2xl shadow-2xl overflow-hidden glass-panel transition-all duration-300 animate-fade-in";

  return (
    <div className={containerClasses}>
      {/* Widget Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/10 bg-black/40 backdrop-blur-md">
        <div className="flex items-center gap-2">
          <div className="flex flex-col leading-tight">
            <span className="text-lg font-bold gradient-text">AskLedger</span>
            <span className="text-[10px] text-gray-500 -mt-1">Billing Analytics Assistant</span>
          </div>
          <div className={`w-2 h-2 rounded-full ml-1 shadow-[0_0_10px_currentColor] ${sessionToken ? 'bg-green-500 text-green-500' : 'bg-red-500 text-red-500'}`}></div>
          {sessionToken && (
            <span className="text-xs text-gray-300 font-medium ml-1 truncate max-w-[100px]">
              {currentUser}
            </span>
          )}
        </div>

        <div className="flex items-center gap-1">
          {sessionToken && (
            <button
              onClick={() => { setSessionToken(null); setCurrentUser(null); }}
              className="px-2 py-1 text-xs text-gray-400 hover:text-white hover:bg-white/10 rounded transition-colors mr-1"
              title="Sign out"
            >
              Sign out
            </button>
          )}
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-1.5 text-gray-400 hover:text-white hover:bg-white/10 rounded-md transition-colors"
            title={isFullscreen ? "Minimize" : "Maximize"}
          >
            {isFullscreen ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
          </button>
          <button
            onClick={() => setIsOpen(false)}
            className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-white/10 rounded-md transition-colors"
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
             <Login
               onLoginSuccess={(token, user) => {
                 setSessionToken(token);
                 setCurrentUser(user);
               }}
               autoLogin={autoLoginUsername}
               onAutoLoginConsumed={onAutoLoginConsumed}
             />
          </div>
        ) : (
          <div className="h-full animate-fade-in px-4 pb-4 flex flex-col">
            <ChatInterface token={sessionToken} />
          </div>
        )}
      </div>
    </div>
  );
}
