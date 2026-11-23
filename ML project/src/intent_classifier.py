import json
import os
import re

import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import FeatureUnion
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression

from src.preprocessing import preprocessor
from src.utilities import get_data_path, get_model_path


class IntentClassifier:
    """Train, evaluate, persist, and run the local intent classifier."""

    MODEL_VERSION = 2
    FEATURE_SETS = ("word", "word+char")
    MODEL_TYPES = ("MultinomialNB", "LogisticRegression", "LinearSVC")

    def __init__(self):
        self.vectorizer = None
        self.model = None
        self.model_name = "LinearSVC"
        self.feature_set = "word+char"
        self.confidence_threshold = 0.10
        self.intents_data = []
        self.tag_to_response = {}
        self.pattern_to_tag = {}
        self.intent_tags = []
        self.is_trained = False
        self.metrics = {}

    def load_intents(self, json_filepath=None) -> list:
        """Load intent answers and their exact-match examples."""
        if not json_filepath:
            json_filepath = get_data_path("intents.json")
        with open(json_filepath, "r", encoding="utf-8") as file:
            data = json.load(file)
        self.intents_data = data.get("intents", [])
        self.tag_to_response = {}
        self.pattern_to_tag = {}
        for intent in self.intents_data:
            self.tag_to_response[intent["tag"]] = intent["responses"]
            patterns = list(intent.get("patterns", []))
            for qa_pair in intent.get("qa_pairs", []):
                patterns.append(qa_pair["question"])
                patterns.extend(qa_pair.get("patterns", []))
            for pattern in patterns:
                normalized = self._normalize_pattern(pattern)
                if normalized:
                    self.pattern_to_tag[normalized] = intent["tag"]
        return self.intents_data

    @staticmethod
    def _normalize_pattern(text: str) -> str:
        """Normalize punctuation and whitespace for exact dataset phrase matching."""
        return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", "", text.lower())).strip()

    def prepare_training_data(self):
        """Build examples and keep each question's paraphrases in the same split group."""
        if not self.intents_data:
            self.load_intents()

        corpus = []
        labels = []
        groups = []
        for intent in self.intents_data:
            tag = intent["tag"]
            seen = set()
            for pattern in intent.get("patterns", []):
                group = f"{tag}:{self._normalize_pattern(pattern)}"
                self._append_example(pattern, tag, group, seen, corpus, labels, groups)

            for qa_pair in intent.get("qa_pairs", []):
                question = qa_pair["question"]
                group = f"{tag}:{self._normalize_pattern(question)}"
                self._append_example(question, tag, group, seen, corpus, labels, groups)
                for pattern in qa_pair.get("patterns", []):
                    self._append_example(pattern, tag, group, seen, corpus, labels, groups)

        return corpus, np.asarray(labels), np.asarray(groups)

    @staticmethod
    def _append_example(pattern, tag, group, seen, corpus, labels, groups):
        normalized = IntentClassifier._normalize_pattern(pattern)
        if not normalized or normalized in seen:
            return
        processed = preprocessor.preprocess_for_vectorizer(pattern)
        if processed:
            seen.add(normalized)
            corpus.append(processed)
            labels.append(tag)
            groups.append(group)

    @staticmethod
    def _build_vectorizer(feature_set):
        word = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            strip_accents="unicode",
            max_features=20000,
            min_df=1,
        )
        if feature_set == "word":
            return word
        if feature_set == "word+char":
            char = TfidfVectorizer(
                analyzer="char_wb",
                ngram_range=(2, 5),
                sublinear_tf=True,
                max_features=50000,
                min_df=1,
            )
            return FeatureUnion(
                [("word", word), ("char", char)],
                transformer_weights={"word": 1.0, "char": 0.75},
            )
        raise ValueError(f"Unsupported feature set: {feature_set}")

    @staticmethod
    def _build_model(model_type, minimum_class_count, random_state=42):
        if model_type == "MultinomialNB":
            return MultinomialNB(alpha=0.1)
        if model_type == "LogisticRegression":
            return LogisticRegression(
                C=2.0,
                max_iter=1500,
                solver="lbfgs",
                class_weight="balanced",
                random_state=random_state,
            )
        if model_type in ("LinearSVC", "SVM", "CalibratedSVM"):
            base = LinearSVC(
                C=1.0,
                dual="auto",
                random_state=random_state,
                max_iter=5000,
            )
            calibration_folds = min(3, minimum_class_count)
            if calibration_folds >= 2:
                return CalibratedClassifierCV(
                    estimator=base,
                    method="sigmoid",
                    cv=calibration_folds,
                )
            return CalibratedClassifierCV(estimator=base, method="sigmoid", cv=2)
        raise ValueError(f"Unsupported model type: {model_type}")

    @staticmethod
    def _minimum_group_count(labels, groups):
        per_label = {}
        for label, group in zip(labels, groups):
            per_label.setdefault(label, set()).add(group)
        return min((len(label_groups) for label_groups in per_label.values()), default=0)

    def _cross_validate(self, texts, labels, groups, model_type, feature_set, random_state):
        fold_count = min(5, self._minimum_group_count(labels, groups))
        if fold_count < 2:
            raise ValueError("Each intent needs at least two independent question groups for cross-validation.")

        splitter = StratifiedGroupKFold(
            n_splits=fold_count,
            shuffle=True,
            random_state=random_state,
        )
        scores = []
        accuracy_scores = []
        oof_truth = []
        oof_probabilities = []
        for train_indices, validation_indices in splitter.split(texts, labels, groups):
            train_texts = [texts[index] for index in train_indices]
            validation_texts = [texts[index] for index in validation_indices]
            train_labels = labels[train_indices]
            validation_labels = labels[validation_indices]

            vectorizer = self._build_vectorizer(feature_set)
            train_vectors = vectorizer.fit_transform(train_texts)
            validation_vectors = vectorizer.transform(validation_texts)
            model = self._build_model(
                model_type,
                int(min(np.unique(train_labels, return_counts=True)[1])),
                random_state,
            )
            model.fit(train_vectors, train_labels)
            predicted = model.predict(validation_vectors)
            scores.append(
                f1_score(
                    validation_labels,
                    predicted,
                    labels=self.intent_tags,
                    average="macro",
                    zero_division=0,
                )
            )
            accuracy_scores.append(float(accuracy_score(validation_labels, predicted)))
            oof_truth.extend(validation_labels.tolist())
            oof_probabilities.extend(model.predict_proba(validation_vectors).tolist())

        threshold, thresholded_macro_f1, fallback_rate = self._tune_threshold(
            np.asarray(oof_truth),
            np.asarray(oof_probabilities),
            self.intent_tags,
        )
        return {
            "macro_f1_mean": float(np.mean(scores)),
            "macro_f1_std": float(np.std(scores)),
            "accuracy_mean": float(np.mean(accuracy_scores)),
            "accuracy_std": float(np.std(accuracy_scores)),
            "folds": fold_count,
            "threshold": threshold,
            "thresholded_macro_f1": thresholded_macro_f1,
            "fallback_rate": fallback_rate,
        }

    @staticmethod
    def _tune_threshold(y_true, probabilities, classes):
        fallback_tag = "unknown_fallback"
        best_threshold = 0.10
        best_score = -1.0
        best_fallback_rate = 0.0
        for threshold in (0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40):
            top_indices = probabilities.argmax(axis=1)
            predictions = np.asarray(classes)[top_indices].copy()
            confidences = probabilities.max(axis=1)
            predictions[confidences < threshold] = fallback_tag
            score = f1_score(
                y_true,
                predictions,
                labels=classes,
                average="macro",
                zero_division=0,
            )
            fallback_rate = float(np.mean(predictions == fallback_tag))
            if score > best_score or (score == best_score and threshold < best_threshold):
                best_threshold = threshold
                best_score = float(score)
                best_fallback_rate = fallback_rate
        return best_threshold, best_score, best_fallback_rate

    def train(self, model_type="LinearSVC", test_size=0.2, random_state=42, feature_set=None, save=True):
        """Select features on grouped CV, evaluate on a held-out fold, then refit on all data."""
        corpus, labels, groups = self.prepare_training_data()
        self.intent_tags = sorted(set(labels.tolist()))
        group_fold_count = min(5, self._minimum_group_count(labels, groups))
        if group_fold_count < 2:
            raise ValueError("Each intent needs at least two independent question groups.")

        outer_splitter = StratifiedGroupKFold(
            n_splits=group_fold_count,
            shuffle=True,
            random_state=random_state,
        )
        train_indices, test_indices = next(outer_splitter.split(corpus, labels, groups))
        train_texts = [corpus[index] for index in train_indices]
        test_texts = [corpus[index] for index in test_indices]
        train_labels = labels[train_indices]
        test_labels = labels[test_indices]
        train_groups = groups[train_indices]

        feature_sets = [feature_set] if feature_set else list(self.FEATURE_SETS)
        cv_results = {}
        for candidate_features in feature_sets:
            cv_results[candidate_features] = self._cross_validate(
                train_texts,
                train_labels,
                train_groups,
                model_type,
                candidate_features,
                random_state,
            )
        selected_feature_set = max(
            feature_sets,
            key=lambda name: cv_results[name]["macro_f1_mean"],
        )
        cross_validation = cv_results[selected_feature_set]
        self.confidence_threshold = cross_validation["threshold"]
        self.feature_set = selected_feature_set
        self.model_name = "LinearSVC" if model_type in ("SVM", "CalibratedSVM") else model_type

        self.vectorizer = self._build_vectorizer(selected_feature_set)
        train_vectors = self.vectorizer.fit_transform(train_texts)
        class_counts = np.unique(train_labels, return_counts=True)[1]
        self.model = self._build_model(model_type, int(class_counts.min()), random_state)
        self.model.fit(train_vectors, train_labels)
        self.is_trained = True

        test_vectors = self.vectorizer.transform(test_texts)
        probabilities = self.model.predict_proba(test_vectors)
        raw_predictions = self.model.classes_[probabilities.argmax(axis=1)]
        confidences = probabilities.max(axis=1)
        thresholded_predictions = raw_predictions.copy()
        thresholded_predictions[confidences < self.confidence_threshold] = "unknown_fallback"

        accuracy = float(accuracy_score(test_labels, raw_predictions))
        precision, recall, weighted_f1, _ = precision_recall_fscore_support(
            test_labels,
            raw_predictions,
            labels=self.intent_tags,
            average="weighted",
            zero_division=0,
        )
        macro_f1 = float(
            f1_score(test_labels, raw_predictions, labels=self.intent_tags, average="macro", zero_division=0)
        )
        thresholded_accuracy = float(accuracy_score(test_labels, thresholded_predictions))
        report = classification_report(
            test_labels,
            raw_predictions,
            labels=self.intent_tags,
            output_dict=True,
            zero_division=0,
        )
        self.metrics = {
            "model_name": f"{self.model_name} · {selected_feature_set}",
            "algorithm": self.model_name,
            "feature_set": selected_feature_set,
            "accuracy": round(accuracy, 4),
            "precision": round(float(precision), 4),
            "recall": round(float(recall), 4),
            "f1_score": round(float(weighted_f1), 4),
            "macro_f1": round(macro_f1, 4),
            "thresholded_accuracy": round(thresholded_accuracy, 4),
            "confidence_threshold": round(float(self.confidence_threshold), 4),
            "validation_fallback_rate": round(
                float(np.mean(thresholded_predictions == "unknown_fallback")),
                4,
            ),
            "cross_validation": {
                "accuracy_mean": round(cross_validation["accuracy_mean"], 4),
                "accuracy_std": round(cross_validation["accuracy_std"], 4),
                "macro_f1_mean": round(cross_validation["macro_f1_mean"], 4),
                "macro_f1_std": round(cross_validation["macro_f1_std"], 4),
                "thresholded_macro_f1": round(cross_validation["thresholded_macro_f1"], 4),
                "fallback_rate": round(cross_validation["fallback_rate"], 4),
                "folds": cross_validation["folds"],
            },
            "classification_report": report,
            "confusion_matrix": confusion_matrix(
                test_labels,
                raw_predictions,
                labels=self.intent_tags,
            ).tolist(),
            "total_samples": len(corpus),
            "total_intents": len(self.intent_tags),
            "held_out_samples": len(test_indices),
            "held_out_fraction": round(len(test_indices) / len(corpus), 4),
        }

        # Keep the held-out metrics intact while fitting the serving model on all labeled groups.
        self.vectorizer = self._build_vectorizer(selected_feature_set)
        all_vectors = self.vectorizer.fit_transform(corpus)
        all_class_counts = np.unique(labels, return_counts=True)[1]
        self.model = self._build_model(model_type, int(all_class_counts.min()), random_state)
        self.model.fit(all_vectors, labels)
        self.is_trained = True
        if save:
            self.save_model()
        return self.metrics

    def compare_all_models(self):
        """Compare three classifiers and word-only vs word-plus-character TF-IDF."""
        results = {}
        for model_type in self.MODEL_TYPES:
            for candidate_features in self.FEATURE_SETS:
                metrics = self.train(
                    model_type=model_type,
                    feature_set=candidate_features,
                    save=False,
                )
                key = f"{model_type} · {candidate_features}"
                results[key] = metrics

        best = max(
            results.values(),
            key=lambda item: (
                item["cross_validation"]["accuracy_mean"],
                item["cross_validation"]["macro_f1_mean"],
            ),
        )
        self.train(
            model_type=best["algorithm"],
            feature_set=best["feature_set"],
            save=True,
        )
        return results

    def save_model(self):
        """Save vectorizer, model, and metadata in the project model directory."""
        if not self.is_trained:
            return
        model_file = get_model_path("intent_model.pkl")
        vectorizer_file = get_model_path("tfidf_vectorizer.pkl")
        meta_file = get_model_path("model_metadata.json")
        joblib.dump(self.model, model_file)
        joblib.dump(self.vectorizer, vectorizer_file)
        metadata = {
            "model_version": self.MODEL_VERSION,
            "model_name": self.model_name,
            "feature_set": self.feature_set,
            "confidence_threshold": self.confidence_threshold,
            "is_trained": self.is_trained,
            "intent_tags": self.intent_tags,
            "metrics": self.metrics,
        }
        with open(meta_file, "w", encoding="utf-8") as file:
            json.dump(metadata, file, indent=2)

    def load_saved_model(self) -> bool:
        """Load compatible fitted artifacts; reject old models trained on stale labels."""
        model_file = get_model_path("intent_model.pkl")
        vectorizer_file = get_model_path("tfidf_vectorizer.pkl")
        meta_file = get_model_path("model_metadata.json")
        if not (os.path.exists(model_file) and os.path.exists(vectorizer_file) and os.path.exists(meta_file)):
            return False
        try:
            with open(meta_file, "r", encoding="utf-8") as file:
                metadata = json.load(file)
            intents = self.load_intents()
            current_tags = sorted(intent["tag"] for intent in intents)
            if (
                metadata.get("model_version") != self.MODEL_VERSION
                or metadata.get("intent_tags") != current_tags
            ):
                return False
            self.model = joblib.load(model_file)
            self.vectorizer = joblib.load(vectorizer_file)
            self.model_name = metadata.get("model_name", "LinearSVC")
            self.feature_set = metadata.get("feature_set", "word+char")
            self.confidence_threshold = float(metadata.get("confidence_threshold", 0.10))
            self.metrics = metadata.get("metrics", {})
            self.intent_tags = metadata["intent_tags"]
            self.is_trained = True
            return True
        except Exception as error:
            print(f"Error loading saved model: {error}")
            return False

    def predict_intent(self, user_text: str, confidence_threshold=None) -> dict:
        """Predict intent and confidence, with an OOV-safe calibrated fallback."""
        if not self.is_trained:
            if not self.load_saved_model():
                self.train()

        exact_tag = self.pattern_to_tag.get(self._normalize_pattern(user_text))
        if exact_tag:
            return {
                "tag": exact_tag,
                "confidence": 1.0,
                "is_fallback": exact_tag == "unknown_fallback",
                "top_predictions": [{"tag": exact_tag, "confidence": 1.0}],
            }

        processed_text = preprocessor.preprocess_for_vectorizer(user_text)
        if not processed_text:
            return {
                "tag": "unknown_fallback",
                "confidence": 0.0,
                "is_fallback": True,
                "top_predictions": [],
            }

        vectors = self.vectorizer.transform([processed_text])
        if vectors.nnz == 0:
            return {
                "tag": "unknown_fallback",
                "confidence": 0.0,
                "is_fallback": True,
                "top_predictions": [],
            }

        probabilities = self.model.predict_proba(vectors)[0]
        classes = self.model.classes_
        sorted_indices = np.argsort(probabilities)[::-1]
        top_tag = classes[sorted_indices[0]]
        top_confidence = float(probabilities[sorted_indices[0]])
        threshold = self.confidence_threshold if confidence_threshold is None else confidence_threshold
        top_predictions = [
            {"tag": classes[index], "confidence": round(float(probabilities[index]), 4)}
            for index in sorted_indices[:3]
        ]
        if top_tag == "unknown_fallback" or top_confidence < threshold:
            return {
                "tag": "unknown_fallback",
                "confidence": top_confidence,
                "is_fallback": True,
                "top_predictions": top_predictions,
            }
        return {
            "tag": top_tag,
            "confidence": top_confidence,
            "is_fallback": False,
            "top_predictions": top_predictions,
        }


intent_classifier = IntentClassifier()
