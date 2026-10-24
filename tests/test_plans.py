def test_plan_price_must_be_greater_than_zero(client):
    for bad_price in ("0", "-5"):
        response = client.post("/plans", json={"name": "Bad", "price": bad_price})
        assert response.status_code == 422


def test_plan_can_be_created_updated_and_deactivated(client, make_plan):
    plan = make_plan(price="10.00")

    response = client.patch(f"/plans/{plan['id']}", json={"price": "12.50", "status": "inactive"})

    assert response.status_code == 200
    assert response.json()["price"] == "12.50"
    assert response.json()["status"] == "inactive"


def test_plan_update_rejects_non_positive_price(client, make_plan):
    plan = make_plan()
    response = client.patch(f"/plans/{plan['id']}", json={"price": "0"})
    assert response.status_code == 422


def test_unknown_plan_returns_404(client):
    response = client.patch("/plans/999", json={"name": "Nope"})
    assert response.status_code == 404
    assert response.json()["error"] == "not_found"