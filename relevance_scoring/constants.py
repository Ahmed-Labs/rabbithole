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

# Tag or suffix of the embedding key to denote its type
# text -> Pooled paper text
# meta -> Title + abstract of paper
TEXT_TAG = ":text"
META_TAG = ":meta"

# Weighting of semantic similarity calculation
TEXT_SEMANTIC_WEIGHT = 0.8
META_SEMANTIC_WEIGHT = 0.2