import { Bot, User, AlertCircle, Database, HelpCircle } from "lucide-react";

interface MultiResult {
  question: string;
  sql_query: string | null;
  results: any[] | null;
  explanation: string;
}

interface ChatMessageProps {
  role: "user" | "assistant" | "error";
  text: string;
  sql?: string | null;
  results?: any[] | null;
  multiResults?: MultiResult[] | null;
}

function ResultTable({ results }: { results: any[] }) {
  if (!results || results.length === 0) return null;
  return (
    <div className="glass rounded-xl overflow-hidden border border-white/5 shadow-inner">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-gray-300">
          <thead className="text-xs uppercase bg-black/40 text-gray-400 border-b border-white/10">
            <tr>
              {Object.keys(results[0]).map((key) => (
                <th key={key} scope="col" className="px-4 py-3 font-semibold whitespace-nowrap">
                  {key.replace(/_/g, " ")}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {results.map((row, rowIndex) => (
              <tr key={rowIndex} className="border-b border-white/5 hover:bg-white/5 transition-colors last:border-0">
                {Object.values(row).map((val: any, colIndex) => (
                  <td key={colIndex} className="px-4 py-3 whitespace-nowrap">
                    {val !== null ? String(val) : <span className="text-gray-600 italic">null</span>}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="px-4 py-2 bg-black/20 text-xs text-gray-500 border-t border-white/5 flex justify-between">
        <span>{results.length} row{results.length !== 1 ? "s" : ""}</span>
      </div>
    </div>
  );
}

export default function ChatMessage({ role, text, sql, results, multiResults }: ChatMessageProps) {
  const isUser = role === "user";
  const isError = role === "error";

  return (
    <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"} animate-fade-in`}>
      <div className={`flex flex-col max-w-[85%] md:max-w-[75%] space-y-2 ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={`flex items-start space-x-3 p-4 rounded-2xl shadow-sm
            ${isUser
              ? "bg-blue-600 text-white rounded-tr-sm"
              : isError
                ? "bg-red-900/40 border border-red-500/30 text-red-200 rounded-tl-sm glass"
                : "glass bg-[#1a1a1a]/80 text-gray-200 rounded-tl-sm border border-white/10"
            }
          `}
        >
          {/* Avatar Icon */}
          <div className={`flex-shrink-0 mt-1 w-8 h-8 flex items-center justify-center rounded-full
            ${isUser ? "bg-white/20" : isError ? "bg-red-500/20" : "bg-blue-500/20 text-blue-400"}
          `}>
            {isUser ? <User size={18} /> : isError ? <AlertCircle size={18} className="text-red-400" /> : <Bot size={18} />}
          </div>

          {/* Message Content */}
          <div className="flex-1 overflow-hidden">
            <p className="text-sm md:text-base leading-relaxed break-words whitespace-pre-wrap">{text}</p>
          </div>
        </div>

        {/* SQL Accordion (single query) */}
        {!isUser && !isError && sql && (
          <div className="w-full mt-2 pl-4 pr-1">
            <details className="group glass rounded-xl border-l-[3px] border-l-blue-500 overflow-hidden cursor-pointer">
              <summary className="flex items-center space-x-2 p-3 text-sm text-gray-300 hover:bg-white/5 transition-colors font-medium">
                <Database size={16} className="text-blue-400" />
                <span>View Generated SQL</span>
              </summary>
              <div className="p-4 bg-black/40 border-t border-white/5 overflow-x-auto text-xs font-mono text-gray-400 leading-relaxed">
                <pre><code>{sql}</code></pre>
              </div>
            </details>
          </div>
        )}

        {/* Single query result table */}
        {!isUser && !isError && results && results.length > 0 && (
          <div className="w-full mt-2 pl-4 pr-1 animate-fade-in" style={{ animationDelay: "200ms" }}>
            <ResultTable results={results} />
          </div>
        )}

        {/* Multi-query sub-results */}
        {!isUser && !isError && multiResults && multiResults.length > 0 && (
          <div className="w-full mt-2 pl-4 pr-1 space-y-3 animate-fade-in" style={{ animationDelay: "200ms" }}>
            {multiResults.map((sub, idx) => (
              <div key={idx} className="glass rounded-xl border border-white/10 overflow-hidden">
                {/* Sub-question header */}
                <div className="flex items-center gap-2 px-4 py-3 bg-black/30 border-b border-white/10">
                  <HelpCircle size={14} className="text-blue-400 flex-shrink-0" />
                  <span className="text-xs text-gray-300 font-medium">{sub.question}</span>
                </div>
                {/* Sub-explanation */}
                <div className="px-4 py-3 text-sm text-gray-200">{sub.explanation}</div>

                {/* Sub SQL */}
                {sub.sql_query && (
                  <details className="group border-t border-white/5 cursor-pointer">
                    <summary className="flex items-center space-x-2 px-4 py-2 text-xs text-gray-400 hover:bg-white/5 transition-colors">
                      <Database size={12} className="text-blue-400" />
                      <span>View SQL</span>
                    </summary>
                    <div className="px-4 pb-3 bg-black/30 overflow-x-auto text-xs font-mono text-gray-500 leading-relaxed">
                      <pre><code>{sub.sql_query}</code></pre>
                    </div>
                  </details>
                )}

                {/* Sub results table */}
                {sub.results && sub.results.length > 0 && (
                  <div className="border-t border-white/5">
                    <ResultTable results={sub.results} />
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
