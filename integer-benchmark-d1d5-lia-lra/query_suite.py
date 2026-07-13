from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetQuerySpec:
    name: str
    node_labels: tuple[str, str, str, str]
    edge_labels: tuple[str, str, str]
    attr1: str
    attr2: str
    two_d_threshold: float
    scalar_threshold: float
    end_gap: float
    range_threshold: float


@dataclass(frozen=True)
class FormulaSeries:
    start: str
    step1: str
    step2: str
    step3: str
    repeat: str

    def at(self, position: int) -> str:
        if position <= 0:
            return self.start
        if position == 1:
            return self.step1
        if position == 2:
            return self.step2
        if position == 3:
            return self.step3
        return self.repeat


@dataclass(frozen=True)
class TemplateQuery:
    template_id: int
    template_name: str
    constraint_name: str
    query: str

    @property
    def query_key(self) -> str:
        return f"{self.template_name}:{self.constraint_name}"


CONSTRAINT_NAMES: tuple[str, ...] = ("D1", "D2", "D3", "D4", "D5", "D6")
LRA_CONSTRAINTS: tuple[str, ...] = ("D1", "D2", "D3")
LIA_CONSTRAINTS: tuple[str, ...] = ("D4", "D5", "D6")

CONSTRAINT_CATEGORIES: dict[str, str] = {
    "D1": "Real Arithmetic",
    "D2": "Real Arithmetic",
    "D3": "Real Arithmetic",
    "D4": "Integer Arithmetic",
    "D5": "Integer Arithmetic",
    "D6": "Integer Arithmetic",
}


def _fmt_num(value: float | int) -> str:
    if isinstance(value, int):
        return str(value)
    if float(value).is_integer():
        return str(int(value))
    return f"{value:g}"


def _node(label: str, formula: str) -> str:
    return f"({label} {{{formula}}})"


def _step(edge: str, label: str, formula: str, *, edge_formula: str = "true") -> str:
    return f"(({edge} {{{edge_formula}}})/({label} {{{formula}}}))"


def _union(parts: list[str]) -> str:
    return f"({' | '.join(parts)})"


def _manhattan_leq(x_attr: str, y_attr: str, x_ref: str, y_ref: str, bound: str) -> str:
    return (
        f"{x_attr} - {x_ref} + {y_attr} - {y_ref} <= {bound} and "
        f"{x_ref} - {x_attr} + {y_attr} - {y_ref} <= {bound} and "
        f"{x_ref} - {x_attr} + {y_ref} - {y_attr} <= {bound} and "
        f"{x_attr} - {x_ref} + {y_ref} - {y_attr} <= {bound}"
    )


def _constraint_formulas(spec: DatasetQuerySpec, constraint_name: str, *, scale: int) -> FormulaSeries:
    attr1 = spec.attr1
    attr2 = spec.attr2

    two_d_threshold = _fmt_num(spec.two_d_threshold * scale)
    scalar_threshold = _fmt_num(spec.scalar_threshold * scale)
    end_gap = _fmt_num(spec.end_gap * scale)
    range_threshold = _fmt_num(spec.range_threshold * scale)

    if constraint_name == "D1":
        formula = _manhattan_leq(attr1, attr2, "?x", "?y", two_d_threshold)
        return FormulaSeries(formula, formula, formula, formula, formula)

    if constraint_name == "D2":
        start = f"??sx = {attr1} and ??sy = {attr2}"
        close_to_start = _manhattan_leq(attr1, attr2, "??sx", "??sy", two_d_threshold)
        rest = f"({attr1} != ??sx or {attr2} != ??sy) and {close_to_start}"
        return FormulaSeries(start, rest, rest, rest, rest)

    if constraint_name == "D3":
        near_x = f"?x - {attr1} <= {scalar_threshold} and {attr1} - ?x <= {scalar_threshold}"
        end_formula = f"{near_x} and ?x + {end_gap} <= {attr1}"
        return FormulaSeries(near_x, near_x, near_x, end_formula, end_formula)

    if constraint_name == "D4":
        return FormulaSeries(
            start=f"??base = {attr1} and ??inc0 = {attr1}",
            step1=f"??inc1 = {attr1} in ??inc1 >= ??inc0 and ??inc1 - ??base <= {range_threshold}",
            step2=f"??inc2 = {attr1} in ??inc2 >= ??inc1 and ??inc2 - ??base <= {range_threshold}",
            step3=f"??inc3 = {attr1} in ??inc3 >= ??inc2 and ??inc3 - ??base <= {range_threshold}",
            repeat=f"{attr1} >= ??inc3 and {attr1} - ??base <= {range_threshold}",
        )

    if constraint_name == "D5":
        even_formula = f"{attr1} == ?half + ?half"
        return FormulaSeries(
            start=f"??dec0 = {attr1}",
            step1=f"??dec1 = {attr1} in ??dec1 <= ??dec0",
            step2=f"??dec2 = {attr1} in ??dec2 <= ??dec1",
            step3=f"??dec3 = {attr1} in ??dec3 <= ??dec2 and {even_formula}",
            repeat=f"{attr1} <= ??dec3 and {even_formula}",
        )

    if constraint_name == "D6":
        return FormulaSeries(
            start=f"2 * {attr1} <= ?pe",
            step1=f"2 * {attr1} <= ?pe",
            step2=f"2 * {attr1} <= ?pe",
            step3=f"2 * {attr1} <= ?pe and {attr1} == ?pe and ?pe == ?half + ?half",
            repeat=f"2 * {attr1} <= ?pe and {attr1} == ?pe and ?pe == ?half + ?half",
        )

    raise ValueError(f"Unsupported constraint: {constraint_name}")


