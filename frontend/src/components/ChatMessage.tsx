import { Bot, User, AlertCircle, Database, HelpCircle } from "lucide-react";
import type { ResultRow, SubResult } from "@/lib/api";

interface ChatMessageProps {
  role: "user" | "assistant" | "error";
  text: string;
  sql?: string | null;
  results?: ResultRow[] | null;
  multiResults?: SubResult[] | null;
}

function ResultTable({ results }: { results: ResultRow[] }) {
  if (!results || results.length === 0) return null;
  return (
    <div className="overflow-hidden rounded-lg border border-rule bg-surface">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-ink">
          <thead className="border-b border-rule bg-paper-2 font-mono text-[11px] uppercase text-graphite">
            <tr>
              {Object.keys(results[0]).map((key) => (
                <th key={key} scope="col" className="px-4 py-2.5 font-medium whitespace-nowrap">
                  {key.replace(/_/g, " ")}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {results.map((row, rowIndex) => (
              <tr key={rowIndex} className="border-b border-rule transition-colors last:border-0 hover:bg-paper">
                {Object.values(row).map((val, colIndex) => (
                  <td key={colIndex} className="px-4 py-2.5 whitespace-nowrap">
                    {val !== null && val !== undefined ? String(val) : <span className="italic text-graphite">null</span>}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex justify-between border-t border-rule bg-paper px-4 py-1.5 font-mono text-[11px] text-graphite">
        <span>{results.length} row{results.length !== 1 ? "s" : ""}</span>
      </div>
    </div>
  );
}

function SqlBlock({ sql, compact = false }: { sql: string; compact?: boolean }) {
  return (
    <details className="group cursor-pointer overflow-hidden rounded-lg border border-rule bg-surface">
      <summary className={`flex items-center gap-2 text-graphite transition-colors hover:text-ink ${compact ? "px-4 py-2 text-xs" : "p-3 text-sm font-medium"}`}>
        <Database size={compact ? 12 : 15} className="text-ledger" />
        <span>{compact ? "View SQL" : "View generated SQL"}</span>
      </summary>
      <div className="overflow-x-auto bg-term p-4 font-mono text-xs leading-relaxed text-[#cfe3d5]">
        <pre><code>{sql}</code></pre>
      </div>
    </details>
  );
}

export default function ChatMessage({ role, text, sql, results, multiResults }: ChatMessageProps) {
  const isUser = role === "user";
  const isError = role === "error";

  return (
    <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"} animate-fade-in`}>
      <div className={`flex flex-col max-w-[85%] md:max-w-[75%] space-y-2 ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={`flex items-start space-x-3 rounded-2xl p-4
            ${isUser
              ? "rounded-tr-sm bg-ink text-paper"
              : isError
                ? "rounded-tl-sm border border-red-200 bg-red-50 text-red-800 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-200"
                : "rounded-tl-sm border border-rule bg-surface text-ink"
            }
          `}
        >
          {/* Avatar Icon */}
          <div className={`mt-1 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full
            ${isUser ? "bg-paper/15" : isError ? "bg-red-100 dark:bg-red-900/40" : "bg-ledger-soft text-ledger"}
          `}>
            {isUser ? <User size={18} /> : isError ? <AlertCircle size={18} className="text-red-600 dark:text-red-300" /> : <Bot size={18} />}
          </div>

          {/* Message Content */}
          <div className="flex-1 overflow-hidden">
            <p className="text-sm md:text-base leading-relaxed break-words whitespace-pre-wrap">{text}</p>
          </div>
        </div>

        {/* SQL (single query) */}
        {!isUser && !isError && sql && (
          <div className="mt-2 w-full pl-4 pr-1">
            <SqlBlock sql={sql} />
          </div>
        )}

        {/* Single query result table */}
        {!isUser && !isError && results && results.length > 0 && (
          <div className="mt-2 w-full animate-fade-in pl-4 pr-1" style={{ animationDelay: "200ms" }}>
            <ResultTable results={results} />
          </div>
        )}

        {/* Multi-query sub-results */}
        {!isUser && !isError && multiResults && multiResults.length > 0 && (
          <div className="mt-2 w-full space-y-3 animate-fade-in pl-4 pr-1" style={{ animationDelay: "200ms" }}>
            {multiResults.map((sub, idx) => (
              <div key={idx} className="overflow-hidden rounded-lg border border-rule bg-surface">
                {/* Sub-question header */}
                <div className="flex items-center gap-2 border-b border-rule bg-paper-2 px-4 py-2.5">
                  <HelpCircle size={14} className="flex-shrink-0 text-ledger" />
                  <span className="text-xs font-medium text-ink">{sub.question}</span>
                </div>
                {/* Sub-explanation */}
                <div className="px-4 py-3 text-sm text-ink">{sub.explanation}</div>

                {/* Sub SQL */}
                {sub.sql_query && (
                  <div className="border-t border-rule px-3 py-2">
                    <SqlBlock sql={sub.sql_query} compact />
                  </div>
                )}

                {/* Sub results table */}
                {sub.results && sub.results.length > 0 && (
                  <div className="border-t border-rule p-3">
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
