import wikipedia




def search_wiki(topic):
    wikipedia.set_lang("sv")
    try:
        search_results = wikipedia.search(topic)
        print(f"Search results for '{topic}': {search_results}")
        return search_results
    except wikipedia.exceptions.DisambiguationError as e:
        search_results = f"⚠️ Ämnet '{topic}' har flera betydelser. Välj ett mer specifikt ämne.\nFörslag: {', '.join(e.options[:5])}"
    except wikipedia.exceptions.PageError:
        search_results = f"⚠️ Ingen artikel hittades för '{topic}'."
    return search_results


def fetch_wiki_article(topic):
    wikipedia.set_lang("sv")
    try:
        page = wikipedia.summary(topic, sentences=100)
        return page
    except wikipedia.exceptions.DisambiguationError as e:
        return f"⚠️ Ämnet '{topic}' har flera betydelser. Välj ett mer specifikt ämne.\nFörslag: {', '.join(e.options[:5])}"
    except wikipedia.exceptions.PageError:
        return f"⚠️ Ingen artikel hittades för '{topic}'."
    


