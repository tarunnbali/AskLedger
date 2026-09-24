"use client";

import { useRef } from "react";
import { gsap, useGSAP, ScrollTrigger, MOTION_OK } from "./gsap";
import { FEATURES, PIPELINE, STACK } from "./content";

/** Left-aligned section heading with a numbered label and a hairline. */
export function SectionHeading({
  index,
  label,
  title,
  lead,
}: {
  index: string;
  label: string;
  title: string;
  lead?: string;
}) {
  return (
    <div data-reveal className="mb-12">
      <div className="mb-6 flex items-center gap-4 font-mono text-xs text-graphite">
        <span className="text-ledger">{index}</span>
        <span className="uppercase tracking-wider">{label}</span>
        <span className="h-px flex-1 bg-rule" />
      </div>
      <div className="grid gap-4 lg:grid-cols-[1.1fr_1fr] lg:items-end lg:gap-16">
        <h2 className="max-w-xl text-3xl font-semibold leading-tight tracking-tight text-ink sm:text-4xl">{title}</h2>
        {lead && <p className="max-w-lg text-graphite lg:justify-self-end">{lead}</p>}
      </div>
    </div>
  );
}

/** Fade/slide up every [data-reveal] element inside the scope as it scrolls in. */
export function useRevealOnScroll(scope: React.RefObject<HTMLElement | null>) {
  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      mm.add(MOTION_OK, () => {
        gsap.set("[data-reveal]", { autoAlpha: 0, y: 40 });
        ScrollTrigger.batch("[data-reveal]", {
          start: "top 88%",
          once: true,
          onEnter: (batch) =>
            gsap.to(batch, { autoAlpha: 1, y: 0, duration: 0.8, ease: "power3.out", stagger: 0.09, overwrite: true }),
        });
      });
    },
    { scope }
  );
}

export function StackMarquee() {
  const root = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      mm.add(MOTION_OK, () => {
        gsap.to("[data-track]", { xPercent: -50, duration: 32, ease: "none", repeat: -1 });
      });
    },
    { scope: root }
  );

  const items = [...STACK, ...STACK];
  return (
    <div ref={root} className="marquee-mask overflow-hidden border-y border-rule py-5">
      <div data-track className="flex w-max gap-12 whitespace-nowrap text-sm text-graphite">
        {items.map((s, i) => (
          <span key={i} className="flex items-center gap-12">
            {s}
            <span className="h-1 w-1 rounded-full bg-ledger/50" />
          </span>
        ))}
      </div>
    </div>
  );
}

export function FeatureCards() {
  const root = useRef<HTMLElement>(null);
  useRevealOnScroll(root);

  return (
    <section ref={root} id="product" className="mx-auto max-w-6xl scroll-mt-20 px-5 py-28">
      <SectionHeading
        index="01"
        label="Product"
        title="Your billing data, as easy to ask as a colleague"
        lead="Finance and customer teams usually wait on an analyst or dig through dashboards. AskLedger lets anyone ask directly and get an answer they can check."
      />
      <div className="grid border-l border-t border-rule sm:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map((f, i) => (
          <article
            key={f.title}
            data-reveal
            className="group flex flex-col border-b border-r border-rule p-7 transition-colors duration-300 hover:bg-paper-2"
          >
            <div className="mb-10 flex items-center justify-between font-mono text-xs text-graphite/70">
              <span className="transition-colors group-hover:text-ledger">{String(i + 1).padStart(2, "0")}</span>
              <f.icon size={16} strokeWidth={1.5} className="text-graphite transition-colors group-hover:text-ink" />
            </div>
            <h3 className="mb-2 text-base font-medium text-ink">{f.title}</h3>
            <p className="mb-6 text-sm leading-relaxed text-graphite">{f.text}</p>
            <code className="mt-auto block truncate border-t border-dashed border-rule pt-4 font-mono text-[11.5px] text-graphite transition-colors group-hover:text-ledger">
              {f.example}
            </code>
          </article>
        ))}
      </div>
    </section>
  );
}

export function Pipeline() {
  const root = useRef<HTMLElement>(null);
  useRevealOnScroll(root);

  useGSAP(
    () => {
      const steps = gsap.utils.toArray<HTMLElement>(".pipeline-step");
      const mm = gsap.matchMedia();

      mm.add(MOTION_OK, () => {
        gsap.fromTo(
          "[data-line-fill]",
          { scaleY: 0 },
          {
            scaleY: 1,
            ease: "none",
            transformOrigin: "top center",
            scrollTrigger: { trigger: "[data-steps]", start: "top 62%", end: "bottom 62%", scrub: 0.4 },
          }
        );
        steps.forEach((step) =>
          ScrollTrigger.create({
            trigger: step,
            start: "top 62%",
            onEnter: () => step.classList.add("is-active"),
            onLeaveBack: () => step.classList.remove("is-active"),
          })
        );
      });

      // Without motion, show every step as active
      mm.add("(prefers-reduced-motion: reduce)", () => {
        steps.forEach((s) => s.classList.add("is-active"));
        gsap.set("[data-line-fill]", { scaleY: 1 });
      });
    },
    { scope: root }
  );

  return (
    <section ref={root} id="how-it-works" className="relative scroll-mt-20 border-t border-rule px-5 py-28">
      <div className="mx-auto max-w-6xl">
        <SectionHeading
          index="02"
          label="How it works"
          title="From question to answer in six steps"
          lead="Scroll through what happens between hitting Enter and reading your answer."
        />
      </div>
      <div data-steps className="relative mx-auto max-w-2xl">
        <div className="absolute bottom-4 left-[17px] top-4 w-px bg-rule" />
        <div data-line-fill className="absolute bottom-4 left-[17px] top-4 w-px bg-ledger" />
        <ol className="space-y-12">
          {PIPELINE.map((s, i) => (
            <li key={s.title} className="pipeline-step relative flex items-start gap-7">
              <div className="step-node relative z-10 flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-rule bg-paper font-mono text-xs text-graphite">
                {String(i + 1).padStart(2, "0")}
              </div>
              <div className="step-copy pt-1">
                <h3 className="flex items-center gap-2 text-lg font-medium text-ink">
                  <s.icon size={16} strokeWidth={1.5} className="text-graphite" />
                  {s.title}
                </h3>
                <p className="mt-1 text-sm leading-relaxed text-graphite">{s.text}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
