# <font style="color:rgb(44, 44, 54);">Dialogue With Intent</font>
## <font style="color:rgb(44, 44, 54);">Table of Contents</font>
- [Introduce](#Introduce)
- [Before and After Annotation](#Before-and-After-Annotation)
- [Complete Sample](#complete-Sample)


## Introduce
| Dialogue Act  | Percentage  | Dialogue Act  | Percentage  |
| --- | --- | --- | --- |
| Asking Symptom | 11.97% | Asking Drug Recommendation | 3.27% |
| Asking Existing Examination and Treatment | 4.04% | Asking Precautions | 1.77% |
| Asking Basic Information | 1.98% | Asking Medical Advice | 1.43% |
| Asking Treatment Intention | 0.20% | Asking Etiology | 0.69% |
| Giving Medical Advice | 6.70% | Asking Diagnosis Result | 0.41% |
| Giving Drug Recommendation | 6.12% | Giving Symptom | 18.07% |
| Giving Precautions | 4.31% | Giving Existing Examination & Treatment | 4.87% |
| Explain Disease Characteristics | 3.90% | Giving Basic Information | 1.56% |
| Explain Etiology | 2.84% | Giving Treatment Needs | 0.81% |
| Explain Drug Effects | 1.21% | Consult Symptom | 2.39% |
| Explain Diagnosis Result | 0.21% | Confirm | 6.48% |
| Reassure | 4.31% | Greet | 1.68% |
| Confirm | 1.72% | Other Feedback | 1.61% |
| Diagnose | 1.29% | Others | 0.20% |
| Greet | 3.25% |  |  |
| Summarizing Symptom | 0.40% |  |  |
| Others | 0.32% |  |  |


## <font style="color:rgb(44, 44, 54);">Before and After Annotation</font>
1.before:

```json
"dialogue": [
    {
        "sentence_id": "1",
        "speaker": "doctor",
        "sentence": "hello"
    }
]
```

2.after:

```json
"dialogue": [
    {
        "sentence_id": "1",
        "speaker": "doctor",
        "sentence": "hello",
        "dialogue_act": "Greet"
    }
]
```

## <font style="color:rgb(44, 44, 54);">Complete Sample</font>
```
Doctor: Hello / 你好                      Greet
Doctor: Are you there? / 在吗              Greet
Patient: Is this stool normal? / 这个粑粑正常吗？   Patient-Consult-Symptom
Doctor: From the picture you sent, the child's stool is a bit loose, and there is mucus in the stool. / 从你发的图片看，这个孩子的大便有点稀，大便当中有粘液   Doctor-Explain Diagnosis Result
Patient: If it's not normal, is it related to the formula I'm feeding? / 不正常的话和吃的奶粉有关吗   Patient-Asking-Etiology
Doctor: The main issue is the presence of mucus in the stool, and a routine stool test is needed. / 最主要的问题就是大便当中有粘液，需要进行大便常规的检查   Doctor-Giving-Medical_Advice
Doctor: It's not particularly related to the formula. / 跟奶粉关系不是特别的大   Doctor-Explain-Etiology
Doctor: How long has this child been using this formula? / 这个孩子使用这种奶粉多长时间了   Doctor-Asking-Basic_Information
Patient: What's going on then? / 那是怎么回事啊   Patient-Asking-Etiology
Doctor: How old is the child now? / 现在这个孩子的年龄多大了   Doctor-Asking-Basic_Information
Doctor: We need to consider it might be caused by poor digestive function. / 需要考虑消化功能不良所引起的   Doctor-Explain-Etiology
Patient: It hasn't been long, about forty days. / 刚开始没多久四十天   Patient-Giving-Basic_Information
Doctor: How many times does the child have a bowel movement each day? / 每天大便几次啊   Doctor-Asking-Symptom
Patient: About four or five times. / 四五次吧   Patient-Giving-Symptom
Doctor: For a child of this age with this type of stool, we should first consider overfeeding, and also pay attention to the mother's diet. / 这个年龄段的孩子出现这种大便，首先应该考虑的就是吃奶过多，另外还需要注意妈妈的饮食Doctor-Explain-Etiology
Doctor: Have you had a routine stool test done? / 有没有进行大便常规的检查   Doctor-Asking-Existing_Examination_and_Treatment
Doctor: A routine stool test is needed, mainly to check for inflammation in the stool. / 需要进行大便常规的检查，主要是看一下大便当中有没有炎症   Doctor-Giving-Medical_Advice
Doctor: If there is no inflammation in the stool, then we should consider simple poor digestive function. / 如果大便当中没有炎症，那就应该考虑单纯的消化功能不良   Doctor-Giving-Medical_Advice
Patient: I've been eating seafood and spicy food these past two days. / 我这两天吃了海鲜还有辣的   Patient-Giving-Symptom
Patient: He cries if he doesn't get fed every time. / 他每次都要吃不给就哭   Patient-Giving-Symptom
Doctor: This might be related. / 可能与这个有关系的   Doctor-Explain-Etiology
Patient: I can also hear gurgling in his stomach. / 我还听到肚子咕咕的   Patient-Giving-Symptom
Doctor: That's the sound of faster bowel movements. / 这就是肠蠕动更快的声音呢   Doctor-Explain-Disease_Characteristics
Doctor: The mother should try to avoid seafood and spicy, stimulating foods. / 妈妈尽可能避免吃海鲜辛辣刺激的食物   Doctor-Giving-Precautions
Patient: So, what should I do in this situation? Do I need to go to the hospital? / 那这个情况我该怎么办要去医院吗   Patient-Asking-Medical_Advice
Doctor: Eating these foods will affect the quality of the milk, leading to the child having diarrhea. / 吃这些食物就会影响奶的质量，就会导致这个孩子出现拉肚子   Doctor-Giving-Precautions
Doctor: The child needs to go to the hospital for a routine stool test. / 这个孩子需要到医院进行大便常规的检查   Doctor-Giving-Medical_Advice
Doctor: If there is no inflammation in the stool, then it should not be a big problem. / 如果大便当中没有炎症，那就应该问题不大的   Doctor-Explain-Disease_Characteristics
Doctor: The child can be given oral Smecta to protect the intestinal mucosa, and Mommy Love to improve the intestinal micro-ecological environment. / 可以给孩子口服思密达保护肠粘膜，妈咪爱改善肠道微生态环境   Doctor-Giving-Drug_Recommendation
Patient: Okay, thank you, doctor. What should I do for the baby? / 好的谢谢你医生要对宝宝做什么吗  Patient-Asking Medical Advice
Doctor: The child should be fed in small amounts multiple times, with appropriate abdominal massage to improve gastrointestinal function. / 应该给孩子采用少量多次的喂养方式，适当的按摩腹部，改善胃肠功能   Doctor-Giving-Medical_Advice
Patient: Okay, I understand, thank you. / 好的知道了谢谢  Confirm


```