def _template_01(prefix: str, spec: DatasetQuerySpec, formulas: FormulaSeries) -> str:
    n0, n1, n2, n3 = spec.node_labels
    e1, e2, e3 = spec.edge_labels
    return (
        f"{prefix} "
        f"{_node(n0, formulas.at(0))}/"
        f"{_union([_step(e1, n1, formulas.at(1)), _step(e2, n2, formulas.at(1)), _step(e3, n3, formulas.at(1))])}/"
        f"{_step(e3, n3, formulas.at(2))}*"
    )


def _template_02(prefix: str, spec: DatasetQuerySpec, formulas: FormulaSeries) -> str:
    n0, n1, _, _ = spec.node_labels
    e1, _, _ = spec.edge_labels
    return f"{prefix} {_node(n0, formulas.at(0))}/{_step(e1, n1, formulas.at(1))}*"


def _template_03(prefix: str, spec: DatasetQuerySpec, formulas: FormulaSeries) -> str:
    n0, n1, n2, n3 = spec.node_labels
    e1, e2, e3 = spec.edge_labels
    return (
        f"{prefix} "
        f"{_node(n0, formulas.at(0))}/"
        f"{_step(e1, n1, formulas.at(1))}/"
        f"{_step(e2, n2, formulas.at(2))}/"
        f"{_step(e3, n3, formulas.at(3))}"
    )


def _template_04(prefix: str, spec: DatasetQuerySpec, formulas: FormulaSeries) -> str:
    n0, n1, n2, _ = spec.node_labels
    e1, e2, _ = spec.edge_labels
    return (
        f"{prefix} "
        f"{_node(n0, formulas.at(0))}/"
        f"{_step(e1, n1, formulas.at(1))}*/"
        f"{_step(e2, n2, formulas.at(2))}"
    )


def _template_05(prefix: str, spec: DatasetQuerySpec, formulas: FormulaSeries) -> str:
    n0, n1, n2, n3 = spec.node_labels
    e1, e2, e3 = spec.edge_labels
    return (
        f"{prefix} "
        f"{_node(n0, formulas.at(0))}/"
        f"{_union([_step(e1, n1, formulas.at(1)), _step(e2, n2, formulas.at(1)), _step(e3, n3, formulas.at(1))])}*"
    )


def _template_06(prefix: str, spec: DatasetQuerySpec, formulas: FormulaSeries) -> str:
    n0, n1, _, _ = spec.node_labels
    e1, _, _ = spec.edge_labels
    return f"{prefix} {_node(n0, formulas.at(0))}/{_step(e1, n1, formulas.at(1))}+"


def _template_07(prefix: str, spec: DatasetQuerySpec, formulas: FormulaSeries) -> str:
    n0, n1, n2, n3 = spec.node_labels
    e1, e2, e3 = spec.edge_labels
    return (
        f"{prefix} "
        f"{_node(n0, formulas.at(0))}/"
        f"{_step(e1, n1, formulas.at(1))}?/"
        f"{_step(e2, n2, formulas.at(2))}?/"
        f"{_step(e3, n3, formulas.at(3))}?"
    )


def _template_08(prefix: str, spec: DatasetQuerySpec, formulas: FormulaSeries) -> str:
    n0, n1, n2, n3 = spec.node_labels
    e1, e2, e3 = spec.edge_labels
    return (
        f"{prefix} "
        f"{_node(n0, formulas.at(0))}/"
        f"{_step(e1, n1, formulas.at(1))}/"
        f"{_union([_step(e2, n2, formulas.at(2)), _step(e3, n3, formulas.at(2))])}"
    )


def _template_09(prefix: str, spec: DatasetQuerySpec, formulas: FormulaSeries) -> str:
    n0, n1, n2, n3 = spec.node_labels
    e1, e2, e3 = spec.edge_labels
    return (
        f"{prefix} "
        f"{_node(n0, formulas.at(0))}/"
        f"{_step(e1, n1, formulas.at(1))}/"
        f"{_step(e2, n2, formulas.at(2))}?/"
        f"{_step(e3, n3, formulas.at(3))}?"
    )


def _template_10(prefix: str, spec: DatasetQuerySpec, formulas: FormulaSeries) -> str:
    n0, n1, n2, n3 = spec.node_labels
    e1, e2, e3 = spec.edge_labels
    branch_1 = f"({_step(e1, n1, formulas.at(1))}/{_step(e2, n2, formulas.at(2))}*)"
    branch_2 = _step(e3, n3, formulas.at(3))
    return f"{prefix} {_node(n0, formulas.at(0))}/({branch_1} | {branch_2})"


