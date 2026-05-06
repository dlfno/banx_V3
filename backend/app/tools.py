from __future__ import annotations

import logging
from typing import Any

import httpx
from langchain_core.tools import tool

from .config import settings

log = logging.getLogger(__name__)

# Series del SIE de Banxico que se consultan en vivo cuando BANXICO_TOKEN está configurado.
_SIE_BASE = "https://www.banxico.org.mx/SieAPIRest/service/v1"
_SIE_RATES_SERIES = "SF61745,SF43718,SF43936,SL11578"   # tasa obj, USD/MXN, fed funds, desempleo
_SIE_INPC_SERIES = "SP1,SP30577"                        # INPC general y subyacente (YoY vía incremento)

# Snapshot de respaldo con valores observados al 5 de mayo de 2026.
# Se usa cuando BANXICO_TOKEN no está configurado o la API del SIE falla.
_MACRO_SNAPSHOT_FALLBACK: dict[str, Any] = {
    "as_of": "2026-05-05",

    # Banxico — última decisión 26/mar/2026 (recorte sorpresa a 6.75 %).
    # Se anticipa un posible recorte adicional a 6.50 % en la reunión de mayo.
    "banxico_target_rate_pct": 6.75,

    # Fed — rango objetivo mantenido en 3.50–3.75 % en reunión del 29/abr/2026.
    "fed_funds_upper_pct": 3.75,

    # INPC general anual — marzo 2026 (dato mensual más reciente, INEGI 9/abr/2026).
    # 1Q-abril 2026 (quincenal) ya marcó 4.53 %; dato mensual de abril se publica 7/mayo.
    "inpc_yoy_pct": 4.59,

    # Subyacente anual — marzo 2026 (INEGI).
    "inpc_subyacente_yoy_pct": 4.45,

    # Servicios anual — marzo 2026 (INEGI, cuadro 1).
    "inpc_servicios_yoy_pct": 4.51,

    # Mercancías anual — marzo 2026 (INEGI, cuadro 1).
    "inpc_mercancias_yoy_pct": 4.38,

    # Expectativas inflación 12 meses — encuesta Banxico a analistas privados (may/2026).
    # Los analistas elevaron su estimación de inflación general 2026 a 4.35 %.
    "expectativas_inflacion_12m_pct": 4.35,

    # USD/MXN — cierre del 5/may/2026 (Infobae / Dow Jones).
    "usd_mxn": 17.38,

    # PIB a/a — estimación oportuna 1T-2026 (INEGI): +0.2 % a/a.
    # Consenso analistas privados para todo 2026: ~1.2 % (encuesta Banxico, may/2026).
    "pib_yoy_pct": 0.2,

    # Desempleo — marzo 2026, cifra desestacionalizada (ENOE/INEGI, 24/abr/2026).
    "tasa_desempleo_pct": 2.8,

    # Meta de inflación Banxico (sin cambio).
    "objetivo_inflacion_pct": 3.00,

    "fuente": (
        "Datos observados al 05-may-2026. "
        "Fuentes: INEGI (INPC mar-2026, ENOE mar-2026, PIB 1T-2026 est. oportuna), "
        "Banxico (decisión 26-mar-2026, encuesta analistas may-2026), "
        "Fed FOMC (reunión 29-abr-2026), "
        "Infobae/Dow Jones (USD/MXN cierre 05-may-2026)."
    ),
}


