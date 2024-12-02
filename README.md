# self-reflective_RAG
Repository for ICDE2025 submission

# Folder Structure Description
This code repository contains the dataset for the intent recognition training and user testing of the paper's system 1 (Medical_HAI), as well as the prompts used in the paper. Below is a detailed structure of the folders and an explanation of each file/subfolder.

## Folder Structure
```
self-reflective_RAG/
│
├── Medical_HAI/
│   ├── chatchat
│   ├── quick_start.md
│   └── ... (other files or subdirectories)
├── dataset/
│   ├── README.md
│   ├── dialogue_with_intent.md
│   ├── patient_profile.md
│   ├── user_test_file_sample.md
│   ├── 45_test_samples_with_no_dialogue/
│   │   ├── sub_case_1/
│   │   │   ├── plot_1.txt
│   │   │   └── concerns_1.txt
│   │   ├── sub_case_2/
│   │   │   ├── plot_2.txt
│   │   │   └── concerns_2.txt
│   │   └── ...
│   ├── 45_test_samples_with_dialogue/
│   │   ├── sub_case_1/
│   │   │   ├── plot_1.txt
│   │   │   ├── profile_1.txt
│   │   │   ├── concerns_1.txt
│   │   │   └── dialogue_1.txt
│   │   ├── sub_case_2/
│   │   │   ├── plot_2.txt
│   │   │   ├── profile_2.txt
│   │   │   ├── concerns_2.txt
│   │   │   └── dialogue_2.txt
│   │   └── ...
│
├── prompt.md
└── README.md

```

# File Description
## Medical_HAI
- chatchat is the library used by the main system.
- quick_start.md introduces how to use the main system.
- Others are various configuration files for the system.

## dataset
### README.md
This file is used to introduce the structure and content of the dataset.
### dialogue_with_intent.md
Introduces the form of the intent recognition dataset, used as the original training data for LSTM sequence prediction.
### patient_profile.md
Sample of patient medical records.
### user_test_file_sample.md
Sample of user's complete script, concerns, and dialogue records.
### 45_test_samples_with_no_dialogue/
Contains 45 cases with user scripts and issues that users are concerned about.
Each case is stored in a subfolder named sub_case_n, where n is the case number.
Each subfolder contains the following files:
- plot_n.txt: User script.
- concerns_n.txt: Issues that users are concerned about.
### 5_test_samples_with_dialogue/
Contains 45 cases with user scripts, issues that users are concerned about, and actual dialogues with doctors.
Each case is stored in a subfolder named sub_case_n, where n is the case number.
Each subfolder contains the following files:
- plot_n.txt: User script.
- profile_n.txt: User medical information.
- concerns_n.txt: Issues that users are concerned about.
- dialogue_n.txt: Actual dialogue records between users and doctors.

## prompt.md
Contains all the prompts used in the paper.