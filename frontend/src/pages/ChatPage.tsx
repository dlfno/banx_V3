import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";
import { api, openChatSocket } from "../api";
import type { Agent, MemoryItem, Message, WsEvent } from "../types";
import AgentCard from "../components/AgentCard";
import MessageBubble from "../components/MessageBubble";
import type { ToolTrace } from "../components/ToolCallTrace";

type Bubble = {
  id: string;
  role: "user" | "assistant";
  content: string;
  trace: ToolTrace[];
  pending?: boolean;
  agentId?: number;
};

export default function ChatPage() {
  const { agentId, sessionId: sessionIdParam } = useParams();
  const navigate = useNavigate();
  const agents = useQuery({ queryKey: ["agents"], queryFn: api.listAgents });

  const [sessionId, setSessionId] = useState<number | null>(null);
  const [sessionAgentId, setSessionAgentId] = useState<number | null>(null);
  const [bubbles, setBubbles] = useState<Bubble[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const scrollerRef = useRef<HTMLDivElement | null>(null);

  const selectedAgent = useMemo<Agent | undefined>(() => {
    if (!agents.data) return undefined;
    if (sessionAgentId) return agents.data.find((a) => a.id === sessionAgentId);
    if (agentId) return agents.data.find((a) => String(a.id) === agentId);
    return agents.data[0];
  }, [agents.data, agentId, sessionAgentId]);

  const memory = useQuery<MemoryItem[]>({
    queryKey: ["memory", selectedAgent?.id],
    queryFn: () => api.getAgentMemory(selectedAgent!.id),
    enabled: !!selectedAgent,
  });

  // Mode A: load existing session from URL
  useEffect(() => {
    if (!sessionIdParam) return;
    const sid = Number(sessionIdParam);
    let cancelled = false;
    (async () => {
      try {
        const prior: Message[] = await api.listChatMessages(sid);
        if (cancelled) return;
        setSessionId(sid);
        setBubbles(
          prior.map((m) => ({
            id: `db-${m.id}`,
            role: m.role === "user" ? "user" : "assistant",
            content: m.content,
            trace: [],
            agentId: m.agent_id ?? undefined,
          })),
        );
        const firstAgentMsg = prior.find((m) => m.agent_id != null);
        if (firstAgentMsg?.agent_id != null) setSessionAgentId(firstAgentMsg.agent_id);
      } catch {
        /* sesión no encontrada */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [sessionIdParam]);

  // Mode B: create new session when agent changes (no :sessionId in URL)
  useEffect(() => {
    if (sessionIdParam) return;
    if (!selectedAgent) return;
    let cancelled = false;
    (async () => {
      const session = await api.createChatSession(selectedAgent.id);
      if (cancelled) return;
      setSessionId(session.id);
      setSessionAgentId(selectedAgent.id);
      setBubbles([]);
    })();
    return () => {
      cancelled = true;
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, [sessionIdParam, selectedAgent?.id]);

  useEffect(() => {
    if (!sessionId) return;
    const ws = openChatSocket(sessionId, handleEvent);
    wsRef.current = ws;
    return () => ws.close();
  }, [sessionId]);

  useEffect(() => {
    scrollerRef.current?.scrollTo({ top: scrollerRef.current.scrollHeight, behavior: "smooth" });
  }, [bubbles]);

  function handleEvent(ev: WsEvent) {
    setBubbles((prev) => {
      const lastIdx = prev.length - 1;
      const last = prev[lastIdx];
      const replaceLast = (patch: Partial<Bubble>) => {
        const updated = [...prev];
        updated[lastIdx] = { ...last, ...patch };
        return updated;
      };
      if (ev.type === "turn_start") {
        return [
          ...prev,
          {
            id: `assistant-${Date.now()}`,
            role: "assistant",
            content: "",
            trace: [],
            pending: true,
            agentId: ev.agent_id,
          },
        ];
      }
      if (ev.type === "token") {
        if (last && last.role === "assistant" && last.pending) {
          return replaceLast({ content: last.content + ev.delta });
        }
        return prev;
      }
      if (ev.type === "tool_start") {
        if (last && last.role === "assistant" && last.pending) {
          return replaceLast({
            trace: [...last.trace, { id: ev.id, name: ev.name, args: ev.args }],
          });
        }
        return prev;
      }
      if (ev.type === "tool_end") {
        if (last && last.role === "assistant" && last.pending) {
          return replaceLast({
            trace: last.trace.map((t) => (t.id === ev.id ? { ...t, output: ev.output } : t)),
          });
        }
        return prev;
      }
      if (ev.type === "final") {
        setSending(false);
        if (last && last.role === "assistant" && last.pending) {
          return replaceLast({
            pending: false,
            content: last.content || ev.text || "",
          });
        }
        return prev;
      }
      if (ev.type === "error") {
        setSending(false);
        return [
          ...prev,
          {
            id: `error-${Date.now()}`,
            role: "assistant",
            content: `⚠️ ${ev.message}`,
            trace: [],
          },
        ];
      }
      return prev;
    });
  }

  function send() {
    if (!input.trim() || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    const user: Bubble = { id: `user-${Date.now()}`, role: "user", content: input, trace: [] };
    setBubbles((b) => [...b, user]);
    wsRef.current.send(JSON.stringify({ type: "user", content: input }));
    setInput("");
    setSending(true);
  }

  return (
    <div className="max-w-6xl mx-auto p-4 grid grid-cols-12 gap-4 h-[calc(100vh-60px)]">
      <aside className="col-span-3 space-y-2 overflow-auto">
        <h2 className="font-semibold text-sm text-stone-700 mb-1">Miembros de la Junta</h2>
        {agents.data?.map((a) => (
          <AgentCard
            key={a.id}
            agent={a}
            selected={selectedAgent?.id === a.id}
            onClick={() => navigate(`/chat/${a.id}`)}
          />
        ))}
        {memory.data && memory.data.length > 0 && (
          <div className="mt-4 p-3 rounded border border-stone-200 bg-white text-xs text-stone-700">
            <div className="font-semibold mb-1">Memoria persistente</div>
            <ul className="space-y-1 list-disc pl-4">
              {memory.data.slice(0, 6).map((m) => (
                <li key={m.id}>
                  <span className="text-stone-400 mr-1">[{m.kind}]</span>
                  {m.content.length > 140 ? m.content.slice(0, 140) + "…" : m.content}
                </li>
              ))}
            </ul>
          </div>
        )}
      </aside>

      <section className="col-span-9 flex flex-col rounded-xl border border-stone-200 bg-stone-50">
        <div className="px-4 py-3 border-b border-stone-200 bg-white flex items-center gap-3">
          <span className="text-xl">{selectedAgent?.avatar}</span>
          <div>
            <div className="font-medium">{selectedAgent?.display_name}</div>
            <div className="text-xs text-stone-500">{selectedAgent?.role} — {selectedAgent?.stance}</div>
          </div>
        </div>
        <div ref={scrollerRef} className="flex-1 overflow-auto px-4 py-3">
          {bubbles.length === 0 && (
            <p className="text-sm text-stone-500">
              Inicia la conversación. El agente puede usar herramientas (web_search, datos macro, calculadora).
            </p>
          )}
          {bubbles.map((b) => (
            <MessageBubble
              key={b.id}
              who={b.role === "user" ? "Tú" : selectedAgent?.display_name || "Agente"}
              avatar={b.role === "user" ? "🧑" : selectedAgent?.avatar}
              role={b.role}
              content={b.content}
              trace={b.trace}
              pending={b.pending}
            />
          ))}
        </div>
        <div className="border-t border-stone-200 p-3 bg-white flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
            placeholder="Escribe tu mensaje…"
            className="flex-1 border border-stone-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-banxico-500"
          />
          <button
            onClick={send}
            disabled={sending || !input.trim()}
            className="bg-banxico-600 hover:bg-banxico-700 disabled:opacity-50 text-white rounded-lg px-4"
          >
            Enviar
          </button>
        </div>
      </section>
    </div>
  );
}
