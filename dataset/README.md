# Dataset 文件夹结构说明

本文件夹包含用于意图识别训练和用户测试的数据集。以下是文件夹的详细结构和每个文件/子文件夹的说明。

## 文件夹结构
dataset/
│
├── README.md
├── dialogue_with_intent.md
├── patient_profile.md
├── user_test_file_sample.md
├── 45_test_samples_with_no_dialogue/
│   ├── sub_case_1/
│   │   ├── plot_1.txt
│   │   └── concerns_1.txt
│   ├── sub_case_2/
│   │   ├── plot_2.txt
│   │   └── concerns_2.txt
│   └── ...
├── 45_test_samples_with_dialogue/
├── sub_case_1/
│   ├── plot_1.txt
│   ├── profile_1.txt
│   ├── concerns_1.txt
│   └── dialogue_1.txt
├── sub_case_2/
│   ├── plot_2.txt
│   ├── profile_2.txt
│   ├── concerns_2.txt
│   └── dialogue_2.txt
└── ...
## 文件说明

### `README.md`
- 本文件，用于介绍数据集的结构和内容。

### `dialogue_with_intent.md`
- 介绍了意图识别数据集的形式，用于 LSTM 序列预测的原始训练数据。

### `patient_profile.md`
- 用户病例样例。

### `user_test_file_sample.md`
- 用户完整剧本、关心的问题、对话记录样例。

### `45_test_samples_with_no_dialogue/`
- 包含 46 个带有用户剧本和用户需要关心的问题的案例。
- 每个案例存储在一个以 `sub_case_n` 命名的子文件夹中，其中 `n` 是案例编号。
- 每个子文件夹包含以下文件：
  - `plot_n.txt`: 用户剧本。
  - `concerns_n.txt`: 用户关心的问题。

### `45_test_samples_with_dialogue/`
- 包含 45 个带有用户剧本、用户需要关心的问题以及与医生实际产生的对话的案例。
- 每个案例存储在一个以 `sub_case_n` 命名的子文件夹中，其中 `n` 是案例编号。
- 每个子文件夹包含以下文件：
  - `plot_n.txt`: 用户剧本。
  - `profile_n.txt`: 用户病例信息。
  - `concerns_n.txt`: 用户关心的问题。
  - `dialogue_n.txt`: 用户与医生的实际对话记录。

