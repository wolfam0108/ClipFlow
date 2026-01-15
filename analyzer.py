class MediaIdentifier:
    def __init__(self, path):
        self.path = path
        self.mp4_signature = b'\x00\x00\x00\x18ftyp'
        self.jpg_signature = b'\xff\xd8\xff'
        self.pdf_signature = b'\x25\x50\x44\x46'

    def check(self):
        try:
            with open(self.path, 'rb') as f:
                signature = f.read(8)
                if signature.startswith(self.jpg_signature):
                    return "это файл JPG"
                elif signature.startswith(self.mp4_signature):
                    return "это файл MP4"
                elif signature.startswith(self.pdf_signature):
                    return "это файл PDF"
                else:
                    return "неизвестный файл"
        except FileNotFoundError:
            return "файл не найден"

test_file = "test_image.jpg" # Укажите имя реально существующего файла
identifier = MediaIdentifier(test_file)

result = identifier.check()
print(f"Результат проверки: {result}")