def _template_11(prefix: str, spec: DatasetQuerySpec, formulas: FormulaSeries) -> str:
    n0, n1, n2, _ = spec.node_labels
    e1, e2, _ = spec.edge_labels
    return (
        f"{prefix} "
        f"{_node(n0, formulas.at(0))}/"
        f"{_step(e1, n1, formulas.at(1))}?/"
        f"{_step(e2, n2, formulas.at(2))}*"
    )


def _template_12(prefix: str, spec: DatasetQuerySpec, formulas: FormulaSeries) -> str:
    n0, n1, n2, n3 = spec.node_labels
    e1, e2, e3 = spec.edge_labels
    return (
        f"{prefix} "
        f"{_node(n0, formulas.at(0))}/"
        f"{_step(e1, n1, formulas.at(1))}/"
        f"{_step(e2, n2, formulas.at(2))}/"
        f"{_step(e3, n3, formulas.at(3))}*"
    )


REGULAR_TEMPLATES: tuple[tuple[int, str, callable], ...] = (
    (1, "regular01", _template_01),
    (2, "regular02", _template_02),
    (3, "regular03", _template_03),
    (4, "regular04", _template_04),
    (5, "regular05", _template_05),
    (6, "regular06", _template_06),
    (7, "regular07", _template_07),
    (8, "regular08", _template_08),
    (9, "regular09", _template_09),
    (10, "regular10", _template_10),
    (11, "regular11", _template_11),
    (12, "regular12", _template_12),
)


def build_constraint_queries(
    spec: DatasetQuerySpec,
    *,
    optimized: bool,
    integer_mode: bool,
    scale: int = 1,
) -> list[TemplateQuery]:
    prefix = "DATA_TEST NAIVE ?e" if not optimized else ("DATA_TEST INT ?e" if integer_mode else "DATA_TEST REAL ?e")
    active_constraints = LIA_CONSTRAINTS if integer_mode else LRA_CONSTRAINTS
    queries: list[TemplateQuery] = []

    for template_id, template_name, template_builder in REGULAR_TEMPLATES:
        for constraint_name in active_constraints:
            formulas = _constraint_formulas(spec, constraint_name, scale=scale)
            queries.append(
                TemplateQuery(
                    template_id=template_id,
                    template_name=template_name,
                    constraint_name=constraint_name,
                    query=template_builder(prefix, spec, formulas),
                )
            )
    return queries


QUERY_SPECS: dict[str, DatasetQuerySpec] = {
    "pokec": DatasetQuerySpec(
        name="pokec",
        node_labels=("people", "people", "people", "people"),
        edge_labels=(":Follow", ":Favorite", ":FollowAnonymously"),
        attr1="AGE",
        attr2="completion_percentage",
        two_d_threshold=100,
        scalar_threshold=15,
        end_gap=100,
        range_threshold=100,
    ),
    "ldbc01": DatasetQuerySpec(
        name="ldbc01",
        node_labels=("person", "person", "tag", "tagclass"),
        edge_labels=(":knows", ":hasInterest", ":hasType"),
        attr1="oid",
        attr2="iid",
        two_d_threshold=100,
        scalar_threshold=15,
        end_gap=100,
        range_threshold=100,
    ),
    "ldbc10": DatasetQuerySpec(
        name="ldbc10",
        node_labels=("Person", "Person", "Tag", "TagClass"),
        edge_labels=(":KNOWS", ":HAS_INTEREST", ":HAS_TYPE"),
        attr1="id",
        attr2="uid",
        two_d_threshold=100,
        scalar_threshold=15,
        end_gap=100,
        range_threshold=100,
    ),
    "icij-leak": DatasetQuerySpec(
        name="icij-leak",
        node_labels=("Entity", "Entity", "Entity", "Intermediary"),
        edge_labels=(":same_as", ":same_name_as", ":underlying"),
        attr1="valid_until",
        attr2="node_id",
        two_d_threshold=100,
        scalar_threshold=15,
        end_gap=100,
        range_threshold=100,
    ),
    "paradise": DatasetQuerySpec(
        name="paradise",
        node_labels=("Officer", "Entity", "Address", "Intermediary"),
        edge_labels=(":OFFICER_OF", ":REGISTERED_ADDRESS", ":INTERMEDIARY_OF"),
        attr1="node_id",
        attr2="valid_until",
        two_d_threshold=0.1,
        scalar_threshold=0.3,
        end_gap=0.1,
        range_threshold=0.1,
    ),
    "telecom": DatasetQuerySpec(
        name="telecom",
        node_labels=("cell", "user", "app", "package"),
        edge_labels=(":lived", ":used", ":bought"),
        attr1="attr1",
        attr2="attr2",
        two_d_threshold=0.1,
        scalar_threshold=0.3,
        end_gap=0.1,
        range_threshold=0.1,
    ),
}
