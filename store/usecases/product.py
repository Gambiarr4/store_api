from typing import List
from uuid import UUID
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import pymongo
from store.db.mongo import db_client
from store.models.product import ProductModel
from store.schemas.product import ProductIn, ProductOut, ProductUpdate, ProductUpdateOut
from store.core.exceptions import NotFoundException, ProductAlreadyExistsError, ProductNotFoundError
from datetime import datetime, timezone


class ProductUsecase:
    def __init__(self) -> None:
        self.client: AsyncIOMotorClient = db_client.get()
        self.database: AsyncIOMotorDatabase = self.client.get_database()
        self.collection = self.database.get_collection("products")

    async def create(self, body: ProductIn) -> ProductOut:
        product_model = ProductModel(**body.model_dump())
        existing_product = await self.database.find_one({"name": product_data.name})
        if existing_product:
            raise ProductAlreadyExistsError()
        await self.collection.insert_one(product_model.model_dump())

        return ProductOut(**product_model.model_dump())

    async def get(self, id: UUID) -> ProductOut:
        result = await self.collection.find_one({"id": id})

        if not result:
            raise NotFoundException(message=f"Product not found with filter: {id}")

        return ProductOut(**result)

    async def query(self, min_price: float = None, max_price: float = None) -> List[ProductOut]:
        query_filter = {}
        price_query = {}

        if min_price is not None:
            price_query["$gt"] = min_price
        
        if max_price is not None:
            price_query["$lt"] = max_price

        if price_query:
            query_filter["price"] = price_query

        products = await self.database.find(query_filter)

        return [ProductOut(**item) async for item in products]

    async def update(self, id: UUID, body: ProductUpdate) -> ProductUpdateOut:
        product = await self.database.find_one({"id": id})
        if not product:
            raise ProductNotFoundError()

        result = await self.collection.find_one_and_update(
            filter={"id": id},
            update={"$set": body.model_dump(exclude_none=True)},
            return_document=pymongo.ReturnDocument.AFTER,
        )

        update_data = body.model_dump(by_alias=True, exclude_none=True)
        if "updated_at" not in update_data:
            update_data["updated_at"] = datetime.now(timezone.utc)

        await self.database.update_one(
            {"id": id}, {"$set": update_data}
        )
        
        return ProductUpdateOut(**result)

    async def delete(self, id: UUID) -> bool:
        product = await self.collection.find_one({"id": id})
        if not product:
            raise NotFoundException(message=f"Product not found with filter: {id}")

        result = await self.collection.delete_one({"id": id})

        return True if result.deleted_count > 0 else False


product_usecase = ProductUsecase()
