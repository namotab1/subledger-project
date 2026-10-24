def pay(client, invoice_id, amount, status="success", currency="USD", reference="pay_001", **extra):
    return client.post(
        "/payments/record",
        json={
            "invoice_id": invoice_id,
            "amount": amount,
            "currency": currency,
            "status": status,
            "provider_reference": reference,
            **extra,
        },
    )


def test_partial_payment_moves_invoice_to_partially_paid(client, billing_setup):
    invoice_id = billing_setup["invoice"]["id"]

    response = pay(client, invoice_id, "20.00")

    assert response.status_code == 201
    body = response.json()
    assert body["payment_attempt"]["status"] == "success"
    assert body["invoice_status"] == "partially_paid"
    assert body["invoice"]["amount_paid"] == "20.00"
    assert body["invoice"]["amount_remaining"] == "29.99"


def test_full_payment_moves_invoice_to_paid(client, billing_setup):
    invoice_id = billing_setup["invoice"]["id"]

    pay(client, invoice_id, "20.00", reference="pay_a")
    response = pay(client, invoice_id, "29.99", reference="pay_b")

    assert response.json()["invoice_status"] == "paid"
    assert response.json()["invoice"]["amount_remaining"] == "0.00"


def test_successful_payment_cannot_exceed_remaining_amount(client, billing_setup):
    invoice_id = billing_setup["invoice"]["id"]
    pay(client, invoice_id, "40.00", reference="pay_a")

    response = pay(client, invoice_id, "10.00", reference="pay_b")  # only 9.99 left

    assert response.status_code == 422
    assert response.json()["error"] == "business_rule_violation"
    assert client.get(f"/invoices/{invoice_id}").json()["amount_paid"] == "40.00"


def test_failed_payment_does_not_increase_amount_paid(client, billing_setup):
    invoice_id = billing_setup["invoice"]["id"]

    response = pay(client, invoice_id, "49.99", status="failed", failure_reason="Card declined")

    assert response.status_code == 201
    body = response.json()
    assert body["payment_attempt"]["status"] == "failed"
    assert body["payment_attempt"]["failure_reason"] == "Card declined"
    assert body["invoice"]["amount_paid"] == "0.00"
    assert body["invoice_status"] == "issued"


def test_failed_payment_without_reason_gets_a_default_reason(client, billing_setup):
    response = pay(client, billing_setup["invoice"]["id"], "10.00", status="failed")

    assert response.json()["payment_attempt"]["failure_reason"]


def test_paid_invoice_rejects_further_payments(client, billing_setup):
    invoice_id = billing_setup["invoice"]["id"]
    pay(client, invoice_id, "49.99", reference="pay_a")

    response = pay(client, invoice_id, "1.00", reference="pay_b")

    assert response.status_code == 409


def test_payment_currency_must_match_invoice_currency(client, billing_setup):
    response = pay(client, billing_setup["invoice"]["id"], "10.00", currency="EUR")

    assert response.status_code == 422


def test_payment_amount_must_be_positive_and_invoice_must_exist(client, billing_setup):
    assert pay(client, billing_setup["invoice"]["id"], "0").status_code == 422
    assert pay(client, 999, "10.00").status_code == 404


def test_invoice_detail_lists_its_payment_attempts(client, billing_setup):
    invoice_id = billing_setup["invoice"]["id"]
    pay(client, invoice_id, "10.00", status="failed", reference="pay_a")
    pay(client, invoice_id, "10.00", reference="pay_b")

    detail = client.get(f"/invoices/{invoice_id}").json()

    assert [a["status"] for a in detail["payment_attempts"]] == ["failed", "success"]