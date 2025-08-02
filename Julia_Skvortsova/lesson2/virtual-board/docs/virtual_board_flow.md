# Improved Flow 

## Phase 0 – Prep & Guardrails

1. **Hypothesis Coverage Matrix:** Map each hypothesis to at least one main question and a back-up probe.
2. **Agent Roles Split:**

   * *Facilitator* (drives flow),
   * *Analyst* (tags, clusters, checks coverage in real time),
   * *QA/Moderator* (monitors for bias, repetition, derailment),
   * *Personas* (users).
3. **Calibration & Warm-up:** Brief neutral prompts to each persona to test tone, domain familiarity, and adjust instructions.

## Phase 1 – Diverge (broaden understanding)

4. **Context-lite Need Exploration:** Ask broad, non-leading questions about pains/goals *before* showing the concept.
5. **Parallel Responses + Automated Theme Extraction:** Let all personas answer; Analyst clusters themes (needs, motivations).

## Phase 2 – Concept Reveal & Focused Inquiry

6. **Introduce Product Idea (standardized brief):** Same to all personas to control exposure bias.
7. **Main Questions in Batches:**

   * Ask a main question to *all* personas simultaneously.
   * Analyst clusters answers, identifies gaps/conflicts.
   * Facilitator issues **theme-based follow-ups** (1–3 targeted probes) to selected personas, not everyone.

## Phase 3 – Converge (prioritize & trade-offs)

8. **Structured Trade-off Tasks:** e.g., forced ranking of features, scenario-based choices, willingness-to-pay questions.
9. **Group Reflection Round:** Show anonymized summarized viewpoints back to personas and ask, “What resonates? What’s missing?” to simulate interaction without full chaos.

## Phase 4 – Meta & Closure

10. **“Red Team” Prompt:** Ask each persona to attack the idea (“What would make you abandon it?”).
11. **Satisfaction & Intention Check:** Likelihood to adopt, refer, pay—capture as quick quantitative scales.
12. **Real-time Coverage Check:** Analyst confirms all hypotheses addressed; unresolved items queued for a micro follow-up loop.
13. **Synthesis & Next Steps:**

    * Insight summary (themes, tensions, quotes),
    * Confidence levels & open questions,
    * Recommendations (pivot, proceed, test with real users),
    * Log of decision criteria.


---

# Spark dynamics without causing echo‑chamber bias

Use this selective‑sharing approach to get the benefits of group dynamics (contrast, co-creation, tension) without sacrificing the validity of individual signals.

1. **Silent Divergence (no sharing yet)**

   * Each persona answers broad and main questions independently.
   * Goal: unprimed, diverse signals.

2. **Curated Reflection Round**

   * Analyst clusters answers → Facilitator shows a short theme list + 1–2 anonymized quotes per theme.
   * Prompt personas: “What resonates? What’s missing or wrong?”
   * This simulates group discussion while limiting anchoring.

3. **Targeted Cross-Probes**

   * If P2 strongly disagrees with Theme A (held by P4), ask P4: “Persona 2 said X; how would you respond?”
   * Limit to high-value conflicts or gaps.

4. **Mini “Fishbowl” Moments (optional)**

   * Pick 2–3 personas to react to each other while others observe (no input). Rotate who’s inside/outside.

5. **Convergence Tasks (public results OK)**

   * Show aggregate rankings or willingness-to-pay charts, then ask: “Seeing this, would you change your stance?”
   * Capture shifts to understand persuasion effects.

6. **Red-Team Round**

   * Share a compilation of “why this could fail” and ask each persona to add/critique.

---

### Risks & Mitigations

| Risk                 | What causes it                   | Mitigation                                                                    |
| -------------------- | -------------------------------- | ----------------------------------------------------------------------------- |
| Anchoring/groupthink | Early exposure to dominant views | Delay sharing; anonymize; counter with “What’s different in your experience?” |
| Persona drift        | LLM personas copy phrasing       | Remind persona briefs; QA agent flags mimicry                                 |
| Info overload        | Raw transcript dumping           | Summaries, quotes <20 words, highlight 3–5 key tensions max                   |
| Over-interrogation   | Too many cross-questions         | Use theme-level probes, cap follow-ups per round                              |

---

### Decision Rule (pseudo-logic)

```
IF phase == "diverge":
    do_not_share_raw()
ELIF phase == "reflect":
    share_synthesized(themes, short_quotes)
    prompt_for_resonance_and_gaps()
ELIF high_conflict_theme_detected:
    run_targeted_cross_probe(persona_ids)
ELIF phase == "converge":
    share_aggregated_results()
    ask_change_of_mind_check()
```

---

### Prompt snippets

**For Reflection Round (Facilitator → Personas):**
“Here are 3 themes that emerged (with anonymized quotes). Which feels most true for you? What’s off? Anything important missing?”

**For Targeted Cross-Probe:**
“Persona {{A}} is worried about {{privacy of data}}. You seemed unconcerned. How would you address that worry from your perspective?”

**For Change-of-Mind Check:**
“After seeing the group’s ranking, would you adjust your own top priority? Why/why not?” 

---

---

## Optional Enhancements

* **Uncertainty & Emotion Scores:** After each answer, have Analyst tag confidence (low/medium/high) and affect (frustration, excitement).
* **Persona Drift Monitor:** QA checks if an agent stays consistent with its brief; re-prompts if off.
* **Insight Repository:** Auto-store tagged quotes, themes, and evidence in a structured format (e.g., JSON or Airtable schema).
* **A/B Prompting:** Try two formulations of a critical question to detect prompt sensitivity.

---
