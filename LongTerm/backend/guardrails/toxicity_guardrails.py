from llm_guard.input_scanners import Toxicity as InputToxicity
from llm_guard.input_scanners.toxicity import MatchType as InputMatchType
from llm_guard.output_scanners import Toxicity as OutputToxicity
from llm_guard.output_scanners.toxicity import MatchType as OutputMatchType


class ToxicityGuardrails:
    def __init__(self):
        self.input_scanner = InputToxicity(
            threshold=0.5,
            match_type=InputMatchType.SENTENCE,
        )

        self.output_scanner = OutputToxicity(
            threshold=0.5,
            match_type=OutputMatchType.SENTENCE,
        )

    def check_input(self, text: str):
        return self.input_scanner.scan(text)

    def check_output(self, prompt: str, output: str):
        return self.output_scanner.scan(prompt, output)
