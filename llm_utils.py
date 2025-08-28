from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from datetime import datetime
import wikipedia
from flashcard_extractor import FlashcardExtractor

llm = ChatOllama(model="gemma3:4b", temperature=0.5)

def random_topics():
    system = f"""You are a helpful assistant that provides a list of random topics that will be used as search terms on wikipedia to generate learning content for an advanced Swedish adult student. Keep them rather general as there will be several results combined in the lesson.
    
    She is rather smart so keep the topics interesting. Current date is {datetime.now().strftime('%Y-%m-%d')}. 
    Prioritize topics related to technology, literature, science, history, or culture. Return a list of 10 interesting topics, separated by commas only.

    Include a variety of topics, they can be a bit weird, niche or even funny.

    She likes to learn about the following topics: AI, folklore, paganism, history, space, science fiction, fantasy, games, 
    literature, technology, history, food, cooking, culture, nature, weird stuff, and anything else that is interesting.

    Return in Swedish."""

    response = llm.invoke([
        SystemMessage(content=system),
        HumanMessage(content="Provide a list of 10 random topics.")
    ])
    try:
        return ["Välj ett ämne"] + [t.strip() for t in response.content.split(",")] + ["Other"]
    except Exception:
        return ["AI i samhället", "Svensk folktro", "Rymdfart", "Kvantfysik", "Vikingatiden"]


class AITeacher:
    def __init__(self, model="gemma3:4b", temperature=0.5):
        self.llm = ChatOllama(model=model, temperature=temperature)
        self.vocab = []
        self.message_history = []
        self.article = ""  # Store the article text for processing
    
    def get_vocab(self):
        return self.vocab


    def process_article(self):
        extr = FlashcardExtractor(self.llm, self.article)
        extr.extract_vocab_entries()
        self.vocab = extr.vocab_entries
        print("Processing finished. Vocabulary extracted:")
    
    
    def diskussion(self, message, text):
        """
        This method is a placeholder for any discussion or additional processing
        that might be needed after the vocabulary extraction.
        """
        system = f"""You are a teacher who helps a Swedish learner at B2/C1 level to discuss articles and help her 
        practice her Swedish.
        You will see a text that is a summary of an article. Your task is to help her discuss the article,
        ask her questions about the article, and help her practice her Swedish.
        Do not provide any explanations or summaries, just ask questions and help her practice her Swedish."""

        self.message_history.append(HumanMessage(content=message))

        response = self.llm.invoke(
            [SystemMessage(content=system), HumanMessage(content=f"Here is the text to discuss: {text}")]
            + self.message_history
        )

        self.message_history.append(AIMessage(content=response.content.strip()))
        
        return response.content.strip() if response.content else "No response from AI teacher."
    
    def feedback(self):
        fdbck = ""
        for m in self.message_history:
            if m.type == "human":

                fdbck += self.llm.invoke("Please provide feedback on the following message in terms of how correct it is: " + m.content).content
                fdbck += "\n\n***********\n\n"

        return fdbck


    def search_wiki(self,topic):
        wikipedia.set_lang("sv")
        try:
            search_results = wikipedia.search(topic)
            return search_results
        except wikipedia.exceptions.DisambiguationError as e:
            search_results = f"⚠️ Ämnet '{topic}' har flera betydelser. Välj ett mer specifikt ämne.\nFörslag: {', '.join(e.options[:5])}"
        except wikipedia.exceptions.PageError:
            search_results = f"⚠️ Ingen artikel hittades för '{topic}'."
        return search_results


    def fetch_wiki_article(self,topic):
        wikipedia.set_lang("sv")
        try:
            page = wikipedia.page(topic)
            self.article = page.content  # Store the article text for later use
            self.process_article()
            return page.html()
        except wikipedia.exceptions.DisambiguationError as e:
            return f"⚠️ Ämnet '{topic}' har flera betydelser. Välj ett mer specifikt ämne.\nFörslag: {', '.join(e.options[:5])}"
        except wikipedia.exceptions.PageError:
            return f"⚠️ Ingen artikel hittades för '{topic}'."
    




