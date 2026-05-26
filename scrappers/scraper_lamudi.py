from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
import time
import unicodedata
import re
import json

def obtener_informacion(driver):
    informacion = {
        "precios": [],
        "delegacion": [],
        "num habitaciones": [],
        "num duchas": [],
        "estacionamiento": [],
        "tipo": [],
        "area terreno": [],
        "area construida": []
    }

    try:
        precio = driver.find_element(By.CLASS_NAME,"prices-and-fees__price")
        informacion['precios'].append(precio.text)
    except Exception as e:
        informacion['precios'].append(None)

    try:
        delegacion = driver.find_element(By.CLASS_NAME,"view-map__text")
        delegacion = alcaldias(delegacion.text)
        informacion['delegacion'].append(delegacion)
    except Exception as e:
        informacion['delegacion'].append(None)

    
    detalles = driver.find_elements(By.CLASS_NAME,"details-item-value")
    habitaciones = None
    banios = None

    for detalle in detalles:
        data_test = detalle.get_attribute("data-test")
        if data_test == "bedrooms-value":
            habitaciones = detalle.text
        elif data_test == "full-bathrooms-value":
            banios = detalle.text


    informacion['num habitaciones'].append(habitaciones)
    informacion['num duchas'].append(banios)    
    
    estacionamiento = driver.find_elements(By.XPATH,"//div[@class='facilities__item']//span[text()='Estacionamiento']")
    if estacionamiento:
        informacion['estacionamiento'].append(1)
    else:
        informacion['estacionamiento'].append(None)

    try:   
        tipo = driver.find_element(By.CLASS_NAME,"place-features__values")
        informacion['tipo'].append(tipo.text)
    except Exception as e:
        informacion['tipo'].append(None)

    try:    
        area_terreno = driver.find_element(By.CSS_SELECTOR,'[data-test="plot-area-value"]')
        informacion['area terreno'].append(area_terreno.text)
    except Exception as e:
        informacion['area terreno'].append(None)

    try:    
        area_construida = driver.find_element(By.CSS_SELECTOR,'[data-test="floor-area-value"]')
        informacion['area construida'].append(area_construida.text)
    except Exception as e:
        informacion['area construida'].append(None)
        
    print("La informacion del inmueble actual es la siguiente\n",informacion)
    return informacion

def verificar_captcha(driver):
    try:
        # Busca un elemento especifico de captcha (como el iframe de Google reCAPTCHA)
        captcha_element = driver.find_element(By.XPATH, "//iframe[@title='reCAPTCHA']")
        return True  # Si encuentra el elemento, el captcha esta presente
    except NoSuchElementException:
        return False  # Si no lo encuentra, no hay captcha

def scrapear_pagina(driver):

    informacion_completa = {
        "precios": [],
        "delegacion": [],
        "num habitaciones": [],
        "num duchas": [],
        "estacionamiento": [],
        "tipo": [],
        "area terreno": [],
        "area construida": []
    }

    informacion_almacen = {}

    inmuebles = driver.find_elements(By.XPATH, "//a[contains(@href, '/detalle/')]")#Todos los inmuebles de la pagina actual
    enlaces_unicos = {inmueble.get_attribute("href") for inmueble in inmuebles}#Para evitar duplicados


    for href in enlaces_unicos:
        print(f"Vamos a escrapear el inmueble: {href}")
        informacion_almacen['estacionamiento']=[]
        driver.execute_script("window.open(arguments[0]);", href)
        driver.switch_to.window(driver.window_handles[1])
        if(verificar_captcha(driver)):
                time.sleep(60)
        else:
            informacion_almacen = obtener_informacion(driver)
            informacion_completa['precios'].append(informacion_almacen['precios'])
            informacion_completa['delegacion'].append(informacion_almacen['delegacion'])
            informacion_completa['num habitaciones'].append(informacion_almacen['num habitaciones'])
            informacion_completa['num duchas'].append(informacion_almacen['num duchas'])
            informacion_completa['estacionamiento'].append(informacion_almacen['estacionamiento'])
            informacion_completa['tipo'].append(informacion_almacen['tipo'])
            informacion_completa['area terreno'].append(informacion_almacen['area terreno'])
            informacion_completa['area construida'].append(informacion_almacen['area construida'])

        driver.close()
        driver.switch_to.window(driver.window_handles[0])

    return informacion_completa

def generar_id(prefijo, index):
    return f"{prefijo}-{index:06d}"

