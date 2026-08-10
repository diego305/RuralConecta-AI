import typing_extensions

def analizar_comentario(texto):
    """
    Analizador NLP Inteligente para el Ámbito Municipal Rural.
    Clasifica automáticamente las solicitudes vecinales en categorías y subcategorías rurales,
    evaluando además el nivel de urgencia y score de sentimiento.
    """
    texto_lower = texto.lower()
    
    categoria = "OTROS"
    subcategoria = "Otros (especificar)"
    prioridad = "BAJA"
    
    # 1. Detección de Categoría y Subcategoría Rural
    if any(word in texto_lower for word in ["camino", "ruta", "pozo", "bache", "ripio", "barro", "zanja", "cuneta", "puente", "baden", "banquina", "huella", "huellas"]):
        categoria = "Red Vial Rural y Caminos"
        prioridad = "ALTA"
        if "intransitable" in texto_lower or "inundado" in texto_lower or "inundacion" in texto_lower or "lluvia" in texto_lower:
            subcategoria = "Caminos Intransitables por Lluvias o Inundación"
        elif "zanja" in texto_lower or "cuneta" in texto_lower or "escurrimiento" in texto_lower:
            subcategoria = "Zanjeo, Cunetas y Escurrimiento de Agua"
        elif "puente" in texto_lower or "baden" in texto_lower:
            subcategoria = "Puentes y Badenes en Mal Estado"
        elif "banquina" in texto_lower or "desmalezado" in texto_lower:
            subcategoria = "Desmalezado de Banquinas y Caminos Rurales"
        else:
            subcategoria = "Baches y Pozos en Caminos de Tierra / Ripio"

    elif any(word in texto_lower for word in ["agua", "tanque", "pozo", "bomba", "canal", "acequia", "cañeria", "caño", "turbia", "riego"]):
        categoria = "Agua Potable Rural y Riego"
        prioridad = "ALTA"
        if "canal" in texto_lower or "acequia" in texto_lower or "riego" in texto_lower:
            subcategoria = "Problemas en Canales de Riego / Acequias"
        elif "bomba" in texto_lower or "motor" in texto_lower:
            subcategoria = "Bomba de Agua Defectuosa o Sin Funcionamiento"
        elif "cañeria" in texto_lower or "caño" in texto_lower or "rotura" in texto_lower:
            subcategoria = "Rotura de Cañería / Red de Agua Rural"
        elif "turbia" in texto_lower or "sucia" in texto_lower or "calidad" in texto_lower:
            subcategoria = "Calidad o Turbidez del Agua"
        else:
            subcategoria = "Falta de Agua en Tanque / Pozo Comunitario"

    elif any(word in texto_lower for word in ["luz", "foco", "oscuro", "oscuridad", "alumbrado", "luminaria", "poste", "cable", "tensión", "transformador", "electrificacion"]):
        categoria = "Electrificación y Alumbrado Rural"
        prioridad = "ALTA"
        if "poste" in texto_lower:
            subcategoria = "Poste Caído o En Peligro"
        elif "cables" in texto_lower or "cable" in texto_lower:
            subcategoria = "Cables Sueltos o Con Riesgo Eléctrico"
        elif "baja tension" in texto_lower or "tension" in texto_lower or "fluctuacion" in texto_lower:
            subcategoria = "Baja Tensión / Fluctuación Eléctrica en Red Rural"
        elif "corte" in texto_lower or "sin luz" in texto_lower:
            subcategoria = "Corte de Luz en Paraje / Zona Rural"
        else:
            subcategoria = "Luminaria Pública Defectuosa en Paraje"

    elif any(word in texto_lower for word in ["basura", "acopio", "basural", "vuelco", "chatarra", "agroquimico", "residuos", "desecho", "mugre", "olor"]):
        categoria = "Residuos y Limpieza Rural"
        prioridad = "MEDIA"
        if "vuelco" in texto_lower or "clandestino" in texto_lower or "camino" in texto_lower:
            subcategoria = "Microbasural o Vuelco Clandestino en Caminos"
        elif "agroquimico" in texto_lower or "chatarra" in texto_lower:
            subcategoria = "Acumulación de Chatarra o Envases Agroquímicos"
        elif "plaza" in texto_lower or "paraje" in texto_lower or "espacio" in texto_lower:
            subcategoria = "Limpieza de Espacios Públicos y Plazas de Parajes"
        else:
            subcategoria = "Retiro de Residuos en Puntos de Acopio Rurales"

    elif any(word in texto_lower for word in ["animal", "vaca", "caballo", "equino", "chancho", "oveja", "plaga", "langosta", "mosquito", "roedor", "vibora", "garrapata", "jabali", "zoonosis", "vacunacion"]):
        categoria = "Zoonosis y Control de Plagas Rurales"
        prioridad = "ALTA"
        if "plaga" in texto_lower or "langosta" in texto_lower or "mosquito" in texto_lower or "roedor" in texto_lower:
            subcategoria = "Plagas Agrícolas / Invertebrados (Langostas, Mosquitos, Roedores)"
        elif "vacunacion" in texto_lower or "castracion" in texto_lower:
            subcategoria = "Vacunación y Castración en Parajes Rurales"
        elif "depredador" in texto_lower or "silvestre" in texto_lower or "puma" in texto_lower:
            subcategoria = "Ataque de Depredadores / Control de Animales Silvestres"
        else:
            subcategoria = "Animales de Granja o Equinos Sueltos en Rutas/Caminos"

    elif any(word in texto_lower for word in ["incendio", "quema", "fuego", "humo", "forestal", "arbol", "rama", "desmonte"]):
        categoria = "Medio Ambiente y Recurso Forestal"
        prioridad = "ALTA"
        if "incendio" in texto_lower or "quema" in texto_lower or "fuego" in texto_lower:
            subcategoria = "Riesgo de Incendio Forestal / Quemas No Autorizadas"
        elif "contaminacion" in texto_lower or "cauce" in texto_lower:
            subcategoria = "Contaminación de Cauces de Agua o Suelos"
        elif "poda" in texto_lower or "cableado" in texto_lower:
            subcategoria = "Poda y Despeje de Cableado en Zonas Rurales"
        else:
            subcategoria = "Caída de Árboles o Ramas Grandes en Caminos"

    elif any(word in texto_lower for word in ["salon", "centro comunitario", "puesto sanitario", "salud", "cartel", "señalizacion", "garita", "colectivo"]):
        categoria = "Infraestructura Comunitaria Rural"
        prioridad = "MEDIA"
        if "señal" in texto_lower or "cartel" in texto_lower:
            subcategoria = "Falta de Señalización en Caminos Rurales"
        elif "garita" in texto_lower or "colectivo" in texto_lower:
            subcategoria = "Paradas de Colectivo Rural en Mal Estado"
        elif "salud" in texto_lower or "puesto sanitario" in texto_lower:
            subcategoria = "Salud Rural / Puesto Sanitario"
        else:
            subcategoria = "Mantenimiento de Centro Comunitario / Salón del Paraje"

    elif any(word in texto_lower for word in ["alambrado", "límite", "limite", "lindero", "vecino", "cultivo", "invasor", "deslinde", "ruido"]):
        categoria = "Convivencia y Mediación Rural"
        prioridad = "BAJA"
        if "agua" in texto_lower or "riego" in texto_lower:
            subcategoria = "Uso Compartido de Agua de Riego"
        elif "cultivo" in texto_lower or "sembrado" in texto_lower:
            subcategoria = "Conflictos por Animales Invasores en Cultivos"
        elif "ruido" in texto_lower or "evento" in texto_lower:
            subcategoria = "Ruidos Molestos o Eventos No Autorizados"
        else:
            subcategoria = "Disputas por Límites de Propiedad o Alambrados"

    # 2. Análisis NLP - Score de Sentimiento y Urgencia
    urgencia_nlp = False
    score_sentimiento = 0.5 # Neutral por defecto (0 a 1)
    
    palabras_urgentes = ["urgente", "peligro", "accidente", "riesgo", "grave", "emergencia", "inundado", "intransitable", "fuego", "sin agua"]
    palabras_negativas = ["harto", "inutiles", "desastre", "verguenza", "indignante", "peor", "bronca", "cansados", "hartos"]
    palabras_agresivas = ["hdp", "choros", "delincuentes", "ladrones", "se la roban toda", "con la de todos", "garcas", "corruptos", "inoperantes", "ñoquis", "vagos", "chantas", "ladris", "estafadores", "robando"]
    
    if any(word in texto_lower for word in palabras_urgentes):
        urgencia_nlp = True
        prioridad = "ALTA"
        
    if any(word in texto_lower for word in palabras_agresivas):
        score_sentimiento = 0.0
    elif any(word in texto_lower for word in palabras_negativas):
        score_sentimiento = 0.1
    elif urgencia_nlp:
        score_sentimiento = 0.3
        
    return {
        "categoria": categoria,
        "subcategoria": subcategoria,
        "prioridad": prioridad,
        "score_sentimiento": score_sentimiento,
        "urgencia_nlp": urgencia_nlp,
        "texto": texto
    }