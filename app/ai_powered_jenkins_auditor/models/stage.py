class Stage:
    """
    Represents a single stage in a Jenkins declarative pipeline.
    """
    def __init__(self, name: str):
        self.name: str = name
        self.steps: list[str] = []
        self.when: list[str] = []  # conditions for 'when' directive
        self.start_line: int = 1 

    def to_dict(self) -> dict:
        return {"name": self.name, "when": self.when, "steps": self.steps}
