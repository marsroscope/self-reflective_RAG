# <font style="color:rgb(44, 44, 54);">Prompt</font>
## <font style="color:rgb(44, 44, 54);">Table of Contents</font>
- [Prompt for LLM 1](#Prompt-for-LLM-1)
- [Prompt for LLM 2](#Prompt-for-LLM-2)
- [Prompts for Medical Consultation Chatbot](#Prompts-for-Medical-Consultation-Chatbot)
## Prompt for LLM 1
Intent Recognition, Patient Profile Construction, and Medical Condition Extraction



**1.Intent Recognition**

```plain
# Intent Recognition

## Objective:
Intent recognition task: Given a sequence of conversations between a doctor and a patient, extract the intent of each sentence in the dialogue and generate an intent sequence.

## Constraints:
- For each sentence, you must select the most appropriate one to three intents from the listed labels below. No additional intents should be created.
- The intents must be provided in the order of the dialogue sequence without explanations.

## Available Labels:
- **Doctor-Asking-Symptom**: The doctor inquires about symptoms or follows up on symptoms not clearly stated by the patient.
- **Doctor-Explain-Disease_Characteristics**: The doctor explains the characteristics and symptoms of the disease.
- **Doctor-Explain-Etiology**: The doctor explains the causes of the disease or potential reasons for the current symptoms.
- **Doctor-Asking-Basic_Information**: The doctor inquires about the patient's basic information or behavioral patterns.
- **Doctor-Asking-Existing_Examination_and_Treatment**: The doctor inquires about any existing examinations and treatments the patient has undergone.
- **Doctor-Giving-Drug_Recommendation**: The doctor gives drug recommendations.
- **Doctor-Giving-Medical_Advice**: The doctor provides medical advice or suggests a basic treatment plan based on existing knowledge.
- **Doctor-Giving-Precautions**: The doctor informs the patient about precautions for treatment or medication or offers advice to prevent the condition from worsening.
- **Doctor-Asking-Treatment_Intention**: The doctor inquires about the patient's treatment preferences.
- **Doctor-Diagnose**: The doctor makes a diagnosis based on symptoms.
- **Doctor-Explain-Diagnosis_Result**: The doctor explains the diagnosis result and the reasoning behind it.
- **Doctor-Summarizing_Symptom**: The doctor summarizes symptoms based on patient data.
- **Doctor-Explain-Drug_Effects**: The doctor explains the effects of a drug.
- **Reassure**: The doctor reassures the patient.
- **Confirm**: The doctor confirms information provided by the patient.
- **Greet**: The doctor greets the patient.
- **Patient-Giving-Symptom**: The patient describes symptoms to the doctor.
- **Patient-Consult-Symptom**: The patient inquires about the significance of symptoms.
- **Patient-Asking-Etiology**: The patient asks about the cause of the illness.
- **Patient-Giving-Basic_Information**: The patient provides basic information.
- **Patient-Giving-Existing_Examination_and_Treatment**: The patient informs about the examinations and treatments already undergone.
- **Patient-Asking-Drug_Recommendation**: The patient inquires about drug recommendations.
- **Patient-Asking-Medical_Advice**: The patient asks for a treatment plan.
- **Patient-Asking-Precautions**: The patient inquires about precautions for treatment or medication.
- **Patient-Giving-Treatment_Needs**: The patient informs the doctor of their treatment needs.
- **Patient-Asking-Diagnosis_Result**: The patient asks for the diagnosis result.
- **Patient-Other_Feedback**: Feedback unrelated to disease description.
- **Patient-Confirm**: The patient confirms information provided by the doctor.
- **Patient-Greet**: The patient greets the doctor.

## Procedure:
1. Read the text `{dialogue}`.
2. Analyze the dialogue from the first sentence, identifying the intent of each sentence.
3. Output the intents in their order of occurrence, using a JSON format where the key represents the sentence number, and the value represents the corresponding intents:

```json
{
  "1": ["intent1", "intent2"],
  "2": ["intent1", "intent2"],
  ...
}
```





**<font style="color:rgb(44, 44, 54);">2.Medical Condition Extraction</font>**

```plain
## Task: 
- Assume you are a doctor. Based on the patient's inquiries and your conversation history with the patient, analyze potential diseases the patient might have and generate 1 to 4 suspected disease keywords.
## Requirements:
- Keywords must use medical terminology.
- Be concise.
- Do not exceed four in number.
## Dialogue:
- {dialogue}
## Patient Inquiry:
- {dialogue[-1]}
## Response Format: 
- List the keywords in the following format, providing only the keywords without additional content or symbols, all on one line, up to 4:
keyword1, keyword2, ...
```





**3.<font style="color:rgb(44, 44, 54);">Patient Profile Construction</font>**

```plain
## Goals:
- Case extraction task: Given a sequence of doctor-patient conversations and an existing case record, identify incorrect information in the record and make necessary modifications or add missing content.
## Constraints:
- You should not make subjective judgments or excessive speculation.
- Make inferences based on the facts stated by the doctor and the patient to fill or modify entries.
- If the current facts do not allow for a clear determination for any part of the record, write not available.
- Only output the case record without extra content.
## Doctor-Patient Conversation Sequence:{dialog}
## Existing Case Record:{case_content}
## Format:

Patient Profile
Chief Complaint:
- Primary Symptom Summary: (Use relatively professional terminology from the medical field for each of the patient's symptoms)
- Duration:
Present Illness History:
- (Detailed description of symptoms, including onset time, symptom characteristics, changes, associated symptoms, etc.)
Past Medical History:
- Disease History:
- Surgical History:
- Drug Allergy History:
- Lifestyle Habits:
- Dietary Preferences:
Examinations:
- Physical Examination: (Temperature, pulse, respiration, blood pressure, and other vital signs)
- Auxiliary Examinations: (Results of blood tests, urine tests, stool tests, biochemical tests, imaging tests (X-ray, CT, MRI, etc.), ECG, ultrasound, etc.)
Diagnosis:
- (If a diagnosis is provided by the doctor in the historical conversation, complete and modify this section according to the doctor's diagnosis; if no diagnosis is provided, write 'not available')
Recommendations:
```



## Prompt for LLM2
Fine-Grained Filtering of Resources Based on User Intent Prediction and Generation of Proactive Questions and Question Prediction



**1.Fine-Grained Filtering**

```plain
# Fine-Grained Filtering

## Objective:
Assume you are a physician's assistant capable of accurately filtering reference materials that assist a doctor in diagnosis and treatment. Based on the table of contents of the materials, the conversation, and the patient's questions, select the corresponding titles of the necessary materials for the doctor.

## Materials Table of Contents:
`{len(allarticle_dictionary)}` entries
`{allarticle_dictionary}`

## Conversation Content:
`{dialog_history}`

## Patient's Questions:
`{questionlist}`

## Response Requirements:
- Read the table of contents of the materials.
- Analyze the patient's needs based on the patient's questions and the context of the conversation.
- From the `{len(allarticle_dictionary)}` titles, select the main title (h1) of the entry containing the required content.
- Then, choose the relevant subtitles within that entry. The original titles should not be modified.
- The main title (h1) is mandatory.
- For other titles, if the selected subtitles are fully covered by their parent titles, provide only the parent title; if the selected subtitles are only partially covered by their parent titles, provide only the subtitles.
- Output the original content of the patient's questions and their corresponding materials in a key-value format.

## Output Format:
Output in the following JSON format:
```json
{
    "Original Question 0": ["Main Title 1", "Sub Title 1", "Sub Title 2", "Main Title 2", ...],
    "Original Question 1": ["Main Title 1", "Sub Title 1", "Sub Title 2", "Main Title 2", ...],
    ...
}
```





**2.Predicted Question Generation**

```plain
# Predicted Question Generation
## Objective: 
Based on the conversation content and the requirements, generate {len(patient_intent)} questions that the patient might ask.
Conversation Content:{dialog}
## Requirements:
{patient_intent}
- The generated questions should not duplicate the questions already present in the conversation content.
- Phrase the questions in the patient's voice and number them accordingly to generate {len(patient_intent)} questions.
## Output Format:
Output in JSON format:
```json
{
    "Patient Question 1": "Question Content",
    "Patient Question 2": "Question Content",
    ...
}
```



## Prompts for Medical Consultation Chatbot


```plain
#Medical Consultation

You are a physician. Below is the conversation history between you and the patient. You have access to a medical knowledge retrieval tool that provides reference materials, including relevant information for each question. Based on the patient's condition, you should provide a professional diagnosis, medication treatment advice, or referral suggestions, and respond to potential concerns of the patient. If the patient has a confirmed medical history, use it to provide more accurate answers. If an accurate diagnosis cannot be made, ask the patient for additional information needed. Use conversational language as much as possible.

## Patient's Questions:
{questionlist}

## Reference Materials:
{content}

## Doctor-Patient Conversation History:
{dialog_history}

## Patient's Medical Record:
{case}

## Response Steps:
1. First, read the patient's questions and respond to each question using the reference materials provided for each question. Fill in the responses in the patient question and response section.
2. Next, review the conversation history to determine if the doctor has already provided treatment advice. If the doctor has not given treatment advice or if the treatment advice needs to be updated, identify that treatment advice (or updated treatment advice) is needed. If no treatment advice (or updated treatment advice) is required, fill in `None` in the *diagnosis_and_advice* section.
3. If treatment advice (or updated treatment advice) is needed, first determine if the patient's condition can be diagnosed based on the available information. If a diagnosis is likely not possible due to missing symptoms, tests, etc., assess what additional information is needed from the patient based on the medical record and ask the patient for this information in a physician's tone. Fill this in the *additional_info_needed* section. If the patient's condition can likely be diagnosed, indicate "None" in the *additional_info_needed* section.
4. Finally, if treatment advice (or updated treatment advice) is needed and the patient’s condition can likely be diagnosed, provide professional diagnosis, medication treatment advice, or referral suggestions based on the materials and conversation history. Ensure the response is precise and accurate. Fill the treatment advice in the *diagnosis_and_advice* section.

## Output Format:
Output in JSON format:

```json
{
    "patient_question0": "Your response to this question",
    "patient_question1": "Your response to this question",
    "patient_question2": "Your response to this question",
    "patient_question3": "Your response to this question",
    "diagnosis_and_advice": "Provide treatment advice (or updated treatment advice) if needed; otherwise, fill with None",
    "additional_info_needed": "If the current patient information is likely insufficient for diagnosis, specify additional needed information; otherwise, fill with None"
}
```

