from typing import List, Dict, Any, Optional
from sqlalchemy import inspect
import enum

from bot.database_interface import bot_declarative_base
from bot.database_interface.session.session_handler import session_scope


def _check_if_something_exists(
    model: bot_declarative_base, options: Dict[str, Any]
) -> bool:
    """
    Checks whether an instance of a model already exists for given `options`.

    Args:
        model (bot_declarative_base): An SQL model instance inheriting from the declarative_base
        options (Dict[str, Any]): A dictionary of query_parameters of syntax {attribute: value_to_query_for}

    Returns:
        bool: True, if an instance of model already exists given the `options`; False, if not.
    """
    with session_scope() as session:
        # use a simple SQL `exists` query
        return (
            session.query(session.query(model).filter_by(**options).exists())
        ).scalar()


def object_as_dict(obj: bot_declarative_base) -> Dict[str, Any]:
    return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}


def dict_enums_to_values(values: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in values.items():
        if isinstance(v, enum.Enum):
            values[k] = v.value
    return values


def get_all_instances_of_something(
    model: bot_declarative_base, options: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Returns all instances of a model as a list, optionally based on a query.

    Args:
        model (bot_declarative_base): The SQL model to query
        options (Optional[Dict[str, Any]]): query filters

    Returns:
        List[bot_declarative_base]: a list of model instances
    """
    with session_scope() as session:
        if options:
            results = session.query(model).filter_by(**options).all()
        else:
            results = session.query(model).all()
        # if not isinstance(results, list):
        #     results = list(results)

        return [dict_enums_to_values(object_as_dict(r)) for r in results]


def delete_first_instance_by_filter(
    model: bot_declarative_base, options: Dict[str, Any]
) -> str:
    with session_scope() as session:
        obj = session.query(model).filter_by(**options).first()
        obj_remnant = obj.__repr__()
        session.delete(obj)
    return obj_remnant