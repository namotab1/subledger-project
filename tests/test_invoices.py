def test_invoice_amount_due_comes_from_plan_price_at_generation_time(
    client, make_plan, make_customer, make_subscription, make_invoice
):
    plan = make_plan(price="49.99")
    customer = make_customer()
    subscription = make_subscription(customer["id"], plan["id"])

    first = make_invoice(subscription["id"])
    client.patch(f"/plans/{plan['id']}", json={"price": "59.99"})
    second = make_invoice(subscription["id"])

    assert first["amount_due"] == "49.99"
    assert second["amount_due"] == "59.99"
    # the first invoice keeps the price it was issued at
    assert client.get(f"/invoices/{first['id']}").json()["amount_due"] == "49.99"


def test_new_invoice_is_issued_and_unpaid(billing_setup):
    invoice = billing_setup["invoice"]

    assert invoice["status"] == "issued"
    assert invoice["amount_paid"] == "0.00"
    assert invoice["amount_remaining"] == "49.99"
    assert invoice["currency"] == "USD"


def test_invoice_cannot_be_generated_for_cancelled_subscription(client, billing_setup):
    client.patch(f"/subscriptions/{billing_setup['subscription']['id']}/cancel")

    response = client.post("/invoices/generate", json={"subscription_id": billing_setup["subscription"]["id"]})

    assert response.status_code == 409


def test_invoice_for_unknown_subscription_returns_404(client):
    assert client.post("/invoices/generate", json={"subscription_id": 999}).status_code == 404
    assert client.get("/invoices/999").status_code == 404


def test_invoice_accepts_an_explicit_billing_period(client, billing_setup):
    response = client.post(
        "/invoices/generate",
        json={
            "subscription_id": billing_setup["subscription"]["id"],
            "period_start": "2026-03-01",
            "period_end": "2026-03-31",
        },
    )

    assert response.status_code == 201
    assert response.json()["period_start"] == "2026-03-01"
    assert response.json()["due_date"] == "2026-03-15"  # 14 days after period start


def test_invoice_rejects_an_invalid_billing_period(client, billing_setup):
    sub_id = billing_setup["subscription"]["id"]

    backwards = client.post(
        "/invoices/generate",
        json={"subscription_id": sub_id, "period_start": "2026-03-31", "period_end": "2026-03-01"},
    )
    only_one = client.post("/invoices/generate", json={"subscription_id": sub_id, "period_start": "2026-03-01"})

    assert backwards.status_code == 422
    assert only_one.status_code == 422