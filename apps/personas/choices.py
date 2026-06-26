from django.db import models


class TipoCentro(models.TextChoices):
    HOSPITAL_PUBLICO = "hospital_publico", "Hospital Público"
    HOSPITAL_PRIVADO = "hospital_privado", "Hospital Privado"
    CLINICA = "clinica", "Clínica"
    CENTRO_ACOPIO = "centro_acopio", "Centro de Acopio"
    REFUGIO = "refugio", "Refugio"
    PROTECCION_CIVIL = "proteccion_civil", "Protección Civil"
    CRUZ_ROJA = "cruz_roja", "Cruz Roja"
    OTRO = "otro", "Otro"


class EstadoVenezolano(models.TextChoices):
    AMAZONAS = "amazonas", "Amazonas"
    ANZOATEGUI = "anzoategui", "Anzoátegui"
    APURE = "apure", "Apure"
    ARAGUA = "aragua", "Aragua"
    BARINAS = "barinas", "Barinas"
    BOLIVAR = "bolivar", "Bolívar"
    CARABOBO = "carabobo", "Carabobo"
    COJEDES = "cojedes", "Cojedes"
    DELTA_AMACURO = "delta_amacuro", "Delta Amacuro"
    DEPENDENCIAS_FED = "dependencias_fed", "Dependencias Federales"
    DISTRITO_CAPITAL = "distrito_capital", "Distrito Capital"
    FALCON = "falcon", "Falcón"
    GUARICO = "guarico", "Guárico"
    LARA = "lara", "Lara"
    MERIDA = "merida", "Mérida"
    MIRANDA = "miranda", "Miranda"
    MONAGAS = "monagas", "Monagas"
    NUEVA_ESPARTA = "nueva_esparta", "Nueva Esparta"
    PORTUGUESA = "portuguesa", "Portuguesa"
    SUCRE = "sucre", "Sucre"
    TACHIRA = "tachira", "Táchira"
    TRUJILLO = "trujillo", "Trujillo"
    LA_GUAIRA = "la_guaira", "La Guaira (Vargas)"
    YARACUY = "yaracuy", "Yaracuy"
    ZULIA = "zulia", "Zulia"


class NacionalidadCedula(models.TextChoices):
    VENEZOLANO = "V", "Venezolano/a (V)"
    EXTRANJERO = "E", "Extranjero/a (E)"
    PASAPORTE = "P", "Pasaporte"


class Sexo(models.TextChoices):
    MASCULINO = "M", "Masculino"
    FEMENINO = "F", "Femenino"
    NO_ESPECIFICA = "no_especifica", "No especifica"


class TipoSangre(models.TextChoices):
    A_POS = "A+", "A+"
    A_NEG = "A-", "A-"
    B_POS = "B+", "B+"
    B_NEG = "B-", "B-"
    AB_POS = "AB+", "AB+"
    AB_NEG = "AB-", "AB-"
    O_POS = "O+", "O+"
    O_NEG = "O-", "O-"


class EstadoPaciente(models.TextChoices):
    SIN_INFORMACION = "sin_informacion", "Sin información"
    REPORTADO = "reportado", "Reportado"
    EN_TRASLADO = "en_traslado", "En traslado"
    EN_CENTRO_ACOPIO = "en_centro_acopio", "En centro de acopio"
    EN_CENTRO_ATENCION = "en_centro_atencion", "En centro de atención"
    HOSPITALIZADO = "hospitalizado", "Hospitalizado — Estable"
    HOSPITALIZADO_CRITICO = "hospitalizado_critico", "Hospitalizado — Crítico"
    DADO_DE_ALTA = "dado_de_alta", "Dado de alta"
    LOCALIZADO_CON_VIDA = "localizado_con_vida", "Localizado con vida"
    NO_CONFIRMADO = "no_confirmado", "Sin confirmar"
    FALLECIDO = "fallecido", "Fallecido"


class CanalReportante(models.TextChoices):
    WHATSAPP = "whatsapp", "WhatsApp"
    WEB_CHAT = "web_chat", "Web Chat"
    INSTAGRAM = "instagram", "Instagram"
    TELEGRAM = "telegram", "Telegram"
    LLAMADA = "llamada", "Llamada"
    OTRO = "otro", "Otro"


class FuenteInformacion(models.TextChoices):
    HOSPITAL = "hospital", "Hospital"
    PROTECCION_CIVIL = "proteccion_civil", "Protección Civil"
    CRUZ_ROJA = "cruz_roja", "Cruz Roja"
    CENTRO_ACOPIO = "centro_acopio", "Centro de Acopio"
    RED_SOCIAL_VERIFICADA = "red_social_verificada", "Red Social Verificada"
    REPORTE_FAMILIAR = "reporte_familiar", "Reporte Familiar"
    OTRO = "otro", "Otro"


class EstadoEstructural(models.TextChoices):
    DERRUMBADO = "derrumbado", "Derrumbado"
    PARCIALMENTE_DANADO = "parcialmente_danado", "Parcialmente dañado"
    INTEGRIDAD_DELICADA = "integridad_delicada", "Integridad delicada"
    EVACUADO = "evacuado", "Evacuado"
    EN_EVALUACION = "en_evaluacion", "En evaluación"
