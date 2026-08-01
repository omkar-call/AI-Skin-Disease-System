import torch
import torch.nn as nn
from torchvision import models
from pathlib import Path

print("Loading Model Loader...")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Device:", device)

CLASS_NAMES = [
    "akiec",
    "bcc",
    "bkl",
    "df",
    "mel",
    "nv",
    "vasc"
]

BASE_DIR = Path(__file__).resolve().parents[2]

possible_paths = [
    BASE_DIR / "saved_models" / "best_model.pth",
    BASE_DIR / "ai_model" / "saved_models" / "best_model.pth",
]

MODEL_PATH = None

for path in possible_paths:
    print("Checking:", path)
    if path.exists():
        MODEL_PATH = path
        break

if MODEL_PATH is None:
    raise FileNotFoundError("best_model.pth not found.")

print("Found model at:", MODEL_PATH)

print("Creating EfficientNet...")
model = models.efficientnet_b0(weights=None)

model.classifier = nn.Sequential(
    nn.Dropout(0.3),
    nn.Linear(model.classifier[1].in_features, len(CLASS_NAMES))
)

print("Loading weights...")
state_dict = torch.load(MODEL_PATH, map_location=device)

model.load_state_dict(state_dict)

model.to(device)
model.eval()

print("===================================")
print("Model Loaded Successfully!")
print("Model Path:", MODEL_PATH)
print("Device:", device)
print("===================================")