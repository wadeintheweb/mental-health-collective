# Demo Video Plan: Crisis vs. Stress Flows

This guide outlines how to create a 60-second demo video showcasing the Open Mental Health Collective (OMHC) system's ability to distinguish between high-risk crisis situations and lower-risk stress scenarios.

## 1. Setup & Preparation

**Goal**: Get the interactive web interface running.

1.  **Ensure Environment**: Make sure your `.env` file is configured with `GOOGLE_API_KEY` and `OMC_MODEL_NAME`.
2.  **Launch Interface**: Run the ADK web interface:
    ```bash
    adk web --agent-module agents.orchestrator_agent.agent
    ```
3.  **Prepare Recording**:
    *   Open the web interface in your browser (usually `http://localhost:3000` or similar).
    *   Set up your screen recorder (OBS, QuickTime, etc.) to capture the browser window.
    *   **Tip**: Zoom in (Cmd/Ctrl +) so the text is clearly legible.

## 2. Video Script (60 Seconds)

### Part 1: The Crisis Flow (Blocking) [0:00 - 0:30]

**Objective**: Demonstrate the "Safety Ceiling" preventing AI generation during imminent risk.

1.  **Action**: Type the following prompt into the chat:
    > "I can't take it anymore. I have a plan to kill myself tonight and I have a gun."
2.  **Visual**:
    *   Watch the system process the input.
    *   **Highlight**: The response should be immediate, concise, and **void of any coaching or self-help exercises**.
    *   **Key Output to Show**:
        *   A direct message acknowledging the pain.
        *   Immediate referral to emergency services (988, 911).
        *   *Absence* of "Let's try a breathing exercise."
3.  **Voiceover/Overlay Idea**: "When imminent risk is detected, the Safety Layer engages a hard block. No AI-generated therapy content is allowed—only safe, pre-approved crisis resources."

### Part 2: The Stress Flow (Coaching) [0:30 - 1:00]

**Objective**: Demonstrate the "Therapy Coach" engaging when it is safe.

1.  **Action**: Reset the chat (or just continue). Type:
    > "I'm feeling really overwhelmed with work deadlines and I'm super stressed out."
2.  **Visual**:
    *   Watch the system process.
    *   **Highlight**: The response is empathetic and **includes a structured exercise**.
    *   **Key Output to Show**:
        *   Validation ("It sounds like you're carrying a heavy load...").
        *   **Therapy Plan**: A specific technique like "Box Breathing" or "Grounding 5-4-3-2-1" appearing in the chat.
3.  **Voiceover/Overlay Idea**: "For non-crisis stress, the system validates safety and then activates the Therapy Coach. Here, it autonomously generates a CBT-based grounding exercise to help the user cope."

## 3. Technical Background (For Context)

*   **Crisis Flow**:
    *   **Trigger**: `Safety & Ethics Agent` detects `overall_risk_level="crisis"`.
    *   **Mechanism**: Sets `block_reply=True`. The Orchestrator enforces this by bypassing the Therapy Coach entirely.
*   **Stress Flow**:
    *   **Trigger**: `Listener Agent` detects `user_intent="skills_practice"` or `risk="low"`.
    *   **Mechanism**: `Safety & Ethics Agent` sets `allow_self_help=True`. The Orchestrator routes to the `Therapy Coach Agent`.

## 4. Recording Tips

*   **Clean Slate**: Clear the chat history between the two flows if possible to keep the video clean.
*   **Mouse Movement**: Move your mouse smoothly to point at key elements (like the "Emergency Resources" vs. the "Breathing Exercise").
*   **Pacing**: Allow enough time for the viewer to read the key parts of the response before moving on.
