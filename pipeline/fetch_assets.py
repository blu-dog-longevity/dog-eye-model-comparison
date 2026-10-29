import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).parent
USER_AGENT = "BLU-Dog-eye-prototype/0.1"

MODELS = [
    {
        "file": "models/rady/yolo_eye_detection_best.pt",
        "url": "https://huggingface.co/spaces/abdelrahmanrady/dog-eye-diagnosis-AI/resolve/7f02c10e6a2bd916dd109fbd85ac28c2daa65e88/yolo_eye_detection_best.pt",
        "sha256": "e5c9f8223d12c878692ca470a18490920ec27bb3515dcaaf9fe49ab6e4fae6af",
    },
    {
        "file": "models/rady/rady4_efficientnet.pth",
        "url": "https://huggingface.co/spaces/abdelrahmanrady/dog-eye-diagnosis-AI/resolve/7f02c10e6a2bd916dd109fbd85ac28c2daa65e88/efficientnet_b3_se_gem_best.pth",
        "sha256": "52abe206513ef94d40d4421dc29b2cb1d970db7ed78d438aa3ce89ff5236949c",
    },
    {
        "file": "models/rady/rady6_efficientnet.pth",
        "url": "https://huggingface.co/spaces/abdelrahmanrady/AI-Eye-Dog/resolve/de6a686e89122722f9f4ab5030fa3e2c1b9e670a/efficientnet_b3_se_gem_best.pth",
        "sha256": "a22d8ad31e89ddd6b5a6eb878317631253c81e4f0375dcfc13582b0928a0f2d8",
    },
    {
        "file": "models/dog_disease/best_model.pth",
        "url": "https://huggingface.co/spaces/AnishKumbhar/DogDiseasePredictor/resolve/d1f3905a61644a888faadd0657f4d1b158efb755/best_model.pth",
        "sha256": "214824b66bb9988b90dc3e699fcbbf37e5ab05b85657bfae45389b452e6dfd89",
    },
    {
        "file": "models/sam2/sam2.1_hiera_tiny.pt",
        "url": "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_tiny.pt",
        "sha256": "7402e0d864fa82708a20fbd15bc84245c2f26dff0eb43a4b5b93452deb34be69",
    },
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        response = urllib.request.urlopen(request)
    except urllib.error.HTTPError as error:
        if error.code != 429:
            raise
        time.sleep(10)
        response = urllib.request.urlopen(request)
    with response, destination.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            output.write(chunk)


def fetch_images() -> None:
    manifest = json.loads((ROOT / "sources.json").read_text())
    for image in manifest["images"]:
        destination = ROOT / "data/images" / image["file"]
        if not destination.exists():
            print(f"Downloading {image['file']}")
            time.sleep(2)
            download(image["url"], destination)


def fetch_models() -> None:
    for model in MODELS:
        destination = ROOT / model["file"]
        if destination.exists() and sha256(destination) == model["sha256"]:
            continue
        print(f"Downloading {model['file']}")
        download(model["url"], destination)
        actual = sha256(destination)
        if actual != model["sha256"]:
            raise RuntimeError(f"Checksum mismatch for {model['file']}: {actual}")


if __name__ == "__main__":
    fetch_images()
    fetch_models()
