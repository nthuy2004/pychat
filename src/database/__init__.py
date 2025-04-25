
from extensions import db

Column = db.Column

class CRUDMixin:
    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()
        return obj

    def update(self, commit=True, **kwargs):
        """Update specific fields of a record."""
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        return commit and self.save() or self

    def save(self, commit=True):
        """Save the record."""
        db.session.add(self)
        if commit:
            db.session.commit()
        return self

    def delete(self, commit=True):
        """Remove the record from the database."""
        db.session.delete(self)
        return commit and db.session.commit()

    def get_by_id(cls, record_id):
        """Get record by ID."""
        if any(
            (
                isinstance(record_id, (str, bytes)) and record_id.isdigit(),
                isinstance(record_id, (int, float)),
            )
        ):
            return db.session.get(cls, int(record_id))
        return None

    @classmethod
    def get_or_create(cls, **kwargs):
        if not kwargs:
            return None, False
        obj = cls.query.filter_by(**kwargs).first()
        if obj:
            return obj, False
        obj = cls(**kwargs)
        obj.save()
        return obj, True

    @classmethod
    def get(cls, **kwargs):
        if not kwargs:
            return None
        obj = cls.query.filter_by(**kwargs).first()
        if obj:
            return obj
        return None
    
    @classmethod
    def get_all(cls, **kwargs):
        if not kwargs:
            return None
        obj = cls.query.filter_by(**kwargs)
        if obj:
            return obj
        return None

    @classmethod
    def create_or_update(cls, **kwargs):
        session = db.session
        id = kwargs.pop("id", None)
        if id is not None:
            obj = cls.query.get(id)
            if obj:
                for k, v in kwargs.items():
                    setattr(obj, k, v)
                session.commit()
                return obj, False
        obj = cls(**kwargs)
        obj.save()
        return obj, True


class Model(CRUDMixin, db.Model):
    __abstract__ = True