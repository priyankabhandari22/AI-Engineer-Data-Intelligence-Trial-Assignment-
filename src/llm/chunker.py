from bs4 import BeautifulSoup


class TextChunker:
    LIMITS = {
        "gemini": 50000,
        "groq": 6000,
        "deepseek": 40000,
    }

    def chunk(self, text: str, provider: str = "groq") -> list[str]:
        limit = self.LIMITS.get(provider, 6000)
        if len(text) <= limit:
            return [text]

        chunks = []
        paragraphs = text.split("\n\n")
        current = ""

        for para in paragraphs:
            if len(current) + len(para) < limit:
                current += para + "\n\n"
            else:
                if current:
                    chunks.append(current.strip())
                current = para + "\n\n"

        if current:
            chunks.append(current.strip())

        return chunks

    def extract_dense_content(self, html: str, max_chars: int = 6000) -> str:
        soup = BeautifulSoup(html, "html.parser")

        for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        lines = [l for l in text.split("\n") if l.strip()]
        text = "\n".join(lines)

        return text[:max_chars]
