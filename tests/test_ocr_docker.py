"""Docker 中跑 Tesseract OCR 测试"""
import pytesseract
from PIL import Image

print("Tesseract version:", pytesseract.get_tesseract_version())
img = Image.open("/tests/test_ocr_image.png")
text = pytesseract.image_to_string(img, lang="chi_sim+eng")
print("=== OCR 结果 ===")
print(text.strip())
print("=== OCR 完成 ===")
