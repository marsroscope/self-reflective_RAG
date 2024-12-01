# <font style="color:rgb(44, 44, 54);">Dialogue With Intent</font>
# <font style="color:rgb(44, 44, 54);">Table of Contents</font>
- [Introduce](#Introduce)
- [Before and After Annotation](#Before and After Annotation)
- [Complete Sample](#completeSample)


## Introduce:
| Dialogue Act (Category 1) | Percentage (Category 1) | Dialogue Act (Category 2) | Percentage (Category 2) |
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

```plain
"dialogue": [
    {
        "sentence_id": "1",
        "speaker": "医生",
        "sentence": "你好",
        "symptom_norm": [],
        "symptom_type": [],
        "local_implicit_info": {}
    }
]
```

2.after:

```json
"dialogue": [
    {
        "sentence_id": "1",
        "speaker": "医生",
        "sentence": "你好",
        "dialogue_act": "Greet",
        "symptom_norm": [],
        "symptom_type": [],
        "local_implicit_info": {}
    }
]
```

## <font style="color:rgb(44, 44, 54);">Complete Sample</font>
```json
    "10626355": {
        "diagnosis": "小儿消化不良",
        "self_report": "宝宝拉这个粑粑正常吗不正常的话和吃的奶粉有关吗？现在吃的羊奶粉欧恩贝谢谢医生了",
        "explicit_info": {
            "Symptom": []
        },
        "dialogue": [
            {
                "sentence_id": "1",
                "speaker": "医生",
                "sentence": "你好",
                "dialogue_act": "Greet",
                "symptom_norm": [],
                "symptom_type": [],
                "local_implicit_info": {}
            },
            {
                "sentence_id": "2",
                "speaker": "医生",
                "sentence": "在吗",
                "dialogue_act": "Greet",
                "symptom_norm": [],
                "symptom_type": [],
                "local_implicit_info": {}
            },
            {
                "sentence_id": "3",
                "speaker": "患者",
                "sentence": "这个粑粑正常吗？",
                "dialogue_act": "Patient-Consult-Symptom",
                "symptom_norm": [],
                "symptom_type": [],
                "local_implicit_info": {}
            },
            {
                "sentence_id": "4",
                "speaker": "医生",
                "sentence": "从你发的图片看，这个孩子的大便有点稀，大便当中有粘液",
                "dialogue_act": "Doctor-Summarizing_Symptom",
                "symptom_norm": [
                    "稀便",
                    "大便粘液"
                ],
                "symptom_type": [
                    "1",
                    "1"
                ],
                "local_implicit_info": {
                    "稀便": "1",
                    "大便粘液": "1"
                }
            },
            {
                "sentence_id": "5",
                "speaker": "患者",
                "sentence": "不正常的话和吃的奶粉有关吗",
                "dialogue_act": "Patient-Asking-Etiology",
                "symptom_norm": [],
                "symptom_type": [],
                "local_implicit_info": {}
            },
            {
                "sentence_id": "6",
                "speaker": "医生",
                "sentence": "最主要的问题就是大便当中有粘液，需要进行大便常规的检查",
                "dialogue_act": "Doctor-Explain-Disease_Characteristics",
                "symptom_norm": [
                    "大便粘液"
                ],
                "symptom_type": [
                    "1"
                ],
                "local_implicit_info": {
                    "大便粘液": "1"
                }
            },
            {
                "sentence_id": "7",
                "speaker": "医生",
                "sentence": "跟奶粉关系不是特别的大",
                "dialogue_act": "Doctor-Explain-Etiology",
                "symptom_norm": [],
                "symptom_type": [],
                "local_implicit_info": {}
            },
            {
                "sentence_id": "8",
                "speaker": "医生",
                "sentence": "这个孩子使用这种奶粉多长时间了",
                "dialogue_act": "Doctor-Asking-Basic_Information",
                "symptom_norm": [],
                "symptom_type": [],
                "local_implicit_info": {}
            },
            {
                "sentence_id": "9",
                "speaker": "患者",
                "sentence": "那是怎么回事啊",
                "dialogue_act": "Patient-Asking-Etiology",
                "symptom_norm": [],
                "symptom_type": [],
                "local_implicit_info": {}
            },
            {
                "sentence_id": "10",
                "speaker": "医生",
                "sentence": "现在这个孩子的年龄多大了",
                "dialogue_act": "Doctor-Asking-Basic_Information",
                "symptom_norm": [],
                "symptom_type": [],
                "local_implicit_info": {}
            },
            {
                "sentence_id": "11",
                "speaker": "医生",
                "sentence": "需要考虑消化功能不良所引起的",
                "dialogue_act": "Doctor-Explain-Etiology",
                "symptom_norm": [
                    "消化不良"
                ],
                "symptom_type": [
                    "1"
                ],
                "local_implicit_info": {
                    "消化不良": "1"
                }
            },
            {
                "sentence_id": "12",
                "speaker": "患者",
                "sentence": "刚开始没多久四十天",
                "dialogue_act": "Patient-Giving-Basic_Information",
                "symptom_norm": [],
                "symptom_type": [],
                "local_implicit_info": {}
            },
            {
                "sentence_id": "13",
                "speaker": "医生",
                "sentence": "每天大便几次啊",
                "dialogue_act": "Doctor-Asking-Symptom",
                "symptom_norm": [],
                "symptom_type": [],
                "local_implicit_info": {}
            },
            {
                "sentence_id": "14",
                "speaker": "患者",
                "sentence": "四五次吧",
                "dialogue_act": "Patient-Giving-Symptom",
                "symptom_norm": [],
                "symptom_type": [],
                "local_implicit_info": {}
            },
            {
                "sentence_id": "15",
                "speaker": "医生",
                "sentence": "这个年龄段的孩子出现这种大便，首先应该考虑的就是吃奶过多，另外还需要注意妈妈的饮食",
                "dialogue_act": "Doctor-Explain-Etiology",
                "symptom_norm": [],
                "symptom_type": [],
                "local_implicit_info": {}
            },
            {
                "sentence_id": "16",
                "speaker": "医生",
                "sentence": "有没有进行大便常规的检查",
                "dialogue_act": "Doctor-Asking-Existing_Examination_and_Treatment",
                "symptom_norm": [],
                "symptom_type": [],
                "local_implicit_info": {}
            },
            {
                "sentence_id": "17",
                "speaker": "医生",
                "sentence": "需要进行大便常规的检查，主要是看一下大便当中有没有炎症",
                "dialogue_act": "Doctor-Asking-Existing_Examination_and_Treatment",
                "symptom_norm": [
                    "炎症"
                ],
                "symptom_type": [
                    "2"
                ],
                "local_implicit_info": {
                    "炎症": "2"
                }
            },
            {
                "sentence_id": "18",
                "speaker": "医生",
                "sentence": "如果大便当中没有炎症，那就应该考虑单纯的消化功能不良",
                "dialogue_act": "Doctor-Explain-Etiology",
                "symptom_norm": [
                    "炎症",
                    "消化不良"
                ],
                "symptom_type": [
                    "2",
                    "1"
                ],
                "local_implicit_info": {
                    "炎症": "2",
                    "消化不良": "1"
                }
            },
            {
                "sentence_id": "19",
                "speaker": "患者",
                "sentence": "我这两天吃了海鲜还有辣的",
                "dialogue_act": "Patient-Giving-Symptom",
                "symptom_norm": [],
                "symptom_type": [],
                "local_implicit_info": {}
            },
            {
                "sentence_id": "20",
                "speaker": "患者",
                "sentence": "他每次都要吃不给就哭",
                "dialogue_act": "Patient-Giving-Symptom",
                "symptom_norm": [
                    "哭闹"
                ],
                "symptom_type": [
                    "1"
                ],
                "local_implicit_info": {
                    "哭闹": "1"
                }
            },
            {
                "sentence_id": "21",
                "speaker": "医生",
                "sentence": "可能与这个有关系的",
                "dialogue_act": "Doctor-Explain-Etiology",
                "symptom_norm": [],
                "symptom_type": [],
                "local_implicit_info": {}
            },
            {
                "sentence_id": "22",
                "speaker": "患者",
                "sentence": "我还听到肚子咕咕的",
                "dialogue_act": "Patient-Giving-Symptom",
                "symptom_norm": [
                    "肠鸣音"
                ],
                "symptom_type": [
                    "1"
                ],
                "local_implicit_info": {
                    "肠鸣音": "1"
                }
            },
            {
                "sentence_id": "23",
                "speaker": "医生",
                "sentence": "这就是肠蠕动更快的声音呢",
                "dialogue_act": "Doctor-Explain-Disease_Characteristics",
                "symptom_norm": [
                    "肠鸣音"
                ],
                "symptom_type": [
                    "1"
                ],
                "local_implicit_info": {
                    "肠鸣音": "1"
                }
            },
            {
                "sentence_id": "24",
                "speaker": "医生",
                "sentence": "妈妈尽可能避免吃海鲜辛辣刺激的食物",
                "dialogue_act": "Doctor-Giving-Precautions",
                "symptom_norm": [],
                "symptom_type": [],
                "local_implicit_info": {}
            },
            {
                "sentence_id": "25",
                "speaker": "患者",
                "sentence": "那这个情况我该怎么办要去医院吗",
                "dialogue_act": "Patient-Asking-Medical_Advice",
                "symptom_norm": [],
                "symptom_type": [],
                "local_implicit_info": {}
            },
            {
                "sentence_id": "26",
                "speaker": "医生",
                "sentence": "吃这些食物就会影响奶的质量，就会导致这个孩子出现拉肚子",
                "dialogue_act": "Doctor-Giving-Precautions",
                "symptom_norm": [
                    "腹泻"
                ],
                "symptom_type": [
                    "1"
                ],
                "local_implicit_info": {
                    "腹泻": "1"
                }
            },
            {
                "sentence_id": "27",
                "speaker": "医生",
                "sentence": "这个孩子需要到医院进行大便常规的检查",
                "dialogue_act": "Doctor-Giving-Medical_Advice",
                "symptom_norm": [],
                "symptom_type": [],
                "local_implicit_info": {}
            },
            {
                "sentence_id": "28",
                "speaker": "医生",
                "sentence": "如果大便当中没有炎症，那就应该问题不大的",
                "dialogue_act": "Doctor-Explain-Disease_Characteristics",
                "symptom_norm": [
                    "炎症"
                ],
                "symptom_type": [
                    "2"
                ],
                "local_implicit_info": {
                    "炎症": "2"
                }
            },
            {
                "sentence_id": "29",
                "speaker": "医生",
                "sentence": "可以给孩子口服思密达保护肠粘膜，妈咪爱改善肠道微生态环境",
                "dialogue_act": "Doctor-Giving-Drug_Recommendation",
                "symptom_norm": [],
                "symptom_type": [],
                "local_implicit_info": {}
            },
            {
                "sentence_id": "30",
                "speaker": "患者",
                "sentence": "好的谢谢你医生要对宝宝做什么吗",
                "dialogue_act": "Confirm",
                "symptom_norm": [],
                "symptom_type": [],
                "local_implicit_info": {}
            },
            {
                "sentence_id": "31",
                "speaker": "医生",
                "sentence": "应该给孩子采用少量多次的喂养方式，适当的按摩腹部，改善胃肠功能",
                "dialogue_act": "Doctor-Giving-Medical_Advice",
                "symptom_norm": [],
                "symptom_type": [],
                "local_implicit_info": {}
            },
            {
                "sentence_id": "32",
                "speaker": "患者",
                "sentence": "好的知道了谢谢",
                "dialogue_act": "Confirm",
                "symptom_norm": [],
                "symptom_type": [],
                "local_implicit_info": {}
            }
        ],
        "report": [
            {
                "主诉": "稀便，便中有粘液。",
                "现病史": "患儿出现稀便，每天大便次数为四五次。",
                "辅助检查": "暂缺。",
                "既往史": "不详。",
                "诊断": "消化不良。",
                "建议": "思密达，妈咪爱，粪便常规检查。"
            },
            {
                "主诉": "大便次数增加。",
                "现病史": "患儿大便次数增加，每天4-5次，为稀便，有粘液。",
                "辅助检查": "暂缺。",
                "既往史": "不详。",
                "诊断": "考虑消化功能不良。",
                "建议": "检查大便常规，若无验证，建议服用思密达保护胃肠黏膜，少食多餐，母亲避免食用海鲜辛辣食物。"
            }
        ],
        "implicit_info": {
            "Symptom": {
                "稀便": "1",
                "大便粘液": "1",
                "消化不良": "1",
                "炎症": "2",
                "哭闹": "1",
                "肠鸣音": "1",
                "腹泻": "1"
            }
        }
    }
```



