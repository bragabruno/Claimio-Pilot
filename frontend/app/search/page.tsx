"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import {
  Button,
  Card,
  ConfidenceBar,
  ErrorNote,
  Field,
  Spinner,
  StateBadge,
  inputClass,
} from "@/components/ui";
import { api, Candidate, money, PropertySearchResponse } from "@/lib/api";

function splitList(value: string): string[] {
  return value
    .split(/[,\n]/)
    .map((s) => s.trim())
    .filter(Boolean);
}

export default function SearchPage() {
  const router = useRouter();
  const [name, setName] = useState("Allison Hill");
  const [priors, setPriors] = useState("Noah Rhodes");
  const [addresses, setAddresses] = useState("");
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PropertySearchResponse | null>(null);
  const [claimantId, setClaimantId] = useState<string | null>(null);

  async function onSearch(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const prior_names = splitList(priors);
      const addrs = splitList(addresses);
      const claimant = await api.createClaimant({
        full_name: name,
        prior_names,
        addresses: addrs,
        is_business: false,
      });
      setClaimantId(claimant.id);
      const res = await api.searchProperties({ name, prior_names, addresses: addrs });
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function onCreateClaim(c: Candidate) {
    if (!claimantId) return;
    setCreating(c.property_id);
    setError(null);
    try {
      const claim = await api.createClaim(claimantId, c.property_id);
      router.push(`/claims/${claim.claim_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setCreating(null);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Search &amp; reconcile</h1>
        <p className="text-sm text-slate-600">
          Match a claimant against the unclaimed-property index. Former names and old addresses are
          handled.
        </p>
      </div>

      <Card className="p-5">
        <form onSubmit={onSearch} className="grid gap-4 sm:grid-cols-3">
          <Field label="Current full name">
            <input className={inputClass} value={name} onChange={(e) => setName(e.target.value)} />
          </Field>
          <Field label="Prior names" hint="comma-separated">
            <input
              className={inputClass}
              value={priors}
              onChange={(e) => setPriors(e.target.value)}
            />
          </Field>
          <Field label="Addresses" hint="comma-separated (optional)">
            <input
              className={inputClass}
              value={addresses}
              onChange={(e) => setAddresses(e.target.value)}
            />
          </Field>
          <div className="sm:col-span-3 flex items-center gap-3">
            <Button type="submit" disabled={loading}>
              {loading ? "Searching…" : "Search property index"}
            </Button>
            {loading && <Spinner label="matching…" />}
          </div>
        </form>
      </Card>

      {error && <ErrorNote message={error} />}

      {result && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-x-6 gap-y-1 text-sm text-slate-600">
            <span>
              <strong className="text-slate-900">{result.candidate_count}</strong> candidates from{" "}
              <strong className="text-slate-900">{result.blocking_count}</strong> blocked
            </span>
            <span className="text-slate-400">|</span>
            <span>
              Data quality: {result.data_quality_summary.total_records} records ·{" "}
              {result.data_quality_summary.missing_address_pct}% missing address ·{" "}
              {result.data_quality_summary.duplicate_groups} dup group(s) · merged{" "}
              {result.data_quality_summary.duplicates_merged}
            </span>
          </div>

          {result.candidates.length === 0 && (
            <Card className="p-5 text-sm text-slate-600">No candidates matched.</Card>
          )}

          <div className="space-y-3">
            {result.candidates.map((c) => (
              <Card key={c.property_id} className="p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <StateBadge state={c.source_state} />
                      <span className="font-medium text-slate-900">{c.owner_name}</span>
                      {c.owner_deceased && (
                        <span className="text-xs text-rose-600">deceased owner</span>
                      )}
                    </div>
                    <div className="text-sm text-slate-500">
                      {money(c.amount_cents)} · {c.property_type.replace(/_/g, " ")} · held by{" "}
                      {c.holder_name}
                    </div>
                    <ul className="mt-1 space-y-0.5 text-sm text-slate-600">
                      {c.match_reasons.map((r, i) => (
                        <li key={i}>↳ {r}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="flex flex-col items-end gap-3">
                    <ConfidenceBar value={c.confidence} />
                    <Button
                      variant="ghost"
                      onClick={() => onCreateClaim(c)}
                      disabled={creating === c.property_id}
                    >
                      {creating === c.property_id ? "Creating…" : "Create claim →"}
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
