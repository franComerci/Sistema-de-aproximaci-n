import machine
from machine import Pin,PWM #son las entradas del buzzer
import micropython
import network#HABILITA LA CONEXION WIFI
import umqtt.simple#biblioteca de mqtt
from umqtt.simple import MQTTClient#importamos el mqtt
import time #para los timesleep
import hcsr04 #biblioteca donde esta el sensor
from hcsr04 import HCSR04 #para el sensor de distancia

# Declaracion Variables de Conexión 
ssid = 'Wokwi-GUEST' # ssid variable del acces-point, al estar en una simulacion de wokwi se le pone el wokwi guest
wifiPassword = '' #el wokwi no tiene clave
mqttServer = 'io.adafruit.com' #es el MQTT server
port = 1883 #puerto siempre para MQTT
user = '' 
password = ''
clientId = 'Celu' #unico y cada placa y proyecto
topic_sens = ''  #topico definido como feed en adafruit, este es de enviar
topic_alarma = '' #topico definido como feed en adafruit, este es de recibir
topic_led = '' #topico definido como feed en adafruit, este es de recibir

# Declaracion Variables
sensorMov = HCSR04(trigger_pin=4, echo_pin=15) # este es el sensor de distancia
ledAlarma = Pin(27,Pin.OUT)
Alarma = PWM(Pin(13), freq=440, duty_u16=32768)
AlarmaActiva = False
Alarma.duty(0)

# Iniciamos Wifi
staIf = network.WLAN(network.STA_IF) #definir el modo statio
staIf.active(True)# este es para prenderlo

# Conectamos al Wifi
staIf.connect(ssid, wifiPassword) #se conecta aca, con el acces point y la contraseña
print("Conectando...") 
while not staIf.isconnected(): #loop infinito donde pregunta si esta conectado o no, devuelve verdadero o falso cuando estas o no conectado, y vas imprimiendo puntos en la pantalla hasta que da true y te aparece conectado
    print(".", end = "")
    time.sleep_ms(100)
print("...Conectado a Wifi...")
print(staIf.ifconfig()) #para ver las ip

# Callback
def funcionCallback(topic, msg): #se ejecuta cada vez que enviamos un topic
    topicRecibido = topic.decode('utf-8') #se decodifican los topicos
    print("Mensaje en topico : " + topicRecibido + " es: " + dato)

    if topicRecibido == topic_alarma and "1" in dato: # topicrec= el que recibimos, el de alarma es el de suscribe y si es 1 en el dato 
        AlarmaActiva = False                          # se apaga la alarma 
        ledAlarma.value(AlarmaActiva)                 
        conexionMQTT.publish(topic_led,str(0))        #pone el string en 0 para demostar que esta apagado el led
        Alarma.duty(0)                                #esto es la frecuencia del buzzer, se empieza en 0

# Conectamos al Broker
try:
    conexionMQTT = MQTTClient(clientId, mqttServer, user=user, password=password, port=int(port))
    conexionMQTT.set_callback(funcionCallback)  #para cualquier mensaje llamamos al callback
    conexionMQTT.connect()                      #se conecta
    conexionMQTT.subscribe(topic_alarma)        #despues de conectarse, te suscribis a los topic
    conexionMQTT.subscribe(topic_led)
    conexionMQTT.subscribe(topic_sens)
    print("...Conectado con el Broker...")

except OSError as e:                #si ocurre un error se manda al except
    print("...Algo falló...")       
    time.sleep(5)
    machine.reset()                 #se resetea el microcontrolador
print("...Leyendo cambios...")

while True:
    try:
        
        conexionMQTT.check_msg() #verifica los mensajes mqtt entrantes
        time.sleep(2)
        distance = sensorMov.distance_cm() #mide la distancia en centimetros, esto se guarda en la variable distance

        if distance <= 200:  #si la distancia es menor a 200cm
            AlarmaActiva = True   # se prende el buzzer
            ledAlarma.value(AlarmaActiva)  #se prende el led
            conexionMQTT.publish(topic_led,str("on"))  #publica el on para el otro dispositivo conectado
            conexionMQTT.publish(topic_sens, str(distance)) #publica la distancia
            Alarma.duty(50) #frecuencia de la alarma esta al 50
        else:
	            conexionMQTT.publish(topic_sens, str(distance))  # se considera que no hay objeto cercano y se publica la distancia

    except OSError as e:  #si ocurre un error se manda al except
        print("Error ",e)
        time.sleep(5)
        machine.reset()   #se resetea el microcontrolador
