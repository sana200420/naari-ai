"""
Phase 5 — ASR noise tolerance test for danger gate
Tests that corrupted transcripts of danger phrases still escalate.
Err toward false escalation — never away from it.
"""
import sys
sys.path.insert(0, '.')

# Simulated ASR corruptions of danger phrases
ASR_CORRUPTED_DANGER = [
    # Original: "heavy bleeding" -> ASR corruptions
    "hevy bleding",
    "heavy bleedin",
    "haevy bleeding",
    # Original: "baby not moving"
    "baby not movng",
    "bby not moving",
    "baby nt moving",
    # Original: "can't breathe"
    "cant breath",
    "cant breth",
    "can't brethe",
    # Original: "I want to die"
    "i want die",
    "i wnt to die",
    "want to dy",
    # Original: "fits in pregnancy"
    "fits in pregnacy",
    "fit in pregnancy",
    # Sindhi corrupted
    "رت وهن",   # رت وهڻ corrupted
    "بخر",      # بخار corrupted
]

def test_asr_noise_tolerance():
    from api.safety.danger_gate import run_danger_gate
    
    passed = 0
    failed = []
    
    for phrase in ASR_CORRUPTED_DANGER:
        result = run_danger_gate(phrase)
        if result.escalate:
            passed += 1
        else:
            failed.append(phrase)
    
    print(f"ASR noise tolerance: {passed}/{len(ASR_CORRUPTED_DANGER)} escalated correctly")
    if failed:
        print(f"MISSED (add to keyword bank):")
        for f in failed:
            print(f"  - '{f}'")
    else:
        print("All ASR-corrupted phrases escalated correctly!")
    
    return len(failed) == 0

if __name__ == "__main__":
    test_asr_noise_tolerance()