def alcaldias(direccion):
    palabras = direccion.split()
    palabras = [palabra.strip(",.") for palabra in palabras]
    alcaldias_cdmx = [
        "Álvaro Obregón",
        "Azcapotzalco",
        "Benito Juárez",
        "Coyoacán",
        "Cuajimalpa de Morelos",
        "Cuauhtémoc",
        "Gustavo A. Madero",
        "Iztacalco",
        "Iztapalapa",
        "Magdalena Contreras",
        "Miguel Hidalgo",
        "Milpa Alta",
        "Tláhuac",
        "Tlalpan",
        "Venustiano Carranza",
        "Xochimilco"
    ]
    for alcaldia in alcaldias_cdmx:
        if alcaldia in direccion:
            alcaldia = alcaldia.lower()
            alcaldia = unicodedata.normalize("NFD", alcaldia)
            alcaldia = alcaldia.encode("ascii","ignore").decode("utf-8")
            return alcaldia

def normalizar(cadena):
    string = [cadena][0]
    print(string)
    if string == None:
        return None
    string = string.lower()
    string = unicodedata.normalize("NFD", string)
    string = string.encode("ascii","ignore").decode()
    return string

def extraer_entero(cadena):
    if cadena == None:
        return None
    # Convertir el valor a cadena si no es None
    cadena = str(cadena) 
    # Buscar el número en la cadena
    match = re.search(r'\d+', cadena)
    if match:
        return float(match.group())  # Convertir a entero
    else:
        return None # Si no encuentra un número, devuelve un no disponible
    
def convertir_lista(listas):
    lista_convertida = []
    for lista in listas:
        lista_convertida.append(lista[0])
    return lista_convertida

def obtener_valor(cadena):
    CAMBIO = 20.14
    if cadena == None:
        return None
    else:
        if "USD" in cadena:
            cadena = re.sub(r'[^\d.]','',cadena)
            try:
                valor_dolares = float(cadena)
                valor_pesos = valor_dolares*CAMBIO
                return valor_pesos
            except Exception as e:
                return None
        else:
            cadena = re.sub(r'[^\d.]','',cadena)
            try:
                valor = float(cadena)
                return valor
            except Exception as e:
                return None

def main():
    informacion_completa = {
        "id": [],
        "precios": [],
        "delegacion": [],
        "num habitaciones": [],
        "num duchas": [],
        "estacionamiento": [],
        "tipo": [],
        "area terreno": [],
        "area construida": []
    }

    informacion_almacen = {}

    service = Service(ChromeDriverManager().install())
    option = webdriver.ChromeOptions()
    option.add_argument("--disable-extensions")
    option.add_argument("--disable-popup-blocking")
    option.add_argument("--disable-notifications")
    option.add_argument("--start-maximized")
    option.add_experimental_option("excludeSwitches", ["enable-automation"])
    option.add_experimental_option("useAutomationExtension", False)
    option.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=service, options = option)
    driver.get("https://www.lamudi.com.mx/distrito-federal/for-sale/")
    prefijo = "LAM"
    index = 1

    for i in range(50):
        if(verificar_captcha(driver)):
            time.sleep(60)
        else:
            print(f"Vamos a scrapear la {i+1} página")
            informacion_almacen=scrapear_pagina(driver)
            informacion_almacen['tipo'] = convertir_lista(informacion_almacen['tipo'])
            informacion_almacen['precios'] = convertir_lista(informacion_almacen['precios'])
            for i in range(len(informacion_almacen['precios'])):
                informacion_completa['id'].append(generar_id(prefijo,index))
                index = index + 1
                informacion_completa['precios'].append(obtener_valor(informacion_almacen['precios'][i]))
                informacion_completa['delegacion'].append(informacion_almacen['delegacion'][i])
                informacion_completa['num habitaciones'].append(extraer_entero(informacion_almacen['num habitaciones'][i]))
                informacion_completa['num duchas'].append(extraer_entero(informacion_almacen['num duchas'][i]))
                informacion_completa['estacionamiento'].append(informacion_almacen['estacionamiento'][i])
                informacion_completa['tipo'].append(normalizar(informacion_almacen['tipo'][i]))
                informacion_completa['area terreno'].append(extraer_entero(informacion_almacen['area terreno'][i]))
                informacion_completa['area construida'].append(extraer_entero(informacion_almacen['area construida'][i]))

            # Ir a la siguiente página
            try:
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "pagination-next"))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                driver.execute_script("arguments[0].click();", next_button)
            except Exception as e:
                break

    informacion_completa['delegacion'] = convertir_lista(informacion_completa['delegacion'])
    informacion_completa['estacionamiento'] = convertir_lista(informacion_completa['estacionamiento'])

    with open('DatosLamudi.json','w',encoding="utf-8") as archivo:
        json.dump(informacion_completa,archivo, ensure_ascii=False, indent = 4)


    driver.quit()

    

if __name__ == "__main__":
    main()