import Link from "next/link";

export default function Home() {
  return (
    <div className="space-y-8">
      <section className="space-y-3">
        <h1 className="text-3xl font-semibold tracking-tight text-slate-900">
          State-aware unclaimed-property claim automation
        </h1>
        <p className="max-w-2xl text-slate-600">
          ClaimPilot matches a claimant to <em>escheated</em> property and produces the correct,
          state-specific document checklist — grounded in retrieved state rules, with citations and
          a visible human-review guardrail.
        </p>
      </section>

      <div className="grid gap-4 sm:grid-cols-2">
        <Link
          href="/search"
          className="group rounded-xl border border-slate-200 bg-white p-5 shadow-sm hover:border-sky-300 hover:shadow"
        >
          <div className="text-sm font-semibold text-sky-600">Search &amp; reconcile →</div>
          <div className="mt-1 font-medium text-slate-900">Find a claimant&apos;s property</div>
          <p className="mt-1 text-sm text-slate-600">
            Enter claimant details (including former names and old addresses) and match against the
            property index with explainable confidence scores.
          </p>
        </Link>

        <Link
          href="/compare"
          className="group rounded-xl border border-slate-200 bg-white p-5 shadow-sm hover:border-sky-300 hover:shadow"
        >
          <div className="text-sm font-semibold text-sky-600">Compare states →</div>
          <div className="mt-1 font-medium text-slate-900">Same claim, two states</div>
          <p className="mt-1 text-sm text-slate-600">
            Run the same claimant and amount against two states side-by-side and watch the required
            documents diverge — each citing its own state&apos;s rule.
          </p>
        </Link>
      </div>

      <p className="text-xs text-slate-400">
        Backend: FastAPI · PostgreSQL + pgvector · OpenAI-compatible LLM. This UI talks to it over
        REST.
      </p>
    </div>
  );
}
