import gradio as gr
from llm_utils import random_topics, AITeacher

# Placeholder backend functions

ai = AITeacher(model="gemma3:4b", temperature=0.5)


def get_subtopics(topic, other_text):
    choices = ai.search_wiki(topic)
    return choices

def display_article(subtopic):
    return ai.fetch_wiki_article(subtopic) if subtopic else "*Ingen artikel vald.*"

def get_vocab_cards(subtopic):
    cards = ai.get_vocab()
    return cards 

def build_flashcard_html(cards):
    style = '''
<style>
    body {
        background: #18181b;
        font-family: 'Segoe UI', Arial, sans-serif;
        margin: 0;
        padding: 0;
    }
    .flashcards {
        display: flex;
        flex-wrap: wrap;
        gap: 24px;
        margin: 32px auto;
        justify-content: center;
        max-width: 1000px;
    }
    .card {
        background: linear-gradient(135deg, #23232a 60%, #18181b 100%);
        border: none;
        border-radius: 18px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.25), 0 1.5px 4px rgba(0,0,0,0.18);
        padding: 28px 22px 20px 22px;
        width: 300px;
        text-align: left;
        transition: transform 0.15s, box-shadow 0.15s;
        position: relative;
    }
    .card:hover {
        transform: translateY(-6px) scale(1.03);
        box-shadow: 0 8px 32px rgba(0,0,0,0.35), 0 2px 8px rgba(0,0,0,0.22);
    }
    .card strong {
        color: #60a5fa;
        font-size: 1.25em;
        letter-spacing: 0.02em;
    }
    .card p {
        margin: 0.5em 0;
        color: #f3f4f6;
        font-size: 1.07em;
        line-height: 1.5;
    }
    .card i {
        color: #a1a1aa;
        font-size: 0.98em;
    }
    .card::before {
        content: "";
        display: block;
        width: 36px;
        height: 4px;
        background: linear-gradient(90deg, #60a5fa 60%, #818cf8 100%);
        border-radius: 2px;
        margin-bottom: 14px;
    }
</style>
    '''
    html = style + "<div class='flashcards'>"
    for c in cards:
        html += f"""    <div class='card'>
        <p><strong>{c.term}</strong> <span style="color:#a1a1aa;">({c.part_of_speech})</span><br>
            {c.definition}</p>
        <p><i><span style="color:#fbbf24;">{c.example}</span></i><br>
            {c.extra_note}
        </p>
    </div> """
    html += "</div>"
    return html

def remove_flashcards(flashcards, remaining):
    # flashcards: List[YourCardDataclass]
    # remaining: List[str] (terms that the user wants to keep)

    # 1. Keep only card‐objects whose term is in `remaining`
    updated_cards = [card for card in flashcards if card.term in remaining]

    # 2. Rebuild the HTML from the filtered list of card‐objects
    html = build_flashcard_html(updated_cards)

    # 3. Prepare the new set of terms for the CheckboxGroup
    remaining_terms = [card.term for card in updated_cards]

    # 4. Return:
    #    a) the updated list of card‐objects (state)
    #    b) the new HTML
    #    c) a gr.update for the CheckboxGroup (choices + selected values)
    return (
        updated_cards,
        html,
        gr.update(choices=remaining_terms, value=remaining_terms)
    )


def build_ui():
    with gr.Blocks(css="styles.css", title="Swedish Course GUI") as demo:
        gr.Markdown("## AI Svenskaövningar")

        # 1. Topic selection
        with gr.Row():
            topic_dd = gr.Dropdown(
                choices=random_topics(),
            )
            other_txt = gr.Textbox(visible=False, placeholder="Skriv in eget ämne...")

        # 2. Subtopic selection (hidden until topic chosen)
        sub_accordion = gr.Accordion("2. Välj underämnen", open=True, visible=False)
        with sub_accordion:
            sub_cb = gr.CheckboxGroup(choices=[], label="Underämnen", visible=False)
            sub_btn = gr.Button("Bekräfta underämnen")

        def on_topic_change(topic, other_text):
            show_other = topic == "Other"
            subs = get_subtopics(topic, other_text)
            return (
                gr.update(visible=show_other),
                gr.update(choices=subs, visible=True),
                gr.update(visible=True)
            )

        topic_dd.change(
            on_topic_change,
            inputs=[topic_dd, other_txt],
            outputs=[other_txt, sub_cb, sub_accordion]
        )

        # 3. Article display (hidden until subtopics confirmed)
        article_accordion = gr.Accordion("3. Artikelvisning", open=False, visible=False)
        with article_accordion:
            article_box = gr.HTML(value="*Din artikel kommer visas här*.")
            sub_btn.click(
                lambda subs: display_article(subs[0] if subs else ""),
                inputs=sub_cb,
                outputs=article_box
            )

        # 4. Vocabulary (flashcards)
        vocab_accordion = gr.Accordion("4. Ordförråd", open=False, visible=False)
        with vocab_accordion:
            vocab_btn = gr.Button("Visa flashcards")
            flashcards_state = gr.State([])
            flashcards_cb = gr.CheckboxGroup(label="Välj vilka kort att behålla", visible=False)
            vocab_html = gr.HTML(visible=False)

            def show_cards(subs):
                cards = get_vocab_cards(subs[0] if subs else "")
                html = build_flashcard_html(cards)
                words = [w.term for w in cards]
                return cards, gr.update(value=html, visible=True), gr.update(choices=words, value=words, visible=True)

            vocab_btn.click(
                show_cards,
                inputs=sub_cb,
                outputs=[flashcards_state, vocab_html, flashcards_cb]
            )

            flashcards_cb.change(
                remove_flashcards,
                inputs=[flashcards_state, flashcards_cb],
                outputs=[flashcards_state, vocab_html, flashcards_cb]
            )

        # 5. Chat
        chat_accordion = gr.Accordion("5. Chatta med AI", open=False, visible=False)
        with chat_accordion:
            chat = gr.Chatbot()
            user_input = gr.Textbox(placeholder="Skriv ditt meddelande...")
            send_btn = gr.Button("Skicka")
            send_btn.click(
                lambda msg, hist: hist + [[msg, "Placeholder AI svar"]],
                inputs=[user_input, chat],
                outputs=chat
            )

        # 6. Feedback
        feedback_accordion = gr.Accordion("6. Feedback", open=False, visible=False)
        with feedback_accordion:
            feedback_btn = gr.Button("Få feedback")
            feedback_box = gr.Textbox(visible=False)
            feedback_btn.click(
                lambda hist: "Placeholder feedback på dina meddelanden",
                inputs=chat,
                outputs=feedback_box
            )
            feedback_btn.click(
                lambda: gr.update(visible=True),
                inputs=None,
                outputs=feedback_box
            )

        # Reveal remaining steps after confirming subtopics
        def reveal_rest(subs):
            return [gr.update(visible=True)] * 4

        sub_btn.click(
            reveal_rest,
            inputs=sub_cb,
            outputs=[
                article_accordion,
                vocab_accordion,
                chat_accordion,
                feedback_accordion
            ]
        )

    return demo


if __name__ == "__main__":
    demo = build_ui()
    demo.launch()
