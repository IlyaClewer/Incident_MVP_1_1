import re
from dataclasses import dataclass
from typing import List, Union, Set, Optional

# ---------------------------
# AST узлы
# ---------------------------

@dataclass(frozen=True)
class EventNode:
    event_id: int

@dataclass(frozen=True)
class AndNode:
    left: "Node"
    right: "Node"

@dataclass(frozen=True)
class OrNode:
    left: "Node"
    right: "Node"

Node = Union[EventNode, AndNode, OrNode]


# ---------------------------
# Нормализация
# ---------------------------

def normalize_formula(formula: str) -> str:
    formula = formula.replace("\xa0", " ")
    formula = re.sub(r"\s+", " ", formula.strip())
    formula = re.sub(r"Event\s*(\d+)", r"\1", formula, flags=re.IGNORECASE)
    return formula


# ---------------------------
# Токенизация
# ---------------------------

def tokenize(formula: str) -> List[Union[int, str]]:
    normalized = normalize_formula(formula)
    raw = re.findall(r"\d+|[()+/]", normalized)

    if not raw:
        raise ValueError("Пустая формула")

    tokens: List[Union[int, str]] = []
    for x in raw:
        if x in ("(", ")", "+", "/"):
            tokens.append(x)
        else:
            tokens.append(int(x))
    return tokens


# ---------------------------
# Парсер
# Приоритет:
#   /  -> OR  (сильнее)
#   +  -> AND (слабее)
# ---------------------------

