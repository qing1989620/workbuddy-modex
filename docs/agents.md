# Agent Team (Rule 10-11)

Roles are invoked **by the orchestrator per stage** — never all at once.

| Role | Invoked at | Gets (fresh context) |
|---|---|---|
| Competition Compliance Auditor | COMPLIANCE_CHECK | problem + profile draft + official rules cache |
| Problem Analyst | PROBLEM_DECOMPOSITION | problem text |
| Research Director | RESEARCH_PLAN | decomposition + research questions |
| Literature Researcher | DOMAIN_RESEARCH | questions; must return verified sources |
| Data Scientist | DATA_AUDIT | raw data + audit report |
| Statistician | STATISTICAL_VALIDATION | results + test assumptions |
| Mathematical Modeler | MODEL_CANDIDATES / FORMULATION | problem characteristics + candidate matrix |
| Optimization Specialist | MATHEMATICAL_FORMULATION (opt problems) | formulation + solver choices |
| ML Specialist | MODEL_SCREENING (ml problems) | leakage-safe protocols |
| Simulation Specialist | EXPERIMENT_PLAN (sim problems) | scenario design |
| Experiment Engineer | EXPERIMENT_EXECUTION | experiment.yaml plans |
| Scientific Programmer | IMPLEMENTATION | plans; must produce runnable scripts |
| Visualization Specialist | figure planning | claims + data; must answer Q/C/D/Why |
| Result Auditor | RESULT_VALIDATION | results + artifacts (independent) |
| Citation Auditor | citation gate | claims + candidate sources |
| Paper Architect | PAPER_BLUEPRINT | evidence graph + profile |
| Scientific Writer | CHAPTER_LOOP | chapter contract + verified evidence |
| Mathematical Reviewer | chapter review | chapter + evidence (NOT writer's self-assessment) |
| Statistical Reviewer | chapter review | chapter stats + assumptions |
| Competition Judge | COMPETITION_JUDGE | paper + evidence + profile (30s/3min/deep) |
| LaTeX Engineer / Word Engineer | FORMAT_RENDER | accepted chapters |
| Adversarial Reviewer | high-risk chapters | evidence; must try to PROVE the chapter wrong |

Reviewer independence (Rule 11, 118): reviewers receive problem + evidence +
chapter. They do NOT receive "the writer thinks this chapter is great" — no
anchoring. Findings close via OPEN -> FIX -> REVERIFY -> CLOSED (Rule 78);
"writer says it's fixed" is not closure.
