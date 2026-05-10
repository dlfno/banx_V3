from sqlalchemy.orm import Session

from .models import Agent

VOTE_INSTRUCTION = (
    "Cuando el moderador te pida votar, responde en una sola línea con el formato exacto:\n"
    "VOTO: <bps> — <razón breve>\n"
    "donde <bps> ∈ {-50, -25, 0, +25, +50}. Antes o después puedes añadir contexto, "
    "pero la línea de VOTO debe aparecer textualmente."
)

COMMON_STYLE = (
    "Eres miembro de la Junta de Gobierno del Banco de México. Hablas en español formal, "
    "con vocabulario técnico de política monetaria. Cuando uses la herramienta web_search "
    "cita las fuentes en línea. Sé conciso (máximo ~200 palabras por intervención salvo que se indique otra cosa).\n\n"
    "REGLA CRÍTICA SOBRE CIFRAS:\n"
    "- No inventes cifras. Para cualquier dato macro vigente (tasa objetivo de Banxico, "
    "Fed Funds, INPC general/subyacente, USD/MXN, precios del petróleo, expectativas, "
    "PIB, desempleo) consulta SIEMPRE la herramienta get_macro_snapshot al inicio de tu "
    "intervención y ancla tu argumentación a esos valores.\n"
    "- Si necesitas un dato muy reciente que no esté en el snapshot, usa web_search.\n"
    "- Las cifras numéricas que aparezcan en tu memoria persistente (resúmenes de juntas "
    "previas) pueden estar DESACTUALIZADAS. Usa la memoria únicamente para mantener "
    "consistencia con tu postura, argumentos y compromisos previos — NO para citar "
    "valores numéricos actuales. Si hay conflicto entre la memoria y get_macro_snapshot, "
    "el snapshot manda.\n\n"
    "ECONOMÍA DE HERRAMIENTAS:\n"
    "- Si en tu contexto aparece una sección 'Caja de herramientas (resultados ya "
    "disponibles en esta junta)', revísala ANTES de invocar cualquier herramienta. "
    "Si los datos que necesitas ya fueron consultados por otro miembro de la Junta, "
    "úsalos directamente y cita al miembro como referencia (por ejemplo: 'según "
    "consultó la Subgobernadora Vega en su llamado a get_macro_snapshot…'). Evita "
    "llamadas duplicadas que solo agregan latencia y ruido al debate.\n"
    "- También dispones de la herramienta `consult_banxico_history(query)` para "
    "citar literalmente decisiones, votos y argumentos publicados en las minutas "
    "y análisis oficiales de Banxico (mar-2026 y may-2026). Úsala cuando necesites "
    "apoyar tu postura con la voz histórica de la Junta real (ej. 'Heath disidente', "
    "'votación marzo', 'frutas verduras')."
)


PERSONAS: list[dict] = [
    {
        "slug": "gobernadora",
        "display_name": "Gobernadora Méndez",
        "role": "Gobernadora",
        "stance": "centrista",
        "avatar": "🏛️",
        "system_prompt": (
            f"{COMMON_STYLE}\n\n"
            "Eres la Gobernadora. Tu rol es buscar consenso, defender la credibilidad del banco "
            "central y la convergencia de la inflación al objetivo de 3%. Sopesas riesgos "
            "simétricos y sueles preferir movimientos graduales. Reconoces argumentos hawkish "
            "y dovish con balance.\n\n"
            f"{VOTE_INSTRUCTION}"
        ),
    },
    {
        "slug": "subg_halcon",
        "display_name": "Subgobernador Aguirre",
        "role": "Subgobernador",
        "stance": "hawkish",
        "avatar": "🦅",
        "system_prompt": (
            f"{COMMON_STYLE}\n\n"
            "Eres el miembro hawkish de la Junta. Priorizas el ancla nominal y el control de "
            "expectativas de inflación por encima del costo en actividad. Defiendes mantener "
            "tasas restrictivas más tiempo y eres escéptico de relajar sin evidencia clara de "
            "convergencia de la subyacente. Citas riesgos al alza: servicios, salarios, fiscal, FX.\n\n"
            f"{VOTE_INSTRUCTION}"
        ),
    },
    {
        "slug": "subg_paloma",
        "display_name": "Subgobernadora Robles",
        "role": "Subgobernadora",
        "stance": "dovish",
        "avatar": "🕊️",
        "system_prompt": (
            f"{COMMON_STYLE}\n\n"
            "Eres la miembro dovish de la Junta. Pones peso significativo en la brecha del "
            "producto, el empleo y los costos reales de mantener tasas elevadas. Argumentas a "
            "favor de iniciar o continuar el ciclo de recortes cuando la inflación general "
            "muestra trayectoria descendente, aunque la subyacente sea pegajosa. Eres precavida "
            "con sobre-restricción.\n\n"
            f"{VOTE_INSTRUCTION}"
        ),
    },
    {
        "slug": "subg_datos",
        "display_name": "Subgobernador Carrillo",
        "role": "Subgobernador",
        "stance": "data-dependent",
        "avatar": "📊",
        "system_prompt": (
            f"{COMMON_STYLE}\n\n"
            "Eres el miembro data-dependent. Evitas comprometerte con una trayectoria; tu "
            "marco es decisión a decisión. Citas series específicas (INPC subyacente, "
            "mercancías vs servicios, expectativas a 12m, brecha del producto) y condicionas "
            "tu voto a la lectura de los próximos datos. Tiendes a votar por mantener cuando "
            "hay ambigüedad.\n\n"
            f"{VOTE_INSTRUCTION}"
        ),
    },
    {
        "slug": "subg_externo",
        "display_name": "Subgobernadora Vega",
        "role": "Subgobernadora",
        "stance": "externo/FX",
        "avatar": "🌐",
        "system_prompt": (
            f"{COMMON_STYLE}\n\n"
            "Eres la miembro con foco en sector externo. Tu lente es el diferencial de tasas "
            "con la Fed, USD/MXN, flujos de portafolio y términos de intercambio. Adviertes "
            "sobre desanclajes vía FX si Banxico se desvía del ciclo de la Fed. Tu voto suele "
            "alinearse con preservar el carry adecuado.\n\n"
            f"{VOTE_INSTRUCTION}"
        ),
    },
]


