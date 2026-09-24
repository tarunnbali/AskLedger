"use client";

import { useRef } from "react";
import { ArrowRight, ArrowUpRight } from "lucide-react";
import { gsap, useGSAP, MOTION_OK } from "./gsap";
import { SectionHeading, useRevealOnScroll } from "./Sections";
import { DEMO_ACCOUNTS, QUESTION_CATEGORIES } from "./content";

export function QuestionCards({ onAsk }: { onAsk: (question: string) => void }) {
  const root = useRef<HTMLElement>(null);
  useRevealOnScroll(root);

  return (
    <section ref={root} id="questions" className="scroll-mt-20 border-t border-rule px-5 py-28">
      <div className="mx-auto max-w-6xl">
        <SectionHeading
          index="03"
          label="What you can ask"
          title="Click any question to try it live"
          lead="Every one of these works against the demo data. Pick one and AskLedger opens, signs you in as a demo company and asks it for you."
        />

        <div className="border-t border-rule">
          {QUESTION_CATEGORIES.map((c) => (
            <div
              key={c.title}
              data-reveal
              className="grid gap-4 border-b border-rule py-7 lg:grid-cols-[260px_1fr] lg:gap-12"
            >
              <div>
                <h3 className="flex items-center gap-2 font-medium text-ink">
                  <c.icon size={16} strokeWidth={1.5} className="text-graphite" />
                  {c.title}
                </h3>
                <p className="mt-1.5 font-mono text-[11px] leading-relaxed text-graphite">Returns: {c.returns}</p>
              </div>
              <ul className="divide-y divide-dashed divide-rule">
                {c.questions.map((q) => (
                  <li key={q}>
                    <button
                      onClick={() => onAsk(q)}
                      className="group flex w-full items-center justify-between gap-4 py-2.5 text-left text-[15px] text-ink/80 transition-colors hover:text-ink"
                    >
                      <span className="transition-transform duration-300 group-hover:translate-x-1">{q}</span>
                      <span className="flex shrink-0 items-center gap-1 font-mono text-[11px] text-graphite/70 transition-colors group-hover:text-ledger">
                        Ask
                        <ArrowUpRight size={13} />
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <p data-reveal className="mt-8 max-w-2xl text-sm text-graphite">
          AskLedger is read-only: it can look things up but never change, cancel or delete anything. It only ever
          answers about the signed-in company&apos;s own data.
        </p>
      </div>
    </section>
  );
}

export function DemoTenants({ onPick }: { onPick: (username: string) => void }) {
  const root = useRef<HTMLElement>(null);
  useRevealOnScroll(root);

  return (
    <section ref={root} id="try" className="scroll-mt-20 border-t border-rule px-5 py-28">
      <div className="mx-auto max-w-6xl">
        <SectionHeading
          index="04"
          label="Demo accounts"
          title="Three companies. Three separate datasets."
          lead="Each account belongs to a different fictional company. Sign in as two of them and ask the same question to see the isolation. Password for all: password123"
        />

        <div data-reveal className="border-t border-rule">
          <div className="hidden grid-cols-[1.2fr_1fr_1fr_auto] gap-6 border-b border-rule py-3 font-mono text-[11px] uppercase tracking-wider text-graphite/70 sm:grid">
            <span>Company</span>
            <span>User</span>
            <span>Data</span>
            <span />
          </div>
          {DEMO_ACCOUNTS.map((a) => (
            <button
              key={a.username}
              onClick={() => onPick(a.username)}
              className="group grid w-full grid-cols-2 items-center gap-x-6 gap-y-1 border-b border-rule py-5 text-left transition-colors hover:bg-paper-2 sm:grid-cols-[1.2fr_1fr_1fr_auto]"
            >
              <span className="font-medium text-ink">{a.tenant}</span>
              <span className="font-mono text-sm text-ink/80">{a.username}</span>
              <span className="text-sm text-graphite">{a.detail}</span>
              <span className="flex items-center gap-1.5 justify-self-end text-sm text-graphite transition-colors group-hover:text-ink">
                Sign in
                <ArrowRight size={14} className="transition-transform group-hover:translate-x-1" />
              </span>
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}

const TRUST = [
  { title: "Row-Level Security", text: "The database scopes every query to your company through a restricted role." },
  { title: "Read-only by design", text: "Only single SELECT statements pass validation. Writes are blocked." },
  { title: "Signed sessions", text: "JWT authentication ties every request to one user and one company." },
  { title: "Rate limited", text: "Per-visitor limits keep the public demo fast and fair." },
];

export function TrustAndCta({ onTryDemo }: { onTryDemo: () => void }) {
  const root = useRef<HTMLElement>(null);
  useRevealOnScroll(root);

  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      mm.add(MOTION_OK, () => {
        // Headline words slide up as the closing section scrolls in
        gsap.from("[data-cta-line]", {
          yPercent: 100,
          duration: 1,
          ease: "power4.out",
          stagger: 0.12,
          scrollTrigger: { trigger: "[data-cta-box]", start: "top 80%" },
        });
      });
    },
    { scope: root }
  );

  return (
    <section ref={root} className="border-t border-rule px-5 pb-12 pt-28">
      <div className="mx-auto max-w-6xl">
        <SectionHeading index="05" label="Security" title="Built so the AI can't leak your data" />
        <div className="grid border-t border-rule sm:grid-cols-2 lg:grid-cols-4">
          {TRUST.map((t, i) => (
            <div
              key={t.title}
              data-reveal
              className="border-b border-rule py-6 sm:pr-6 lg:border-b-0 lg:border-r lg:px-6 lg:first:pl-0 lg:last:border-r-0"
            >
              <div className="mb-4 font-mono text-xs text-graphite/70">{String(i + 1).padStart(2, "0")}</div>
              <h3 className="mb-1.5 text-sm font-medium text-ink">{t.title}</h3>
              <p className="text-sm leading-relaxed text-graphite">{t.text}</p>
            </div>
          ))}
        </div>

        <div data-cta-box className="mt-32 border-t border-rule pt-16">
          <h2 className="text-4xl font-semibold leading-[1.05] tracking-tight text-ink sm:text-6xl">
            <span className="block overflow-hidden pb-1">
              <span data-cta-line className="block">
                Your data has answers.
              </span>
            </span>
            <span className="block overflow-hidden pb-1">
              <span data-cta-line className="block text-ledger">
                Just ask.
              </span>
            </span>
          </h2>
          <div className="mt-10 flex flex-wrap items-center gap-6">
            <button
              onClick={onTryDemo}
              className="group inline-flex items-center gap-2 rounded-full bg-ink px-6 py-3 font-medium text-paper transition-colors hover:bg-ledger"
            >
              Try the live demo
              <ArrowRight size={17} className="transition-transform group-hover:translate-x-1" />
            </button>
            <span className="text-sm text-graphite">No sign-up. Pick a demo company and start asking.</span>
          </div>
        </div>

        <footer className="mt-24 flex flex-col justify-between gap-3 border-t border-rule pt-8 font-mono text-[11px] text-graphite/70 sm:flex-row">
          <span>AskLedger · a portfolio project</span>
          <span>Next.js · FastAPI · PostgreSQL · Gemini · GSAP</span>
        </footer>
      </div>
    </section>
  );
}
