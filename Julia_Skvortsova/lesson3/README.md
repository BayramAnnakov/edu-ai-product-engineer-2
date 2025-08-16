# Homework #3 – Product Management Agents

In Progress, For details check pm-agent/README.md

## Objective

Develop a **multi-agent system** that implements the specified product management workflow.

---

## Workflow & Tasks

### 1. Classification of User Reviews

* Input: User reviews from Homework #1.
* Output: Classify each review into one of three categories:
  1. Bug Reports
  2. Feature Requests
  3. Other (praises, general comments, etc.)

---

### 2. Bug Reports

For each classified bug report:

1. **Check for duplicates**
   * Search an existing bug tracker (e.g., Jira, GitHub Issues) for similar reports.
2. **Create a detailed bug report**
   * Use an LLM and a bug reporting policy to draft a structured report.
3. **Advanced task (optional)**
   * Search the code repository for relevant code snippets.
   * Use LLM to suggest a possible fix.

---

### 3. Feature Requests

For each classified feature request:

1. **Competitor research**
   * Use a research bot to investigate if competitor products already have similar features.
   * The research bot should use LLM-as-a-planner to design the research plan.
2. **Feature report preparation**
   * Produce a competitor analysis and a detailed feature description.
3. **PM approval**
   * Send a Slack message to the Product Manager requesting review and approval of the proposed feature.

---

## Requirements

* Use at least **3 design patterns** from https://www.anthropic.com/engineering/building-effective-agents
* Use **Model Context Protocol (MCP)** where applicable.

---
