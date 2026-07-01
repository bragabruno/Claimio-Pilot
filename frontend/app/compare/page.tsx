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
import { api, ClaimPreviewResponse } from "@/lib/api";

const STATES = ["CA", "NY", "TX", "FL", "IL"];

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

  const labelsA = new Set(results?.[0].required_items.map((i) => i.label));
  const labelsB = new Set(results?.[1].required_items.map((i) => i.label));

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

      {results && (
        <div className="grid gap-4 md:grid-cols-2">
          {results.map((r, idx) => {
            const otherLabels = idx === 0 ? labelsB : labelsA;
            return (
              <Card key={r.state + idx} className="p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <StateBadge state={r.state} large />
                  {r.needs_human_review && <StatusPill status="needs_human_review" />}
                </div>
                <div>
                  <div className="text-xs font-semibold text-slate-500 uppercase mb-2">
                    Required documents
                  </div>
                  <ul className="space-y-2">
                    {r.required_items.map((item) => {
                      const unique = !otherLabels.has(item.label);
                      return (
                        <li
                          key={item.label}
                          className={`rounded-lg border p-2.5 ${
                            unique
                              ? "border-amber-300 bg-amber-50"
                              : "border-slate-200 bg-white"
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-slate-900">{item.label}</span>
                            {unique && (
                              <span className="text-[10px] font-semibold uppercase text-amber-700">
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
                  <pre className="mt-2 whitespace-pre-wrap rounded-lg bg-slate-50 border border-slate-200 p-3 text-xs text-slate-700 font-sans">
                    {r.draft_letter}
                  </pre>
                </details>
                <div className="text-xs text-slate-400">
                  {r.citations.length} citations · {r.trace.tokens} tokens · est.{" "}
                  {r.trace.cost_cents}¢
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
