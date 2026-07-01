"use client";

import { useState } from "react";

import {
  Button,
  Card,
  ErrorNote,
  Field,
  Spinner,
  StateBadge,
  StatusPill,
  inputClass,
} from "@/components/ui";
import { api, ClaimPreviewResponse, RequiredItem } from "@/lib/api";

const STATES = ["CA", "NY", "TX", "FL", "IL"];

function orderItems(items: RequiredItem[]): RequiredItem[] {
  return [...items].sort((a, b) => {
    if (a.origin !== b.origin) return a.origin === "deterministic" ? -1 : 1;
    if (a.requirement !== b.requirement) return a.requirement === "required" ? -1 : 1;
    return 0;
  });
}

export default function ComparePage() {
  const [name, setName] = useState("Jordan Rivera");
  const [amount, setAmount] = useState("1500");
  const [deceased, setDeceased] = useState(false);
  const [business, setBusiness] = useState(false);
  const [stateA, setStateA] = useState("CA");
  const [stateB, setStateB] = useState("TX");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<[ClaimPreviewResponse, ClaimPreviewResponse] | null>(null);
  const [showAI, setShowAI] = useState(false);

  async function onCompare(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResults(null);
    try {
      const amount_cents = Math.round(parseFloat(amount || "0") * 100);
      const body = (state: string) => ({
        state,
        amount_cents,
        owner_deceased: deceased,
        is_business: business,
        name,
      });
      const [a, b] = await Promise.all([
        api.previewClaim(body(stateA)),
        api.previewClaim(body(stateB)),
      ]);
      setResults([a, b]);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Compare states</h1>
        <p className="text-sm text-slate-600">
          The same claimant and amount, two states, side-by-side. Watch the required documents
          diverge — each grounded in its own state&apos;s rule.
        </p>
      </div>

      <Card className="p-5">
        <form onSubmit={onCompare} className="grid gap-4 sm:grid-cols-4">
          <Field label="Claimant name">
            <input className={inputClass} value={name} onChange={(e) => setName(e.target.value)} />
          </Field>
          <Field label="Claim amount (USD)">
            <input
              className={inputClass}
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              inputMode="decimal"
            />
          </Field>
          <Field label="State A">
            <select className={inputClass} value={stateA} onChange={(e) => setStateA(e.target.value)}>
              {STATES.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </Field>
          <Field label="State B">
            <select className={inputClass} value={stateB} onChange={(e) => setStateB(e.target.value)}>
              {STATES.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </Field>
          <div className="sm:col-span-4 flex flex-wrap items-center gap-5">
            <label className="flex items-center gap-2 text-sm text-slate-600">
              <input type="checkbox" checked={deceased} onChange={(e) => setDeceased(e.target.checked)} />
              deceased owner
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-600">
              <input type="checkbox" checked={business} onChange={(e) => setBusiness(e.target.checked)} />
              business entity
            </label>
            <Button type="submit" disabled={loading}>
              {loading ? "Comparing…" : "Compare"}
            </Button>
            {loading && <Spinner label="running both pipelines…" />}
          </div>
        </form>
      </Card>

      {error && <ErrorNote message={error} />}

      {results &&
        (() => {
          const [ra, rb] = results;
          const detOnly = (r: ClaimPreviewResponse) =>
            r.required_items.filter((i) => i.origin === "deterministic");
          const va = orderItems(showAI ? ra.required_items : detOnly(ra));
          const vb = orderItems(showAI ? rb.required_items : detOnly(rb));
          const la = new Set(va.map((i) => i.label));
          const lb = new Set(vb.map((i) => i.label));
          const diffs = [...new Set([...va, ...vb].map((i) => i.label))].filter(
            (l) => la.has(l) !== lb.has(l)
          );
          const aiCount =
            ra.required_items.length +
            rb.required_items.length -
            detOnly(ra).length -
            detOnly(rb).length;
          const cols: [ClaimPreviewResponse, RequiredItem[], Set<string>][] = [
            [ra, va, lb],
            [rb, vb, la],
          ];
          return (
            <div className="space-y-4">
              <Card className="p-4 border-sky-200 bg-sky-50">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="text-sm text-slate-700">
                    <span className="font-semibold">
                      Same claimant · ${amount} · {ra.state} vs {rb.state}.
                    </span>{" "}
                    {diffs.length > 0 ? (
                      <>
                        <span className="font-semibold text-amber-700">
                          {diffs.length} requirement{diffs.length > 1 ? "s" : ""} differ:
                        </span>{" "}
                        {diffs.join(", ")}.
                      </>
                    ) : (
                      "Requirements are identical for these inputs."
                    )}
                  </div>
                  {aiCount > 0 && (
                    <button
                      onClick={() => setShowAI((v) => !v)}
                      className="whitespace-nowrap text-xs font-medium text-sky-700 hover:underline"
                    >
                      {showAI ? "Hide" : "Show"} {aiCount} AI-suggested
                    </button>
                  )}
                </div>
              </Card>

              <div className="grid gap-4 md:grid-cols-2">
                {cols.map(([r, items, otherLabels], idx) => (
                  <Card key={r.state + idx} className="p-5 space-y-4">
                    <div className="flex items-center justify-between">
                      <StateBadge state={r.state} large />
                      {showAI && r.needs_human_review && (
                        <StatusPill status="needs_human_review" />
                      )}
                    </div>
                    <div>
                      <div className="mb-2 text-xs font-semibold uppercase text-slate-500">
                        Required documents
                      </div>
                      <ul className="space-y-2">
                        {items.map((item) => {
                          const unique = !otherLabels.has(item.label);
                          return (
                            <li
                              key={item.label}
                              className={`rounded-lg border p-2.5 ${
                                unique ? "border-amber-300 bg-amber-50" : "border-slate-200 bg-white"
                              }`}
                            >
                              <div className="flex items-center gap-2">
                                <span className="text-sm font-medium text-slate-900">
                                  {item.label}
                                </span>
                                {item.origin === "llm" && (
                                  <span className="text-[10px] font-semibold uppercase text-sky-600">
                                    AI
                                  </span>
                                )}
                                {item.status === "needs_human_review" && (
                                  <StatusPill status="needs_human_review" />
                                )}
                                {unique && (
                                  <span className="ml-auto text-[10px] font-semibold uppercase text-amber-700">
                                    differs
                                  </span>
                                )}
                              </div>
                              <div className="text-xs text-slate-500">{item.why}</div>
                            </li>
                          );
                        })}
                      </ul>
                    </div>
                    <details className="text-sm">
                      <summary className="cursor-pointer text-sky-600">Draft letter</summary>
                      <pre className="mt-2 whitespace-pre-wrap rounded-lg border border-slate-200 bg-slate-50 p-3 font-sans text-xs text-slate-700">
                        {r.draft_letter}
                      </pre>
                    </details>
                    <div className="text-xs text-slate-400">
                      {r.citations.length} citations · {r.trace.tokens} tokens · est.{" "}
                      {r.trace.cost_cents}¢
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          );
        })()}
    </div>
  );
}
