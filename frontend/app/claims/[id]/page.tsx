"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

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
import {
  api,
  Claimant,
  ClaimResponse,
  DocumentUploadResponse,
  RequiredItem,
} from "@/lib/api";

const DOC_TYPES = [
  "drivers_license",
  "passport",
  "state_id",
  "utility_bill",
  "bank_statement",
  "death_certificate",
];

export default function ClaimWorkspace() {
  const params = useParams();
  const id = params.id as string;

  const [claim, setClaim] = useState<ClaimResponse | null>(null);
  const [claimant, setClaimant] = useState<Claimant | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [showTrace, setShowTrace] = useState(false);

  const [docType, setDocType] = useState("drivers_license");
  const [rawText, setRawText] = useState("");
  const [uploading, setUploading] = useState(false);
  const [lastUpload, setLastUpload] = useState<DocumentUploadResponse | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const c = await api.getClaim(id);
        setClaim(c);
        const cl = await api.getClaimant(c.claimant_id);
        setClaimant(cl);
        setRawText(
          `${c.state} DRIVER LICENSE\nDL A1234567\nNAME: ${cl.full_name}\nDOB: 05/04/1990\nEXP: 05/04/2029`
        );
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      }
    })();
  }, [id]);

  const citationText = (chunkId: string | null): string | null => {
    if (!chunkId || !claim) return null;
    return claim.citations.find((c) => c.chunk_id === chunkId)?.text ?? null;
  };

  function toggle(label: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(label)) next.delete(label);
      else next.add(label);
      return next;
    });
  }

  async function onUpload() {
    setUploading(true);
    setError(null);
    try {
      const resp = await api.uploadDocument(id, { raw_text: rawText, doc_type_hint: docType });
      setLastUpload(resp);
      setClaim((prev) =>
        prev
          ? {
              ...prev,
              required_items: resp.required_items,
              status: resp.status,
              needs_human_review: resp.needs_human_review,
            }
          : prev
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setUploading(false);
    }
  }

  if (error) return <ErrorNote message={error} />;
  if (!claim) return <Spinner label="loading claim…" />;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <StateBadge state={claim.state} large />
          <div>
            <div className="font-semibold text-slate-900">
              Claim workspace{claimant ? ` — ${claimant.full_name}` : ""}
            </div>
            <div className="text-xs text-slate-500">claim {claim.claim_id.slice(0, 8)}</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <StatusPill status={claim.status} />
          {claim.needs_human_review && <StatusPill status="needs_human_review" />}
          <Button variant="ghost" onClick={() => setShowTrace((v) => !v)}>
            {showTrace ? "Hide trace" : "Trace"}
          </Button>
        </div>
      </div>

      {showTrace && (
        <Card className="p-4 bg-slate-50">
          <div className="text-xs font-semibold text-slate-500 uppercase mb-2">
            Pipeline trace · {claim.trace.retrieval_hits} retrieval hits · {claim.trace.tokens}{" "}
            tokens · est. {claim.trace.cost_cents}¢
          </div>
          <ol className="space-y-1 text-sm text-slate-600">
            {claim.trace.steps.map((s, i) => (
              <li key={i}>
                <span className="font-mono text-xs text-sky-700">{s.step}</span> — {s.detail}
              </li>
            ))}
          </ol>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Required documents checklist */}
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-slate-500 uppercase">Required documents</h2>
          {claim.required_items.map((item: RequiredItem) => {
            const isOpen = expanded.has(item.label);
            const cite = citationText(item.source_rule_chunk_id);
            return (
              <Card key={item.label} className="p-4">
                <div className="flex items-start gap-3">
                  <span
                    className={`mt-0.5 h-4 w-4 shrink-0 rounded-full border ${
                      item.satisfied_by_uploaded_doc
                        ? "bg-emerald-500 border-emerald-500"
                        : "border-slate-300"
                    }`}
                  />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-slate-900">{item.label}</span>
                      <span className="text-xs text-slate-400">{item.requirement}</span>
                      {item.status === "needs_human_review" && (
                        <StatusPill status="needs_human_review" />
                      )}
                    </div>
                    <p className="text-sm text-slate-600">{item.why}</p>
                    <button
                      onClick={() => toggle(item.label)}
                      className="mt-1 text-xs font-medium text-sky-600 hover:underline"
                    >
                      {isOpen ? "Hide cited rule" : "Show cited rule"}
                    </button>
                    {isOpen && (
                      <div className="mt-2 rounded-lg bg-slate-50 border border-slate-200 p-3 text-xs text-slate-700 whitespace-pre-wrap font-mono">
                        {cite ??
                          (item.source_rule_chunk_id
                            ? `Grounded in ${claim.state} rules (chunk ${item.source_rule_chunk_id.slice(
                                0,
                                8
                              )}).`
                            : "No citation — routed to human review.")}
                      </div>
                    )}
                  </div>
                </div>
              </Card>
            );
          })}
        </div>

        {/* Draft letter */}
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-slate-500 uppercase">Draft claimant letter</h2>
          <Card className="p-4">
            <pre className="whitespace-pre-wrap text-sm text-slate-700 font-sans">
              {claim.draft_letter}
            </pre>
          </Card>
        </div>
      </div>

      {/* Document upload */}
      <div className="space-y-3">
        <h2 className="text-sm font-semibold text-slate-500 uppercase">Upload a document</h2>
        <Card className="p-4 space-y-3">
          <div className="grid gap-3 sm:grid-cols-[200px_1fr]">
            <Field label="Document type">
              <select
                className={inputClass}
                value={docType}
                onChange={(e) => setDocType(e.target.value)}
              >
                {DOC_TYPES.map((d) => (
                  <option key={d} value={d}>
                    {d.replace(/_/g, " ")}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Document text (synthetic sample)">
              <textarea
                className={`${inputClass} h-28 font-mono`}
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
              />
            </Field>
          </div>
          <div className="flex items-center gap-3">
            <Button onClick={onUpload} disabled={uploading}>
              {uploading ? "Extracting…" : "Extract & check"}
            </Button>
            {uploading && <Spinner label="running extraction…" />}
          </div>

          {lastUpload && (
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm">
              <div className="text-slate-700">
                Extracted <strong>{lastUpload.extracted.doc_type}</strong>
                {lastUpload.extracted.name ? ` · ${lastUpload.extracted.name}` : ""}
              </div>
              {lastUpload.satisfied_labels.length > 0 && (
                <div className="text-emerald-700">
                  ✓ satisfied: {lastUpload.satisfied_labels.join(", ")}
                </div>
              )}
              {lastUpload.mismatches.length > 0 && (
                <ul className="text-rose-700">
                  {lastUpload.mismatches.map((m, i) => (
                    <li key={i}>⚠ {m}</li>
                  ))}
                </ul>
              )}
              <div className="text-slate-500">
                claim status now <StatusPill status={lastUpload.status} />
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
