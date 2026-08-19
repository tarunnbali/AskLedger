import ChatWidget from "../components/ChatWidget";

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-4 bg-gradient-to-br from-[#121212] to-[#1a1a1a]">
      {/* Background Content */}
      <div className="w-full max-w-4xl flex flex-col items-center justify-center text-center animate-fade-in pb-12">
        <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-4">
          Ask<span className="gradient-text">Ledger</span>
        </h1>
        <p className="text-gray-400 text-lg md:text-xl max-w-2xl mb-8">
          Ask your subscription and billing data questions in plain English. Click the chat button on the bottom right to start querying naturally.
        </p>
        <div className="glass px-6 py-4 rounded-xl flex items-center justify-center gap-4 text-sm text-gray-400">
           <div className="flex items-center gap-2">
             <div className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_10px_currentColor]"></div>
             System Online
           </div>
           <div>|</div>
           <div>v0.1.0-beta</div>
        </div>
      </div>

      <footer className="fixed bottom-4 left-0 w-full text-center text-gray-500 text-xs sm:text-sm">
        <p>Built with Next.js, FastAPI, and Postgres</p>
      </footer>

      {/* Floating Chat Widget */}
      <ChatWidget />
    </main>
  );
}