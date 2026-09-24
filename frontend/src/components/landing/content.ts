import {
  MessageSquareText,
  Code2,
  ShieldCheck,
  Table2,
  Split,
  HelpCircle,
  TrendingUp,
  ListChecks,
  CalendarClock,
  BadgePercent,
  Layers,
  LockKeyhole,
  Brain,
  ScanSearch,
  Database,
  Sparkles,
  type LucideIcon,
} from "lucide-react";

export type Feature = { icon: LucideIcon; title: string; text: string; example: string };

export const FEATURES: Feature[] = [
  {
    icon: MessageSquareText,
    title: "Plain-English questions",
    text: "Ask the way you'd ask a colleague. No SQL, no dashboards, no filters to configure.",
    example: '“Which subscriptions are pending?”',
  },
  {
    icon: Code2,
    title: "SQL written for you",
    text: "An LLM turns your question into a PostgreSQL query against the real schema, then corrects itself if the query fails.",
    example: "SELECT … WHERE s.status = 'active'",
  },
  {
    icon: ShieldCheck,
    title: "Only ever your data",
    text: "Row-Level Security in the database scopes every query to your company, even if the AI gets it wrong.",
    example: "SET app.current_tenant = 'acme'",
  },
  {
    icon: Table2,
    title: "Shows its working",
    text: "Every answer comes with the SQL it ran and the full result table, so you can check the numbers.",
    example: '7 rows · SQL attached',
  },
  {
    icon: Split,
    title: "Handles multi-part questions",
    text: "Ask two things at once and it splits them, answers each separately and shows both.",
    example: '2 questions → 2 answers',
  },
  {
    icon: HelpCircle,
    title: "Asks when it's unsure",
    text: "Vague questions get a clarifying question back instead of a confident guess.",
    example: '→ “Which subscription do you mean?”',
  },
];

export type PipelineStep = { icon: LucideIcon; title: string; text: string };

export const PIPELINE: PipelineStep[] = [
  { icon: MessageSquareText, title: "You ask", text: "“What's my total active ARR?”" },
  { icon: Brain, title: "Understand the intent", text: "Small talk, a data question, a vague question or several questions at once." },
  { icon: Code2, title: "Write the SQL", text: "Gemini writes a query against the billing schema." },
  { icon: ScanSearch, title: "Safety check", text: "Only a single read-only SELECT gets through. Row count is capped." },
  { icon: Database, title: "Run it, scoped to you", text: "PostgreSQL Row-Level Security filters every row to your tenant." },
  { icon: Sparkles, title: "Explain the answer", text: "Results come back as plain English, with the SQL and table attached." },
];

export type QuestionCategory = {
  icon: LucideIcon;
  title: string;
  returns: string;
  questions: string[];
};

export const QUESTION_CATEGORIES: QuestionCategory[] = [
  {
    icon: TrendingUp,
    title: "Revenue & metrics",
    returns: "Totals like ARR, MRR and revenue",
    questions: ["What's my total active ARR?", "What's my MRR?", "What's my total revenue across all subscriptions?"],
  },
  {
    icon: ListChecks,
    title: "Subscription status",
    returns: "Counts and lists of active, cancelled or pending plans",
    questions: [
      "How many active subscriptions do I have?",
      "Show me all my cancelled subscriptions",
      "Which subscriptions are pending?",
    ],
  },
  {
    icon: CalendarClock,
    title: "Billing & payments",
    returns: "Upcoming dates and amounts, per subscription",
    questions: ["When is my next payment due?", "Show me my upcoming billing schedule"],
  },
  {
    icon: BadgePercent,
    title: "Pricing & discounts",
    returns: "Prices, discount rates and rankings",
    questions: [
      "Which subscriptions have a discount?",
      "What is my most expensive subscription?",
      "Show me the billing amount for each subscription",
    ],
  },
  {
    icon: Layers,
    title: "Multi-part questions",
    returns: "Each part answered separately",
    questions: ["Show me my pending subscriptions and when my next payment is due"],
  },
  {
    icon: LockKeyhole,
    title: "Built-in guardrails",
    returns: "A clarifying question, or a polite refusal",
    questions: ["What's my subscription?", "Show me Bob's subscriptions"],
  },
];

export type HeroExample = {
  question: string;
  sql: string;
  answerLead: string;
  value: number;
  prefix?: string;
  suffix?: string;
};

// Real answers from the demo tenant Acme Corp (user: alice)
export const HERO_EXAMPLES: HeroExample[] = [
  {
    question: "What's my total active ARR?",
    sql: "SELECT SUM(sc.total_revenue) AS total_arr\nFROM subscription_calculations sc\nJOIN subscriptions s ON s.id = sc.subscription_id\nWHERE s.status = 'active'\n  AND sc.calculation_type = 'ARR'\n  AND sc.is_active = TRUE;",
    answerLead: "Your total active ARR is",
    value: 1990,
    prefix: "$",
  },
  {
    question: "How many active subscriptions do I have?",
    sql: "SELECT COUNT(s.id) AS active_count\nFROM subscriptions s\nWHERE s.status = 'active';",
    answerLead: "Active subscriptions right now",
    value: 7,
  },
  {
    question: "Which subscriptions have a discount?",
    sql: "SELECT s.subscription_name, sft.discount_rate\nFROM subscriptions s\nJOIN subscription_financial_terms sft\n  ON s.id = sft.subscription_id\nWHERE sft.discount_rate > 0\nORDER BY sft.discount_rate DESC;",
    answerLead: "Discounted plans, from 5% to 20%",
    value: 10,
  },
];

export const DEMO_ACCOUNTS = [
  { username: "alice", tenant: "Acme Corp", detail: "11 subscriptions" },
  { username: "bob", tenant: "Globex Inc", detail: "7 subscriptions" },
  { username: "charlie", tenant: "Initech LLC", detail: "8 subscriptions" },
];

export const STACK = ["Next.js", "FastAPI", "PostgreSQL", "Row-Level Security", "Gemini", "SQLAlchemy", "JWT auth", "GSAP", "Tailwind CSS"];
