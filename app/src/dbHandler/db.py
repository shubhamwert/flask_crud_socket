from flask_sqlalchemy import SQLAlchemy
db=SQLAlchemy()
def add_item_to_table(table_name: str, db, item: dict):
    """
    Generic helper to add a row to a given SQLAlchemy table.

    :param table_name: Name of the SQLAlchemy model class (as string)
    :param db: The SQLAlchemy instance
    :param item: A dictionary of column names and values
    :return: The created model instance or raises ValueError
    """
    # Get the model class from the table name
    model_class = db.Model._decl_class_registry.get(table_name)
    
    if model_class is None:
        raise ValueError(f"Table '{table_name}' not found in SQLAlchemy models.")

    # Create a new instance
    instance = model_class(**item)

    # Add and commit to DB
    db.session.add(instance)
    db.session.commit()

    return instance