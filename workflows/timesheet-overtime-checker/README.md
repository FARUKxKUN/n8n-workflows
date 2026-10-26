# Timesheet and overtime compliance checker

Every Sunday it totals each employee's hours, auto-approves compliant weeks, and has an AI agent write an escalation email to the manager for overtime, with duplicate protection and an exception log.

Part of my daily automation series.

**Nodes:** 16 · **Uses:** Schedule, Google Sheets, AI Agent, OpenAI, Gmail

## Flow

```mermaid
flowchart LR
    n0(["Weekly Schedule (Sun 6PM)"])
    n1["Get Timesheet Entries"]
    n2["Sum Hours by Employee"]
    n3["Calculate Overtime Status"]
    n4["IF - Needs Flag?"]
    n5["Overtime Escalation Agent"]
    n6["OpenAI Chat Model (LOCAL TEST)"]
    n7["Parse Agent Output"]
    n8["Send Escalation Email"]
    n9["Log Entry (Flagged)"]
    n10["Build Auto-Approval Record"]
    n11["Log Entry (Compliant)"]
    n12["Get Overtime Log"]
    n13["Check Not Duplicate"]
    n14["IF - Can Proceed?"]
    n15["Log Exception"]
    n0 --> n12
    n1 --> n2
    n2 --> n3
    n3 --> n13
    n4 --> n5
    n4 --> n10
    n5 --> n7
    n6 -.-> n5
    n7 --> n8
    n8 --> n9
    n10 --> n11
    n13 --> n14
    n14 --> n4
    n14 --> n15
    n12 --> n1
```

Dotted lines are AI sub-nodes (model, memory, tools) plugged into an agent.

## How it works

1. Runs weekly (Sunday 18:00) and reads the timesheet entries.
2. Sums hours per employee and calculates the overtime status.
3. Compliant weeks get an auto-approval record in the log.
4. Flagged weeks are checked against the log so the same week is never escalated twice.
5. An AI agent writes the escalation email to the manager; it is sent and logged. Anything that can't proceed goes to an exception log.

## Setup

1. In n8n: **Workflows > Import from file** and pick [`workflow.json`](workflow.json).
2. Connect your own credentials (none are included):
- OpenAI credential
- Gmail and Google Sheets credentials, and your sheet IDs
3. Replace every `YOUR_...` placeholder, run it once by hand, then activate it.
