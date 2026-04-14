"""Mocked CRM logic inspired by HubSpot campaign workflows."""

from __future__ import annotations

import json
from datetime import datetime

from config import CAMPAIGN_LOGS_FILE, CONTACTS_FILE, PERSONAS, SEGMENT_DEFINITIONS_FILE
from services.campaign_logger import CampaignLogger


class CRMService:
    """Manage local contacts, persona segmentation, and mocked campaign sends."""

    def __init__(self) -> None:
        self.logger = CampaignLogger()

    def run_campaign(self, content: dict) -> dict:
        """Load contacts, upsert them locally, segment by persona, and create campaign logs."""
        contacts = self._load_contacts()
        segment_definitions = self._load_segment_definitions()
        newsletters_by_persona = {
            item["persona"]: item for item in content.get("newsletters", []) if item.get("persona")
        }
        send_date = datetime.utcnow().isoformat() + "Z"

        segments = {persona: [] for persona in PERSONAS}
        refreshed_contacts = []

        for contact in contacts:
            updated_contact = self._upsert_contact(contact)
            refreshed_contacts.append(updated_contact)
            persona = updated_contact.get("persona")
            if persona in segments:
                segments[persona].append(updated_contact)

        self._save_contacts(refreshed_contacts)

        campaign_entries = []
        for persona, segment_contacts in segments.items():
            newsletter = newsletters_by_persona.get(persona, {})
            segment_definition = segment_definitions.get(persona, {})
            entry = {
                "campaign_id": f"campaign-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{persona.lower().split()[0]}",
                "blog_title": content.get("blog_title"),
                "persona": persona,
                "segment_name": segment_definition.get("segment_name", persona),
                "hubspot_list_id": segment_definition.get("hubspot_list_id", "list-generic"),
                "newsletter_version_id": newsletter.get("newsletter_version_id", "newsletter-generic-v1"),
                "send_date": send_date,
                "total_contacts": len(segment_contacts),
                "contact_ids": [contact["id"] for contact in segment_contacts],
                "mock_hubspot_endpoint": self._hubspot_campaign_send_endpoint(),
                "mock_hubspot_list_membership_endpoint": self._hubspot_list_membership_endpoint(),
                "mock_payload_preview": self._build_mock_campaign_payload(persona, newsletter, segment_contacts),
                "mock_response_preview": {
                    "status": "QUEUED",
                    "emailCampaignId": entry_id_placeholder(persona),
                    "audienceListId": segment_definition.get("hubspot_list_id", "list-generic"),
                },
            }
            self.logger.append_record(CAMPAIGN_LOGS_FILE, entry)
            campaign_entries.append(entry)

        return {
            "contacts": refreshed_contacts,
            "segments": segments,
            "campaign_entries": campaign_entries,
        }

    def _load_contacts(self) -> list:
        """Load local contacts from JSON storage."""
        try:
            with CONTACTS_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)
            return data if isinstance(data, list) else []
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_contacts(self, contacts: list) -> None:
        """Persist the updated contacts file."""
        with CONTACTS_FILE.open("w", encoding="utf-8") as file:
            json.dump(contacts, file, indent=2)

    def _load_segment_definitions(self) -> dict:
        """Load sample segment metadata that mirrors how CRM audience lists are usually configured."""
        try:
            with SEGMENT_DEFINITIONS_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)
            if isinstance(data, list):
                return {item["persona"]: item for item in data if isinstance(item, dict) and item.get("persona")}
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return {}

    def _upsert_contact(self, contact: dict) -> dict:
        """Simulate a create or update step similar to a CRM sync."""
        normalized = dict(contact)
        normalized["persona"] = self._normalize_persona(contact.get("persona", ""))
        normalized["last_updated_at"] = datetime.utcnow().isoformat() + "Z"
        normalized["crm_status"] = "updated" if contact.get("email") else "created"
        normalized["lifecycle_stage"] = contact.get("lifecycle_stage", "subscriber")
        normalized["mock_hubspot_contact_endpoint"] = self._hubspot_contact_upsert_endpoint()
        return normalized

    def _normalize_persona(self, persona: str) -> str:
        """Ensure contacts always map into one of the supported personas."""
        for supported_persona in PERSONAS:
            if persona.strip().lower() == supported_persona.lower():
                return supported_persona
        return "Freelance Creative Professional"

    def _hubspot_contact_upsert_endpoint(self) -> str:
        """
        Example real-world HubSpot style endpoint:
        POST /crm/v3/objects/contacts/batch/upsert

        Example payload shape:
        {
          "inputs": [
            {
              "idProperty": "email",
              "id": "sam@brightstudio.com",
              "properties": {
                "firstname": "Sam",
                "lastname": "Lee",
                "jobtitle": "Founder",
                "persona": "Creative Agency Owner",
                "lifecyclestage": "subscriber"
              }
            }
          ]
        }
        """
        return "/crm/v3/objects/contacts/batch/upsert"

    def _hubspot_list_membership_endpoint(self) -> str:
        """
        Example audience membership endpoint style for a marketing sync:
        POST /crm/v3/lists/{listId}/memberships/add

        This is mocked here so the take-home stays local and deterministic.
        """
        return "/crm/v3/lists/{listId}/memberships/add"

    def _hubspot_campaign_send_endpoint(self) -> str:
        """
        Example realistic marketing endpoint style:
        POST /marketing/v3/emails/send

        In a real implementation, the app would authenticate, map persona segments to contact lists,
        and send the selected newsletter template to the corresponding list ID.
        """
        return "/marketing/v3/emails/send"

    def _build_mock_campaign_payload(self, persona: str, newsletter: dict, contacts: list) -> dict:
        """Return a realistic mocked payload preview to show where API logic would plug in."""
        return {
            "message": {
                "subject": newsletter.get("subject_line", f"NovaMind update for {persona}"),
                "previewText": newsletter.get("preview_text", ""),
                "from": {"email": "marketing@novamind.ai", "name": "NovaMind"},
            },
            "segment": {
                "persona": persona,
                "recipientCount": len(contacts),
                "contactIds": [contact["id"] for contact in contacts],
            },
            "content": {
                "newsletterVersionId": newsletter.get("newsletter_version_id", "newsletter-generic-v1"),
                "body": newsletter.get("body", ""),
            },
        }


def entry_id_placeholder(persona: str) -> str:
    """Build a realistic-looking placeholder ID for the mocked send response."""
    return f"hs-email-{persona.lower().replace(' ', '-').replace('at-a-', '').replace('professional', 'pro')}"
