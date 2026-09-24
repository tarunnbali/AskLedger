"use client";

import { useRef } from "react";
import { ArrowRight, ChevronDown } from "lucide-react";
import { gsap, useGSAP, ScrollTrigger, SplitText, MOTION_OK, MOTION_REDUCED } from "./gsap";
import HeroDemo from "./HeroDemo";
import ThemeToggle from "../ThemeToggle";

interface HeroProps {
  onTryDemo: () => void;
}

const NAV_LINKS = [
  { href: "#product", label: "Product" },
  { href: "#how-it-works", label: "How it works" },
  { href: "#questions", label: "Questions" },
  { href: "#try", label: "Demo accounts" },
];

export default function Hero({ onTryDemo }: HeroProps) {
  const root = useRef<HTMLElement>(null);
  const ctaRef = useRef<HTMLButtonElement>(null);

  useGSAP(
    () => {
      const nav = root.current!.querySelector<HTMLElement>("[data-nav]")!;
      ScrollTrigger.create({
        start: 40,
        end: "max",
        onToggle: (self) => nav.classList.toggle("is-scrolled", self.isActive),
      });

      const mm = gsap.matchMedia();

      mm.add(MOTION_REDUCED, () => {
        gsap.set("[data-hero-reveal]", { autoAlpha: 1 });
      });

      mm.add(MOTION_OK, () => {
        gsap.set("[data-hero-reveal]", { autoAlpha: 1 });

        const tl = gsap.timeline({ defaults: { ease: "power3.out" } });
        tl.from(nav, { y: -24, autoAlpha: 0, duration: 0.6 })
          .from("[data-badge]", { y: 16, autoAlpha: 0, duration: 0.5 }, "-=0.3");

        let introPlayed = false;
        SplitText.create("[data-headline]", {
          type: "words",
          mask: "words",
          autoSplit: true,
          onSplit: (self) => {
            // Only the first split gets the reveal; later re-splits (e.g. on
            // resize) just show the words in place
            if (introPlayed) return;
            introPlayed = true;
            const reveal = gsap.from(self.words, { yPercent: 110, duration: 0.9, stagger: 0.07 });
            tl.add(reveal, 0.35);
            return reveal;
          },
        });

        tl.from("[data-sub]", { y: 18, autoAlpha: 0, duration: 0.7 }, 0.9)
          .from("[data-cta] > *", { y: 16, autoAlpha: 0, duration: 0.6, stagger: 0.1 }, 1.05)
          .from("[data-demo]", { y: 40, autoAlpha: 0, rotateX: 8, duration: 1.1 }, 0.6)
          .from("[data-scroll-hint]", { autoAlpha: 0, duration: 0.6 }, 1.6);

        // Parallax: demo window drifts up slower than the page
        gsap.to("[data-demo]", {
          yPercent: -8,
          ease: "none",
          scrollTrigger: { trigger: root.current, start: "top top", end: "bottom top", scrub: true },
        });

        // Magnetic primary button
        const btn = ctaRef.current!;
        const xTo = gsap.quickTo(btn, "x", { duration: 0.4, ease: "power3" });
        const yTo = gsap.quickTo(btn, "y", { duration: 0.4, ease: "power3" });
        const move = (e: MouseEvent) => {
          const r = btn.getBoundingClientRect();
          xTo((e.clientX - (r.left + r.width / 2)) * 0.25);
          yTo((e.clientY - (r.top + r.height / 2)) * 0.35);
        };
        const leave = () => {
          xTo(0);
          yTo(0);
        };
        btn.addEventListener("mousemove", move);
        btn.addEventListener("mouseleave", leave);
        return () => {
          btn.removeEventListener("mousemove", move);
          btn.removeEventListener("mouseleave", leave);
        };
      });
    },
    { scope: root }
  );

  return (
    <section ref={root} className="relative overflow-hidden">
      {/* Background: ledger-paper rules with a margin line */}
      <div className="pointer-events-none absolute inset-0 bg-ledger-rules [mask-image:linear-gradient(to_bottom,black_40%,transparent)]" />
      <div className="pointer-events-none absolute inset-y-0 left-[calc(50%-37.5rem)] hidden w-px bg-rule xl:block" />

      {/* Nav */}
      <header data-nav data-hero-reveal className="nav-shell invisible fixed inset-x-0 top-0 z-40">
        <nav className="mx-auto flex max-w-6xl items-center justify-between px-5 py-3.5">
          <a href="#" className="flex items-center gap-2 text-lg font-semibold tracking-tight">
            <span className="flex h-7 w-7 items-center justify-center rounded-md bg-ledger font-mono text-sm font-bold text-paper">
              A
            </span>
            <span>
              Ask<span className="text-ledger">Ledger</span>
            </span>
          </a>
          <div className="hidden items-center gap-7 text-sm text-graphite md:flex">
            {NAV_LINKS.map((l) => (
              <a key={l.href} href={l.href} className="transition-colors hover:text-ink">
                {l.label}
              </a>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <button
              onClick={onTryDemo}
              className="rounded-full bg-ink px-4 py-1.5 text-sm font-medium text-paper transition-colors hover:bg-ledger"
            >
              Try the demo
            </button>
          </div>
        </nav>
      </header>

      {/* Hero content */}
      <div className="relative z-10 mx-auto grid max-w-6xl items-center gap-14 px-5 pb-20 pt-32 lg:grid-cols-[1.05fr_1fr] lg:pt-40">
        <div data-hero-reveal className="invisible">
          <div
            data-badge
            className="mb-6 inline-flex items-center gap-2 rounded-full border border-rule bg-paper px-3 py-1.5 font-mono text-xs text-graphite"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-ledger" />
            AI analytics for subscription billing data
          </div>

          <h1
            data-headline
            className="text-5xl font-semibold leading-[1.05] tracking-tight text-ink sm:text-6xl lg:text-[3.7rem]"
          >
            Ask your billing data anything.{" "}
            <span className="text-ledger">Get answers, not dashboards.</span>
          </h1>

          <p data-sub className="mt-6 max-w-xl text-lg leading-relaxed text-graphite">
            AskLedger turns plain-English questions about your subscriptions, revenue and payments into secure SQL,
            runs it on your data only, and explains the result.
          </p>

          <div data-cta className="mt-9 flex flex-wrap items-center gap-3">
            <button
              ref={ctaRef}
              onClick={onTryDemo}
              className="group inline-flex items-center gap-2 rounded-full bg-ink px-6 py-3.5 font-medium text-paper transition-colors hover:bg-ledger"
            >
              Try the live demo
              <ArrowRight size={18} className="transition-transform group-hover:translate-x-1" />
            </button>
            <a
              href="#questions"
              className="rounded-full px-5 py-3.5 font-medium text-ink ring-1 ring-rule transition-colors hover:bg-paper-2"
            >
              See what you can ask
            </a>
          </div>
        </div>

        <div data-demo data-hero-reveal className="invisible flex justify-center [perspective:1200px] lg:justify-end">
          <HeroDemo />
        </div>
      </div>

      <a
        href="#product"
        data-scroll-hint
        className="relative z-10 mx-auto mb-6 flex w-fit flex-col items-center gap-1 font-mono text-xs text-graphite transition-colors hover:text-ink"
      >
        Scroll to explore
        <ChevronDown size={16} className="animate-bounce" />
      </a>
    </section>
  );
}
