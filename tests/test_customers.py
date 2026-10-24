def test_customer_email_must_be_unique(client, make_customer):
    make_customer(email="dup@example.com")

    response = client.post("/customers", json={"name": "Other", "email": "dup@example.com"})

    assert response.status_code == 409


def test_customer_email_uniqueness_ignores_case(client, make_customer):
    make_customer(email="case@example.com")

    response = client.post("/customers", json={"name": "Other", "email": "CASE@Example.com"})

    assert response.status_code == 409


def test_customer_lookup_and_list(client, make_customer):
    customer = make_customer()

    assert client.get(f"/customers/{customer['id']}").json()["email"] == "alice@example.com"
    assert len(client.get("/customers").json()) == 1
    assert client.get("/customers/999").status_code == 404