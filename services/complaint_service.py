from datetime import datetime
import random

from extensions import db

from models.category import Category
from models.complaint import Complaint

from services.ai_support_service import analyze_complaint
from services.intelligent import IntelligentEngine
from services.history_service import HistoryService


class ComplaintService:
    """Handles complaint submission and intelligent assessment."""

    @staticmethod
    def submit(customer_id, form, meter_number, location):
        try:
            title = form.subject.data.strip()
            description = form.description.data.strip()

            # Run the locally trained AI assessment.
            ai_result = analyze_complaint(description)

            # Match the AI-predicted category to the database.
            category = Category.query.filter_by(
                name=ai_result["category"]
            ).first()

            # Fall back to the customer's selected category.
            if category is None:
                category = Category.query.filter_by(
                    id=form.category.data
                ).first()

            if category is None:
                raise ValueError("Please select a valid complaint category.")

            # Assign recommended priority.
            priority = ai_result["recommended_priority"]

            # Electrical safety emergencies receive Critical priority.
            if ai_result["safety_alert"]:
                priority = "Critical"

            # Retain existing duplicate detection.
            duplicate = IntelligentEngine.is_duplicate(
                customer_id,
                meter_number,
                description
            )

            # Generate complaint number.
            complaint_number = (
                f"CMP-{datetime.now():%Y%m%d%H%M%S}-"
                f"{random.randint(1000, 9999)}"
            )

            # Create complaint.
            complaint = Complaint(
                complaint_number=complaint_number,
                customer_id=customer_id,
                category_id=category.id,
                meter_number=meter_number,
                title=title,
                description=description,
                location=location,
                priority=priority,
                duplicate=duplicate,
                status="Pending"
            )

            db.session.add(complaint)
            db.session.flush()

            # Record AI assessment in complaint history.
            remarks = (
                "Customer submitted complaint. "
                f"AI category: {ai_result['category']}. "
                f"Classification confidence: "
                f"{ai_result['confidence']}%. "
                f"Recommended priority: {priority}. "
                f"Customer sentiment: {ai_result['sentiment']}. "
                f"Safety alert: {ai_result['safety_alert']}."
            )

            HistoryService.log(
                complaint_id=complaint.id,
                action="Complaint Submitted",
                previous_status=None,
                new_status="Pending",
                remarks=remarks,
                performed_by=customer_id
            )

            db.session.commit()

            return (
                True,
                "Complaint submitted successfully. "
                f"AI classification: {category.name}. "
                f"Recommended priority: {priority}."
            )

        except Exception as e:
            db.session.rollback()

            return (
                False,
                f"Failed to submit complaint: {str(e)}"
            )
