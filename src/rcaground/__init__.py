"""rcaground: reproducible evaluation of evidence grounding in LLM root cause analysis.

Subpackages:
    rcaground.signals     adapters that normalise public RCA benchmarks (RCAEval,
                          OpenRCA) into one FailureCase schema, plus alert synthesis
    rcaground.graph       service dependency graphs from traces or static topology
    rcaground.agents      evidence ranking and the reference RCA generator
    rcaground.bench       benchmark harness, baselines, and the two-stage
                          faithfulness checker
    rcaground.audit       run manifests and cost/timing ledger
    rcaground.llm         provider-agnostic chat client
"""

__version__ = "0.1.0.dev0"
