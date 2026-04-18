import json
import logging
import os

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
    room_io,
)
from livekit.plugins import ai_coustics, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# ── Defaults (used when no metadata is provided) ────────────────────────────
DEFAULT_STT = "deepgram/nova-3"
DEFAULT_LLM = "google/gemini-2.5-flash-lite"
DEFAULT_TTS = "xai/tts-1"
DEFAULT_VOICE = "ara"
DEFAULT_LANGUAGE = "pt-BR"
DEFAULT_TEMPERATURE = 0.8


DEFAULT_INSTRUCTIONS = (
"You are a very useful AI voice assistant. The user interacts with you via voice."
"You help users with sarcasm, ambiguous answers, and statements in the form of questions, making it clear that the user didn't ask a good question. Always be truthful in your answers."
"You are curious, have a sense of humor, but always try to tease the user."
)

LANG_HINTS = {
    "pt-BR": "Responda sempre em português do Brasil.",
    "es-419": "Responde siempre en español latinoamericano.",
    "es-ES": "Responde siempre en español de España.",
    "en-US": "Always respond in English.",
}


class Assistant(Agent):
    def __init__(self, instructions: str = "", language: str = "pt-BR") -> None:
        base = instructions.strip() if instructions.strip() else DEFAULT_INSTRUCTIONS
        lang_hint = LANG_HINTS.get(language, "")
        full_instructions = f"{base}\n{lang_hint}" if lang_hint else base
        super().__init__(instructions=full_instructions)


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # ── Read pipeline config from job metadata ───────────────────────────
    config = {}
    if ctx.job.metadata:
        try:
            config = json.loads(ctx.job.metadata)
            logger.info(f"Received pipeline config: {config}")
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in job metadata, using defaults")

    stt_model = config.get("stt", DEFAULT_STT)
    llm_model = config.get("llm", DEFAULT_LLM)
    tts_model = config.get("tts", DEFAULT_TTS)
    tts_voice = config.get("voice", DEFAULT_VOICE)
    tts_language = config.get("language", DEFAULT_LANGUAGE)
    temperature = config.get("temperature", DEFAULT_TEMPERATURE)
    noise_cancellation = config.get("noiseCancellation", True)
    preemptive = config.get("preemptiveGeneration", True)

    logger.info(
        f"Pipeline: STT={stt_model}, LLM={llm_model}(t={temperature}), "
        f"TTS={tts_model}, voice={tts_voice}, lang={tts_language}, "
        f"noise_cancel={noise_cancellation}, preemptive={preemptive}"
    )

    # ── Build the voice pipeline dynamically ─────────────────────────────
    session = AgentSession(
        stt=inference.STT(model=stt_model, language="multi"),
        llm=inference.LLM(model=llm_model, extra_kwargs={"temperature": temperature}),
        tts=inference.TTS(
            model=tts_model,
            voice=tts_voice,
            language=tts_language,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=preemptive,
    )

    # ── Start the session ────────────────────────────────────────────────
    custom_instructions = config.get("instructions", "")

    audio_input_opts = room_io.AudioInputOptions()
    if noise_cancellation:
        audio_input_opts = room_io.AudioInputOptions(
            noise_cancellation=ai_coustics.audio_enhancement(
                model=ai_coustics.EnhancerModel.QUAIL_VF_L
            ),
        )

    await session.start(
        agent=Assistant(instructions=custom_instructions, language=tts_language),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=audio_input_opts,
        ),
    )

    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
