#using glot library , have to define what is allowed and disallowed
from typing import Iterable, Type
from sqlglot import parse, exp
from sqlglot.expressions import Expression

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


def is_valid(query: str,*,dialect:str,allowed_list: Iterable[Type[Expression]]=read_only_allowed,
             disallowed_list: Iterable[Type[Expression]]=read_only_disallowed) -> bool:

    try:
        expression = parse(query,dialect=dialect)
    except Exception as exc:
        print(f"Exception {exc}")
        return False
    
    allowed_list =  tuple(allowed_list)
    disallowed_list = tuple(disallowed_list)
    for statement in expression:
        if not isinstance(statement,allowed_list):
            return False

        for node in statement.walk():
            if isinstance(node,disallowed_list):
                return False

    return True
    
    
