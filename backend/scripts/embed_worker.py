"""
Embedding Worker — 由 conda Python 独立运行，加载本地模型
使用方法: conda\python.exe embed_worker.py < texts.json > embeddings.json
"""
import json
import sys
import warnings
import os
warnings.filterwarnings("ignore")
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

MODEL_DIR = r"D:\APP\models\embedding\shibing624_text2vec-base-chinese"
_model = None


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_DIR, device="cpu")
    return _model


def main():
    texts = json.loads(sys.stdin.read())
    if not texts:
        print(json.dumps([]))
        return

    model = get_model()
    embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    print(json.dumps([list(map(float, e)) for e in embeddings]))


if __name__ == "__main__":
    main()
