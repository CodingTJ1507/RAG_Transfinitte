'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, Play, RefreshCw, CheckCircle2, XCircle, AlertCircle, Loader2, BarChart3, Check } from 'lucide-react';
import { API_BASE_URL } from '../../lib/api';
import { EvaluationReport, EvaluationCaseResult } from '../../lib/types';

function MetricTile({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <div className="bg-white rounded-xl border border-[#dde4ec] p-4 shadow-2xs">
      <span className="text-[11px] font-medium text-slate-500 block">{label}</span>
      <span className="text-2xl font-bold text-[#162748] mt-1 block">{value}</span>
      <span className="text-[10px] text-slate-400">{hint}</span>
    </div>
  );
}

function ResultRow({
  row,
  toPct,
}: {
  row: EvaluationCaseResult;
  toPct: (val?: number | null) => string;
}) {
  const expectedSet = new Set(row.expected_source_ids);
  const retrievedSet = new Set(row.retrieved_source_ids);
  const missingExpected = row.expected_source_ids.filter((s) => !retrievedSet.has(s));

  return (
    <tr className="hover:bg-slate-50/60 transition-colors">
      <td className="py-2 px-3 font-mono font-bold text-[#162748]">{row.question_id}</td>
      <td className="py-2 px-3 text-slate-600 capitalize">{row.category.replace('_', ' ')}</td>
      <td className="py-2 px-2 text-center">
        {row.hit ? (
          <CheckCircle2 className="w-4 h-4 text-emerald-600 inline" />
        ) : (
          <XCircle className="w-4 h-4 text-rose-500 inline" />
        )}
      </td>
      <td className="py-2 px-2 text-right font-mono text-slate-700">{toPct(row.recall_at_k)}</td>
      <td className="py-2 px-2 text-right font-mono text-slate-700">{toPct(row.ndcg_at_k)}</td>
      <td className="py-2 px-2 text-right font-mono text-slate-700">{toPct(row.reciprocal_rank)}</td>
      <td className="py-2 px-2 text-center">
        {row.passed ? (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold font-mono bg-emerald-50 text-emerald-700 border border-emerald-200">
            PASS
          </span>
        ) : (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold font-mono bg-rose-50 text-rose-700 border border-rose-200">
            FAIL
          </span>
        )}
      </td>
      <td className="py-2 px-3 space-y-1 max-w-sm">
        <div className="flex flex-wrap gap-1 items-center">
          <span className="text-[10px] text-slate-400 font-mono">Exp:</span>
          {row.expected_source_ids.map((src) => {
            const isMissing = missingExpected.includes(src);
            return (
              <span
                key={src}
                className={`px-1.5 py-0.5 rounded text-[10px] font-mono border ${
                  isMissing
                    ? 'bg-rose-50 text-rose-700 border-rose-300 font-bold'
                    : 'bg-emerald-50 text-emerald-800 border-emerald-300'
                }`}
                title={isMissing ? 'Missing from retrieved top-k' : 'Retrieved'}
              >
                {src}
              </span>
            );
          })}
        </div>
        <div className="flex flex-wrap gap-1 items-center">
          <span className="text-[10px] text-slate-400 font-mono">Got:</span>
          {row.retrieved_source_ids.slice(0, 5).map((src) => (
            <span
              key={src}
              className={`px-1.5 py-0.5 rounded text-[10px] font-mono border ${
                expectedSet.has(src)
                  ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                  : 'bg-slate-100 text-slate-600 border-slate-200'
              }`}
            >
              {src}
            </span>
          ))}
          {row.retrieved_source_ids.length > 5 && (
            <span className="text-[10px] text-slate-400 font-mono">
              +{row.retrieved_source_ids.length - 5} more
            </span>
          )}
        </div>
      </td>
      <td className="py-2 px-3 text-slate-500 max-w-xs">
        {row.failure_reasons.length > 0 ? (
          <ul className="list-disc pl-3 text-[11px] text-rose-600 space-y-0.5">
            {row.failure_reasons.map((reason, idx) => (
              <li key={idx}>{reason}</li>
            ))}
          </ul>
        ) : (
          <span className="text-[11px] text-emerald-600 flex items-center space-x-1">
            <Check className="w-3 h-3" />
            <span>Passed all checks</span>
          </span>
        )}
      </td>
    </tr>
  );
}

