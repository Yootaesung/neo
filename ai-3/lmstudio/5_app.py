import lmstudio as lms

image_path = 
image_handle = lms.prepare_image(image_path)

model = lms.llm('google/gemma-3-4b')
chat = lms.chat(model)

chat.add_message("Describe this image please", image=image_handle)

prediction = chat.respond(chat)

print(prediction)