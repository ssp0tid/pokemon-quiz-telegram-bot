import random


class HintSystem:
    def __init__(self, max_hints=2):
        self.max_hints = max_hints
        self.used_hints = {}

    def get_available_hints(self, session_id):
        used = self.used_hints.get(session_id, 0)
        return self.max_hints - used

    def use_hint(self, session_id):
        used = self.used_hints.get(session_id, 0)
        if used >= self.max_hints:
            return None
        self.used_hints[session_id] = used + 1
        hints = ["eliminate", "time", "reveal"]
        return hints[used] if used < len(hints) else "eliminate"

    def generate_eliminate_hint(self, question):
        options = question["options"]
        correct_answer = question["answer"]
        wrong_options = [opt[1] for opt in options if opt[1] != correct_answer][:2]
        return f"💡 *Eliminate Hint:* Wrong answers: {', '.join(wrong_options)}"

    def generate_time_hint(self, remaining):
        return f"⏰ *Time Hint:* You have {remaining} seconds left!"

    def generate_reveal_hint(self, question):
        answer = question["answer"]
        first_letter = answer[0]
        length = len(answer)
        hidden = "".join(["_" if c.isalpha() else c for c in answer])
        return (
            f"🔍 *Reveal Hint:* Starts with '{first_letter}', {length} chars: {hidden}"
        )

    def generate_hint(self, session_id, question, remaining):
        hint_type = self.use_hint(session_id)
        if not hint_type:
            return None

        if hint_type == "eliminate":
            return self.generate_eliminate_hint(question)
        elif hint_type == "time":
            return self.generate_time_hint(remaining)
        elif hint_type == "reveal":
            return self.generate_reveal_hint(question)
        return None

    def reset(self, session_id):
        self.used_hints[session_id] = 0

    def get_used_count(self, session_id):
        return self.used_hints.get(session_id, 0)