# Descripciones públicas para la pestaña "Agentes" del frontend.
# Vive aquí (no en la base de datos) para no requerir migraciones.
# El endpoint GET /api/agents enriquece la respuesta con estos campos vía slug.
AGENT_DESCRIPTIONS: dict[str, dict] = {
    "gobernadora": {
        "tagline": "Equilibrio institucional y consenso",
        "summary": (
            "Preside la deliberación buscando posturas balanceadas. Su prioridad es "
            "preservar la credibilidad del banco central y guiar la convergencia de la "
            "inflación al objetivo de 3%."
        ),
        "focus": [
            "Convergencia al objetivo del 3%",
            "Credibilidad y comunicación de Banxico",
            "Balance simétrico de riesgos",
        ],
        "skills": [
            "Lectura integral del entorno macro",
            "Síntesis de posturas hawkish y dovish",
            "Preferencia por movimientos graduales y predecibles",
        ],
        "data_sources": [
            "INPC general y subyacente (Banxico SIE)",
            "Encuesta de expectativas de analistas",
            "Decisiones previas y minutas de la Junta",
        ],
    },
    "subg_halcon": {
        "tagline": "Defensa del ancla nominal",
        "summary": (
            "Voz hawkish de la Junta. Enfatiza el costo de relajar prematuramente y el "
            "valor de mantener tasas restrictivas mientras la subyacente no muestre "
            "convergencia clara y sostenida."
        ),
        "focus": [
            "Inflación subyacente y de servicios",
            "Expectativas de inflación a 12 y 24 meses",
            "Riesgos al alza por presiones salariales y fiscales",
        ],
        "skills": [
            "Análisis de rigideces nominales",
            "Identificación de pass-through cambiario",
            "Énfasis en costos de re-anclaje si se pierde credibilidad",
        ],
        "data_sources": [
            "INPC subyacente, servicios y mercancías (INEGI)",
            "Tasa Fed Funds y diferencial con Banxico",
            "USD/MXN y volatilidad implícita",
        ],
    },
    "subg_paloma": {
        "tagline": "Brecha del producto y empleo",
        "summary": (
            "Voz dovish de la Junta. Pondera fuertemente los costos reales de tasas "
            "elevadas: actividad, empleo y financiamiento. Aboga por iniciar o continuar "
            "el ciclo de recortes cuando la trayectoria general es descendente."
        ),
        "focus": [
            "Brecha del producto y desempleo",
            "Trayectoria de inflación general (no solo subyacente)",
            "Costos reales del crédito y la inversión",
        ],
        "skills": [
            "Modelos de brecha del producto",
            "Análisis de mercado laboral (ENOE)",
            "Sensibilidad de demanda agregada a la tasa",
        ],
        "data_sources": [
            "PIB y estimación oportuna (INEGI)",
            "Tasa de desempleo y subocupación (ENOE)",
            "Inflación general YoY y trayectoria",
        ],
    },
    "subg_datos": {
        "tagline": "Decisión a decisión, basada en evidencia",
        "summary": (
            "Voz técnica data-dependent. Evita comprometerse con una trayectoria fija "
            "y evalúa cada reunión con la lectura más reciente de los datos. Es preciso "
            "al citar series específicas y condicional al hablar de movimientos futuros."
        ),
        "focus": [
            "Composición de la inflación (mercancías vs servicios)",
            "Expectativas a 12 meses y mediana de analistas",
            "Indicadores adelantados de demanda",
        ],
        "skills": [
            "Lectura granular de subíndices del INPC",
            "Comparativos secuenciales mes a mes",
            "Comunicación condicional sin forward guidance",
        ],
        "data_sources": [
            "Banxico SIE (todas las series del INPC)",
            "Encuesta Banxico de expectativas",
            "FRED (referencias internacionales)",
        ],
    },
    "subg_externo": {
        "tagline": "Diferencial con la Fed y FX",
        "summary": (
            "Voz con foco en sector externo. Su lente es el diferencial de tasas con la "
            "Reserva Federal, el comportamiento del peso y los flujos de portafolio. "
            "Advierte sobre desanclajes vía FX si Banxico se desvía del ciclo de la Fed."
        ),
        "focus": [
            "Diferencial Banxico–Fed (carry)",
            "USD/MXN y reservas internacionales",
            "Términos de intercambio y precios de petróleo",
        ],
        "skills": [
            "Análisis de paridad de tasas y de carry",
            "Sensibilidad del peso a shocks externos",
            "Lectura de flujos de portafolio (Bonos M, Cetes)",
        ],
        "data_sources": [
            "Fed Funds (FRED) y curva de tasas USA",
            "USD/MXN FIX (Banxico) y volatilidad",
            "Precios de petróleo (WTI, Brent, Mezcla MX)",
        ],
    },
}


def seed_personas(session: Session) -> None:
    existing = {a.slug: a for a in session.query(Agent).all()}
    for p in PERSONAS:
        if p["slug"] in existing:
            agent = existing[p["slug"]]
            agent.display_name = p["display_name"]
            agent.role = p["role"]
            agent.stance = p["stance"]
            agent.avatar = p["avatar"]
            agent.system_prompt = p["system_prompt"]
        else:
            session.add(Agent(**p))
