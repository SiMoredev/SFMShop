# Файл scripts/lesson_59_jwt_manual.py
import hmac
import hashlib
import json
import base64

SECRET_KEY = "sfmshop-secret"


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _sign(message: str) -> str:
    signature = hmac.new(
        SECRET_KEY.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return _b64url_encode(signature)


def create_token(payload: dict) -> str:
    """Собрать JWT HS256: header.payload.signature"""
    header = {"alg": "HS256", "typ": "JWT"}
    header_part = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_part = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    message = f"{header_part}.{payload_part}"
    return f"{message}.{_sign(message)}"


def verify_token(token: str) -> dict:
    """Проверить подпись и вернуть payload. Если подпись неверна - ValueError."""
    try:
        header_part, payload_part, signature = token.split(".")
    except ValueError:
        raise ValueError("Неверный формат токена")

    message = f"{header_part}.{payload_part}"
    expected = _sign(message)
    if not hmac.compare_digest(expected, signature):
        raise ValueError("Неверная подпись токена")

    return json.loads(_b64url_decode(payload_part))


if __name__ == "__main__":
    token = create_token({"user_id": 7, "email": "ivan@sfmshop.ru", "role": "manager"})
    print(f"Токен (части): {token.count('.') + 1}")

    data = verify_token(token)
    print(f"user_id: {data['user_id']}")
    print(f"email: {data['email']}")
    print(f"role: {data['role']}")

    tampered = token[:-3] + ("aaa" if token[-3:] != "aaa" else "bbb")
    try:
        verify_token(tampered)
    except ValueError as e:
        print(f"Подделка отклонена: {e}")