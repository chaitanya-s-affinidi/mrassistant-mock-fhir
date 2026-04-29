# Specialty Mapping for Mr Assistant

This document provides the mapping table for Mr Assistant Voice Agent prompt engineering. Use this to map patient's stated "reason for visit" to the correct specialty code for the `list_practitioners_by_specialty` MCP tool.

## Specialty Codes

| Code | Display Name | Description |
|------|--------------|-------------|
| `general-medicine` | General Medicine | Primary care, general health |
| `cardiology` | Cardiology | Heart and cardiovascular |
| `dermatology` | Dermatology | Skin conditions |
| `obgyn` | OB/GYN | Obstetrics and gynecology |
| `orthopedics` | Orthopedics | Bones, joints, muscles |

---

## Mapping Table

### General Medicine (`general-medicine`)

Use for routine care and non-specific symptoms:

| Patient Says | Maps To |
|--------------|---------|
| "annual checkup" | `general-medicine` |
| "regular checkup" | `general-medicine` |
| "routine exam" | `general-medicine` |
| "physical exam" | `general-medicine` |
| "health screening" | `general-medicine` |
| "fever" | `general-medicine` |
| "cold" | `general-medicine` |
| "flu" | `general-medicine` |
| "cough" | `general-medicine` |
| "headache" | `general-medicine` |
| "fatigue" | `general-medicine` |
| "feeling unwell" | `general-medicine` |
| "not feeling well" | `general-medicine` |
| "general consultation" | `general-medicine` |
| "follow-up" | `general-medicine` |
| "vaccination" | `general-medicine` |
| "immunization" | `general-medicine` |

---

### Cardiology (`cardiology`)

Use for heart and cardiovascular concerns:

| Patient Says | Maps To |
|--------------|---------|
| "chest pain" | `cardiology` |
| "heart problems" | `cardiology` |
| "heart issues" | `cardiology` |
| "heart palpitations" | `cardiology` |
| "irregular heartbeat" | `cardiology` |
| "high blood pressure" | `cardiology` |
| "hypertension" | `cardiology` |
| "shortness of breath" | `cardiology` |
| "difficulty breathing" | `cardiology` |
| "dizziness" | `cardiology` |
| "fainting" | `cardiology` |
| "swollen ankles" | `cardiology` |
| "cholesterol" | `cardiology` |
| "cardiac checkup" | `cardiology` |

---

### Dermatology (`dermatology`)

Use for skin-related concerns:

| Patient Says | Maps To |
|--------------|---------|
| "skin rash" | `dermatology` |
| "rash" | `dermatology` |
| "acne" | `dermatology` |
| "pimples" | `dermatology` |
| "eczema" | `dermatology` |
| "psoriasis" | `dermatology` |
| "skin irritation" | `dermatology` |
| "itchy skin" | `dermatology` |
| "dry skin" | `dermatology` |
| "mole check" | `dermatology` |
| "skin growth" | `dermatology` |
| "warts" | `dermatology` |
| "hair loss" | `dermatology` |
| "skin infection" | `dermatology` |
| "hives" | `dermatology` |
| "allergic reaction on skin" | `dermatology` |

---

### OB/GYN (`obgyn`)

Use for women's health and pregnancy:

| Patient Says | Maps To |
|--------------|---------|
| "pregnancy" | `obgyn` |
| "pregnant" | `obgyn` |
| "prenatal checkup" | `obgyn` |
| "prenatal care" | `obgyn` |
| "women's health" | `obgyn` |
| "gynecology" | `obgyn` |
| "menstrual problems" | `obgyn` |
| "period issues" | `obgyn` |
| "irregular periods" | `obgyn` |
| "fertility" | `obgyn` |
| "contraception" | `obgyn` |
| "birth control" | `obgyn` |
| "pap smear" | `obgyn` |
| "breast exam" | `obgyn` |
| "menopause" | `obgyn` |
| "pelvic pain" | `obgyn` |

---

### Orthopedics (`orthopedics`)

Use for bone, joint, and muscle concerns:

| Patient Says | Maps To |
|--------------|---------|
| "broken bone" | `orthopedics` |
| "fracture" | `orthopedics` |
| "joint pain" | `orthopedics` |
| "knee pain" | `orthopedics` |
| "back pain" | `orthopedics` |
| "shoulder pain" | `orthopedics` |
| "hip pain" | `orthopedics` |
| "arthritis" | `orthopedics` |
| "sprain" | `orthopedics` |
| "sports injury" | `orthopedics` |
| "muscle pain" | `orthopedics` |
| "neck pain" | `orthopedics` |
| "spine problems" | `orthopedics` |
| "carpal tunnel" | `orthopedics` |
| "tendonitis" | `orthopedics` |
| "ligament injury" | `orthopedics` |

---

## Prompt Engineering Example

Add this to the Mr Assistant Voice Agent prompt:

```
When the patient states their reason for visit, map it to one of these specialty codes:
- general-medicine: checkups, fever, cold, flu, general health
- cardiology: chest pain, heart issues, blood pressure, palpitations
- dermatology: skin rash, acne, eczema, moles, skin irritation
- obgyn: pregnancy, women's health, menstrual issues, prenatal care
- orthopedics: joint pain, back pain, fractures, sports injuries

Extract the specialty code and store it in {{specialty}} variable.
Then call list_practitioners_by_specialty with specialty={{specialty}}.
```

---

## Fallback Rule

If the patient's reason doesn't clearly match a specialty:
1. **Default to `general-medicine`**
2. The general practitioner can refer to a specialist if needed
