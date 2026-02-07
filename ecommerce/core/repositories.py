"""
Base repository pattern for data access.
"""
from typing import Type, TypeVar, Generic, Optional, List
from django.db.models import Model, QuerySet

T = TypeVar('T', bound=Model)


class BaseRepository(Generic[T]):
    """Base repository for common database operations."""

    model: Type[T]

    def __init__(self):
        if not hasattr(self, 'model'):
            raise NotImplementedError("Subclasses must define 'model' attribute")

    def get_all(self) -> QuerySet[T]:
        return self.model.objects.all()

    def get_by_id(self, pk: int) -> Optional[T]:
        try:
            return self.model.objects.get(pk=pk)
        except self.model.DoesNotExist:
            return None

    def create(self, **kwargs) -> T:
        return self.model.objects.create(**kwargs)

    def update(self, instance: T, **kwargs) -> T:
        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save()
        return instance

    def delete(self, instance: T) -> None:
        instance.delete()

    def filter(self, **kwargs) -> QuerySet[T]:
        return self.model.objects.filter(**kwargs)

    def exists(self, **kwargs) -> bool:
        return self.model.objects.filter(**kwargs).exists()
