def test_subscription_cannot_be_created_for_inactive_plan(client, make_plan, make_customer):
    plan = make_plan(status="inactive")
    customer = make_customer()

    response = client.post("/subscriptions", json={"customer_id": customer["id"], "plan_id": plan["id"]})

    assert response.status_code == 409
    assert "inactive" in response.json()["detail"]


def test_customer_cannot_have_two_active_subscriptions_to_same_plan(
    client, make_plan, make_customer, make_subscription
):
    plan = make_plan()
    customer = make_customer()
    make_subscription(customer["id"], plan["id"])

    response = client.post("/subscriptions", json={"customer_id": customer["id"], "plan_id": plan["id"]})

    assert response.status_code == 409


def test_customer_can_resubscribe_after_cancelling(client, make_plan, make_customer, make_subscription):
    plan = make_plan()
    customer = make_customer()
    first = make_subscription(customer["id"], plan["id"])

    cancelled = client.patch(f"/subscriptions/{first['id']}/cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert cancelled.json()["cancelled_at"] is not None

    second = client.post("/subscriptions", json={"customer_id": customer["id"], "plan_id": plan["id"]})
    assert second.status_code == 201


def test_cancelling_twice_is_a_conflict(client, make_plan, make_customer, make_subscription):
    plan = make_plan()
    customer = make_customer()
    subscription = make_subscription(customer["id"], plan["id"])

    client.patch(f"/subscriptions/{subscription['id']}/cancel")
    response = client.patch(f"/subscriptions/{subscription['id']}/cancel")

    assert response.status_code == 409


def test_billing_period_follows_plan_cycle(client, make_plan, make_customer, make_subscription):
    customer = make_customer()
    cases = {"monthly": "2026-02-28", "quarterly": "2026-04-30", "yearly": "2027-01-31"}
    for cycle, expected_end in cases.items():
        plan = make_plan(name=cycle, billing_cycle=cycle)
        subscription = make_subscription(customer["id"], plan["id"], start_date="2026-01-31")
        assert subscription["current_period_end"] == expected_end  # month-end is clamped, not overflowed


def test_subscriptions_can_be_filtered(client, make_plan, make_customer, make_subscription):
    plan = make_plan()
    alice = make_customer(email="a@example.com")
    bob = make_customer(email="b@example.com", name="Bob")
    make_subscription(alice["id"], plan["id"])
    make_subscription(bob["id"], plan["id"])

    assert len(client.get("/subscriptions").json()) == 2
    assert len(client.get(f"/subscriptions?customer_id={alice['id']}").json()) == 1