#using glot library , have to define what is allowed and disallowed
from typing import Iterable, Type
from sqlglot import  exp
from sqlglot.expressions import Expression

from model.services_contract import ValidationResult

read_only_allowed  = (
    exp.Select,
    exp.With,
    exp.Except,
    exp.Show,
    exp.Describe,
)

read_only_disallowed = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Create,
    exp.Drop,
    exp.Alter,
    exp.TruncateTable,
    exp.Merge,
    exp.Grant,
    exp.Revoke,
    exp.Analyze,
)


def is_valid(expression: list[Expression],*,allowed_list: Iterable[Type[Expression]]=read_only_allowed,
             disallowed_list: Iterable[Type[Expression]]=read_only_disallowed) -> ValidationResult:


    allowed_list =  tuple(allowed_list)
    disallowed_list = tuple(disallowed_list)
    not_valid = False
    for statement in expression:
        if not isinstance(statement,allowed_list):
            not_valid = True
            break

        for node in statement.walk():
            if isinstance(node,disallowed_list):
                not_valid = True
                break

    if not_valid:
        return ValidationResult(
            valid=False,
            errors=["Query contains disallowed statements"],
        )

    errors: list[str] = []
    return ValidationResult(valid=True, errors=errors)
    
    
