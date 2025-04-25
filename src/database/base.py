from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.model import Model, DefaultMeta, _QueryProperty
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import declarative_base


class BaseModel(Model):
    pass

class UnlockedAlchemy(SQLAlchemy):
    def _make_declarative_base(self, model_class, disable_autonaming: bool = False, ):
        metadata = self._make_metadata(None)
        if not isinstance(model_class, DeclarativeMeta):
            model = declarative_base(
                cls=model_class, name="Model", metadata=metadata, metaclass=DeclarativeMeta
            )
        else:
            model = model_class

        if None not in self.metadatas:
            # Use the model's metadata as the default metadata.
            model.metadata.info["bind_key"] = None
            self.metadatas[None] = model.metadata
        else:
            # Use the passed in default metadata as the model's metadata.
            model.metadata = self.metadatas[None]

        model.query_class = self.Query
        model.query = _QueryProperty()
        model.__fsa__ = self
        return model