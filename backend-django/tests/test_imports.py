import json

import pytest
from django.core.files.base import ContentFile

from crm.models import Contact, Lead
from core.models import Asset
from imports.models import ImportBatch
from imports.worker import process_csvs


@pytest.mark.django_db
def test_process_customers_creates_contact(django_user_model):
    user = django_user_model.objects.create_user(
        username="user", email="user@example.com", password="pass12345"
    )
    batch = ImportBatch.objects.create(
        source="nadlan_one",
        mode=ImportBatch.MODE_CUSTOMERS,
        tenant=user,
        user=user,
        dry_run=False,
        conflict_policy="update",
    )

    csv_content = (
        "CustomerID,DisplayName,PrimaryPhone,Tags,Email,Comments\n"
        "CUST-1,ישראל כהן,0501234567,משקיע,client@example.com,לקוח ותיק\n"
    )
    batch.customers_csv.save("customers.csv", ContentFile(csv_content))

    results = process_csvs(batch, ImportBatch.MODE_CUSTOMERS, dry_run=False, conflict_policy="update", enable_linking=False)

    contact = Contact.objects.get(external_id="CUST-1")
    assert contact.owner == user
    assert contact.phone == "+972501234567"
    assert contact.external_source == "nadlan_one"
    assert contact.import_batch_id == batch.id
    assert results["summary"]["processed"] == 1
    assert results["summary"]["inserted"] == 1


@pytest.mark.django_db
def test_process_properties_creates_asset_and_links(django_user_model):
    user = django_user_model.objects.create_user(
        username="broker", email="broker@example.com", password="pass12345"
    )
    batch = ImportBatch.objects.create(
        source="nadlan_one",
        mode=ImportBatch.MODE_PROPERTIES,
        tenant=user,
        user=user,
        dry_run=False,
        conflict_policy="update",
        enable_linking=True,
    )

    customers_csv = (
        "CustomerID,DisplayName,PrimaryPhone\n"
        "CUST-10,רות לוי,0507654321\n"
    )
    properties_csv = (
        "PropertyID,City,Street,NumHouse,Phone1,Type,Price\n"
        "PROP-22,תל אביב,דיזנגוף,100,050-765-4321,דירה,2300000\n"
    )
    batch.customers_csv.save("customers.csv", ContentFile(customers_csv))
    batch.properties_csv.save("properties.csv", ContentFile(properties_csv))

    results = process_csvs(batch, ImportBatch.MODE_PROPERTIES, dry_run=False, conflict_policy="update", enable_linking=True)

    contact = Contact.objects.get(external_id="CUST-10")
    asset = Asset.objects.get(external_id="PROP-22")
    assert asset.created_by == user
    assert asset.city == "תל אביב"
    assert asset.external_source == "nadlan_one"
    assert asset.import_batch_id == batch.id
    assert Lead.objects.filter(contact=contact, asset=asset).exists()
    assert results["summary"]["processed"] == 2
    assert results["summary"].get("linked") == 1


@pytest.mark.django_db
def test_process_customers_dry_run_reports_without_creating(django_user_model):
    user = django_user_model.objects.create_user(
        username="dryrun", email="dryrun@example.com", password="pass12345"
    )
    batch = ImportBatch.objects.create(
        source="nadlan_one",
        mode=ImportBatch.MODE_CUSTOMERS,
        tenant=user,
        user=user,
        dry_run=True,
        conflict_policy="update",
    )

    csv_content = (
        "CustomerID,DisplayName,PrimaryPhone\n"
        "DRY-1,בדיקה,0500000000\n"
    )
    batch.customers_csv.save("customers.csv", ContentFile(csv_content))

    results = process_csvs(
        batch,
        ImportBatch.MODE_CUSTOMERS,
        dry_run=True,
        conflict_policy="update",
        enable_linking=False,
    )

    assert Contact.objects.filter(external_id="DRY-1").count() == 0
    assert results["summary"]["processed"] == 1
    assert results["summary"]["inserted"] == 1

    json_report = json.loads(results["json_report"])
    assert json_report[0]["status"] == "inserted"
    assert "Dry run" in json_report[0]["message"]


@pytest.mark.django_db
def test_process_properties_dry_run_respects_conflict_policy(django_user_model):
    user = django_user_model.objects.create_user(
        username="asset-owner", email="asset@example.com", password="pass12345"
    )
    existing_asset = Asset.objects.create(
        scope_type="address",
        city="תל אביב",
        street="דיזנגוף",
        number=50,
        external_source="nadlan_one",
        external_id="PROP-EXISTING",
    )
    existing_asset.created_by = user
    existing_asset.save()

    batch = ImportBatch.objects.create(
        source="nadlan_one",
        mode=ImportBatch.MODE_PROPERTIES,
        tenant=user,
        user=user,
        dry_run=True,
        conflict_policy="skip",
    )

    properties_csv = (
        "PropertyID,City,Street,NumHouse,Phone1,Type,Price\n"
        "PROP-EXISTING,תל אביב,דיזנגוף,50,0507654321,דירה,2000000\n"
    )
    batch.properties_csv.save("properties.csv", ContentFile(properties_csv))

    results = process_csvs(
        batch,
        ImportBatch.MODE_PROPERTIES,
        dry_run=True,
        conflict_policy="skip",
        enable_linking=False,
    )

    assert Asset.objects.filter(external_id="PROP-EXISTING").count() == 1
    assert results["summary"]["processed"] == 1
    assert results["summary"]["skipped"] == 1

    json_report = json.loads(results["json_report"])
    assert json_report[0]["status"] == "skipped"
    assert "Dry run" in json_report[0]["message"]
