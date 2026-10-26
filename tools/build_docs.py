"""Builds each workflow's README (with a Mermaid diagram drawn from the real connections) and the repo index.

    python tools/build_docs.py
"""
import io
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / "workflows"

# Hand-written description of each workflow. Diagram, node count and integrations come from workflow.json.
META = {
    "ai-avatar-video-pipeline": {
        "short": "Topic in, finished talking-avatar video ad out",
        "title": "AI avatar video pipeline",
        "summary": "Turns a topic into a finished talking-avatar video ad: an AI copywriter writes the script, a second agent critiques and rewrites it, OpenAI voices it, VEED animates the avatar, and the result is emailed and logged.",
        "context": "Built for a client project (an AI video pipeline delivered with Brody Automates). This is the working version.",
        "steps": [
            "A form takes the topic and an avatar image URL.",
            "Agent 1 writes a short Instagram Reels ad script; agent 2 reviews it as a creative director and rewrites it.",
            "OpenAI text-to-speech generates the voiceover; audio and image are uploaded to Uploadcare to get public URLs.",
            "VEED Fabric 1.0 generates the talking video; the workflow waits for the render.",
            "If the video URL is valid, the video is emailed and logged to Google Sheets; otherwise a failure email goes out.",
        ],
        "setup": ["OpenAI credential (chat + audio)", "VEED credential", "Uploadcare public key (replace `YOUR_UPLOADCARE_PUBLIC_KEY`)", "Gmail and Google Sheets credentials, and your sheet ID"],
    },
    "lead-capture-and-follow-up": {
        "short": "Lead intake, AI first message, daily follow-ups, weekly report",
        "title": "Lead capture and follow-up machine",
        "summary": "The lead system behind Tbibia, my dental clinic software: every new lead is cleaned, deduplicated, scored and given an AI-written first message, then daily and weekly jobs make sure nobody is forgotten.",
        "context": "Built for my own product, Tbibia (tbibia.com).",
        "steps": [
            "A webhook receives a lead from the site (name, phone, clinic, city, source, message).",
            "A Code node normalizes the phone number (Tunisian format) and drops invalid leads.",
            "Google Sheets is checked for duplicates.",
            "Claude writes a personal first WhatsApp message in French; if the AI call fails, a template is used instead.",
            "The lead is scored, saved to the sheet and emailed to me.",
            "Every day at 9:00: leads not contacted after 24h and contacted leads silent for 3+ days (max 2 follow-ups) are emailed as a to-do list.",
            "Every Monday at 8:00: a weekly report of the pipeline.",
        ],
        "setup": ["Header-auth credential for the Anthropic API (`x-api-key`)", "Gmail and Google Sheets credentials, and your sheet ID"],
    },
    "compliance-document-expiry-tracker": {
        "short": "AI-drafted renewal reminders before documents expire",
        "title": "Compliance document expiry tracker",
        "summary": "Checks a register of licences, certificates and contracts every morning, and has an AI agent draft a renewal reminder for anything close to or past its expiry date.",
        "context": "Part of my daily automation series.",
        "steps": [
            "Runs every day at 8:00 and reads the document register from Google Sheets.",
            "Calculates days until expiry for each document.",
            "For documents that need a reminder, an AI agent drafts a renewal email with the right urgency.",
            "The reminder is sent by Gmail and logged back to the sheet.",
        ],
        "setup": ["OpenAI credential", "Gmail and Google Sheets credentials, and your sheet ID"],
    },
    "timesheet-overtime-checker": {
        "short": "Weekly overtime check with AI escalation emails",
        "title": "Timesheet and overtime compliance checker",
        "summary": "Every Sunday it totals each employee's hours, auto-approves compliant weeks, and has an AI agent write an escalation email to the manager for overtime, with duplicate protection and an exception log.",
        "context": "Part of my daily automation series.",
        "steps": [
            "Runs weekly (Sunday 18:00) and reads the timesheet entries.",
            "Sums hours per employee and calculates the overtime status.",
            "Compliant weeks get an auto-approval record in the log.",
            "Flagged weeks are checked against the log so the same week is never escalated twice.",
            "An AI agent writes the escalation email to the manager; it is sent and logged. Anything that can't proceed goes to an exception log.",
        ],
        "setup": ["OpenAI credential", "Gmail and Google Sheets credentials, and your sheet IDs"],
    },
    "saas-renewal-auditor": {
        "short": "Keep, downgrade or cancel advice before each renewal",
        "title": "Subscription and SaaS renewal auditor",
        "summary": "Watches every software subscription a team pays for. When one renews within 30 days, an AI agent looks at usage and cost and advises the owner to keep, downgrade or cancel.",
        "context": "Part of my daily automation series.",
        "steps": [
            "Runs every day at 7:00 and reads the subscription list.",
            "Calculates days to renewal and usage status.",
            "For renewals within 30 days, an AI agent writes a short recommendation.",
            "Duplicate and validity checks run before anything is sent; the alert is emailed and logged, exceptions go to their own log.",
        ],
        "setup": ["OpenAI credential", "Gmail and Google Sheets credentials, and your sheet IDs"],
    },
    "clinic-booking-chat-agent": {
        "short": "Chat agent that checks Calendar and books appointments",
        "title": "Clinic booking chat agent",
        "summary": "A chat agent that books dental appointments: it collects the patient's details step by step, checks real availability in Google Calendar, confirms the slot and saves the booking to Google Sheets.",
        "context": "Built as a demo for clinics; Gemini as the model, with conversation memory.",
        "steps": [
            "A chat trigger receives the patient's message.",
            "The agent (Gemini, with a short memory window) asks one question at a time: name, phone, email, service, preferred time.",
            "It calls a Google Calendar tool to check availability.",
            "It writes the confirmed booking to Google Sheets and summarizes it for the patient.",
        ],
        "setup": ["Google Gemini credential", "Google Calendar and Google Sheets credentials, your calendar and sheet IDs"],
    },
    "voice-agent-appointment-scheduler": {
        "short": "Availability and booking tools for an AI phone agent",
        "title": "Voice agent appointment scheduler",
        "summary": "The backend tools for an AI phone agent: one webhook checks if a requested time is free, another books it in Google Calendar.",
        "context": "Called as tools by a voice AI agent during a live call.",
        "steps": [
            "`POST /get_availability`: Gemini's Information Extractor turns the caller's words (\"next Tuesday afternoon\") into a time.",
            "A Code node checks it against business hours and existing Calendar events, and suggests the next free slot if needed.",
            "`POST /book_appointment`: a Switch routes the request, the event is created in Google Calendar, and the result goes back to the voice agent.",
        ],
        "setup": ["Google Gemini credential", "Google Calendar credential and your calendar ID", "Point your voice agent's tool calls at the two webhook URLs"],
    },
    "ai-research-assistant": {
        "short": "Topic in a sheet, research report in your inbox",
        "title": "AI research assistant",
        "summary": "Add a topic to a Google Sheet and get a structured research report by email: it searches Wikipedia, cleans the sources and has Llama 3.3 on Groq write the report.",
        "context": "One of my first finished n8n projects.",
        "steps": [
            "A Google Sheets trigger fires when a new topic row is added.",
            "The Wikipedia API is searched and the results are cleaned of HTML.",
            "A request is built for Groq (Llama 3.3 70B) to write a structured report.",
            "The report is formatted as an HTML email and sent with Gmail.",
        ],
        "setup": ["Groq API key (replace `YOUR_GROQ_API_KEY`, or better, move it to a header-auth credential)", "Google Sheets and Gmail credentials, and your sheet ID"],
    },
}

