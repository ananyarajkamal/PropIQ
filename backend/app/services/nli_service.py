"""Local Sequence-Pair Natural Language Inference (NLI) Service for PropIQ.

Uses Hugging Face AutoTokenizer & AutoModelForSequenceClassification to execute pairwise
NLI contradiction inference on (Statement A, Statement B) candidate pairs.

Dynamically inspects model.config.id2label to map output probabilities to:
- CONTRADICTION
- NEUTRAL
- ENTAILMENT

Singleton loader: Models and tokenizers are loaded once per process and run in eval/inference mode.
"""

import logging
from typing import Dict, Tuple, Optional
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

logger = logging.getLogger("propiq_backend")

# Default lightweight pretrained NLI cross-encoder model
DEFAULT_NLI_MODEL_NAME = "cross-encoder/nli-deberta-v3-small"


class NLIService:
    """Service wrapper for local sequence-pair NLI contradiction inference."""

    _instance: Optional['NLIService'] = None
    _initialized: bool = False

    def __new__(cls, model_name: str = DEFAULT_NLI_MODEL_NAME):
        if cls._instance is None:
            cls._instance = super(NLIService, cls).__new__(cls)
        return cls._instance

    def __init__(self, model_name: str = DEFAULT_NLI_MODEL_NAME):
        if self._initialized:
            return

        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.id2label = {}
        self.label_mapping = {}
        self.is_available = False

        self._load_model()
        NLIService._initialized = True

    def _load_model(self) -> None:
        """Load pretrained NLI model and tokenizer once per process."""
        try:
            logger.info("Initializing local NLI model '%s'...", self.model_name)
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self.model.eval()

            # Dynamically inspect model config id2label mapping
            raw_id2label = getattr(self.model.config, "id2label", {})
            logger.info("NLI model raw id2label mapping: %s", raw_id2label)

            # Map raw labels dynamically to CONTRADICTION, NEUTRAL, ENTAILMENT
            self.label_mapping = {}
            for idx, label in raw_id2label.items():
                label_upper = str(label).upper()
                if "CONTRADICT" in label_upper:
                    self.label_mapping[idx] = "CONTRADICTION"
                elif "ENTAIL" in label_upper:
                    self.label_mapping[idx] = "ENTAILMENT"
                elif "NEUTRAL" in label_upper:
                    self.label_mapping[idx] = "NEUTRAL"
                else:
                    self.label_mapping[idx] = label_upper

            self.is_available = True
            logger.info("Local NLI model '%s' loaded successfully.", self.model_name)
        except Exception as err:
            logger.warning(
                "Could not load primary NLI model '%s': %s. Attempting fallback 'roberta-large-mnli'...",
                self.model_name,
                str(err),
            )
            try:
                self.model_name = "roberta-large-mnli"
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
                self.model.eval()

                raw_id2label = getattr(self.model.config, "id2label", {})
                self.label_mapping = {}
                for idx, label in raw_id2label.items():
                    label_upper = str(label).upper()
                    if "CONTRADICT" in label_upper:
                        self.label_mapping[idx] = "CONTRADICTION"
                    elif "ENTAIL" in label_upper:
                        self.label_mapping[idx] = "ENTAILMENT"
                    elif "NEUTRAL" in label_upper:
                        self.label_mapping[idx] = "NEUTRAL"
                    else:
                        self.label_mapping[idx] = label_upper

                self.is_available = True
                logger.info("Fallback NLI model '%s' loaded successfully.", self.model_name)
            except Exception as fallback_err:
                logger.error("Failed to load local NLI model: %s", str(fallback_err))
                self.is_available = False

    def predict_pair(self, statement_a: str, statement_b: str) -> Tuple[Dict[str, float], str]:
        """Perform pairwise NLI inference on (Statement A, Statement B).

        Args:
            statement_a: Premise statement excerpt.
            statement_b: Hypothesis statement excerpt.

        Returns:
            Tuple of ({'CONTRADICTION': float, 'NEUTRAL': float, 'ENTAILMENT': float}, top_label).
        """
        if not self.is_available or self.model is None or self.tokenizer is None:
            # Fallback if model failed to load
            return {"CONTRADICTION": 0.0, "NEUTRAL": 1.0, "ENTAILMENT": 0.0}, "NEUTRAL"

        try:
            inputs = self.tokenizer(
                statement_a,
                statement_b,
                return_tensors="pt",
                truncation=True,
                max_length=256,
                padding=True,
            )

            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probabilities = torch.softmax(logits, dim=-1)[0].tolist()

            scores = {"CONTRADICTION": 0.0, "NEUTRAL": 0.0, "ENTAILMENT": 0.0}
            for idx, prob in enumerate(probabilities):
                mapped_label = self.label_mapping.get(idx, f"LABEL_{idx}")
                scores[mapped_label] = float(prob)

            top_label = max(scores, key=scores.get)
            return scores, top_label

        except Exception as err:
            logger.error("NLI pairwise inference error: %s", str(err))
            return {"CONTRADICTION": 0.0, "NEUTRAL": 1.0, "ENTAILMENT": 0.0}, "NEUTRAL"


def get_nli_service() -> NLIService:
    """Retrieve singleton instance of local NLIService."""
    return NLIService()
