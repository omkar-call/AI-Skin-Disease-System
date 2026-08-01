import torch
from PIL import Image
from torchvision import transforms

from models.model_loader import model, device, CLASS_NAMES

# ==========================================
# Image Preprocessing
# ==========================================

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# ==========================================
# Disease Information
# ==========================================

DISEASES = {
    "akiec": {
        "name": "Actinic Keratoses",
        "risk": "Medium"
    },
    "bcc": {
        "name": "Basal Cell Carcinoma",
        "risk": "Medium"
    },
    "bkl": {
        "name": "Benign Keratosis",
        "risk": "Low"
    },
    "df": {
        "name": "Dermatofibroma",
        "risk": "Low"
    },
    "mel": {
        "name": "Melanoma",
        "risk": "High"
    },
    "nv": {
        "name": "Melanocytic Nevus",
        "risk": "Low"
    },
    "vasc": {
        "name": "Vascular Lesion",
        "risk": "Low"
    }
}

# ==========================================
# Prediction Function
# ==========================================

def predict_image(image_path):
    try:
        print("=" * 50)
        print("Prediction Started")

        print("Step 1: Opening image")
        image = Image.open(image_path).convert("RGB")

        print("Step 2: Preprocessing image")
        image = transform(image)

        print("Step 3: Adding batch dimension")
        image = image.unsqueeze(0).to(device)

        print("Step 4: Model evaluation mode")
        model.eval()

        print("Step 5: Running inference")

        with torch.no_grad():
            outputs = model(image)

        print("Step 6: Calculating probabilities")

        probabilities = torch.softmax(outputs, dim=1)

        confidence, predicted = torch.max(probabilities, dim=1)

        print("Step 7: Preparing result")

        predicted_index = predicted.item()

        class_code = CLASS_NAMES[predicted_index]

        disease = DISEASES[class_code]

        result = {
            "code": class_code,
            "disease": disease["name"],
            "risk": disease["risk"],
            "confidence": round(confidence.item() * 100, 2)
        }

        print("Prediction Completed Successfully")
        print(result)
        print("=" * 50)

        return result

    except Exception as e:
        print("=" * 50)
        print("Prediction Error")
        print(str(e))
        print("=" * 50)
        raise