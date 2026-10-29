from pathlib import Path

import numpy as np
import timm
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms
from transformers import ViTConfig, ViTForImageClassification
from ultralytics import YOLO


RADY4_CLASSES = ["Cataract", "Cherry_eye", "Iris_atrophy", "Healthy"]
RADY6_CLASSES = [
    "Cataract",
    "Cherry_eye",
    "Conjunctivitis",
    "Glaucoma",
    "Healthy",
    "Iris_atrophy",
]
DOG_DISEASE_CLASSES = [
    "Acral Lick Dermatitis",
    "Acute moist dermatitis",
    "Canine atopic dermatitis",
    "Cherry Eye",
    "Ear infections",
    "External Parasites",
    "Folliculitis",
    "Healthy",
    "Leishmaniasis",
    "Lupus",
    "Nuclear sclerosis",
    "Otitis externa",
    "Pruritus",
    "Pyoderma",
    "Rabies",
    "Ringworm",
    "Sarcoptic Mange",
    "Sebaceous adenitis",
    "Seborrhea",
    "Skin tumor",
]


class SEBlock(nn.Module):
    def __init__(self, in_features: int, reduction: int = 16):
        super().__init__()
        mid = max(in_features // reduction, 4)
        self.se = nn.Sequential(
            nn.Linear(in_features, mid, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(mid, in_features, bias=False),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x * self.se(x)


class GeMPooling(nn.Module):
    def __init__(self, p: float = 3.0, eps: float = 1e-6):
        super().__init__()
        self.p = nn.Parameter(torch.ones(1) * p)
        self.eps = eps

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return F.adaptive_avg_pool2d(
            x.clamp(min=self.eps).pow(self.p), (1, 1)
        ).pow(1.0 / self.p)


class EfficientNetClassifier(nn.Module):
    def __init__(self, num_classes: int):
        super().__init__()
        self.backbone = timm.create_model(
            "efficientnet_b3", pretrained=False, num_classes=0, global_pool=""
        )
        in_features = self.backbone.num_features
        self.gem_pool = GeMPooling(p=3.0)
        self.se_block = SEBlock(in_features, reduction=16)
        self.head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(in_features, 512),
            nn.BatchNorm1d(512),
            nn.SiLU(),
            nn.Dropout(p=0.4),
            nn.Linear(512, 256),
            nn.BatchNorm1d(256),
            nn.SiLU(),
            nn.Dropout(p=0.2),
            nn.Linear(256, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        features = self.backbone(x)
        features = self.gem_pool(features).flatten(1)
        features = self.se_block(features).unsqueeze(-1).unsqueeze(-1)
        return self.head(features)


RADY_TRANSFORM = transforms.Compose(
    [
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
        ),
    ]
)


def load_state(path: Path) -> dict[str, torch.Tensor]:
    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    if not isinstance(checkpoint, dict):
        return checkpoint
    return (
        checkpoint.get("model_state_dict")
        or checkpoint.get("state_dict")
        or checkpoint.get("model")
        or checkpoint
    )


def crop_eye(image: Image.Image, box: list[float], padding: float = 0.15) -> Image.Image:
    x1, y1, x2, y2 = box
    pad_x = (x2 - x1) * padding
    pad_y = (y2 - y1) * padding
    left = max(0, int(x1 - pad_x))
    top = max(0, int(y1 - pad_y))
    right = min(image.width, int(x2 + pad_x))
    bottom = min(image.height, int(y2 + pad_y))
    return image.crop((left, top, right, bottom))


class RadyRunner:
    def __init__(self, yolo_path: Path, checkpoint_path: Path, classes: list[str]):
        self.detector = YOLO(yolo_path)
        self.classes = classes
        self.classifier = EfficientNetClassifier(len(classes))
        self.classifier.load_state_dict(load_state(checkpoint_path), strict=True)
        self.classifier.eval()

    def detect(self, image: Image.Image) -> list[dict]:
        result = self.detector(image, conf=0.25, verbose=False, device="cpu")[0]
        if result.boxes is None:
            return []
        return [
            {
                "box": result.boxes.xyxy[index].cpu().tolist(),
                "detection_score": float(result.boxes.conf[index].cpu()),
            }
            for index in range(len(result.boxes))
        ]

    def classify(self, crop: Image.Image) -> dict:
        tensor = RADY_TRANSFORM(crop.convert("RGB")).unsqueeze(0)
        with torch.inference_mode():
            probabilities = torch.softmax(self.classifier(tensor), dim=1)[0]
        scores = {
            name: float(score) for name, score in zip(self.classes, probabilities)
        }
        prediction = max(scores, key=scores.get)
        return {"prediction": prediction, "score": scores[prediction], "scores": scores}


class DogDiseaseRunner:
    def __init__(self, checkpoint_path: Path):
        config = ViTConfig(
            attention_probs_dropout_prob=0.0,
            hidden_act="gelu",
            hidden_dropout_prob=0.0,
            hidden_size=768,
            image_size=224,
            initializer_range=0.02,
            intermediate_size=3072,
            layer_norm_eps=1e-12,
            num_attention_heads=12,
            num_channels=3,
            num_hidden_layers=12,
            patch_size=16,
            qkv_bias=True,
            num_labels=len(DOG_DISEASE_CLASSES),
        )
        self.model = ViTForImageClassification(config)
        self.model.load_state_dict(
            torch.load(checkpoint_path, map_location="cpu", weights_only=True), strict=True
        )
        self.model.eval()

    def classify(self, image: Image.Image) -> dict:
        resized = image.resize((224, 224)).convert("RGB")
        tensor = torch.from_numpy(np.asarray(resized).copy()).permute(2, 0, 1).float()
        with torch.inference_mode():
            probabilities = torch.softmax(self.model(tensor.unsqueeze(0)).logits, dim=1)[0]
        scores = {
            name: float(score) for name, score in zip(DOG_DISEASE_CLASSES, probabilities)
        }
        prediction = max(scores, key=scores.get)
        return {"prediction": prediction, "score": scores[prediction], "scores": scores}
