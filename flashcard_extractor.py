from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage


import json
import re
from dataclasses import dataclass
from typing import List

@dataclass
class VocabEntry:
    term: str
    part_of_speech: str
    definition: str
    example: str
    extra_note: str




class FlashcardExtractor:
    def __init__(self, llm, article):
        self.llm = llm
        self.article = article
        self.vocab_entries = []
    
        self.system = SystemMessage(content="""
                You are a vocabulary‐expansion assistant for a Swedish learner at B2/C1 level.  
                You will see one sentence at a time from a Swedish article.
                Your task is to identify and extract vocabulary items that are particularly useful or interesting for a language learner at a higher level.

                1. Identify between 1 and 3 “interesting” vocabulary items (single words or multi-word phrases) that meet at least one of these criteria:  
                • Less frequent, but useful in journalistic or academic texts.  
                - Useful words or phrases that are not basic vocabulary.
                • Idiomatic expressions or common collocations.  
                • Words/phrases that convey nuance or are hard to paraphrase.  
                • Topic-specific or domain-specific terms I’m unlikely to know.  
                - Verbs that are irregular.
                - Words that are commonly used in formal or literary contexts.
                - Do not include proper nouns, names of people, places, or organizations.


                Return as a JSON list of items, each with the following structure without markdown or formatting Do not include any comments or explanations, just the JSON list:  

                {{
                    "term": "word or phrase in bold",
                    "part_of_speech": "noun/verb/adjective/idiom",
                    "definition": "concise Swedish definition",
                    "example": "original sentence from the article",
                    "extra_note": "brief note on formality, register, or collocations"
                }}



                ———

                When you receive an article, just start processing—no other output is needed. 

                """)

    def extract_vocab_entries(self):
        """
        Extract words from a sentence, ignoring punctuation.
        """
        sentences = self.article.split(". ")

        for sentence in sentences:
            if not sentence.strip():
                continue
            
            # Invoke the LLM with the current sentence
            response = self.llm.invoke([
                self.system,
                HumanMessage(content=f"The sentence to analyze is: {sentence}")
            ])
            print("Response from LLM:", response.content)  # Debugging output
            # Parse the response and add to vocabulary
            try:
                vocab_items = self.parse_vocab_entries(response.content)

                for item in vocab_items:
                    if item:
                        self.vocab_entries.append(item)  # Convert string representation of dict to dict
            except Exception as e:
                print(f"Error processing sentence: {sentence}\n{e}")
        


    def _strip_code_fences(self,text: str) -> str:
        """
        Remove any lines starting with ``` (and the trailing fence).
        """
        return "\n".join(
            line for line in text.splitlines()
            if not line.strip().startswith("```")
        )

    def parse_vocab_entries(self,text: str) -> List[VocabEntry]:
        """
        Accepts either raw JSON or a Markdown-fenced JSON block,
        strips any ``` fences, parses the JSON, validates its shape,
        and returns a list of VocabEntry.
        """
        cleaned = self._strip_code_fences(text)
        try:
            raw = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON after stripping fences: {e}")

        if not isinstance(raw, list):
            raise ValueError("Expected top-level JSON array of entries")

        entries: List[VocabEntry] = []
        for idx, item in enumerate(raw):
            if not isinstance(item, dict):
                raise ValueError(f"Entry {idx} is not an object")
            for field in ("term", "part_of_speech", "definition", "example", "extra_note"):
                if field not in item:
                    raise ValueError(f"Entry {idx} missing required field '{field}'")
            entries.append(VocabEntry(**{f: item[f] for f in VocabEntry.__annotations__}))
        return entries




