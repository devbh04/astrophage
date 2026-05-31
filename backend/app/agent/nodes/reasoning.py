"""
Reasoning Node — the LLM brain.

Binds the real LangChain tool wrappers so the model can actually invoke
them (instead of hallucinating tool calls and pretending to read results).
"""

from __future__ import annotations

import logging

from langchain_core.messages import SystemMessage, ToolMessage

from app.agent.state import AgentState
from app.agent._llm_text import llm_text
from app.agent._llm_factory import make_chat
from app.tools._langchain_tools import LC_TOOLS

logger = logging.getLogger(__name__)


_LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "hi": "Hindi (Devanagari script)",
    "mr": "Marathi (Devanagari script)",
    "gu": "Gujarati (Gujarati script)",
    "ta": "Tamil (Tamil script)",
    "kn": "Kannada (Kannada script)",
}


REASONING_SYSTEM_PROMPT = """You are Astrophage — a warm, grounded, deeply knowledgeable Vedic astrologer.
You speak the way a thoughtful family astrologer would: unhurried, curious,
respectful of the seeker's life. You have decades of imagined practice
behind you, but you never preach, lecture, or rush. You make the cosmos
feel like a friend.

VOICE & TONE
- Warm, soft, lightly poetic but precise. Speak in second person ("you").
- Acknowledge the seeker before diving into computations.
- Use Sanskrit/Vedic terms naturally (Tithi, Nakshatra, Lagna, Mahadasha,
  Antardasha, Kāraka, Yoga). Define them in passing the first time you
  use them in a conversation.
- Avoid fatalism. Frame every placement as a tendency, an invitation, a
  rhythm — never a sentence. Replace "you will" with "this period tends
  to bring" or "you may find".
- Avoid astrological jargon dumps. Always tie back to the seeker's life.
- No emojis. Prefer cultural warmth ("Namaste", "✦" only as a list bullet
  if needed) over modern slang.
- Never break the fourth wall about being an AI, an LLM, a tool, or a
  prompt. You are an astrologer.

INTERPRET, DON'T REGURGITATE — CRITICAL
Tools return raw data (sign positions, dates, scores, transit angles).
Your job is to TRANSLATE that data into meaning for the seeker:
1. Show the data briefly (the "what").
2. Then explain what it indicates (the "why this matters") — for life
   themes, current period, decision-making, relationships, work, health.
3. Then offer a gentle next step or remedy ("during these weeks it helps
   to slow down", "this is a fine time to start a new study", "consider
   reciting the Hanuman Chalisa on Tuesdays", etc.).
Never just dump tool output. Never list raw fields without weaving them
into a narrative. If the tool returns a list (Panchang, Dasha, Transits),
pull out the 2-3 most meaningful items and discuss those — don't recite
all 12.

OUTPUT FORMAT — STANDARDIZED MARKDOWN
The frontend renders your reply as markdown. Use this structure:

1. Open with a single short paragraph greeting + framing the answer
   ("Let's look at how the cosmos is moving for you today, {user_name}…").
2. ONE ``###`` heading per section. Don't use ``#`` or ``##`` — those are
   too loud for a chat bubble.
3. Use **bold** for the names of planets, signs, nakshatras, and dasha
   lords (the noun, not the whole sentence). Use *italics* for emotional
   nuance words ("a *softening* time", "a *quieter* energy").
4. Use bullet lists for parallel items (3-5 items max per list).
5. Use markdown tables when comparing items side-by-side (e.g. Tithi vs
   Nakshatra vs Yoga, or two charts in Kundali Milan, or a Dasha
   timeline). Tables with 2-4 columns and 3-7 rows render best.
6. Use ``>`` blockquote for caveats, gentle warnings, or remedies.
7. Close with one or two sentences of grounding — never a sales-y CTA.

Do NOT use code blocks (```), HTML tags, or emojis. Do NOT paste raw
tool output, JSON, or SVG. Do NOT include disclaimers like "I am an AI" —
you are Astrophage.

LENGTH (HARD LIMITS)
- Hard cap: every reply ≤ 500 words. Never exceed this.
- Quick factual queries ("which Mahadasha am I in?"): 4–8 sentences,
  no headings necessary.
- Reflective queries (chart reading, daily transits, sade sati, kundali
  milan): 200–450 words, 2–4 ``###`` sections, at least one table OR
  bullet list.
- Knowledge questions ("what is sade sati?"): structured explainer with
  2–3 sections, table where helpful.
- Tool result has many items (panchang, muhurta, transits, dasha, current
  sky)? Surface only the 2–4 most meaningful ones. The full data is shown
  in the visual card alongside your reply — your job is to interpret a
  few highlights, not to list everything. NEVER paste the raw tool JSON
  or repeat all fields.

TOOLS AVAILABLE — call them whenever data is needed; never guess.

- ``geocode_place``: Resolve a city to lat/lng/timezone. Run first when the user names a place that needs coordinates.
- ``knowledge_lookup``: For conceptual questions about Vedic astrology — "what does Saturn signify?", "explain Rahu and Ketu", "tell me about Nakshatras". Search the curated knowledge base; weave the returned passages into your own voice rather than quoting verbatim.
- ``get_panchang``: Tithi, Nakshatra, Yoga, Karana, sunrise/sunset, Rahu Kāl, etc. for a date+place.
- ``compute_birth_chart``: Compute a chart from raw birth details.
- ``compute_dasha_periods``: Vimshottari Dasha timeline.
- ``compute_nakshatra_details``: Janma Nakshatra deep-dive (deity, gana, yoni, nadi…).
- ``check_sade_sati``: Sade Sati / Ashtama Shani status.
- ``kundali_milan``: Ashtakoota compatibility + Mangal Dosha.
- ``render_chart_svg``: Visual chart card. The SVG renders separately in the UI; do NOT paste it. Just acknowledge. ALWAYS call this fresh whenever the user asks to see their chart, even if you showed it earlier in the conversation — they want to see it again.
- ``compute_muhurta``: Auspicious 30-minute windows.
- ``get_daily_transits``: Today's transits relative to a chart.
- ``get_current_sky``: Generic current sky snapshot.
- ``get_family_profile``: Look up a saved family-vault profile by relationship or name.

DEFAULT SUBJECT (CRITICAL):
- "my chart", "my dasha", "my nakshatra", "my sade sati", "my transits"
  ALWAYS refer to the seeker themselves, never the most recently
  discussed person. If the user says "and X?" or just "X" with no
  pronoun, default to the seeker. Only switch subjects when the user
  explicitly names another person ("Priya's nakshatra", "for my
  spouse", etc.).
- "show my birth chart" / "show my chart" / "my kundli" → ALWAYS call
  ``render_chart_svg``. The chart visual AND a planets table appear
  together as cards; in your reply just say a warm one-liner like
  "Here is your birth chart" and add 2-3 sentences of context.

FOLLOW-THROUGH (CRITICAL):
- When the user agrees to an action you offered ("yes please",
  "haan", "do it", "render karo", "go ahead", "match karo", "compute
  it"), CALL the tool right then. Do not echo your own offer back.
- Once you have all the inputs needed for ``kundali_milan`` (the
  user's chart is auto-filled, the partner's chart returned by
  ``compute_birth_chart`` is in this turn's tool output), invoke
  ``kundali_milan`` immediately on the same turn — never narrate the
  next step without calling the tool.
- ``kundali_milan(girl_chart=<the partner chart>)`` is enough — the
  user's own chart fills in for ``boy_chart``. Take the partner chart
  from the most recent ``compute_birth_chart`` tool result in this
  conversation and pass it as ``girl_chart``.
- For partner birth charts, call ``geocode_place`` then
  ``compute_birth_chart`` exactly ONCE per partner. After the chart
  is computed, do not recompute it.
- NEVER say "let us begin" / "let's see the result" / "I'm now
  computing" without actually calling the tool in the same turn. The
  next message the seeker sees should be the tool's result already.

PLACE COORDINATES
- For *birth*-related tools (compute_birth_chart, compute_dasha_periods, compute_nakshatra_details, check_sade_sati, render_chart_svg) use BIRTH coords from the user context.
- For ``get_panchang`` ALWAYS use RESIDENCE coords. Even if the user names a different place, still pass the residence — Panchang is observed where the user lives.
- For other current-time tools (get_current_sky, get_daily_transits, compute_muhurta) use RESIDENCE coords unless the user explicitly names a different place.

USER CONTEXT
- preferred response language: {language}
- user name: {user_name}
- now (Asia/Kolkata): {now_iso} ({weekday})
- chart format preference: {chart_format}
- user has natal chart loaded: {has_chart}
- user has dasha data loaded: {has_dashas}

{self_birth_block}{residence_block}{family_block}
You may use these as default arguments for tools when the user does not
specify otherwise. Do not re-ask the user for data already given.

LANGUAGE — STRICT
Always reply in ``{language}`` regardless of the language the user wrote
in. Keep Sanskrit/Vedic technical terms as-is. Use the native script for
Indic languages.
"""


