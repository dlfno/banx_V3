import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../api";

function fmtDate(iso: string | null | undefined): string {
  if (!iso) return "";
  return new Date(iso).toLocaleString();
}

export default function HomePage() {
  const meetings = useQuery({ queryKey: ["meetings"], queryFn: api.listMeetings });
  const chats = useQuery({ queryKey: ["chat-sessions"], queryFn: api.listChatSessions });

  return (
    <div className="max-w-6xl mx-auto p-6">
      <p className="text-stone-600 mb-6 max-w-2xl">
        Simulador multi-agente de la Junta de Gobierno del Banco de México. Cinco miembros con posturas
        distintas debaten, votan y emiten minuta. Puedes hablar 1-a-1 con un miembro o iniciar una junta.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Link
          to="/chat"
          className="rounded-xl border border-stone-200 bg-white p-5 hover:border-banxico-500 hover:shadow-sm transition"
        >
          <div className="text-2xl mb-2">💬</div>
          <h2 className="font-semibold text-lg">Chat 1-a-1</h2>
          <p className="text-sm text-stone-600">
            Habla con un miembro específico. Cada agente conserva memoria persistente entre sesiones y entre modos.
          </p>
        </Link>
        <Link
          to="/meeting"
          className="rounded-xl border border-stone-200 bg-white p-5 hover:border-banxico-500 hover:shadow-sm transition"
        >
          <div className="text-2xl mb-2">🏛️</div>
          <h2 className="font-semibold text-lg">Simulación de Junta</h2>
          <p className="text-sm text-stone-600">
            Define un tema y ejecuta una junta completa: aperturas, debate, votación y minuta automática.
          </p>
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-10">
        <section>
          <h2 className="font-semibold mb-3">Juntas previas</h2>
          {meetings.isLoading && <p className="text-stone-500 text-sm">Cargando…</p>}
          {meetings.data?.length === 0 && (
            <p className="text-stone-500 text-sm">Aún no hay juntas. Inicia una desde la tarjeta de arriba.</p>
          )}
          <ul className="space-y-2">
            {meetings.data?.map((m) => (
              <li key={m.id}>
                <Link
                  to={`/meeting/${m.id}`}
                  className="block rounded border border-stone-200 bg-white p-3 hover:border-stone-400"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium truncate">{m.topic}</span>
                    <span className="font-mono text-sm text-banxico-700">
                      {m.decision_bps !== null
                        ? (m.decision_bps > 0 ? `+${m.decision_bps}` : `${m.decision_bps}`) + " bps"
                        : "en curso"}
                    </span>
                  </div>
                  <div className="text-xs text-stone-500 flex items-center gap-2">
                    <span>{fmtDate(m.started_at)}</span>
                    <span>·</span>
                    <span>creado por <span className="font-medium text-stone-700">{m.created_by.display_name}</span></span>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </section>

        <section>
          <h2 className="font-semibold mb-3">Chats previos</h2>
          {chats.isLoading && <p className="text-stone-500 text-sm">Cargando…</p>}
          {chats.data?.length === 0 && (
            <p className="text-stone-500 text-sm">Aún no hay chats. Inicia uno desde la tarjeta de arriba.</p>
          )}
          <ul className="space-y-2">
            {chats.data?.map((c) => (
              <li key={c.id}>
                <Link
                  to={`/chat/session/${c.id}`}
                  className="block rounded border border-stone-200 bg-white p-3 hover:border-stone-400"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium truncate">
                      <span className="mr-1">{c.agent_avatar}</span>
                      {c.agent_name}
                    </span>
                    <span className="text-xs text-stone-500">{c.message_count} mensajes</span>
                  </div>
                  <div className="text-xs text-stone-500 flex items-center gap-2">
                    <span>
                      {c.last_message_at
                        ? `último: ${fmtDate(c.last_message_at)}`
                        : `iniciado: ${fmtDate(c.started_at)}`}
                    </span>
                    <span>·</span>
                    <span>chateó <span className="font-medium text-stone-700">{c.created_by.display_name}</span></span>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
