# File: a2a_dspy_openai_app.py  (patched)
from __future__ import annotations
import os, sys, json, argparse
from typing import List, Dict, Optional
import dspy

# --------------------------- CONFIG -----------------------------------------
# === PATCH START: drop-in replacement for your config bits ====================
# Keep all your other code as-is. Replace AppConfig + configure_dspy + health_check.

import dspy
from typing import Optional

class AppConfig:
    """Runtime config for DSPy<->OpenAI; only pass supported args."""
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.3,
        max_tokens: int = 1024,
        api_base: Optional[str] = None,   # e.g. https://api.openai.com/v1 or your proxy
        project: Optional[str] = None     # optional, ignored by most backends
    ):
        import os
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set. Export it or pass --api-key.")
        self.model = model
        self.temperature = float(temperature)
        self.max_tokens = int(max_tokens)
        self.api_base = api_base or os.getenv("OPENAI_BASE_URL")  # optional
        self.project = project or os.getenv("OPENAI_PROJECT")     # optional

def configure_dspy(cfg: AppConfig) -> None:
    """
    Configure DSPy with OpenAI provider.
    IMPORTANT: Only pass args the provider accepts; avoid max_new_tokens/system_prompt/etc.
    """
    provider_key = f"openai/{cfg.model}"  # model encoded here; don't also pass model=...
    lm_kwargs = {
        "api_key": cfg.api_key,
        "temperature": cfg.temperature,
        "max_tokens": cfg.max_tokens,   # ✅ OpenAI supports 'max_tokens'
    }
    if cfg.api_base:
        lm_kwargs["api_base"] = cfg.api_base  # works for OpenAI, Azure-compatible, proxies

    lm = dspy.LM(provider_key, **lm_kwargs)
    dspy.configure(lm=lm)

def health_check() -> None:
    """Minimal call to validate credentials/model early."""
    class _Ping(dspy.Signature):
        msg = dspy.InputField()
        pong = dspy.OutputField()
    dspy.Predict(_Ping)(msg="ping")
# === PATCH END ===============================================================


# --------------------------- YOUR AGENTS (unchanged) ------------------------
class DoctorAssessmentSignature(dspy.Signature):
    patient_complaint = dspy.InputField(desc="Patient's reported symptoms or concerns")
    conversation_history = dspy.InputField(desc="Previous conversation context")
    medical_assessment = dspy.OutputField(desc="Doctor's medical assessment")
    clarifying_questions = dspy.OutputField(desc="Questions to ask the patient")
    diagnosis_confidence = dspy.OutputField(desc="Confidence level 1-10 in current assessment")
    next_action = dspy.OutputField(desc="What should happen next (e.g., 'ask_patient', 'consult_specialist', 'conclude')")

class PatientResponseSignature(dspy.Signature):
    doctor_questions = dspy.InputField(desc="Questions from the doctor")
    patient_actual_condition = dspy.InputField(desc="Patient's actual medical condition (hidden from doctor)")
    conversation_history = dspy.InputField(desc="Previous conversation context")
    patient_response = dspy.OutputField(desc="Patient's answers to doctor's questions")
    additional_symptoms = dspy.OutputField(desc="New symptoms patient mentions")
    emotional_state = dspy.OutputField(desc="Patient's emotional state (anxious/calm/confused)")

class SpecialistConsultSignature(dspy.Signature):
    case_summary = dspy.InputField(desc="Summary of patient case from doctor")
    specific_concern = dspy.InputField(desc="Specific concern or question from doctor")
    specialist_opinion = dspy.OutputField(desc="Specialist's expert opinion")
    additional_tests = dspy.OutputField(desc="Recommended additional tests or examinations")
    risk_assessment = dspy.OutputField(desc="Risk level and urgency assessment")
    agreement_level = dspy.OutputField(desc="Level of agreement with initial assessment (1-10)")

class DoctorAgent(dspy.Module):
    def __init__(self):
        super().__init__()
        self.assess = dspy.ChainOfThought(DoctorAssessmentSignature)
    def forward(self, patient_complaint: str, conversation_history: str = "") -> Dict:
        r = self.assess(patient_complaint=patient_complaint, conversation_history=conversation_history)
        return {
            'medical_assessment': r.medical_assessment,
            'clarifying_questions': r.clarifying_questions,
            'diagnosis_confidence': r.diagnosis_confidence,
            'next_action': r.next_action,
            'agent_type': 'doctor'
        }

class PatientAgent(dspy.Module):
    def __init__(self, actual_condition: str):
        super().__init__()
        self.respond = dspy.ChainOfThought(PatientResponseSignature)
        self.actual_condition = actual_condition
    def forward(self, doctor_questions: str, conversation_history: str = "") -> Dict:
        r = self.respond(doctor_questions=doctor_questions, patient_actual_condition=self.actual_condition, conversation_history=conversation_history)
        return {
            'patient_response': r.patient_response,
            'additional_symptoms': r.additional_symptoms,
            'emotional_state': r.emotional_state,
            'agent_type': 'patient'
        }