ORDER = list(META)

FRIENDLY = {
    "formTrigger": "n8n Form", "webhook": "Webhook", "scheduleTrigger": "Schedule", "chatTrigger": "Chat",
    "googleSheetsTrigger": "Google Sheets", "googleSheets": "Google Sheets", "googleSheetsTool": "Google Sheets",
    "gmail": "Gmail", "googleCalendar": "Google Calendar", "googleCalendarTool": "Google Calendar",
    "lmChatOpenAi": "OpenAI", "openAi": "OpenAI", "lmChatGoogleGemini": "Gemini", "lmChatGroq": "Groq",
    "veed": "VEED", "agent": "AI Agent", "informationExtractor": "Information Extractor", "memoryBufferWindow": "Memory",
    "code": "Code (JavaScript)",
}


def short_type(node):
    return node["type"].split(".")[-1]


def label(name):
    text = re.sub(r"[^\w\s&?.,:/()+-]", "", name).strip()
    return text.replace('"', "'") or "node"


def integrations(wf):
    seen = []
    for n in wf["nodes"]:
        name = FRIENDLY.get(short_type(n))
        if short_type(n) == "httpRequest":
            url = str(n["parameters"].get("url", ""))
            for host, nice in (("anthropic", "Claude API"), ("groq", "Groq"), ("uploadcare", "Uploadcare"), ("wikipedia", "Wikipedia API")):
                if host in url:
                    name = nice
        if name and name not in seen:
            seen.append(name)
    return seen