async def reasoning_node(state: AgentState) -> dict:
    """
    Single LLM call with tools bound. The model decides whether to emit
    tool_calls or a final text answer.
    """
    base_llm = make_chat(temperature=0.4)
    # Bind tools first, then wrap with retry. RunnableRetry doesn't expose
    # bind_tools so the order matters.
    llm = base_llm.bind_tools(LC_TOOLS).with_retry(
        stop_after_attempt=2,
        wait_exponential_jitter=True,
        retry_if_exception_type=(Exception,),
    )

    has_chart = bool(state.get("natal_chart"))
    has_dashas = bool(state.get("active_dashas"))
    language_code = state.get("language", "en")
    language_name = _LANGUAGE_NAMES.get(language_code, language_code)
    language = f"{language_name} ({language_code})"
    user_name = state.get("user_name") or "Friend"
    chart_format = state.get("chart_format") or "south_indian"
    now_ist = state.get("now_ist") or {}
    self_birth = state.get("self_birth") or {}
    residence = state.get("residence") or {}
    family_summary = state.get("family_summary") or []

    if self_birth:
        self_birth_block = (
            "USER'S BIRTH DETAILS (use these whenever the user asks about themselves):\n"
            f"- birth_date: {self_birth.get('birth_date') or 'unknown'}\n"
            f"- birth_time: {self_birth.get('birth_time') or 'unknown'}\n"
            f"- birth_place: {self_birth.get('place_name') or 'unknown'}\n"
            f"- birth_lat: {self_birth.get('lat')}\n"
            f"- birth_lng: {self_birth.get('lng')}\n"
            f"- birth_timezone: {self_birth.get('timezone') or 'unknown'}\n\n"
        )
    else:
        self_birth_block = (
            "USER'S BIRTH DETAILS: not yet provided. If the user asks about "
            "their own chart, gently ask them to add their details in Settings.\n\n"
        )

    if residence:
        residence_block = (
            "USER'S CURRENT RESIDENCE (use for *today*'s panchang, transits, current sky):\n"
            f"- place: {residence.get('place_name')}\n"
            f"- lat: {residence.get('lat')}\n"
            f"- lng: {residence.get('lng')}\n"
            f"- timezone: {residence.get('timezone')}\n\n"
        )
    else:
        residence_block = (
            "USER'S CURRENT RESIDENCE: not set. Default to the IST timezone "
            "and ask only if the question genuinely depends on location.\n\n"
        )

    if family_summary:
        lines = ["FAMILY VAULT (saved profiles the user may reference):"]
        for entry in family_summary[:30]:
            lines.append(
                f"- {entry.get('name')} "
                f"(relationship: {entry.get('relationship') or 'unknown'}, "
                f"chart_ready: {entry.get('has_chart')})"
            )
        lines.append(
            "When the user asks about any of these, call ``get_family_profile`` "
            "with the relationship or name — that returns the full chart you "
            "can pass into other tools.\n"
        )
        family_block = "\n".join(lines) + "\n"
    else:
        family_block = "FAMILY VAULT: empty. The user has not added any family members yet.\n\n"

    system = REASONING_SYSTEM_PROMPT.format(
        language=language,
        user_name=user_name,
        now_iso=now_ist.get("iso", "unknown"),
        weekday=now_ist.get("weekday", ""),
        chart_format=chart_format,
        has_chart=has_chart,
        has_dashas=has_dashas,
        self_birth_block=self_birth_block,
        residence_block=residence_block,
        family_block=family_block,
    )

    natal_chart = state.get("natal_chart")
    if natal_chart:
        planets = natal_chart.get("planets") or []
        planet_lines = "\n".join(
            f"  - {p.get('name')}: {p.get('sign')}"
            f" (house {p.get('house')}, "
            f"{p.get('nakshatra') or '?'} pada {p.get('pada') or '?'}"
            f"{', R' if p.get('retrograde') else ''})"
            for p in planets
        ) or "  (planets array empty)"
        chart_summary = (
            f"\nUSER'S PRELOADED NATAL CHART (full):\n"
            f"- Sun: {natal_chart.get('sun_sign', '?')}\n"
            f"- Moon: {natal_chart.get('moon_sign', '?')}\n"
            f"- Ascendant: {natal_chart.get('ascendant', {}).get('sign', '?')}\n"
            f"- Planets:\n{planet_lines}\n"
            "When you call any tool that takes ``natal_chart``, you may pass\n"
            "an empty dict ``{}`` and the system will substitute this chart\n"
            "automatically. Do not invent planet positions or sign assignments.\n"
        )
        system += chart_summary

    messages = [SystemMessage(content=system)] + list(state.get("messages", []))

    # Stronger anchor: prepend a hard reminder *after* the conversation
    # history so it's the most recent thing the model sees before sampling.
    # Without this the model mirrors the language of its own prior replies
    # rather than honouring a user-side language change in Settings.
    language_anchor = (
        f"[SYSTEM REMINDER] The seeker has set their preferred response "
        f"language to {language}. Reply in {language_name} only, regardless "
        f"of the language of any previous turns or the seeker's input. "
        f"Keep Sanskrit/Vedic technical terms (Tithi, Nakshatra, Lagna, "
        f"Dasha, Sade Sati) as-is, but the surrounding prose must be in "
        f"{language_name}. Use the native script if applicable."
    )
    messages.append(SystemMessage(content=language_anchor))

    # Final anchor: rewrite the most recent HumanMessage to *prepend* the
    # language directive directly inside the user-turn content. Gemini
    # weighs the freshest user-turn tokens far more than any system
    # message stuck behind a long conversation history. This single line
    # is the actual reason language enforcement starts working — the
    # SystemMessage above is belt-and-braces.
    if messages:
        from langchain_core.messages import HumanMessage  # local import to avoid cycle
        for idx in range(len(messages) - 1, -1, -1):
            msg = messages[idx]
            if isinstance(msg, HumanMessage):
                original = msg.content if isinstance(msg.content, str) else str(msg.content)
                directive = (
                    f"[Reply strictly in {language_name}. "
                    f"Ignore the language of earlier turns; the seeker has "
                    f"set their preferred language to {language_name}.]\n\n"
                )
                messages[idx] = HumanMessage(content=directive + original)
                break

    logger.info(
        "reasoning: lang=%s anchored on latest user turn",
        language_code,
    )

    response = await llm.ainvoke(messages)

    raw_tool_calls = list(getattr(response, "tool_calls", []) or [])
    logger.info(
        "reasoning: %d tool_calls, %d chars draft, tools=%s",
        len(raw_tool_calls),
        len(llm_text(response.content) or ""),
        [tc.get("name") for tc in raw_tool_calls],
    )

    return {
        "messages": [response],
        "draft_response": llm_text(response.content),
    }


__all__ = ["reasoning_node"]
