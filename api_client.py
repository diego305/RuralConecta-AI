import requests

def obtener_datos(id_post):
    respuesta = requests.get(f"https://jsonplaceholder.typicode.com/posts/{id_post}")
    #print(respuesta.status_code)
    return respuesta.json()
