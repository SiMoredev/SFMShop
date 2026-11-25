
def reverse(text: str) -> str:
    words = {}
    for item in text.split():
        word = item.rstrip(",.!?")
        words[word.lower()] = item[len(word):]

    result = " ".join(w + m for w, m in zip(reversed(words), words.values())).capitalize()
    return result

print(reverse("Hey, hello world!"))
print(reverse("Hi, my dear old world!"))
print(reverse("One two, three."))