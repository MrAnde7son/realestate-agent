from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


class Deal(models.Model):
    """Represents a transaction workspace for a single asset."""

    class Stage(models.TextChoices):
        DISCOVERY = "discovery", "Discovery"
        NEGOTIATION = "negotiation", "Negotiation"
        LEGAL = "legal", "Legal"
        FINANCING = "financing", "Financing"
        CLOSING = "closing", "Closing"
        ABANDONED = "abandoned", "Abandoned"

    class Confidentiality(models.TextChoices):
        STANDARD = "standard", "Standard"
        RESTRICTED = "restricted", "Restricted"
        INTERNAL = "internal", "Internal"

    asset = models.ForeignKey(
        "core.Asset",
        on_delete=models.CASCADE,
        related_name="deals",
    )
    stage = models.CharField(
        max_length=20, choices=Stage.choices, default=Stage.DISCOVERY
    )
    deal_lead = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="led_deals",
    )
    confidentiality_level = models.CharField(
        max_length=20,
        choices=Confidentiality.choices,
        default=Confidentiality.STANDARD,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["asset", "stage"]),
            models.Index(fields=["deal_lead"]),
        ]

    def __str__(self) -> str:  # pragma: no cover - debug helper
        return f"Deal #{self.pk} for asset {self.asset_id}"


class PartyRole(models.Model):
    """Connects users or contacts to a deal with a defined responsibility."""

    class Role(models.TextChoices):
        BUYER = "buyer", "Buyer"
        SELLER = "seller", "Seller"
        AGENT = "agent", "Agent"
        LAWYER = "lawyer", "Lawyer"
        ARCHITECT = "architect", "Architect"
        BANKER = "banker", "Banker"
        OTHER = "other", "Other"

    class Side(models.TextChoices):
        BUYER = "buyer", "Buyer"
        SELLER = "seller", "Seller"
        NEUTRAL = "neutral", "Neutral"

    class InvitationStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"

    deal = models.ForeignKey(
        Deal,
        on_delete=models.CASCADE,
        related_name="party_roles",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="party_roles",
    )
    external_contact_json = models.JSONField(default=dict, blank=True)
    role = models.CharField(max_length=16, choices=Role.choices)
    side = models.CharField(max_length=8, choices=Side.choices)
    invitation_status = models.CharField(
        max_length=16,
        choices=InvitationStatus.choices,
        default=InvitationStatus.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["deal", "role"]),
            models.Index(fields=["deal", "side"]),
        ]

    def __str__(self) -> str:  # pragma: no cover - debug helper
        name = (
            self.user.email
            if self.user_id
            else self.external_contact_json.get("name", "External")
        )
        return f"{name} as {self.role} ({self.side})"


class Negotiation(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        PAUSED = "paused", "Paused"
        CLOSED = "closed", "Closed"

    deal = models.ForeignKey(
        Deal,
        on_delete=models.CASCADE,
        related_name="negotiations",
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.OPEN
    )
    visibility_rules = models.JSONField(default=dict, blank=True)
    current_offer = models.ForeignKey(
        "Offer",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="current_for_negotiations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["deal", "status"]),
        ]

    def __str__(self) -> str:  # pragma: no cover - debug helper
        return f"Negotiation #{self.pk} (deal {self.deal_id})"


class Offer(models.Model):
    class FinancingType(models.TextChoices):
        CASH = "cash", "Cash"
        MORTGAGE = "mortgage", "Mortgage"
        MIXED = "mixed", "Mixed"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COUNTERED = "countered", "Countered"
        ACCEPTED = "accepted", "Accepted"
        WITHDRAWN = "withdrawn", "Withdrawn"
        EXPIRED = "expired", "Expired"
        REJECTED = "rejected", "Rejected"

    negotiation = models.ForeignKey(
        Negotiation,
        on_delete=models.CASCADE,
        related_name="offers",
    )
    submitted_by = models.ForeignKey(
        PartyRole,
        on_delete=models.PROTECT,
        related_name="offers_submitted",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    currency = models.CharField(max_length=8, default="ILS")
    financing_type = models.CharField(
        max_length=10, choices=FinancingType.choices
    )
    down_payment_pct = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    conditions_json = models.JSONField(default=dict, blank=True)
    expiration_at = models.DateTimeField()
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.ACTIVE
    )
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["expiration_at", "status"]),
        ]

    def is_expired(self) -> bool:
        return (
            self.status == self.Status.ACTIVE
            and timezone.now() >= self.expiration_at
        )

    def mark_expired(self) -> None:
        if self.status == self.Status.ACTIVE:
            self.status = self.Status.EXPIRED
            self.save(update_fields=["status", "updated_at"])


