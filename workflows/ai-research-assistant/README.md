# AI research assistant

Add a topic to a Google Sheet and get a structured research report by email: it searches Wikipedia, cleans the sources and has Llama 3.3 on Groq write the report.

One of my first finished n8n projects.

**Nodes:** 9 · **Uses:** Google Sheets, Wikipedia API, Code (JavaScript), Groq, Gmail

## Flow

```mermaid
flowchart LR
    n0(["Google Sheets Trigger"])
    n1["Wiki Search"]
    n2["Code in JavaScript"]
    n3["Clean from Data"]
    n4["Prepare Groq Request"]
    n5["groq"]
    n6["Send a message"]
    n7["Format Response"]
    n8["Mail Creation"]
    n0 --> n3
    n1 --> n2
    n3 --> n1
    n2 --> n4
    n4 --> n5
    n5 --> n7
    n7 --> n8
    n8 --> n6
```

Dotted lines are AI sub-nodes (model, memory, tools) plugged into an agent.

## How it works

1. A Google Sheets trigger fires when a new topic row is added.
2. The Wikipedia API is searched and the results are cleaned of HTML.
3. A request is built for Groq (Llama 3.3 70B) to write a structured report.
4. The report is formatted as an HTML email and sent with Gmail.

## Setup

1. In n8n: **Workflows > Import from file** and pick [`workflow.json`](workflow.json).
2. Connect your own credentials (none are included):
- Groq API key (replace `YOUR_GROQ_API_KEY`, or better, move it to a header-auth credential)
- Google Sheets and Gmail credentials, and your sheet ID
3. Replace every `YOUR_...` placeholder, run it once by hand, then activate it.