export default function BenchmarkPage() {
  const [report, setReport] = useState<EvaluationReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [checkAnswers, setCheckAnswers] = useState(false);

  const runBenchmark = async () => {
    setLoading(true);
    setError(null);
    try {
      const url = `${API_BASE_URL}/api/eval/benchmark?top_k=10${checkAnswers ? '&generate_answers=true' : ''}`;
      const response = await fetch(url, {
        signal: AbortSignal.timeout(120000),
      });

      if (!response.ok) {
        let detail = `Error ${response.status}: Failed to run benchmark`;
        try {
          const body = await response.json();
          if (body?.detail) {
            detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
          }
        } catch {
          // ignore json parse errors
        }
        throw new Error(detail);
      }

      const data: EvaluationReport = await response.json();
      setReport(data);
    } catch (err: unknown) {
      if (err instanceof Error) {
        if (err.name === 'TimeoutError') {
          setError('Benchmark request timed out after 2 minutes. Try running retrieval-only or check server load.');
        } else {
          setError(err.message);
        }
      } else {
        setError('An unexpected error occurred while running the benchmark.');
      }
    } finally {
      setLoading(false);
    }
  };

  const toPct = (val?: number | null) => {
    if (val === undefined || val === null || Number.isNaN(val)) return '—';
    return `${Math.round(val * 100)}%`;
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] text-[#162748] font-sans">
      {/* Top Navigation */}
      <header className="border-b border-[#dde4ec] bg-white px-6 py-4 flex items-center justify-between shadow-2xs">
        <div className="flex items-center space-x-3">
          <Link
            href="/"
            className="p-1.5 rounded-lg text-slate-500 hover:text-[#162748] hover:bg-slate-100 transition-colors cursor-pointer"
            title="Back to Investigation Console"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div className="w-7 h-7 rounded-lg bg-[#162748] flex items-center justify-center p-1 shrink-0 border border-[#09bec1]/30">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/concord-mark.svg" alt="Concord.ai" className="w-4 h-4 object-contain" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-sm font-bold text-[#162748]">Concord.ai Benchmark</h1>
              <span className="text-[10px] uppercase font-semibold font-mono px-1.5 py-0.5 rounded bg-[#09bec1]/15 text-[#087f82] border border-[#09bec1]/30">
                Evaluation
              </span>
            </div>
            <p className="text-[11px] text-slate-500">
              Retrieval & Answer Quality Benchmark across 20 Golden Questions
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <Link
            href="/"
            className="text-xs font-medium text-slate-600 hover:text-[#162748] transition-colors"
          >
            Investigation Console
          </Link>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-6 py-8 space-y-6">
        {/* Controls Card */}
        <section className="bg-white rounded-2xl border border-[#dde4ec] p-5 shadow-2xs space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h2 className="text-sm font-bold text-[#162748]">Run Evaluation Benchmark</h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Evaluates top-k=10 retrieval against ground truth sources across exact identifiers, multi-hop, and conflicting evidence.
              </p>
            </div>

            <div className="flex items-center space-x-4">
              <label className="flex items-center space-x-2 text-xs text-slate-700 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={checkAnswers}
                  onChange={(e) => setCheckAnswers(e.target.checked)}
                  disabled={loading}
                  className="rounded border-[#dde4ec] text-[#09bec1] focus:ring-[#09bec1] cursor-pointer"
                />
                <span>Also check answers (uses about 3 Gemini calls per question)</span>
              </label>

              <button
                onClick={runBenchmark}
                disabled={loading}
                className="px-4 py-2 bg-[#162748] hover:bg-[#1f3660] disabled:bg-slate-300 text-white text-xs font-semibold rounded-xl flex items-center space-x-2 transition-colors cursor-pointer disabled:cursor-not-allowed shadow-2xs"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-[#09bec1]" />
                    <span>Scoring...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 text-[#09bec1]" />
                    <span>Run benchmark</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </section>

        {/* State 1: Idle State */}
        {!loading && !error && !report && (
          <section className="bg-white rounded-2xl border border-[#dde4ec] p-12 text-center shadow-2xs space-y-3">
            <div className="w-12 h-12 rounded-full bg-[#eaf0f6] text-[#162748] flex items-center justify-center mx-auto border border-[#d4dee8]">
              <BarChart3 className="w-6 h-6 text-[#09bec1]" />
            </div>
            <h3 className="text-sm font-bold text-[#162748]">No Benchmark Results Yet</h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
              Click &quot;Run benchmark&quot; above to score the 20 benchmark evaluation questions against expected sources. Results include Hit Rate, Recall@k, nDCG@k, MRR, and Pass Rate.
            </p>
          </section>
        )}

        {/* State 2: Running State */}
        {loading && (
          <section className="bg-white rounded-2xl border border-[#dde4ec] p-12 text-center shadow-2xs space-y-3">
            <div className="w-12 h-12 rounded-full bg-[#09bec1]/10 text-[#09bec1] flex items-center justify-center mx-auto animate-pulse">
              <Loader2 className="w-6 h-6 animate-spin text-[#09bec1]" />
            </div>
            <h3 className="text-sm font-bold text-[#162748]">Scoring 20 questions, about a minute</h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
              Retrieving evidence candidates and computing evaluation metrics for all 20 ground-truth benchmark cases...
            </p>
          </section>
        )}

        {/* State 3: Error State */}
        {error && !loading && (
          <section className="bg-rose-50 border border-rose-200 rounded-2xl p-6 shadow-2xs space-y-3">
            <div className="flex items-center space-x-2 text-rose-800 font-semibold text-xs">
              <AlertCircle className="w-4 h-4 text-rose-600" />
              <span>Benchmark Execution Failed</span>
            </div>
            <p className="text-xs text-rose-700 leading-relaxed font-mono">
              {error}
            </p>
            <div>
              <button
                onClick={runBenchmark}
                className="px-3.5 py-1.5 bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold rounded-lg flex items-center space-x-1.5 transition-colors cursor-pointer"
              >
                <RefreshCw className="w-3 h-3" />
                <span>Retry</span>
              </button>
            </div>
          </section>
        )}

        {/* State 4: Done State */}
        {report && !loading && (
          <div className="space-y-6">
            {/* Aggregate Score Tiles */}
            <section className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              <MetricTile
                label="Hit Rate"
                value={toPct(report.aggregate.hit_rate)}
                hint="top-k hit fraction"
              />
              <MetricTile
                label="Mean Recall"
                value={toPct(report.aggregate.mean_recall_at_k)}
                hint="required sources"
              />
              <MetricTile
                label="MRR"
                value={toPct(report.aggregate.mean_reciprocal_rank)}
                hint="reciprocal rank"
              />
              <MetricTile
                label="Mean nDCG"
                value={toPct(report.aggregate.mean_ndcg_at_k)}
                hint="discounted gain"
              />
              <MetricTile
                label="Pass Rate"
                value={toPct(report.aggregate.pass_rate)}
                hint={`${report.cases_run} test cases`}
              />
              {report.aggregate.mean_faithfulness !== undefined && (
                <MetricTile
                  label="Faithfulness"
                  value={toPct(report.aggregate.mean_faithfulness)}
                  hint="verified claims"
                />
              )}
            </section>

            {/* Questions Table */}
            <section className="bg-white rounded-2xl border border-[#dde4ec] overflow-hidden shadow-2xs">
              <div className="px-5 py-3.5 border-b border-[#dde4ec] flex items-center justify-between">
                <h3 className="text-xs font-bold text-[#162748] uppercase tracking-wider">
                  Test Case Results ({report.results.length} questions)
                </h3>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="bg-slate-50 text-slate-600 border-b border-[#dde4ec]">
                      <th className="py-2.5 px-3 font-semibold">ID</th>
                      <th className="py-2.5 px-3 font-semibold">Category</th>
                      <th className="py-2.5 px-2 font-semibold text-center">Hit</th>
                      <th className="py-2.5 px-2 font-semibold text-right">Recall</th>
                      <th className="py-2.5 px-2 font-semibold text-right">nDCG</th>
                      <th className="py-2.5 px-2 font-semibold text-right">MRR</th>
                      <th className="py-2.5 px-2 font-semibold text-center">Status</th>
                      <th className="py-2.5 px-3 font-semibold">Expected vs Retrieved Sources</th>
                      <th className="py-2.5 px-3 font-semibold">Failure Reasons</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#dde4ec]">
                    {report.results.map((row) => (
                      <ResultRow key={row.question_id} row={row} toPct={toPct} />
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        )}
      </main>
    </div>
  );
}
