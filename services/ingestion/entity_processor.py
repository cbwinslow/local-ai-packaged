"""
Entity Processing Module

Extracts entities (persons, organizations, locations, etc.) from text using
spaCy and provides relationship analysis.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import re
from collections import defaultdict, Counter
import hashlib

# Optional spaCy imports
try:
    import spacy
    from spacy.tokens import Doc
    from spacy.lang.en import English
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    spacy = None

# Optional transformers for enhanced NER
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    pipeline = None

logger = logging.getLogger(__name__)


class EntityProcessor:
    """Processes text to extract entities using spaCy and other methods."""

    def __init__(
        self,
        model_name: str = "en_core_web_md",
        use_transformers: bool = False,
        confidence_threshold: float = 0.7
    ):
        """
        Initialize entity processor.

        Args:
            model_name: spaCy model to use
            use_transformers: Whether to use transformers for enhanced NER
            confidence_threshold: Minimum confidence for entity extraction
        """
        self.model_name = model_name
        self.use_transformers = use_transformers and TRANSFORMERS_AVAILABLE
        self.confidence_threshold = confidence_threshold

        self.nlp = None
        self.transformer_ner = None

        # Cache for processed documents
        self.cache = {}

        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load(model_name)
                logger.info(f"Loaded spaCy model: {model_name}")
            except OSError:
                logger.warning(f"spaCy model {model_name} not found, loading basic English")
                try:
                    self.nlp = English()
                    self.nlp.add_pipe("sentencizer")
                except Exception as e:
                    logger.error(f"Failed to load spaCy: {e}")

        if self.use_transformers and TRANSFORMERS_AVAILABLE:
            try:
                self.transformer_ner = pipeline(
                    "ner",
                    model="dbmdz/bert-large-cased-finetuned-conll03-english",
                    aggregation_strategy="simple"
                )
                logger.info("Loaded transformer NER model")
            except Exception as e:
                logger.error(f"Failed to load transformer NER: {e}")
                self.use_transformers = False

        # Entity type mappings
        self.entity_types = {
            'PERSON': 'Person',
            'ORG': 'Organization',
            'GPE': 'Location',  # Geo-political entity
            'LOC': 'Location',
            'MISC': 'Miscellaneous',  # For transformers
            'NORP': 'Nationality/Religious/Political Group',
            'FAC': 'Facility',
            'PRODUCT': 'Product',
            'EVENT': 'Event',
            'WORK_OF_ART': 'Work of Art',
            'LAW': 'Law',
            'LANGUAGE': 'Language',
            'DATE': 'Date',
            'TIME': 'Time',
            'PERCENT': 'Percent',
            'MONEY': 'Money',
            'QUANTITY': 'Quantity',
            'ORDINAL': 'Ordinal',
            'CARDINAL': 'Cardinal'
        }

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract entities from text.

        Args:
            text: Input text

        Returns:
            List of entity dictionaries
        """
        if not text or not text.strip():
            return []

        # Check cache first
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in self.cache:
            return self.cache[text_hash]

        entities = []

        # Extract entities using spaCy
        spacy_entities = self._extract_with_spacy(text)
        entities.extend(spacy_entities)

        # Extract entities using transformers if enabled
        if self.use_transformers:
            transformer_entities = self._extract_with_transformers(text)
            entities.extend(transformer_entities)

        # Remove duplicates and merge similar entities
        entities = self._merge_entities(entities)

        # Cache results
        self.cache[text_hash] = entities

        return entities

    def _extract_with_spacy(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using spaCy."""
        if not self.nlp or not SPACY_AVAILABLE:
            return []

        try:
            doc = self.nlp(text)

            entities = []
            for ent in doc.ents:
                # Filter by confidence (spaCy doesn't have direct confidence, use length as proxy)
                if len(ent.text.strip()) < 2:
                    continue

                entity_dict = {
                    'text': ent.text.strip(),
                    'label': self.entity_types.get(ent.label_, ent.label_),
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'confidence': 0.8,  # Default confidence for spaCy
                    'source': 'spacy',
                    'entity_type': ent.label_,
                    'context': self._get_entity_context(doc, ent),
                    'sentence': ent.sent.text.strip() if ent.sent else ""
                }

                entities.append(entity_dict)

            return entities

        except Exception as e:
            logger.error(f"spaCy entity extraction failed: {e}")
            return []

    def _extract_with_transformers(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using transformers NER."""
        if not self.transformer_ner or not TRANSFORMERS_AVAILABLE:
            return []

        try:
            results = self.transformer_ner(text)

            entities = []
            for result in results:
                if result['score'] < self.confidence_threshold:
                    continue

                entity_dict = {
                    'text': result['word'].strip(),
                    'label': self.entity_types.get(result['entity_group'], result['entity_group']),
                    'start': result['start'],
                    'end': result['end'],
                    'confidence': float(result['score']),
                    'source': 'transformers',
                    'entity_type': result['entity_group'],
                    'context': self._get_context_around_position(text, result['start'], result['end']),
                    'sentence': self._get_sentence_containing(text, result['start'])
                }

                entities.append(entity_dict)

            return entities

        except Exception as e:
            logger.error(f"Transformers entity extraction failed: {e}")
            return []

    def _merge_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge duplicate or overlapping entities.

        Args:
            entities: Raw entity list

        Returns:
            Merged entity list
        """
        if not entities:
            return entities

        # Sort by start position
        entities.sort(key=lambda x: x['start'])

        merged = []
        current = entities[0]

        for entity in entities[1:]:
            # Check for significant overlap
            if (entity['start'] < current['end'] and
                entity['text'].lower().strip() == current['text'].lower().strip()):

                # Merge - keep higher confidence and combine sources
                if entity['confidence'] > current['confidence']:
                    current = entity

                # Add source if different
                if entity['source'] not in current['source']:
                    current['source'] += f" + {entity['source']}"

                current['confidence'] = max(current['confidence'], entity['confidence'])

            else:
                merged.append(current)
                current = entity

        merged.append(current)
        return merged

    def _get_entity_context(self, doc: 'Doc', entity) -> str:
        """Get context around an entity in spaCy doc."""
        start = max(0, entity.start - 3)
        end = min(len(doc), entity.end + 3)
        return doc[start:end].text

    def _get_context_around_position(self, text: str, start: int, end: int, window: int = 50) -> str:
        """Get context around a position in text."""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end].strip()

    def _get_sentence_containing(self, text: str, position: int) -> str:
        """Get the sentence containing the given position."""
        if not SPACY_AVAILABLE or not self.nlp:
            # Fallback: find approximate sentence boundaries
            sentences = re.split(r'[\.\!\?]+', text)
            pos = 0
            for sentence in sentences:
                if pos <= position <= pos + len(sentence):
                    return sentence.strip()
                pos += len(sentence) + 1
            return ""

        try:
            doc = self.nlp(text)
            for sent in doc.sents:
                if sent.start_char <= position <= sent.end_char:
                    return sent.text.strip()
            return ""
        except:
            return ""

    def get_entity_stats(self, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate statistics about extracted entities.

        Args:
            entities: List of entity dictionaries

        Returns:
            Dictionary with entity statistics
        """
        if not entities:
            return {'total_entities': 0}

        labels = [ent['label'] for ent in entities]
        label_counts = Counter(labels)

        # Most frequent entities
        entity_texts = [ent['text'] for ent in entities]
        entity_counts = Counter(entity_texts)
        top_entities = entity_counts.most_common(10)

        # Average confidence
        confidences = [ent['confidence'] for ent in entities]
        avg_confidence = sum(confidences) / len(confidences)

        return {
            'total_entities': len(entities),
            'unique_entities': len(set(entity_texts)),
            'entity_type_counts': dict(label_counts),
            'top_entities': top_entities,
            'avg_confidence': avg_confidence,
            'confidence_range': (min(confidences), max(confidences)) if confidences else (0, 0)
        }

    def find_entity_relationships(self, entities: List[Dict[str, Any]], text: str) -> List[Dict[str, Any]]:
        """
        Find relationships between entities in the text.

        Args:
            entities: List of entities
            text: Original text

        Returns:
            List of relationship dictionaries
        """
        relationships = []

        # Group entities by type
        entities_by_type = defaultdict(list)
        for ent in entities:
            entities_by_type[ent['entity_type']].append(ent)

        # Find co-occurrences within sentences
        for ent1 in entities:
            for ent2 in entities:
                if ent1 == ent2:
                    continue

                # Check if entities appear in same sentence
                sent1 = ent1.get('sentence', '')
                sent2 = ent2.get('sentence', '')

                if sent1 and sent2 and sent1 == sent2 and abs(ent1['start'] - ent2['start']) < 200:
                    # Determine relationship type based on entity types
                    rel_type = self._determine_relationship(ent1['entity_type'], ent2['entity_type'])

                    relationship = {
                        'entity1': ent1['text'],
                        'entity2': ent2['text'],
                        'entity1_type': ent1['entity_type'],
                        'entity2_type': ent2['entity_type'],
                        'relationship_type': rel_type,
                        'context': sent1,
                        'confidence': min(ent1['confidence'], ent2['confidence'])
                    }

                    relationships.append(relationship)

        # Remove duplicates
        unique_rels = []
        seen = set()

        for rel in relationships:
            key = (rel['entity1'], rel['entity2'], rel['relationship_type'])
            if key not in seen:
                unique_rels.append(rel)
                seen.add(key)

        return unique_rels

    def _determine_relationship(self, type1: str, type2: str) -> str:
        """Determine relationship type based on entity types."""
        # Simple rule-based relationship determination
        if type1 == 'PERSON' and type2 == 'ORG':
            return 'works_for'
        elif type1 == 'ORG' and type2 == 'PERSON':
            return 'employs'
        elif type1 == 'PERSON' and type2 == 'GPE':
            return 'located_in'
        elif type1 == 'GPE' and type2 == 'PERSON':
            return 'has_resident'
        elif type1 == type2:
            return 'same_type'
        else:
            return 'related_to'

    def extract_keywords(self, text: str, max_keywords: int = 20) -> List[Dict[str, Any]]:
        """
        Extract keywords and key phrases from text.

        Args:
            text: Input text
            max_keywords: Maximum number of keywords to extract

        Returns:
            List of keyword dictionaries
        """
        if not SPACY_AVAILABLE or not self.nlp:
            return []

        try:
            doc = self.nlp(text)

            # Extract noun phrases and noun chunks
            keywords = []

            # Get noun chunks
            for chunk in doc.noun_chunks:
                if (len(chunk.text.split()) > 1 and  # At least 2 words
                    not chunk.text.lower().startswith(('the', 'a', 'an', 'this', 'that'))):

                    keyword = {
                        'text': chunk.text,
                        'type': 'noun_phrase',
                        'start': chunk.start_char,
                        'end': chunk.end_char,
                        'root': chunk.root.text
                    }
                    keywords.append(keyword)

            # Get named entities as keywords
            entities = self.extract_entities(text)
            for entity in entities:
                keyword = {
                    'text': entity['text'],
                    'type': 'named_entity',
                    'start': entity['start'],
                    'end': entity['end'],
                    'entity_type': entity['entity_type']
                }
                keywords.append(keyword)

            # Sort by length and remove duplicates
            keywords = sorted(keywords, key=lambda x: len(x['text']), reverse=True)
            unique_keywords = []
            seen = set()

            for kw in keywords:
                if kw['text'].lower() not in seen:
                    unique_keywords.append(kw)
                    seen.add(kw['text'].lower())

            return unique_keywords[:max_keywords]

        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            return []


# Utility functions
def normalize_entity_text(text: str) -> str:
    """
    Normalize entity text for better matching.

    Args:
        text: Raw entity text

    Returns:
        Normalized text
    """
    # Remove extra whitespace and normalize case
    normalized = ' '.join(text.split()).strip()

    # Handle common variations
    # e.g., "U.S.A." -> "USA", "Mr. Smith" -> "Smith"

    return normalized


def fuzzy_entity_match(entity1: str, entity2: str, threshold: float = 0.8) -> bool:
    """
    Check if two entity strings are similar using fuzzy matching.

    Args:
        entity1: First entity string
        entity2: Second entity string
        threshold: Similarity threshold (0-1)

    Returns:
        True if entities match
    """
    try:
        from thefuzz import fuzz
        return fuzz.ratio(entity1.lower(), entity2.lower()) >= (threshold * 100)
    except ImportError:
        # Fallback to simple string comparison
        return entity1.lower().strip() == entity2.lower().strip()


# Test function
def main():
    """Test entity processing."""
    processor = EntityProcessor()

    sample_text = """
    President Joe Biden met with Senator Elizabeth Warren at the White House in Washington, D.C.
    They discussed healthcare policies and reforms to Medicare and Social Security programs.
    """

    entities = processor.extract_entities(sample_text)

    print("Extracted entities:")
    for entity in entities:
        print(f"  {entity['text']} -> {entity['label']} (confidence: {entity['confidence']:.2f})")

    stats = processor.get_entity_stats(entities)
    print(f"\nStatistics: {stats}")

    relationships = processor.find_entity_relationships(entities, sample_text)
    if relationships:
        print("\nRelationships:")
        for rel in relationships:
            print(f"  {rel['entity1']} {rel['relationship_type']} {rel['entity2']}")


if __name__ == "__main__":
    main()
