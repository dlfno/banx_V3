import type { Agent } from "../types";

export type VoteEntry = { agent_id: number; agent: string; decision_bps: number; rationale: string };

const formatBps = (bps: number) => (bps > 0 ? `+${bps}` : `${bps}`);

export default function VoteTally({
  votes,
  agents,
  decision,
}: {
  votes: VoteEntry[];
  agents: Agent[];
  decision: number | null;
}) {
  if (!votes.length && decision === null) return null;
  const byId = Object.fromEntries(agents.map((a) => [a.id, a]));
  return (
    <div className="rounded-lg border border-stone-200 bg-white p-3">
      <h3 className="font-semibold text-sm mb-2">Votación</h3>
      <ul className="text-sm space-y-2">
        {votes.map((v) => {
          const a = byId[v.agent_id];
          const isFallback = v.rationale?.startsWith("Voto no parseable");
          return (
            <li key={v.agent_id}>
              <div className="flex items-baseline gap-2">
                <span className="text-stone-500 w-6">{a?.avatar}</span>
                <span className="flex-1 truncate">{v.agent}</span>
                <span className={`font-mono font-semibold ${isFallback ? "text-amber-600" : ""}`}>
                  {formatBps(v.decision_bps)} bps
                </span>
              </div>
              {v.rationale && (
                <p className={`text-xs ml-8 mt-0.5 leading-snug ${isFallback ? "text-amber-600 italic" : "text-stone-400"}`}>
                  {v.rationale}
                </p>
              )}
            </li>
          );
        })}
      </ul>
      {decision !== null && (
        <div className="mt-3 pt-3 border-t border-stone-200">
          <div className="text-xs text-stone-500">Decisión final</div>
          <div className="text-2xl font-semibold text-banxico-700">{formatBps(decision)} bps</div>
        </div>
      )}
    </div>
  );
}