def mermaid(wf):
    nodes = [n for n in wf["nodes"] if short_type(n) != "stickyNote"]
    ids = {n["name"]: f"n{i}" for i, n in enumerate(nodes)}
    lines = ["flowchart LR"]
    for n in nodes:
        t = short_type(n)
        shape = ("([", "])") if "rigger" in t or t in ("webhook", "chatTrigger", "formTrigger") else ("[", "]")
        lines.append(f'    {ids[n["name"]]}{shape[0]}"{label(n["name"])}"{shape[1]}')
    for src, outputs in wf["connections"].items():
        if src not in ids:
            continue
        for kind, branches in outputs.items():
            for branch in branches or []:
                for edge in branch or []:
                    dst = edge.get("node")
                    if dst not in ids:
                        continue
                    arrow = "-->" if kind == "main" else "-.->"
                    lines.append(f"    {ids[src]} {arrow} {ids[dst]}")
    return "\n".join(lines)


def workflow_readme(slug, wf):
    m = META[slug]
    tools = ", ".join(integrations(wf))
    steps = "\n".join(f"{i}. {s}" for i, s in enumerate(m["steps"], 1))
    setup = "\n".join(f"- {s}" for s in m["setup"])
    return f"""# {m['title']}

{m['summary']}

{m['context']}

**Nodes:** {len([n for n in wf['nodes'] if short_type(n) != 'stickyNote'])} · **Uses:** {tools}

## Flow

```mermaid
{mermaid(wf)}
```

Dotted lines are AI sub-nodes (model, memory, tools) plugged into an agent.

## How it works

{steps}

## Setup

1. In n8n: **Workflows > Import from file** and pick [`workflow.json`](workflow.json).
2. Connect your own credentials (none are included):
{setup}
3. Replace every `YOUR_...` placeholder, run it once by hand, then activate it.
"""


def index(rows):
    table = "\n".join(f"| [{META[s]['title']}](workflows/{s}) | {META[s]['short']} | {n} | {tools} |" for s, n, tools in rows)
    return f"""# n8n workflows

Automations and AI agents I built and ran in [n8n](https://n8n.io): client work, my own product and a daily automation series. Each folder has the workflow export, a diagram generated from its real connections, and setup notes.

![n8n](https://img.shields.io/badge/n8n-EA4B71?style=flat&logo=n8n&logoColor=white)
![Workflows](https://img.shields.io/badge/workflows-{len(rows)}-e2643a?style=flat)
![License MIT](https://img.shields.io/badge/license-MIT-555555?style=flat)

| Workflow | What it does | Nodes | Uses |
|---|---|---|---|
{table}

## Patterns you will find here

- **AI agents with guardrails:** a second agent critiques the first (video pipeline), a template fallback when the model call fails (lead machine), structured parsing of agent output before anything is sent.
- **Idempotency:** duplicate checks against a log before escalating or alerting, so a re-run never emails twice.
- **Exception paths:** failed renders and invalid rows go to their own email or log instead of failing silently.
- **Scheduled audits:** daily and weekly jobs over Google Sheets registers.
- **Agent tools:** webhooks built as tools for a voice agent, Calendar and Sheets tools for a chat agent.

## Using a workflow

1. Download the folder's `workflow.json`.
2. In n8n: **Workflows > Import from file**.
3. Add your own credentials. None are included: every key, email, sheet and calendar ID has been replaced with a `YOUR_...` placeholder or removed.

The READMEs and diagrams are generated by [`tools/build_docs.py`](tools/build_docs.py).

## About

Built by [Farouk Battikh](https://github.com/FARUKxKUN), AI automation developer. Portfolio: [farukportfolio.live](https://farukportfolio.live)

## License

[MIT](LICENSE)
"""


def main():
    rows = []
    for slug in ORDER:
        wf = json.load(io.open(WORKFLOWS / slug / "workflow.json", encoding="utf-8"))
        (WORKFLOWS / slug / "README.md").write_text(workflow_readme(slug, wf), encoding="utf-8", newline="\n")
        rows.append((slug, len([n for n in wf["nodes"] if short_type(n) != "stickyNote"]), ", ".join(integrations(wf))))
    (ROOT / "README.md").write_text(index(rows), encoding="utf-8", newline="\n")
    print(f"built {len(rows)} workflow READMEs and the index")


if __name__ == "__main__":
    main()
