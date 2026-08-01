import os
import torch
import torch.nn as nn
import pandas as pd
import numpy as np
from PIL import Image

from torchvision import transforms, models
from torch.utils.data import Dataset, DataLoader

from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    accuracy_score
)

import matplotlib.pyplot as plt
import seaborn as sns

# ====================================================
# PATHS
# ====================================================

CSV_PATH = r"C:\AI-Skin-Disease-System\ai_model\dataset\test.csv"

MODEL_PATH = r"C:\AI-Skin-Disease-System\ai_model\saved_models\best_model.pth"

# ====================================================
# CLASS NAMES
# ====================================================

CLASS_NAMES = [
    "akiec",
    "bcc",
    "bkl",
    "df",
    "mel",
    "nv",
    "vasc"
]

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ====================================================
# IMAGE TRANSFORM
# ====================================================

transform = transforms.Compose([
    transforms.Resize((224,224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485,0.456,0.406],
        std=[0.229,0.224,0.225]
    )
])

# ====================================================
# CUSTOM DATASET
# ====================================================

class TestDataset(Dataset):

    def __init__(self, csv_file, transform=None):
        self.df = pd.read_csv(csv_file)
        self.transform = transform

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):

        img_path = self.df.iloc[idx]["image_path"]
        label = int(self.df.iloc[idx]["label"])

        image = Image.open(img_path).convert("RGB")

        if self.transform:
            image = self.transform(image)

        return image, label

# ====================================================
# LOAD DATA
# ====================================================

test_dataset = TestDataset(CSV_PATH, transform)

test_loader = DataLoader(
    test_dataset,
    batch_size=32,
    shuffle=False
)

# ====================================================
# LOAD MODEL
# ====================================================

model = models.efficientnet_b0(weights=None)

in_features = model.classifier[1].in_features

model.classifier = nn.Sequential(
    nn.Dropout(0.3),
    nn.Linear(in_features, 7)
)

model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))

model.to(DEVICE)
model.eval()

print("Model Loaded Successfully")

# ====================================================
# PREDICT
# ====================================================

y_true = []
y_pred = []

with torch.no_grad():

    for images, labels in test_loader:

        images = images.to(DEVICE)

        outputs = model(images)

        preds = torch.argmax(outputs, dim=1)

        y_true.extend(labels.numpy())
        y_pred.extend(preds.cpu().numpy())

# ====================================================
# ACCURACY
# ====================================================

acc = accuracy_score(y_true, y_pred)

print(f"\nAccuracy : {acc*100:.2f}%")

# ====================================================
# CLASSIFICATION REPORT
# ====================================================

print("\nClassification Report\n")

print(
    classification_report(
        y_true,
        y_pred,
        target_names=CLASS_NAMES
    )
)

# ====================================================
# CONFUSION MATRIX
# ====================================================

cm = confusion_matrix(y_true, y_pred)

plt.figure(figsize=(9,7))

sns.heatmap(
    cm,
    annot=True,
    fmt="d",
    cmap="Blues",
    xticklabels=CLASS_NAMES,
    yticklabels=CLASS_NAMES
)

plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("Confusion Matrix")

plt.tight_layout()

plt.savefig("confusion_matrix.png", dpi=300)

plt.show()

print("\nSaved confusion_matrix.png")

# ====================================================
# NORMALIZED MATRIX
# ====================================================

cm_norm = cm.astype(float) / cm.sum(axis=1)[:, np.newaxis]

plt.figure(figsize=(9,7))

sns.heatmap(
    cm_norm,
    annot=True,
    fmt=".2f",
    cmap="Greens",
    xticklabels=CLASS_NAMES,
    yticklabels=CLASS_NAMES
)

plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("Normalized Confusion Matrix")

plt.tight_layout()

plt.savefig("normalized_confusion_matrix.png", dpi=300)

plt.show()

print("Saved normalized_confusion_matrix.png")