class SpecialistAgent(dspy.Module):
    def __init__(self, specialty: str = "General Surgery"):
        super().__init__()
        self.consult = dspy.ChainOfThought(SpecialistConsultSignature)
        self.specialty = specialty
    def forward(self, case_summary: str, specific_concern: str) -> Dict:
        r = self.consult(case_summary=case_summary, specific_concern=specific_concern)
        return {
            'specialist_opinion': r.specialist_opinion,
            'additional_tests': r.additional_tests,
            'risk_assessment': r.risk_assessment,
            'agreement_level': r.agreement_level,
            'specialty': self.specialty,
            'agent_type': 'specialist'
        }

class A2AConversationOrchestrator:
    def __init__(self):
        self.doctor = DoctorAgent()
        self.specialist = SpecialistAgent()
        self.conversation_log: List[Dict] = []
    def run_consultation(self, patient_complaint: str, patient_actual_condition: str, max_turns: int = 5) -> Dict:
        patient = PatientAgent(actual_condition=patient_actual_condition)
        print("=" * 80); print("🏥 A2A MEDICAL CONSULTATION STARTING"); print("=" * 80)
        current_input = patient_complaint; conversation_history = ""
        for turn in range(max_turns):
            print(f"\n{'─'*80}\n📋 TURN {turn+1}\n{'─'*80}\n")
            print("👨‍⚕️ DOCTOR THINKING...")
            doctor_response = self.doctor(patient_complaint=current_input, conversation_history=conversation_history)
            self.conversation_log.append({'turn': turn+1, 'speaker': 'doctor', 'data': doctor_response})
            print(f"\n💭 Assessment: {doctor_response['medical_assessment']}")
            print(f"❓ Questions: {doctor_response['clarifying_questions']}")
            print(f"📊 Confidence: {doctor_response['diagnosis_confidence']}/10")
            print(f"➡️ Next Action: {doctor_response['next_action']}")
            conversation_history += f"\n[Turn {turn+1} - Doctor]: {doctor_response['medical_assessment']} | Questions: {doctor_response['clarifying_questions']}"
            if 'consult' in str(doctor_response['next_action']).lower():
                print("\n🔬 CONSULTING SPECIALIST...")
                specialist_response = self.specialist(case_summary=conversation_history, specific_concern=doctor_response['medical_assessment'])
                self.conversation_log.append({'turn': turn+1, 'speaker': 'specialist', 'data': specialist_response})
                print(f"\n🩺 Specialist Opinion: {specialist_response['specialist_opinion']}")
                print(f"🧪 Tests Recommended: {specialist_response['additional_tests']}")
                print(f"⚠️ Risk Assessment: {specialist_response['risk_assessment']}")
                print(f"🤝 Agreement: {specialist_response['agreement_level']}/10")
                conversation_history += f"\n[Specialist Consult]: {specialist_response['specialist_opinion']}"
            if 'conclude' in str(doctor_response['next_action']).lower():
                print("\n✅ CONSULTATION CONCLUDING"); break
            print("\n🧑 PATIENT RESPONDING...")
            patient_response = patient(doctor_questions=doctor_response['clarifying_questions'], conversation_history=conversation_history)
            self.conversation_log.append({'turn': turn+1, 'speaker': 'patient', 'data': patient_response})
            print(f"\n💬 Response: {patient_response['patient_response']}")
            print(f"🤒 Additional Symptoms: {patient_response['additional_symptoms']}")
            print(f"😟 Emotional State: {patient_response['emotional_state']}")
            current_input = f"{patient_response['patient_response']} {patient_response['additional_symptoms']}".strip()
            conversation_history += f"\n[Turn {turn+1} - Patient]: {patient_response['patient_response']}"
        print("\n"+"="*80); print("✨ CONSULTATION COMPLETE"); print("="*80)
        return {
            'consultation_complete': True,
            'total_turns': len(self.conversation_log),
            'conversation_log': self.conversation_log,
            'final_assessment': doctor_response['medical_assessment'],
            'final_confidence': doctor_response['diagnosis_confidence']
        }
    def export_conversation(self, filename: str = "consultation_log.json") -> None:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.conversation_log, f, indent=2, ensure_ascii=False)
        print(f"📝 Conversation saved to {filename}")

def example_post_operative_consultation(export_path: Optional[str] = None) -> Dict:
    orchestrator = A2AConversationOrchestrator()
    result = orchestrator.run_consultation(
        patient_complaint=("I had an appendectomy 3 days ago and now I have some pain around the incision site. It's getting worse and the area feels warm."),
        patient_actual_condition=("Patient has early surgical site infection with mild fever (100.8°F), increased pain (6/10), redness around incision (2cm diameter), minimal purulent drainage. No signs of sepsis or peritonitis."),
        max_turns=4
    )
    print("\n"+"="*80); print("📊 CONSULTATION SUMMARY"); print("="*80)
    print(f"Total Turns: {result['total_turns']}"); print(f"Final Assessment: {result['final_assessment']}"); print(f"Doctor Confidence: {result['final_confidence']}/10")
    if export_path:
        os.makedirs(os.path.dirname(export_path), exist_ok=True)
        orchestrator.export_conversation(export_path)
    return result

