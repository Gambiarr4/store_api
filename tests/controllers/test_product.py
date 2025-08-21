from typing import List

import pytest
from tests.factories import product_data
from fastapi import status
from store.schemas.product import ProductOut
from datetime import datetime


async def test_controller_create_should_return_success(client, products_url):
    response = await client.post(products_url, json=product_data())

    content = response.json()

    del content["created_at"]
    del content["updated_at"]
    del content["id"]

    assert response.status_code == status.HTTP_201_CREATED
    assert content == {
        "name": "Iphone 14 Pro Max",
        "quantity": 10,
        "price": "8.500",
        "status": True,
    }


async def test_controller_get_should_return_success(
    client, products_url, product_inserted
):
    response = await client.get(f"{products_url}{product_inserted.id}")

    content = response.json()

    del content["created_at"]
    del content["updated_at"]

    assert response.status_code == status.HTTP_200_OK
    assert content == {
        "id": str(product_inserted.id),
        "name": "Iphone 14 Pro Max",
        "quantity": 10,
        "price": "8.500",
        "status": True,
    }


async def test_controller_get_should_return_not_found(client, products_url):
    response = await client.get(f"{products_url}4fd7cd35-a3a0-4c1f-a78d-d24aa81e7dca")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "Product not found with filter: 4fd7cd35-a3a0-4c1f-a78d-d24aa81e7dca"
    }


@pytest.mark.usefixtures("products_inserted")
async def test_controller_query_should_return_success(client, products_url):
    response = await client.get(products_url)

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), List)
    assert len(response.json()) > 1


async def test_controller_patch_should_return_success(
    client, products_url, product_inserted
):
    response = await client.patch(
        f"{products_url}{product_inserted.id}", json={"price": "7.500"}
    )

    content = response.json()

    del content["created_at"]
    del content["updated_at"]

    assert response.status_code == status.HTTP_200_OK
    assert content == {
        "id": str(product_inserted.id),
        "name": "Iphone 14 Pro Max",
        "quantity": 10,
        "price": "7.500",
        "status": True,
    }


async def test_controller_delete_should_return_no_content(
    client, products_url, product_inserted
):
    response = await client.delete(f"{products_url}{product_inserted.id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT


async def test_controller_delete_should_return_not_found(client, products_url):
    response = await client.delete(
        f"{products_url}4fd7cd35-a3a0-4c1f-a78d-d24aa81e7dca"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "Product not found with filter: 4fd7cd35-a3a0-4c1f-a78d-d24aa81e7dca"
    }

async def test_should_return_409_if_product_already_exists(client, products_url):
    product_payload = {
        "name": "Produto Teste 1",
        "quantity": 10,
        "price": 8500.00
    }
    response = await client.post(products_url, json=product_payload)
    assert response.status_code == status.HTTP_201_CREATED
    response = await client.post(products_url, json=product_payload)

    assert response.status_code == status.HTTP_409_CONFLICT
    assert "Product with this name already exists" in response.json().get("detail")

async def test_should_return_404_if_product_not_found_on_update(client, products_url):
    response = await client.patch(f"{products_url}00000000-0000-0000-0000-000000000000", json={"price": 100})

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Product not found" in response.json().get("detail")

async def test_should_update_updated_at_automatically(client, products_url):
    product_payload = {
        "name": "Smartphone X",
        "quantity": 25,
        "price": 7500.00
    }
    response_post = await client.post(products_url, json=product_payload)

    product_created = ProductOut.model_validate(response_post.json())
    original_created_at = product_created.created_at
    original_updated_at = product_created.updated_at

    update_payload = {"price": 7800.00}
    response_patch = await client.patch(
        f"{products_url}{product_created.id}", json=update_payload
    )

    assert response_patch.status_code == status.HTTP_200_OK
    product_updated = ProductOut.model_validate(response_patch.json())

    assert product_updated.updated_at != original_updated_at
    assert product_updated.created_at == original_created_at
    assert product_updated.price == 7800.00

async def test_should_filter_products_by_price_range(client, products_url):
    product_under = {
        "name": "Produto Sub-5K",
        "quantity": 10,
        "price": 4500.00
    }
    product_in_range = {
        "name": "Produto na Faixa",
        "quantity": 20,
        "price": 6000.00
    }
    product_over = {
        "name": "Produto Acima de 8K",
        "quantity": 30,
        "price": 9000.00
    }

    await client.post(products_url, json=product_under)
    await client.post(products_url, json=product_in_range)
    await client.post(products_url, json=product_over)

    response = await client.get(f"{products_url}?price_gt=5000&price_lt=8000")

    assert response.status_code == status.HTTP_200_OK

    products_filtered = [ProductOut.model_validate(p) for p in response.json()]

    assert len(products_filtered) == 1

    assert products_filtered[0].name == product_in_range["name"]
    