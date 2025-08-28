import gradio as gr
from llm_utils import random_topics
from wiki_utils import search_wiki, fetch_wiki_article
from llm_utils import AITeacher

ai = AITeacher(model="gemma3:4b", temperature=0.5)

global article_text




def fetch_and_confirm(topic):
    if topic == "Other":
        return (
            gr.update(visible=False),                    # hide “Du har valt…”
            gr.update(visible=False),                    # hide continue-button
            gr.update(visible=True, interactive=True)    # show custom textbox
        )
    else:
        return (
            gr.update(value=f"Du har valt ämnet: {topic}.", visible=True),
            gr.update(visible=True),                     # show continue-button
            gr.update(visible=False)                     # hide custom textbox
        )

def on_continue_and_search(dropdown_value, custom_value):
    # 1) resolve topic
    topic = custom_value.strip() if dropdown_value == "Other" else dropdown_value
    if not topic:
        # no topic: warn, hide phase two & articles, clear state
        return (
            gr.update(value="⚠️ Ange ett ämne!", visible=True),
            gr.update(visible=False),   # hide phase_two
            "",                         # clear topic_state
            gr.update(choices=[], visible=False)  # hide article_choices
        )
    # 2) search titles
    titles = search_wiki(topic) or ["⚠️ Inga artiklar hittades. Prova ett annat ämne."]
    # 3) return: confirmation, reveal phase two, store state, populate checkboxes
    return (
        gr.update(value=f"Slutligt ämne: {topic}", visible=True),
        gr.update(visible=True),                      # show phase_two row
        topic,                                        # topic_state
        gr.update(choices=titles, value=[], visible=True)  # article_choices
    )

def chat_ai(history, message):
    # history: list of (user, ai) tuples, message: latest user message
    global article_text
    ai_reply = ai.diskussion(history, article_text)
    return ai_reply

def give_feedback():
    return ai.feedback()

with gr.Blocks() as demo:
    gr.Markdown("## 🇸🇪 Svenskaövningar")

    # 1) shared state
    topic_state = gr.State("")

    # 2) first-phase controls
    topic_dropdown   = gr.Dropdown(choices=random_topics() + ["Other"], label="Välj ett ämne")
    next_step_msg    = gr.Textbox(visible=False, interactive=False)
    custom_topic_box = gr.Textbox(label="Ange eget ämne", visible=False)
    continue_button  = gr.Button("Gå vidare", visible=False)

    topic_dropdown.change(
        fn=fetch_and_confirm,
        inputs=[topic_dropdown],
        outputs=[next_step_msg, continue_button, custom_topic_box]
    )
    custom_topic_box.change(
        fn=lambda v: (
            gr.update(visible=False),
            gr.update(visible=bool(v.strip()))
        ),
        inputs=[custom_topic_box],
        outputs=[next_step_msg, continue_button]
    )
"""
    # 3) second-phase row (single block)
    with gr.Row(visible=False) as phase_two:
        article_choices = gr.CheckboxGroup(label="Välj artiklar att läsa", visible=False, interactive=True)
        extract_button  = gr.Button("Hämta artiklar")
        articles_box    = gr.Textbox(label="Hämtade artiklar", visible=False)
    
    
    # 4) wire “Gå vidare” to resolve topic + search + show phase two + store state
    continue_button.click(
        fn=on_continue_and_search,
        inputs=[topic_dropdown, custom_topic_box],
        outputs=[next_step_msg, phase_two, topic_state, article_choices]
    )

    def set_article_text(selected_articles):
        global article_text
        article_text = "\n\n".join([fetch_wiki_article(article) for article in selected_articles])
        return article_text, gr.update(visible=True)

    extract_button.click(
        fn=lambda selected_articles, topic: (
            set_article_text(selected_articles),
            gr.update(visible=True)  # show articles_box
        ),
        inputs=[article_choices, topic_state],
        outputs=gr.HTML(label="Hämtade artiklar")
    )"""

   with gr.Row(visible=False) as phase_two:
        article_choices = gr.CheckboxGroup(label="Välj artiklar", choices=[])
        extract_button  = gr.Button("Hämta artiklar")
    
        # THIS is the only place we render HTML:
        articles_html = gr.HTML(visible=False, label="Hämtade artiklar")

        extract_button.click(
            fn=on_extract,
            inputs=[article_choices],
            outputs=[articles_html, articles_html]
        )


#######################################################################################################################################################

# Show vocab

    gr.Markdown("### 📚 Ordförråd")
    vocab_button = gr.Button("Visa ordförråd")
    vocab_output = gr.Textbox(label="Ordförråd", visible=False, interactive=False)
    vocab_button.click(
        fn=lambda: ai.process_article(),
        inputs=[],
        outputs=[vocab_output]
    )



#######################################################################################################################################################
        # 5) Chat window under articles
    gr.Markdown("### 💬 Diskutera med AI-läraren")
    chat = gr.ChatInterface(
        fn=chat_ai,
        chatbot=gr.Chatbot(height=300),
        textbox=gr.Textbox(placeholder="Skriv din fråga här...", label="Din fråga"),
        title="AI-diskussion",
        description="Ställ frågor om ämnet eller artiklarna till AI-läraren.",
        submit_btn="Skicka"
    )

    feedback_button = gr.Button("Få feedback")
    feedback_output = gr.Textbox(label="Feedback", visible=True, interactive=False)
    feedback_button.click(
        fn=give_feedback,
        inputs=[],
        outputs=[feedback_output]
    )
    
demo.launch()