def _fetch_sie_snapshot(token: str) -> dict | None:
    """Consulta la API REST del SIE de Banxico y devuelve un dict con los valores más recientes.
    Devuelve None si el token es inválido o la API no responde en 8 segundos."""
    headers = {"Bmx-Token": token, "Accept": "application/json"}
    result: dict[str, Any] = {}

    try:
        with httpx.Client(timeout=8.0) as client:
            # ── Tasas y tipo de cambio ──────────────────────────────────────────────
            r1 = client.get(
                f"{_SIE_BASE}/series/{_SIE_RATES_SERIES}/datos/oportuno",
                headers=headers,
            )
            r1.raise_for_status()
            for serie in r1.json()["bmx"]["series"]:
                sid = serie["idSerie"]
                datos = serie.get("datos") or []
                if not datos:
                    continue
                raw = datos[0].get("dato", "N/E")
                if raw in ("N/E", ""):
                    continue
                val = float(raw)
                fecha = datos[0].get("fecha", "")  # DD/MM/YYYY

                if sid == "SF61745":
                    result["banxico_target_rate_pct"] = val
                    if fecha:
                        d, m, y = fecha.split("/")
                        result["as_of"] = f"{y}-{m}-{d}"
                elif sid == "SF43718":
                    result["usd_mxn"] = val
                elif sid == "SF43936":
                    result["fed_funds_upper_pct"] = val
                elif sid == "SL11578":
                    result["tasa_desempleo_pct"] = val

            # ── INPC variación anual ────────────────────────────────────────────────
            r2 = client.get(
                f"{_SIE_BASE}/series/{_SIE_INPC_SERIES}/datos/oportuno",
                headers=headers,
                params={"incremento": "PorcAnual"},
            )
            r2.raise_for_status()
            for serie in r2.json()["bmx"]["series"]:
                sid = serie["idSerie"]
                datos = serie.get("datos") or []
                if not datos:
                    continue
                raw = datos[0].get("dato", "N/E")
                if raw in ("N/E", ""):
                    continue
                val = float(raw)
                if sid == "SP1":
                    result["inpc_yoy_pct"] = val
                elif sid == "SP30577":
                    result["inpc_subyacente_yoy_pct"] = val

        return result if result else None

    except Exception as exc:
        log.warning("SIE API no disponible, usando snapshot de respaldo: %s", exc)
        return None


@tool("get_macro_snapshot", return_direct=False)
def get_macro_snapshot() -> dict:
    """Devuelve un snapshot reciente de variables macro relevantes para la decisión de política monetaria
    (tasa Banxico vigente, tasa Fed, INPC headline y subyacente, expectativas, USD/MXN, PIB, desempleo).
    Úsala antes de argumentar para anclar tus cifras."""
    snapshot = dict(_MACRO_SNAPSHOT_FALLBACK)

    if settings.BANXICO_TOKEN:
        live = _fetch_sie_snapshot(settings.BANXICO_TOKEN)
        if live:
            snapshot.update(live)
            snapshot["fuente"] = "Banxico SIE API (datos en vivo)"
        else:
            snapshot["fuente"] += " [SIE no disponible, usando respaldo]"

    return snapshot


@tool("calculator", return_direct=False)
def calculator(expression: str) -> str:
    """Evalúa una expresión aritmética simple. Acepta +, -, *, /, **, paréntesis y números.
    Útil para diferenciales de tasa, conversiones simples y porcentajes."""
    import numexpr

    try:
        value = numexpr.evaluate(expression).item()
        return str(value)
    except Exception as exc:  # pragma: no cover - defensive
        return f"calculator error: {exc}"


@tool("web_search", return_direct=False)
def web_search(query: str) -> str:
    """Busca en la web información reciente relevante (datos macro, declaraciones de la Fed, comunicados de Banxico,
    noticias de mercado). Devuelve título, URL y extracto de los principales resultados.
    Si no hay TAVILY_API_KEY configurada, devuelve un mensaje indicándolo."""
    if not settings.TAVILY_API_KEY:
        return "web_search no disponible: configurar TAVILY_API_KEY en el backend."
    try:
        from langchain_community.tools import TavilySearchResults

        searcher = TavilySearchResults(max_results=5, tavily_api_key=settings.TAVILY_API_KEY)
        results = searcher.invoke({"query": query})
        if not results:
            return "Sin resultados."
        lines = []
        for r in results:
            title = r.get("title", "(sin título)")
            url = r.get("url", "")
            content = (r.get("content") or "").strip().replace("\n", " ")
            if len(content) > 400:
                content = content[:400] + "…"
            lines.append(f"- {title}\n  {url}\n  {content}")
        return "\n".join(lines)
    except Exception as exc:  # pragma: no cover - network/dep dependent
        return f"web_search error: {exc}"


ALL_TOOLS = [get_macro_snapshot, calculator, web_search]


def tools_by_name() -> dict:
    return {t.name: t for t in ALL_TOOLS}
