import network
from umqtt.simple import MQTTClient
from machine import Pin, time_pulse_us
from time import sleep
import ujson

# ======== CONFIGURAÇÕES ========
NOME_REDE_WIFI = "WIFI_IOT_CFP601"
SENHA_WIFI = "iot@senai601"

BROKER_MQTT = "10.110.22.7"
PORTA_MQTT = 1883
TOPICO_MQTT = "fabrica/contador"
ID_CLIENTE_MQTT = "esp32-contador-ultrassonico"

PIN_TRIG = 33  # saída do sensor ultrassônico
PIN_ECHO = 32  # entrada do sensor ultrassônico

DISTANCIA_DETECCAO_CM = 10  # limite para detectar peça
VELOCIDADE_SOM_CM_US = 0.0343  # velocidade do som em cm/us


def conectar_wifi(nome_rede, senha):
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)
    if not wifi.isconnected():
        print("Conectando ao Wi-Fi...")
        wifi.connect(nome_rede, senha)
        while not wifi.isconnected():
            print(".", end="")
            sleep(0.5)
    print("\n Conectado ao Wi-Fi! IP:", wifi.ifconfig()[0])


def conectar_broker_mqtt(id_cliente, endereco_broker):
    cliente = MQTTClient(id_cliente, endereco_broker, port=PORTA_MQTT)
    while True:
        try:
            cliente.connect()
            print("Conectado ao broker MQTT!")
            return cliente
        except Exception as erro:
            print("Erro ao conectar ao MQTT:", erro)
            sleep(2)


def medir_distancia(trig, echo):
    trig.off()
    sleep(0.002)
    trig.on()
    sleep(0.00001)
    trig.off()

    LIMITE_ESPERA_US = 30000  # tempo máximo de espera pelo pulso
    duracao_pulso = time_pulse_us(echo, 1, LIMITE_ESPERA_US)

    if duracao_pulso < 0:
        return -1  # erro na leitura

    distancia_cm = (duracao_pulso * VELOCIDADE_SOM_CM_US) / 2
    return distancia_cm


def publicar_mensagem_mqtt(cliente, topico, mensagem):
    try:
        cliente.publish(topico, mensagem)
    except Exception as erro:
        print("Erro ao publicar, tentando reconectar...", erro)
        try:
            cliente.connect()
            cliente.publish(topico, mensagem)
            print("Reconectado e publicado com sucesso!")
        except:
            print("Falha ao reconectar ao broker MQTT.")


def main():
    conectar_wifi(NOME_REDE_WIFI, SENHA_WIFI)
    cliente_mqtt = conectar_broker_mqtt(ID_CLIENTE_MQTT, BROKER_MQTT)

    pino_trig = Pin(PIN_TRIG, Pin.OUT)
    pino_echo = Pin(PIN_ECHO, Pin.IN)

    contador_peca_1 = 0
    contador_peca_2 = 0
    contador_peca_3 = 0
    peca_detectada_anteriormente = False

    print("Aguardando inicialização (2s)...")
    sleep(2)

    while True:
        distancia_cm = medir_distancia(pino_trig, pino_echo)

        if distancia_cm < 0:
            print("Erro na leitura do sensor")
        else:
            print(f"Distância medida: {distancia_cm:.2f} cm")
            if distancia_cm <= DISTANCIA_DETECCAO_CM and not peca_detectada_anteriormente:
                # Atualiza contadores
                contador_peca_1 = contador_peca_1 + 1
                contador_peca_2 = contador_peca_2 + 2
                contador_peca_3 = contador_peca_3 + 3
                peca_detectada_anteriormente = True

                vetor_contadores = [contador_peca_1, contador_peca_2, contador_peca_3]
                print(f"Vetor enviado: {vetor_contadores}")

                publicar_mensagem_mqtt(cliente_mqtt, TOPICO_MQTT, ujson.dumps(vetor_contadores))

            elif distancia_cm > DISTANCIA_DETECCAO_CM:
                peca_detectada_anteriormente = False

        sleep(0.2)


if __name__ == "__main__":
    main()
