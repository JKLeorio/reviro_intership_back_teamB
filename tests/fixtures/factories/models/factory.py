from sqlalchemy import select, inspect
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
import factory



class CustomFactoryBase(factory.Factory):
    class Meta:
        model = dict
        abstract = True
    
    class _Config:
        factory_model = None
        factory_model_schema = None
        unique_fields = ()
    
    @classmethod
    def get_config(cls, key, default=None):
        for par_cls in cls.__mro__:
            config = getattr(par_cls, '_Config', None)
            if config and hasattr(config, key):
                return getattr(config, key)
        return default
        


class FactorySessionController:
    factory_cls: CustomFactoryBase = None
    session: AsyncSession = None
    _factory_model: Any = None
    _factory_model_schema: BaseModel = None

    def __init__(
            self, 
            factory_cls: CustomFactoryBase,
            session: AsyncSession,
            *args,
            **kwargs
            ):
        
        self.factory_cls = factory_cls
        self.session = session
        self._read_from_config(self.factory_cls)

    
    def _read_from_config(self, factory_cls: CustomFactoryBase):
        self._factory_model = factory_cls.get_config('factory_model')
        self._factory_model_schema = factory_cls.get_config('factory_model_schema')
        if self._factory_model is None:
            raise BaseException(f'set factory_model in Config class of {factory_cls}')
        if self._factory_model_schema is None:
            raise BaseException('set factory_model_schema in Config class')
    
    def _load_options(load_options_queue: dict):
        pass

    async def _get_or_create(
            self, 
            field: Any,
            value: Any,
            factory_model_cls: Any
            ):
        stmt = (select(factory_model_cls)
                .where(
                    getattr(factory_model_cls, field)
                    ==
                    value
                    )
                )
        result = await self.session.execute(stmt)
        instanse = result.scalar_one_or_none()
        # if instanse is None:
        #     instanse = factory_model_cls()
        return instanse

    def _get_in_load_attributes(
            self, 
            factory_cls, 
            generated_data: dict
            ):
        in_load_attributes = list()
        for key, value in generated_data.items():
            if hasattr(factory_cls, key):
                factory_attr = getattr(factory_cls, key)
                if type(factory_attr) is factory.SubFactory:
                    in_load_attributes.append(key)
        return in_load_attributes
    
    async def _ConvertFactoryDataToModel(
            self, 
            factory_model_cls: Any, 
            factory_cls: CustomFactoryBase, 
            in_load_attributes: list,
            generated_data: dict
            ):
        instance = factory_model_cls()
        load_queue = dict()
        in_load_attributes = self._get_in_load_attributes(
            factory_cls=factory_cls,
            generated_data=generated_data
        )
        factory_attr = None

        unique_fields = factory_cls.get_config('unique_fields')

        relationship_fields = [
            factory.SubFactory,
            factory.RelatedFactory
        ]

        for key, value in generated_data.items():
            if hasattr(factory_cls, key):
                factory_attr = getattr(factory_cls, key)
                if type(factory_attr) in relationship_fields:
                    field_factory_cls = factory_attr.get_factory()
                    field_model_cls = field_factory_cls.get_config('factory_model')
                    converted_field_data, in_load = await self._ConvertFactoryDataToModel(
                        factory_model_cls=field_model_cls,
                        factory_cls=field_factory_cls,
                        in_load_attributes=in_load_attributes,
                        generated_data=value
                        )
                    setattr(
                        instance, 
                        key,
                        converted_field_data
                        )
                else:
                    if key in unique_fields:
                        unique_instance = await self._get_or_create(key, value, factory_model_cls)
                        if unique_instance is not None:
                            return [unique_instance, in_load_attributes]
                    setattr(instance, key, value)
        return [instance, in_load_attributes]

    async def create(self, validate_with_schema: bool=True, **kwargs):
        """
        returns alchemy_model instance after save and commit
        """
        unique_fields = self.factory_cls.get_config('unique_fields')
        generated_data: dict = self.factory_cls.build()
        for key, value in kwargs.items():
            if key in unique_fields:
                # setattr(generated_data, key, value)
                generated_data[key] = value
        instance, in_load_attributes = await self._ConvertFactoryDataToModel(
            factory_cls=self.factory_cls,
            factory_model_cls=self._factory_model,
            in_load_attributes= [],
            generated_data=generated_data
            )
        for key, value in kwargs.items():
            if key not in unique_fields:
                setattr(instance, key, value)
        if inspect(instance).transient:
            self.session.add(instance)
            await self.session.commit()
        await self.session.refresh(
            instance,
            attribute_names=in_load_attributes
            )
        if validate_with_schema:
            refreshed_validated_instanse = self._factory_model_schema.model_validate(instance)
            return refreshed_validated_instanse
        return instance

    async def create_batch(self, size: int = 1, **kwargs):
        """
        returns alchemy_model instances after save and commit
        """
        response = list()
        for i in range(size):
            response.append(await self.create(**kwargs))
        return response

    async def build(self, **kwargs):
        """
        returns alchemy_model instance without commit or flush
        """
        generated_data: dict = self.factory_cls.create()
        instance, in_load_attributes = await self._ConvertFactoryDataToModel(
            factory_cls=self.factory_cls,
            factory_model_cls=self._factory_model,
            in_load_attributes=[],
            generated_data=generated_data
            )
        return instance

    async def build_batch(self, size: int = 1, **kwargs):
        """
        returns alchemy_model instances without commit or flush
        """
        response = list()
        for i in range(size):
            response.append(await self.build(**kwargs))
        return response