# -------- Researcher ↔ Critic (unchanged) -----------------------------------
class ResearcherSignature(dspy.Signature):
    topic = dspy.InputField(desc="Research topic to investigate")
    critic_feedback = dspy.InputField(desc="Previous feedback from critic agent")
    hypothesis = dspy.OutputField(desc="Proposed research hypothesis")
    methodology = dspy.OutputField(desc="How to test this hypothesis")
    confidence = dspy.OutputField(desc="Confidence in hypothesis (1-10)")

class CriticSignature(dspy.Signature):
    hypothesis = dspy.InputField(desc="Research hypothesis to evaluate")
    methodology = dspy.InputField(desc="Proposed methodology")
    critique = dspy.OutputField(desc="Critical analysis of the hypothesis")
    improvements = dspy.OutputField(desc="Suggested improvements")
    approval_score = dspy.OutputField(desc="Approval rating 1-10 (8+ means approved)")

class ResearcherAgent(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(ResearcherSignature)
    def forward(self, topic: str, critic_feedback: str = "No feedback yet") -> Dict:
        r = self.generate(topic=topic, critic_feedback=critic_feedback)
        return {'hypothesis': r.hypothesis, 'methodology': r.methodology, 'confidence': r.confidence}

class CriticAgent(dspy.Module):
    def __init__(self):
        super().__init__()
        self.evaluate = dspy.ChainOfThought(CriticSignature)
    def forward(self, hypothesis: str, methodology: str) -> Dict:
        r = self.evaluate(hypothesis=hypothesis, methodology=methodology)
        return {'critique': r.critique, 'improvements': r.improvements, 'approval_score': r.approval_score}

def a2a_research_conversation(topic: str, max_iterations: int = 3) -> Dict:
    print("=" * 80); print(f"🔬 A2A RESEARCH CONVERSATION: {topic}"); print("=" * 80)
    researcher, critic = ResearcherAgent(), CriticAgent()
    critic_feedback = "No feedback yet - this is your first attempt"
    final = {'final_hypothesis': None, 'final_methodology': None, 'iterations': 0, 'approved': False}
    for i in range(max_iterations):
        print(f"\n{'─'*80}\n🔄 ITERATION {i+1}\n{'─'*80}\n")
        print("👨‍🔬 RESEARCHER: Generating hypothesis...")
        ro = researcher(topic=topic, critic_feedback=critic_feedback)
        print(f"\n📊 Hypothesis: {ro['hypothesis']}"); print(f"🔬 Methodology: {ro['methodology']}"); print(f"💪 Confidence: {ro['confidence']}/10")
        print(f"\n🎓 CRITIC: Evaluating hypothesis...")
        co = critic(hypothesis=ro['hypothesis'], methodology=ro['methodology'])
        print(f"\n💭 Critique: {co['critique']}"); print(f"💡 Improvements: {co['improvements']}"); print(f"✅ Approval: {co['approval_score']}/10")
        try:
            score = int(''.join(ch for ch in str(co['approval_score']) if ch.isdigit()) or "0")
        except Exception:
            score = 0
        if score >= 8:
            print("\n🎉 APPROVED! Final hypothesis accepted.")
            return {'final_hypothesis': ro['hypothesis'], 'final_methodology': ro['methodology'], 'iterations': i+1, 'approved': True}
        critic_feedback = f"Previous critique: {co['critique']}. Improvements needed: {co['improvements']}"
        final.update(final_hypothesis=ro['hypothesis'], final_methodology=ro['methodology'], iterations=i+1, approved=False)
    print("\n⏰ Max iterations reached. Hypothesis not fully approved."); return final

# --------------------------- CLI --------------------------------------------
def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run DSPy A2A with ChatGPT API.")
    p.add_argument("--api-key", default=None)
    p.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    p.add_argument("--temperature", type=float, default=float(os.getenv("OPENAI_TEMPERATURE", "0.3")))
    p.add_argument("--max-tokens", type=int, default=int(os.getenv("OPENAI_MAX_TOKENS", "1024")))
    p.add_argument("--scenario", choices=["medical", "research"], default="research")
    p.add_argument("--export", default=None)
    p.add_argument("--topic", default="4-day work week impact")
    p.add_argument("--system-prompt", default=None)
    p.add_argument("--api-base", default=None)  # e.g., https://api.openai.com/v1 or Azure endpoint
    p.add_argument("--project", default=None)
    return p

def main(argv: Optional[List[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)
    cfg = AppConfig(
        api_key=args.api_key, model=args.model, temperature=args.temperature,
        max_tokens=args.max_tokens,
        api_base=args.api_base, project=args.project
    )
    configure_dspy(cfg); health_check()
    if args.scenario == "medical":
        result = example_post_operative_consultation(export_path=args.export)
    else:
        result = a2a_research_conversation(topic=args.topic, max_iterations=3)
    print("\n[RESULT]"); print(json.dumps(result, indent=2, ensure_ascii=False)); return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr); sys.exit(1)
