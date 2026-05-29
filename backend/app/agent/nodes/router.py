"""Router Node — classifies user intent into one of 8 buckets."""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.agent.state import AgentState
from app.config import get_settings

ROUTER_SYSTEM_PROMPT = """You are an intent classifier for a Vedic astrology AI assistant.

Given the user's message, classify their intent into exactly ONE of these categories:

- chart_request: User wants to generate or view a birth chart
- daily_horoscope: User asks about today's energy, daily predictions, or transits
- dasha_query: User asks about Dasha periods, Mahadasha, Antardasha, planetary periods
- compatibility: User asks about Kundali Milan, compatibility, marriage matching
- muhurta_request: User wants to find auspicious timing for an event
- panchang_query: User asks about today's Tithi, Nakshatra, Rahu Kaal, Panchang
- remedy_request: User asks about remedies, gemstones, mantras for planetary issues
- free_form: General astrology question, greeting, or anything else

Respond with ONLY the category name, nothing else."""


async def router_node(state: AgentState) -> dict:
    """Classify the user's intent and set state.intent."""
    settings = get_settings()
    llm = ChatGoogleGenerativeAI(
        model=settings.llm_model,
        google_api_key=settings.google_api_key,
        temperature=0,
    )

    # Get the last user message
    last_message = ""
    for msg in reversed(state.get("messages", [])):
        if hasattr(msg, "type") and msg.type == "human":
            last_message = msg.content
            break
        elif isinstance(msg, dict) and msg.get("role") == "user":
            last_message = msg.get("content", "")
            break

    if not last_message:
        return {"intent": "free_form"}

    response = await llm.ainvoke([
        SystemMessage(content=ROUTER_SYSTEM_PROMPT),
        HumanMessage(content=last_message),
    ])

    intent = response.content.strip().lower().replace(" ", "_")

    # Validate intent is one of our known categories
    valid_intents = {
        "chart_request", "daily_horoscope", "dasha_query",
        "compatibility", "muhurta_request", "panchang_query",
        "remedy_request", "free_form",
    }
    if intent not in valid_intents:
        intent = "free_form"

    return {"intent": intent}
