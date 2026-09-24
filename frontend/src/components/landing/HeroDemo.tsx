"use client";

import { useRef } from "react";
import { Bot, Database, Lock, User } from "lucide-react";
import { gsap, useGSAP, MOTION_OK, MOTION_REDUCED } from "./gsap";
import { HERO_EXAMPLES } from "./content";

const STAGES = ["Understanding", "Writing SQL", "Running securely"];

// Types `text` into `el` one character at a time, keeping line breaks
function typeInto(el: HTMLElement, text: string, charDuration: number) {
  const state = { n: 0 };
  return gsap.to(state, {
    n: text.length,
    duration: text.length * charDuration,
    ease: "none",
    onUpdate: () => {
      el.textContent = text.slice(0, Math.round(state.n));
    },
  });
}

function formatValue(v: number, prefix = "", suffix = "") {
  return `${prefix}${Math.round(v).toLocaleString("en-US")}${suffix}`;
}

export default function HeroDemo() {
  const root = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      const q = (sel: string) => root.current!.querySelector(sel) as HTMLElement;
      const questionEl = q("[data-question]");
      const questionBubble = q("[data-question-bubble]");
      const stages = gsap.utils.toArray<HTMLElement>("[data-stage]", root.current);
      const sqlPanel = q("[data-sql-panel]");
      const sqlEl = q("[data-sql]");
      const answer = q("[data-answer]");
      const answerLead = q("[data-answer-lead]");
      const answerValue = q("[data-answer-value]");

      const mm = gsap.matchMedia();

      mm.add(MOTION_REDUCED, () => {
        // Static: show the first example fully rendered
        const ex = HERO_EXAMPLES[0];
        questionEl.textContent = ex.question;
        sqlEl.textContent = ex.sql;
        answerLead.textContent = ex.answerLead;
        answerValue.textContent = formatValue(ex.value, ex.prefix, ex.suffix);
        gsap.set([questionBubble, sqlPanel, answer], { autoAlpha: 1 });
        gsap.set(stages, { opacity: 1 });
      });

      mm.add(MOTION_OK, () => {
        const master = gsap.timeline({ repeat: -1, delay: 1.1 });

        HERO_EXAMPLES.forEach((ex) => {
          const counter = { v: 0 };
          const tl = gsap.timeline();
          tl.call(() => {
            questionEl.textContent = "";
            sqlEl.textContent = "";
          })
            .set([questionBubble, sqlPanel, answer], { autoAlpha: 0, y: 10 })
            .set(stages, { opacity: 0.25 })
            .to(questionBubble, { autoAlpha: 1, y: 0, duration: 0.35, ease: "power2.out" })
            .add(typeInto(questionEl, ex.question, 0.035))
            .to(stages[0], { opacity: 1, duration: 0.25 }, "+=0.25")
            .to(sqlPanel, { autoAlpha: 1, y: 0, duration: 0.35, ease: "power2.out" }, "+=0.35")
            .to(stages[1], { opacity: 1, duration: 0.25 }, "<")
            .add(typeInto(sqlEl, ex.sql, 0.011))
            .to(stages[2], { opacity: 1, duration: 0.25 }, "+=0.15")
            .call(() => {
              answerLead.textContent = ex.answerLead;
              answerValue.textContent = formatValue(0, ex.prefix, ex.suffix);
            })
            .to(answer, { autoAlpha: 1, y: 0, duration: 0.45, ease: "back.out(1.6)" }, "+=0.3")
            .to(
              counter,
              {
                v: ex.value,
                duration: 1,
                ease: "power3.out",
                onUpdate: () => {
                  answerValue.textContent = formatValue(counter.v, ex.prefix, ex.suffix);
                },
              },
              "<"
            )
            .to([questionBubble, sqlPanel, answer], { autoAlpha: 0, y: -8, duration: 0.4, stagger: 0.05 }, "+=2.6");
          master.add(tl);
        });

        // Don't burn CPU animating the demo while it's off screen
        const observer = new IntersectionObserver(([entry]) => {
          if (entry.isIntersecting) master.play();
          else master.pause();
        });
        observer.observe(root.current!);
        return () => observer.disconnect();
      });
    },
    { scope: root }
  );

  return (
    <div
      ref={root}
      className="relative w-full max-w-xl rounded-xl border border-black/80 bg-term text-[#e8e6df] shadow-[0_30px_60px_-24px_rgba(22,24,29,0.55)]"
      aria-label="Animated example of AskLedger answering a question"
    >
      {/* Window chrome */}
      <div className="flex items-center justify-between border-b border-white/[0.07] px-4 py-3">
        <div className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
          <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
          <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
        </div>
        <span className="text-[11px] text-gray-500">AskLedger · signed in as alice</span>
        <span className="flex items-center gap-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] text-emerald-300">
          <Lock size={10} /> Acme Corp only
        </span>
      </div>

      <div className="flex min-h-[370px] flex-col gap-4 p-5">
        {/* Question */}
        <div data-question-bubble className="invisible flex justify-end">
          <div className="flex max-w-[85%] items-start gap-2 rounded-2xl rounded-tr-sm bg-ledger px-4 py-2.5 text-sm text-paper">
            <span data-question className="caret" />
            <User size={15} className="mt-0.5 shrink-0 opacity-70" />
          </div>
        </div>

        {/* Pipeline stages */}
        <div className="flex flex-wrap gap-2 text-[11px]">
          {STAGES.map((s) => (
            <span
              key={s}
              data-stage
              className="rounded-full border border-emerald-400/25 bg-emerald-400/10 px-2.5 py-1 font-mono text-emerald-200"
              style={{ opacity: 0.25 }}
            >
              {s}
            </span>
          ))}
        </div>

        {/* Generated SQL */}
        <div data-sql-panel className="invisible overflow-hidden rounded-xl border border-white/[0.07] bg-black/50">
          <div className="flex items-center gap-1.5 border-b border-white/[0.06] px-3 py-1.5 text-[10px] uppercase tracking-wider text-gray-500">
            <Database size={11} className="text-emerald-400" /> Generated SQL
          </div>
          <pre className="min-h-[92px] whitespace-pre-wrap break-words px-3 py-2.5 font-mono text-[11.5px] leading-relaxed text-[#cfe3d5]">
            <code data-sql />
          </pre>
        </div>

        {/* Answer */}
        <div data-answer className="invisible flex items-start gap-3 rounded-2xl rounded-tl-sm border border-white/10 bg-white/[0.04] px-4 py-3">
          <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-emerald-400/15 text-emerald-300">
            <Bot size={15} />
          </span>
          <div>
            <div data-answer-lead className="text-xs text-gray-400" />
            <div data-answer-value className="font-mono text-3xl font-semibold tabular-nums text-[#9fd8b5]" />
          </div>
        </div>
      </div>
    </div>
  );
}
