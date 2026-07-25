import json
import time
import logging
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)


class AIDiagnosticsService:
    def __init__(self, tenant):
        self.tenant = tenant
        self.settings = self._load_settings()
        self.client = None

    def _load_settings(self):
        from .models import AISettings
        try:
            return AISettings.objects.get(tenant=self.tenant)
        except AISettings.DoesNotExist:
            return None

    def suggest_icd10(self, diagnosis_text: str, context: dict | None = None) -> dict:
        return self._call_ai(
            prompt=f"Suggest up to 5 ICD-10-CM codes for the following diagnosis. Return as JSON array with 'code', 'description', and 'confidence' fields.\nDiagnosis: {diagnosis_text}",
            response_schema="array",
            suggestion_type="icd10",
        )

    def draft_soap(self, encounter_data: dict) -> dict:
        return self._call_ai(
            prompt=f"Draft a SOAP note from the following encounter data. Return as JSON with 'subjective', 'objective', 'assessment', and 'plan' fields.\nData: {json.dumps(encounter_data)}",
            response_schema="object",
            suggestion_type="soap",
        )

    def check_drug_interaction(self, medications: list[dict]) -> dict:
        med_names = [m.get("drug_name", m.get("name", "unknown")) for m in medications]
        return self._call_ai(
            prompt=f"Check for potential drug-drug interactions among these medications. Return as JSON array with 'drugs', 'severity', 'description' fields.\nMedications: {', '.join(med_names)}",
            response_schema="array",
            suggestion_type="drug_interaction",
        )

    def analyze_symptoms(self, symptoms: str, vitals: dict | None = None) -> dict:
        context = ""
        if vitals:
            context = f"\nVitals: {json.dumps(vitals)}"
        return self._call_ai(
            prompt=f"Analyze these symptoms and provide possible differential diagnoses. Return as JSON with 'differential_diagnoses' array, 'recommended_tests' array, and 'urgency' field.\nSymptoms: {symptoms}{context}",
            response_schema="object",
            suggestion_type="symptom",
        )

    def suggest_treatment_plan(self, diagnosis: str, patient_info: dict | None = None) -> dict:
        context = f"\nPatient: {json.dumps(patient_info)}" if patient_info else ""
        return self._call_ai(
            prompt=f"Suggest a treatment plan for this diagnosis. Return as JSON with 'plan_steps' array, 'medications' array, 'follow_up' string.\nDiagnosis: {diagnosis}{context}",
            response_schema="object",
            suggestion_type="treatment",
        )

    def suggest_cpt_codes(self, procedure_description: str) -> dict:
        return self._call_ai(
            prompt=f"Suggest CPT codes for this procedure. Return as JSON array with 'code', 'description', and 'confidence' fields.\nProcedure: {procedure_description}",
            response_schema="array",
            suggestion_type="cpt",
        )

    def draft_prescription(self, diagnosis: str, patient_info: dict | None = None) -> dict:
        context = f"\nPatient: {json.dumps(patient_info)}" if patient_info else ""
        return self._call_ai(
            prompt=f"Draft a prescription for this diagnosis. Return as JSON with 'drug_name', 'dosage', 'frequency', 'duration', 'notes' fields.\nDiagnosis: {diagnosis}{context}",
            response_schema="object",
            suggestion_type="prescription",
        )

    def _call_ai(self, prompt: str, response_schema: str, suggestion_type: str) -> dict:
        if not self.settings:
            return self._fallback(prompt, suggestion_type, "AI not configured")

        if self.settings.provider == "local" or not self.settings.api_key:
            return self._local_inference(prompt, suggestion_type)

        try:
            return self._call_openai(prompt, response_schema, suggestion_type)
        except Exception as e:
            logger.error(f"AI call failed: {e}")
            return self._fallback(prompt, suggestion_type, str(e))

    def _call_openai(self, prompt: str, response_schema: str, suggestion_type: str) -> dict:
        import openai
        start = time.time()
        openai.api_key = self.settings.api_key
        if self.settings.api_endpoint:
            openai.base_url = self.settings.api_endpoint

        response = openai.chat.completions.create(
            model=self.settings.model,
            messages=[
                {"role": "system", "content": "You are a clinical AI assistant. Provide accurate, evidence-based medical information. Always include confidence levels and disclaimers."},
                {"role": "user", "content": prompt},
            ],
            temperature=self.settings.temperature,
            max_tokens=self.settings.max_tokens,
            response_format={"type": "json_object"},
        )
        latency = int((time.time() - start) * 1000)
        content = response.choices[0].message.content

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            parsed = {"raw": content}

        suggestion = self._save_suggestion(suggestion_type, {"prompt": prompt}, parsed, None, latency)
        return {"id": str(suggestion.id), "suggestion_type": suggestion_type, **parsed}

    def _local_inference(self, prompt: str, suggestion_type: str) -> dict:
        return self._fallback(prompt, suggestion_type, "Offline mode")

    def _fallback(self, prompt: str, suggestion_type: str, reason: str) -> dict:
        fallbacks = {
            "icd10": {"suggestions": [{"code": "R69", "description": "Illness, unspecified", "confidence": 0.3}], "is_fallback": True, "reason": reason},
            "soap": {"subjective": "", "objective": "", "assessment": "", "plan": "", "is_fallback": True, "reason": reason},
            "drug_interaction": [{"drugs": ["Unknown"], "severity": "unknown", "description": "Unable to check: " + reason}],
            "symptom": {"differential_diagnoses": [], "recommended_tests": [], "urgency": "unknown", "is_fallback": True, "reason": reason},
            "treatment": {"plan_steps": [], "medications": [], "follow_up": "", "is_fallback": True, "reason": reason},
            "cpt": [{"code": "99213", "description": "Office consultation", "confidence": 0.3}],
            "prescription": {"drug_name": "", "dosage": "", "frequency": "", "duration": "", "notes": reason},
        }
        data = fallbacks.get(suggestion_type, {"is_fallback": True, "reason": reason})
        suggestion = self._save_suggestion(suggestion_type, {"prompt": prompt}, data, None, 0, is_fallback=True, error=reason)
        return {"id": str(suggestion.id), "suggestion_type": suggestion_type, **data}

    def _save_suggestion(self, suggestion_type, input_data, output_data, confidence, latency_ms, is_fallback=False, error=""):
        from .models import AISuggestion
        suggestion = AISuggestion.objects.create(
            tenant=self.tenant,
            suggestion_type=suggestion_type,
            input_data=input_data,
            output_data=output_data,
            confidence=confidence,
            latency_ms=latency_ms,
            is_fallback=is_fallback,
            error=error,
            model_used=self.settings.model if self.settings else "fallback",
        )
        return suggestion

    def accept_suggestion(self, suggestion_id: str, user) -> dict:
        from .models import AISuggestion
        try:
            suggestion = AISuggestion.objects.for_tenant(self.tenant).get(id=suggestion_id)
            suggestion.accepted = True
            suggestion.accepted_by = user
            suggestion.reviewed_at = time.timezone.now()
            suggestion.save(update_fields=["accepted", "accepted_by", "reviewed_at"])
            self._log_audit(user, "suggestion_accepted", suggestion)
            return {"status": "accepted"}
        except AISuggestion.DoesNotExist:
            return {"status": "error", "error": "Suggestion not found"}

    def reject_suggestion(self, suggestion_id: str, user) -> dict:
        from .models import AISuggestion
        try:
            suggestion = AISuggestion.objects.for_tenant(self.tenant).get(id=suggestion_id)
            suggestion.accepted = False
            suggestion.accepted_by = user
            suggestion.reviewed_at = time.timezone.now()
            suggestion.save(update_fields=["accepted", "accepted_by", "reviewed_at"])
            self._log_audit(user, "suggestion_rejected", suggestion)
            return {"status": "rejected"}
        except AISuggestion.DoesNotExist:
            return {"status": "error", "error": "Suggestion not found"}

    def _log_audit(self, user, action, suggestion=None, details=None):
        from .models import AIAuditLog
        AIAuditLog.objects.create(
            tenant=self.tenant,
            user=user,
            action=action,
            suggestion=suggestion,
            details=details or {},
        )
