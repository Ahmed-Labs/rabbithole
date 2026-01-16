# Relevance scoring config
SEMANTIC_SIMILARITY_WEIGHT = 0.75
YEAR_SIMILARITY_WEIGHT = 0.15
CITATION_SCORE_WEIGHT = 0.10

# LLM scoring config
LLM_SCORE_WEIGHT = 0.5

# Model to use for genearting LLM relevance score
GPT_MODEL = "gpt-5-nano"

# LLM scores and explanations will only be generated for papers
# with a relevance score above this threshold.
LLM_SCORING_THRESHOLD = 0.8