class Parser:
    def __init__(self, tokens: List[Union[int, str]]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Optional[Union[int, str]]:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consume(self) -> Union[int, str]:
        token = self.peek()
        if token is None:
            raise ValueError("Неожиданный конец формулы")
        self.pos += 1
        return token

    def parse(self) -> Node:
        node = self.parse_and()
        if self.peek() is not None:
            raise ValueError(f"Лишние токены в конце: {self.tokens[self.pos:]}")
        return node

    def parse_and(self) -> Node:
        node = self.parse_or()
        while self.peek() == "+":
            self.consume()
            node = AndNode(left=node, right=self.parse_or())
        return node

    def parse_or(self) -> Node:
        node = self.parse_atom()
        while self.peek() == "/":
            self.consume()
            node = OrNode(left=node, right=self.parse_atom())
        return node

    def parse_atom(self) -> Node:
        token = self.peek()

        if token == "(":
            self.consume()
            node = self.parse_and()
            if self.peek() != ")":
                raise ValueError("Ожидалась ')'")
            self.consume()
            return node

        if isinstance(token, int):
            self.consume()
            return EventNode(event_id=token)

        raise ValueError(f"Ожидался event_id или скобка, получено: {token}")


def compile_formula(formula: str) -> Node:
    tokens = tokenize(formula)
    return Parser(tokens).parse()


# ---------------------------
# Вычисление
# ---------------------------

def evaluate(node: Node, active_event_ids: Set[int]) -> bool:
    if isinstance(node, EventNode):
        return node.event_id in active_event_ids

    if isinstance(node, AndNode):
        return evaluate(node.left, active_event_ids) and evaluate(node.right, active_event_ids)

    if isinstance(node, OrNode):
        return evaluate(node.left, active_event_ids) or evaluate(node.right, active_event_ids)

    raise TypeError(f"Неизвестный тип узла: {type(node)}")


# ---------------------------
# Объяснение (опционально)
# ---------------------------

def matched_events(node: Node, active_event_ids: Set[int]) -> Set[int]:
    if isinstance(node, EventNode):
        return {node.event_id} if node.event_id in active_event_ids else set()

    if isinstance(node, AndNode):
        if evaluate(node, active_event_ids):
            return matched_events(node.left, active_event_ids) | matched_events(node.right, active_event_ids)
        return set()

    if isinstance(node, OrNode):
        left_ok = evaluate(node.left, active_event_ids)
        right_ok = evaluate(node.right, active_event_ids)

        if left_ok and right_ok:
            return matched_events(node.left, active_event_ids) | matched_events(node.right, active_event_ids)
        if left_ok:
            return matched_events(node.left, active_event_ids)
        if right_ok:
            return matched_events(node.right, active_event_ids)
        return set()

    raise TypeError(f"Неизвестный тип узла: {type(node)}")


# ---------------------------
# Публичный API движка
# ---------------------------

class DiagnosisRule:
    def __init__(self, diagnosis_id: int, title: str, formula: str):
        self.diagnosis_id = diagnosis_id
        self.title = title
        self.formula = formula
        self.ast = compile_formula(formula)

    def check(self, active_event_ids: Set[int]) -> bool:
        return evaluate(self.ast, active_event_ids)

    def explain(self, active_event_ids: Set[int]) -> dict:
        return {
            "diagnosis_id": self.diagnosis_id,
            "title": self.title,
            "formula": self.formula,
            "matched": self.check(active_event_ids),
            "matched_events": sorted(matched_events(self.ast, active_event_ids)),
        }


# ---------------------------
# Локальный тест
# ---------------------------

if __name__ == "__main__":
    rules = [
        DiagnosisRule(
            1,
            "ИОХВ",
            "(Event 20/Event 25/(Event 64+Event 68)/Event 63/Event 65) + (Event 1/Event 23/Event 56/Event 66/Event 67/Event 69)"
        ),
        DiagnosisRule(
            2,
            "Инфекция кровотока",
            "Event 2 + Event 17/Event 75"
        ),
        DiagnosisRule(
            3,
            "КАИК",
            "Event 3 + Event 16/Event 17/Event 75"
        ),
    ]

    test_cases = [
        {"name": "case_1", "events": {25, 56}},
        {"name": "case_2", "events": {64, 68, 69}},
        {"name": "case_3", "events": {2, 17}},
        {"name": "case_4", "events": {3, 16}},
        {"name": "case_5", "events": {64, 69}},
    ]

    for case in test_cases:
        print("=" * 80)
        print(case["name"], sorted(case["events"]))
        for rule in rules:
            result = rule.explain(case["events"])
            print(result)













# import re
#
# class Expr:
#     def __init__(self, kind, value=None, left=None, right=None):
#         self.kind = kind
#         self.value = value
#         self.left = left
#         self.right = right
#
#     def __add__(self, other):
#         return Expr("AND", left=self, right=other)
#
#     def __truediv__(self, other):
#         return Expr("OR", left=self, right=other)
#
#     def check(self, active_events: set[int]) -> bool:
#         if self.kind == "EVENT":
#             return self.value in active_events
#         if self.kind == "AND":
#             return self.left.check(active_events) and self.right.check(active_events)
#         if self.kind == "OR":
#             return self.left.check(active_events) or self.right.check(active_events)
#         raise ValueError(f"Unknown kind: {self.kind}")
#
#     def __repr__(self):
#         if self.kind == "EVENT":
#             return f"E({self.value})"
#         return f"({self.left} {self.kind} {self.right})"
#
#
# def E(n: int) -> Expr:
#     return Expr("EVENT", value=n)
#
#
# def normalize_formula(formula: str) -> str:
#     formula = formula.replace("\xa0", " ")
#     formula = re.sub(r"Event\s*(\d+)", r"E(\1)", formula, flags=re.IGNORECASE)
#     formula = re.sub(r"\s+", " ", formula).strip()
#     return formula
#
#
# def build_expr(formula: str) -> Expr:
#     normalized = normalize_formula(formula)
#     return eval(normalized, {"__builtins__": {}}, {"E": E})
#
# print(__name__)
# if __name__ == "__main__":
#     formula = "(Event 20/Event 25/(Event 64+Event 68)/Event 63/Event 65) + (Event 1/Event 23/Event 56/Event 66/Event 67/Event 69)"
#     formula1 = "Event 2 + Event 17/Event 75 "
#     expr = build_expr(formula)
#     expr1 = build_expr(formula1)
#
#     print("Нормализовано:", normalize_formula(formula))
#     print("Дерево:", expr)
#
#     print("\n"+"Нормализовано:", normalize_formula(formula1))
#     print("Дерево:", expr1)
#     active_events_1 = {25, 56}
#     active_events_2 = {64, 68, 69}
#     active_events_3 = {64, 69}
#     active_events_4 = {2, 17}
#     active_events_5 = {2, 17,75}
#     active_events_6 = {2, 6}
#
#     print("case 1:", expr.check(active_events_1))  # True
#     print("case 2:", expr.check(active_events_2))  # True
#     print("case 3:", expr.check(active_events_3))  # False
#
#     print("\n"+"case 4:", expr1.check(active_events_4))  # True
#     print("case 5:", expr1.check(active_events_5))  # True
#     print("case 6:", expr1.check(active_events_6))  # False
