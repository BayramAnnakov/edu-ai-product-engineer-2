# Feature Research Workflow

## Context
- **Feature Request**: {{feature_description}}
- **Original Review**: {{review_text}}
- **Review ID**: {{review_id}}
- **Competitors to Analyze**: {{competitors}}
- **Project**: {{project}}
- **Session ID**: {{session_id}}

## Your Task

Coordinate a comprehensive competitive research workflow for this feature request. You will orchestrate four specialized agents to:

1. **Plan the Research** (ResearchPlannerAgent)
   - Design a research strategy
   - Identify specific questions to answer
   - Create search queries

2. **Execute Web Research** (WebResearchAgent)
   - Search for competitor implementations
   - Gather evidence with citations
   - Find official documentation

3. **Analyze Competitors** (CompetitorAnalystAgent)
   - Compare feature implementations
   - Identify strengths and gaps
   - Create comparison matrix

4. **Write Feature Specification** (FeatureSpecWriterAgent)
   - Generate detailed feature spec
   - Define acceptance criteria
   - Propose differentiation strategy

## Workflow Steps

### Step 1: Research Planning
Hand off to ResearchPlannerAgent with:
- The feature description
- List of competitors
- Request for a comprehensive research plan

Expected output: FeatureResearchPlan with tasks and queries

### Step 2: Web Research Execution
Hand off to WebResearchAgent with:
- The research plan from Step 1
- Instruction to find evidence for each competitor
- Requirement for citations

Expected output: List of CompetitorFinding objects with evidence

### Step 3: Competitive Analysis
Hand off to CompetitorAnalystAgent with:
- All findings from Step 2
- Request to create comparison matrix
- Instruction to identify gaps and opportunities

Expected output: FeatureComparisonMatrix with detailed analysis

### Step 4: Feature Specification
Hand off to FeatureSpecWriterAgent with:
- The comparison matrix from Step 3
- Original feature request context
- Request for actionable specification

Expected output: CompetitorResearchReport with full specification

## Quality Requirements

- **Every claim must have a source URL**
- **Minimum 3 competitors analyzed**
- **At least 5 evidence URLs total**
- **Clear differentiation strategy**
- **Specific acceptance criteria**

## Output Format

Return the final CompetitorResearchReport from the FeatureSpecWriterAgent, ensuring it follows this schema:

{{report_schema}}

## Important Notes

- Prefer official sources (company websites, documentation)
- Note pricing tiers and limitations
- Identify both what competitors do and don't do
- Focus on actionable insights for product development
- Flag any uncertainties or gaps in research

Begin by handing off to the ResearchPlannerAgent to create the research plan.