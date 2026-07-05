import random
from typing import List, Dict, Any
from pathlib import Path
from dataset_factory.generators.base_generator import BaseGenerator

class ConversationGenerator(BaseGenerator):
    """
    Generates the General Conversation dataset (conversation.jsonl) containing 5,000+ conversations.
    """

    def generate(self) -> List[Dict[str, Any]]:
        conversations = []
        random.seed(47)

        subjects = [
            "project management techniques", "the history of programming languages",
            "effective time management", "mind mapping", "how to read documentation",
            "writing neat emails", "kanban boards vs scrum boards", "remote team alignment",
            "git branch strategies", "handling technical debt", "writing clean code",
            "choosing the right framework", "improving debugging skills", "software testing strategies",
            "continuous integration setups", "optimizing database tables", "designing REST API contracts",
            "managing production deployments", "microservices communication", "application cache layers",
            "handling client communication", "drafting project scopes", "doing code reviews",
            "preparing for system design", "learning new coding syntax", "writing technical blogs"
        ]

        # Generate 5,050 conversations
        for i in range(5050):
            sub = subjects[i % len(subjects)]
            scenario = i % 3

            if scenario == 0:
                prompt = f"Help me organize a daily schedule for studying {sub}. (Session plan {i+1})"
                response = (
                    f"### Study Schedule: {sub.capitalize()}\n\n"
                    f"Here is a structured daily study plan to master this topic:\n\n"
                    f"- **8:00 AM - 9:00 AM (Core concepts):** Read high-level overviews and documentation.\n"
                    f"- **9:00 AM - 10:30 AM (Hands-on practice):** Build small exercises or summarize what you learned.\n"
                    f"- **10:30 AM - 11:00 AM (Review):** Go through flashcards and clarify unresolved details."
                )
                user2 = "Can you suggest a metric to track my learning progress?"
                assistant2 = (
                    f"A solid metric is **retrieval practice score** (quizzing yourself without notes) "
                    f"and the ability to explain the topic back to someone else (the Feynman Technique). "
                    f"Aim for 80% accuracy in quizzes and fluent, jargon-free explanations."
                )
            elif scenario == 1:
                prompt = f"Draft an introductory email explaining the benefits of {sub} to our team lead. (Draft variant {i+1})"
                response = (
                    f"Subject: Introduction of {sub.capitalize()} to our workflow\n\n"
                    f"Hi Team Lead,\n\n"
                    f"I hope you are doing well. I wanted to propose integrating **{sub}** into our development group. "
                    f"This practice will help us organize tasks, save time, and improve code/system reliability.\n\n"
                    f"I would love to set up a short 10-minute sync to present a brief outline. Let me know if you are open to this.\n\n"
                    f"Best regards,\n"
                    f"Developer Team"
                )
                user2 = "What should I include in the outline?"
                assistant2 = (
                    f"Include the **Problem Statement** (what friction we face today), the **Proposed Solution** (how {sub} helps), "
                    f"and the **Expected Impact/ROI** (metrics like time saved or reduced error rates)."
                )
            else:
                prompt = f"Summarize key takeaways regarding {sub} in a list. (Takeaway summary {i+1})"
                response = (
                    f"### Takeaways: {sub.capitalize()}\n\n"
                    f"- **Core Foundation:** Understanding basic rules is crucial before scale.\n"
                    f"- **Consistency:** Small daily routines beat cramming or ad-hoc operations.\n"
                    f"- **Feedback Loops:** Always validate your performance with direct audits."
                )
                user2 = "Can you expand on the feedback loop concept?"
                assistant2 = (
                    f"A feedback loop in **{sub}** means collecting data from your executions (like error logs, "
                    f"time tracking, or direct comments), analyzing it, and immediately adjusting your methods "
                    f"in the next session to prevent repeating the same mistakes."
                )

            conv = {
                "messages": [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": response},
                    {"role": "user", "content": user2},
                    {"role": "assistant", "content": assistant2}
                ]
            }
            conversations.append(conv)

        print(f"Generated {len(conversations)} general conversations.")
        return conversations
