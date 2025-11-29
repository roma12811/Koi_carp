from openai import OpenAI


# Для локального тесту використовуємо опис картинки замість Base64
screenshot_description = "A screenshot of wscode"
def define_program():
    prompt = "You are a UI expert. Return the name of programe on screenshot, the current location on screenshot and top 5 possible actions a user can perform in this program. No explanations, no extra text."

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[{
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt},
            ],
        }],
    )
    return response

# print(response.output_text)


