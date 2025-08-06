from typing import Coroutine
from sqlalchemy.ext.asyncio import AsyncSession
from tests.fixtures.factories.models.factory import FactorySessionController, CustomFactoryBase



def modern_factory_of_factories(factory_cls: CustomFactoryBase, session: AsyncSession ) -> Coroutine:
    async def _factory(count: int = 1, strategy: str = 'create', **kwargs):
        '''
        count:

        count of elements thats return

        strategy:

        function have two strategy
        create -> return instance after commit
        build -> return instance without commit
        '''
        session_controller = FactorySessionController(factory_cls, session)
        strategies = ['create', 'build']
        if strategy not in strategies:
            raise KeyError(
                f"indicate the correct strategy, strategies -> {strategies}, current -> {strategy}"
                )
        if count > 1:
            if strategy == 'create':
                instanse = await session_controller.create_batch(count, **kwargs)
            elif strategy == 'build':
                instanse = await session_controller.build_batch(count, **kwargs)
        else:
            if strategy == 'create':
                instanse = await session_controller.create(**kwargs)
            elif strategy == 'build':
                instanse = await session_controller.build(**kwargs)
        return instanse
    return _factory