class OfferAttachment(models.Model):
    offer = models.ForeignKey(
        Offer,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    document = models.ForeignKey(
        "Document",
        on_delete=models.CASCADE,
        related_name="offer_attachments",
    )
    created_at = models.DateTimeField(auto_now_add=True)


class Document(models.Model):
    class Kind(models.TextChoices):
        LEGAL = "legal", "Legal"
        APPRAISAL = "appraisal", "Appraisal"
        ARCHITECT = "architect", "Architect"
        MORTGAGE = "mortgage", "Mortgage"
        GENERIC = "generic", "Generic"

    class Visibility(models.TextChoices):
        DEAL = "deal", "Entire Deal"
        BUYER_SIDE = "buyer_side", "Buyer Side"
        SELLER_SIDE = "seller_side", "Seller Side"
        PUBLIC_LINK = "public_link", "Public Link"

    class Status(models.TextChoices):
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    asset = models.ForeignKey(
        "core.Asset",
        on_delete=models.CASCADE,
        related_name="workspace_documents",
        null=True,
        blank=True,
    )
    deal = models.ForeignKey(
        Deal,
        on_delete=models.CASCADE,
        related_name="documents",
        null=True,
        blank=True,
    )
    kind = models.CharField(
        max_length=20, choices=Kind.choices, default=Kind.GENERIC
    )
    title = models.CharField(max_length=255)
    storage_url = models.URLField(max_length=500)
    hash = models.CharField(max_length=128, blank=True)
    uploader_partyrole = models.ForeignKey(
        PartyRole,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="uploaded_documents",
    )
    visibility_scope = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.DEAL,
    )
    extracted_json = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PROCESSING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["kind", "status"]),
            models.Index(fields=["deal", "visibility_scope"]),
        ]


class AuditLog(models.Model):
    entity_type = models.CharField(max_length=64)
    entity_id = models.CharField(max_length=64)
    action = models.CharField(max_length=64)
    by_partyrole = models.ForeignKey(
        PartyRole,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    diff_json = models.JSONField(default=dict, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    ua = models.CharField(max_length=256, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class LegalCase(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        AWAITING_DOCS = "awaiting_docs", "Awaiting Documents"
        REVIEW = "review", "Review"
        SIGNED = "signed", "Signed"
        CLOSED = "closed", "Closed"

    deal = models.ForeignKey(
        Deal,
        on_delete=models.CASCADE,
        related_name="legal_cases",
    )
    responsible_partyrole = models.ForeignKey(
        PartyRole,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="legal_cases",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.OPEN
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Task(models.Model):
    class Status(models.TextChoices):
        TODO = "todo", "To Do"
        IN_PROGRESS = "in_progress", "In Progress"
        BLOCKED = "blocked", "Blocked"
        DONE = "done", "Done"

    legalcase = models.ForeignKey(
        LegalCase,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tasks",
    )
    deal = models.ForeignKey(
        Deal,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tasks",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    assignee_partyrole = models.ForeignKey(
        PartyRole,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
    )
    due_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.TODO
    )
    checklist_json = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["due_at", "status"]),
        ]


class Appraisal(models.Model):
    class Source(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        EXTERNAL_API = "external_api", "External API"

    asset = models.ForeignKey(
        "core.Asset",
        on_delete=models.CASCADE,
        related_name="appraisals",
    )
    deal = models.ForeignKey(
        Deal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appraisals",
    )
    appraised_value = models.DecimalField(max_digits=12, decimal_places=0)
    valuation_date = models.DateField()
    appraiser_name = models.CharField(max_length=255)
    methodology = models.CharField(max_length=255, blank=True)
    confidence_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    source = models.CharField(
        max_length=20, choices=Source.choices, default=Source.UPLOADED
    )
    variance_vs_nadlaner_pct = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class PlanSet(models.Model):
    class Status(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        REVIEW = "review", "Review"
        APPROVED = "approved", "Approved"

    asset = models.ForeignKey(
        "core.Asset",
        on_delete=models.CASCADE,
        related_name="plan_sets",
    )
    architect_partyrole = models.ForeignKey(
        PartyRole,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="plan_sets",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.UPLOADED
    )
    metadata_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class MortgageApplication(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        PENDING_BANK = "pending_bank", "Pending Bank"
        APPROVED = "approved", "Approved"
        DECLINED = "declined", "Declined"
        EXPIRED = "expired", "Expired"

    deal = models.ForeignKey(
        Deal,
        on_delete=models.CASCADE,
        related_name="mortgage_applications",
    )
    applicant_partyrole = models.ForeignKey(
        PartyRole,
        on_delete=models.CASCADE,
        related_name="mortgage_applications",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    requested_amount = models.DecimalField(max_digits=12, decimal_places=0)
    ltv_pct = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    income_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class MortgageOffer(models.Model):
    class ProductType(models.TextChoices):
        FIXED = "fixed", "Fixed"
        VARIABLE = "variable", "Variable"
        MIXED = "mixed", "Mixed"
        PRIME = "prime", "Prime"
        LINKED_CPI = "linked_cpi", "Linked CPI"
        NON_LINKED = "non_linked", "Non Linked"

    mortgageapplication = models.ForeignKey(
        MortgageApplication,
        on_delete=models.CASCADE,
        related_name="offers",
    )
    lender_name = models.CharField(max_length=255)
    product_type = models.CharField(max_length=20, choices=ProductType.choices)
    term_months = models.PositiveIntegerField()
    rate_pct = models.DecimalField(max_digits=5, decimal_places=2)
    apr_estimate_pct = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    monthly_payment = models.DecimalField(max_digits=10, decimal_places=2)
    fees_total = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    valid_until = models.DateTimeField()
    score = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    source = models.CharField(max_length=20, default="manual")
    raw_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["valid_until", "score"]),
        ]
