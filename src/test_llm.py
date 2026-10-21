from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

#Python busca nuestro .env y carga: OPENAI_API_KEY=... 
#La clave queda disponible para las librerías que la necesiten, pero no necesitamos escribirla dentro del código.

client = OpenAI()

#OpenAI es una clase. Y client es un objeto, una instancia de esa clase.
#Estamos creando el objeto client clasificado como OpenAI. Que utilizaremos para comunicarnos con la API de OpenAI.

# Y ahora hacemos la primera petición. Response será un objeto (una variable) que contendrá la respuesta de la API.

response = client.responses.create(
    model="gpt-5.6-luna",
    input="Reply with exactly this word: CONNECTED"
)

# Ahora, response es un objeto con bastante información, solo queremos que nos devuelva el texto de salida (.output_text)
print(response.output_text)