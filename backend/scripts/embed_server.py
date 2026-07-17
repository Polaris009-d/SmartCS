"""
Embedding 微服务 — 长驻进程，模型只加载一次
启动: python embed_server.py --port 8001
"""
import json
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

MODEL_DIR = r"D:\APP\models\embedding\shibing624_text2vec-base-chinese"
_model = None


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_DIR, device="cpu")
        print(f"Model loaded: dim={_model.get_sentence_embedding_dimension()}", flush=True)
    return _model


class EmbedHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        try:
            texts = json.loads(body)
            model = get_model()
            embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
            result = json.dumps([list(map(float, e)) for e in embeddings], ensure_ascii=False)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(result.encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # 静默日志


if __name__ == "__main__":
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8001
    # 启动时预加载模型
    print("Loading model...", flush=True)
    get_model()
    server = HTTPServer(("127.0.0.1", port), EmbedHandler)
    print(f"Embed server running on http://127.0.0.1:{port}", flush=True)
    server.serve_forever()
